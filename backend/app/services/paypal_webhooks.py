from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from app.models.billing import BillingEvent, BillingSubscription
from app.models.user import User
from app.services.billing import PAID_PRO_PLAN

PAYPAL_SANDBOX_API_BASE = "https://api-m.sandbox.paypal.com"
PAYPAL_LIVE_API_BASE = "https://api-m.paypal.com"

PAYPAL_ACTIVE_EVENTS = {
    "BILLING.SUBSCRIPTION.ACTIVATED",
    "PAYMENT.SALE.COMPLETED",
    "PAYMENT.CAPTURE.COMPLETED",
    "CHECKOUT.ORDER.COMPLETED",
}

PAYPAL_CANCEL_EVENTS = {
    "BILLING.SUBSCRIPTION.CANCELLED",
    "BILLING.SUBSCRIPTION.CANCELED",
    "BILLING.SUBSCRIPTION.SUSPENDED",
}

PAYPAL_REVIEW_EVENTS = {
    "PAYMENT.SALE.REFUNDED",
    "PAYMENT.SALE.REVERSED",
    "PAYMENT.CAPTURE.REFUNDED",
    "CUSTOMER.DISPUTE.CREATED",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PayPalWebhookVerificationError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _paypal_api_base() -> str:
    env = os.getenv("PAYPAL_ENV", "sandbox").strip().lower()
    return PAYPAL_LIVE_API_BASE if env == "live" else PAYPAL_SANDBOX_API_BASE


def _verification_disabled_for_tests() -> bool:
    disabled = os.getenv("PAYPAL_WEBHOOK_VERIFY_DISABLED", "").strip().lower()
    return disabled in {"1", "true", "yes"} and bool(os.getenv("PYTEST_CURRENT_TEST"))


def _required_header(headers: Headers, name: str) -> str:
    value = headers.get(name)
    if not value:
        raise PayPalWebhookVerificationError(f"Missing PayPal webhook header: {name}")
    return value


def _get_paypal_access_token() -> str:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise PayPalWebhookVerificationError("PayPal client credentials are not configured.")

    response = httpx.post(
        f"{_paypal_api_base()}/v1/oauth2/token",
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()

    token = response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise PayPalWebhookVerificationError("PayPal access token response was invalid.")

    return token


def verify_paypal_webhook_signature(
    *,
    headers: Headers,
    webhook_event: dict[str, Any],
) -> bool:
    if _verification_disabled_for_tests():
        return True

    webhook_id = os.getenv("PAYPAL_WEBHOOK_ID")
    if not webhook_id:
        raise PayPalWebhookVerificationError("PAYPAL_WEBHOOK_ID is not configured.")

    token = _get_paypal_access_token()

    verification_payload = {
        "auth_algo": _required_header(headers, "paypal-auth-algo"),
        "cert_url": _required_header(headers, "paypal-cert-url"),
        "transmission_id": _required_header(headers, "paypal-transmission-id"),
        "transmission_sig": _required_header(headers, "paypal-transmission-sig"),
        "transmission_time": _required_header(headers, "paypal-transmission-time"),
        "webhook_id": webhook_id,
        "webhook_event": webhook_event,
    }

    response = httpx.post(
        f"{_paypal_api_base()}/v1/notifications/verify-webhook-signature",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=verification_payload,
        timeout=15,
    )
    response.raise_for_status()

    return response.json().get("verification_status") == "SUCCESS"


def _normalize_email(value: str | None) -> str | None:
    if not value:
        return None

    stripped = value.strip().lower()
    if stripped.startswith("meetiq:"):
        stripped = stripped.split(":", 1)[1].strip().lower()

    return stripped if EMAIL_RE.match(stripped) else None


def _get_nested_str(payload: dict[str, Any], path: list[str]) -> str | None:
    current: Any = payload

    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)

    return current if isinstance(current, str) else None


def _walk_values(value: Any) -> list[str]:
    values: list[str] = []

    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, dict):
        for nested in value.values():
            values.extend(_walk_values(nested))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_values(item))

    return values


def _extract_email(payload: dict[str, Any]) -> str | None:
    resource = payload.get("resource")
    candidates: list[str | None] = []

    if isinstance(resource, dict):
        candidates.extend(
            [
                _get_nested_str(resource, ["subscriber", "email_address"]),
                _get_nested_str(resource, ["payer", "email_address"]),
                _get_nested_str(resource, ["payer", "payer_info", "email"]),
                _get_nested_str(resource, ["custom_id"]),
                _get_nested_str(resource, ["invoice_id"]),
                _get_nested_str(resource, ["payer_email"]),
                _get_nested_str(resource, ["email_address"]),
            ]
        )

    for candidate in candidates:
        normalized = _normalize_email(candidate)
        if normalized:
            return normalized

    for value in _walk_values(payload):
        normalized = _normalize_email(value)
        if normalized:
            return normalized

    return None


def _extract_resource_id(payload: dict[str, Any], key: str) -> str | None:
    resource = payload.get("resource")
    if not isinstance(resource, dict):
        return None

    value = resource.get(key)
    return value if isinstance(value, str) and value else None


def _extract_provider_subscription_id(payload: dict[str, Any]) -> str | None:
    resource = payload.get("resource")
    if not isinstance(resource, dict):
        return None

    for key in ("billing_agreement_id", "subscription_id", "id"):
        value = resource.get(key)
        if isinstance(value, str) and value:
            return value

    return None


def _extract_provider_payment_id(payload: dict[str, Any]) -> str | None:
    resource = payload.get("resource")
    if not isinstance(resource, dict):
        return None

    for key in ("id", "parent_payment", "capture_id"):
        value = resource.get(key)
        if isinstance(value, str) and value:
            return value

    return None


def _extract_period_end(payload: dict[str, Any]) -> datetime | None:
    resource = payload.get("resource")
    if not isinstance(resource, dict):
        return None

    raw_value = _get_nested_str(resource, ["billing_info", "next_billing_time"])
    if not raw_value:
        return None

    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _find_user_by_email(db: Session, email: str | None) -> User | None:
    if not email:
        return None

    return db.query(User).filter(User.email == email.lower().strip()).first()


def _record_event(
    db: Session,
    *,
    payload: dict[str, Any],
    status: str,
    user: User | None,
    error_message: str | None = None,
) -> BillingEvent:
    provider_event_id = str(payload.get("id") or "")
    event_type = str(payload.get("event_type") or "unknown")

    event = BillingEvent(
        provider="paypal",
        provider_event_id=provider_event_id,
        event_type=event_type,
        user_id=user.id if user else None,
        payload_json=payload,
        processing_status=status,
        error_message=error_message,
        processed_at=_utc_now() if status == "processed" else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _activate_paid_subscription(
    db: Session,
    *,
    user: User,
    payload: dict[str, Any],
) -> BillingSubscription:
    provider_subscription_id = _extract_provider_subscription_id(payload)
    provider_payment_id = _extract_provider_payment_id(payload)
    provider_customer_id = _extract_resource_id(payload, "payer_id")
    current_period_end = _extract_period_end(payload)

    existing = None
    query = db.query(BillingSubscription).filter(
        BillingSubscription.user_id == user.id,
        BillingSubscription.provider == "paypal",
    )

    if provider_subscription_id:
        existing = query.filter(
            BillingSubscription.provider_subscription_id == provider_subscription_id
        ).first()
    elif provider_payment_id:
        existing = query.filter(
            BillingSubscription.provider_payment_id == provider_payment_id
        ).first()

    if existing is not None:
        existing.status = "active"
        existing.plan_code = PAID_PRO_PLAN
        existing.current_period_end = current_period_end
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    subscription = BillingSubscription(
        user_id=user.id,
        provider="paypal",
        provider_customer_id=provider_customer_id,
        provider_subscription_id=provider_subscription_id,
        provider_payment_id=provider_payment_id,
        plan_code=PAID_PRO_PLAN,
        status="active",
        current_period_start=_utc_now(),
        current_period_end=current_period_end,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def _cancel_paypal_subscription(
    db: Session,
    *,
    payload: dict[str, Any],
) -> bool:
    provider_subscription_id = _extract_provider_subscription_id(payload)
    provider_payment_id = _extract_provider_payment_id(payload)

    query = db.query(BillingSubscription).filter(BillingSubscription.provider == "paypal")

    if provider_subscription_id:
        query = query.filter(
            BillingSubscription.provider_subscription_id == provider_subscription_id
        )
    elif provider_payment_id:
        query = query.filter(BillingSubscription.provider_payment_id == provider_payment_id)
    else:
        return False

    subscription = query.order_by(BillingSubscription.id.desc()).first()
    if subscription is None:
        return False

    subscription.status = "canceled"
    db.add(subscription)
    db.commit()
    return True


def process_paypal_webhook_event(
    db: Session,
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    provider_event_id = str(payload.get("id") or "")
    event_type = str(payload.get("event_type") or "")

    if not provider_event_id:
        return {"status": "ignored", "reason": "missing_event_id"}

    existing = (
        db.query(BillingEvent)
        .filter(
            BillingEvent.provider == "paypal",
            BillingEvent.provider_event_id == provider_event_id,
        )
        .first()
    )
    if existing is not None:
        return {
            "status": "duplicate",
            "provider": "paypal",
            "event_id": provider_event_id,
            "event_type": existing.event_type,
        }

    email = _extract_email(payload)
    user = _find_user_by_email(db, email)

    if event_type in PAYPAL_ACTIVE_EVENTS:
        if user is None:
            _record_event(
                db,
                payload=payload,
                status="failed",
                user=None,
                error_message=f"No MeetIQ user matched PayPal email: {email or 'unknown'}",
            )
            return {
                "status": "unmatched",
                "provider": "paypal",
                "event_id": provider_event_id,
                "event_type": event_type,
                "matched_email": email,
            }

        subscription = _activate_paid_subscription(db, user=user, payload=payload)
        _record_event(db, payload=payload, status="processed", user=user)

        return {
            "status": "processed",
            "provider": "paypal",
            "event_id": provider_event_id,
            "event_type": event_type,
            "user_id": user.id,
            "user_email": user.email,
            "plan_code": subscription.plan_code,
            "billing_status": subscription.status,
        }

    if event_type in PAYPAL_CANCEL_EVENTS:
        canceled = _cancel_paypal_subscription(db, payload=payload)
        _record_event(db, payload=payload, status="processed", user=user)

        return {
            "status": "processed",
            "provider": "paypal",
            "event_id": provider_event_id,
            "event_type": event_type,
            "canceled": canceled,
        }

    if event_type in PAYPAL_REVIEW_EVENTS:
        _record_event(
            db,
            payload=payload,
            status="received",
            user=user,
            error_message="PayPal event requires manual billing review.",
        )
        return {
            "status": "review",
            "provider": "paypal",
            "event_id": provider_event_id,
            "event_type": event_type,
        }

    _record_event(
        db,
        payload=payload,
        status="ignored",
        user=user,
        error_message="Unsupported PayPal event type.",
    )
    return {
        "status": "ignored",
        "provider": "paypal",
        "event_id": provider_event_id,
        "event_type": event_type,
    }
