from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from app.models.billing import BillingEvent, BillingPaymentAttempt, BillingSubscription
from app.models.user import User
from app.services.billing import PAID_PRO_PLAN, grant_square_paid_access

SQUARE_ACTIVE_EVENTS = {
    "payment.updated",
    "invoice.payment_made",
}

SQUARE_CANCEL_EVENTS = {
    "invoice.canceled",
    "subscription.canceled",
}

SQUARE_REVIEW_EVENTS = {
    "invoice.refunded",
    "invoice.scheduled_charge_failed",
    "refund.created",
    "refund.updated",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SquareWebhookVerificationError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _verification_disabled_for_tests() -> bool:
    disabled = os.getenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "").strip().lower()
    return disabled in {"1", "true", "yes"} and bool(os.getenv("PYTEST_CURRENT_TEST"))


def verify_square_webhook_signature(
    *,
    headers: Headers,
    raw_body: bytes,
) -> bool:
    if _verification_disabled_for_tests():
        return True

    signature_key = os.getenv("SQUARE_WEBHOOK_SIGNATURE_KEY")
    notification_url = os.getenv("SQUARE_WEBHOOK_NOTIFICATION_URL")
    provided_signature = headers.get("x-square-hmacsha256-signature")

    if not signature_key:
        raise SquareWebhookVerificationError("SQUARE_WEBHOOK_SIGNATURE_KEY is not configured.")

    if not notification_url:
        raise SquareWebhookVerificationError("SQUARE_WEBHOOK_NOTIFICATION_URL is not configured.")

    if not provided_signature:
        raise SquareWebhookVerificationError("Missing Square webhook signature header.")

    message = notification_url.encode("utf-8") + raw_body
    digest = hmac.new(
        signature_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()
    expected_signature = base64.b64encode(digest).decode("utf-8")

    return hmac.compare_digest(expected_signature, provided_signature)


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


def _square_object(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return {}

    obj = data.get("object")
    return obj if isinstance(obj, dict) else {}


def _payment(payload: dict[str, Any]) -> dict[str, Any]:
    obj = _square_object(payload)
    payment = obj.get("payment")
    return payment if isinstance(payment, dict) else obj


def _invoice(payload: dict[str, Any]) -> dict[str, Any]:
    obj = _square_object(payload)
    invoice = obj.get("invoice")
    return invoice if isinstance(invoice, dict) else obj


def _extract_email(payload: dict[str, Any]) -> str | None:
    payment = _payment(payload)
    invoice = _invoice(payload)

    candidates = [
        # Prefer MeetIQ-controlled metadata before Square buyer receipt email.
        # In live Square checkout, buyer_email_address can be the payer email,
        # while payment.note contains the MeetIQ account email from checkout creation.
        _get_nested_str(payment, ["note"]),
        _get_nested_str(payment, ["reference_id"]),
        _get_nested_str(payment, ["buyer_email_address"]),
        _get_nested_str(invoice, ["primary_recipient", "email_address"]),
        _get_nested_str(invoice, ["description"]),
        _get_nested_str(invoice, ["title"]),
    ]

    for candidate in candidates:
        normalized = _normalize_email(candidate)
        if normalized:
            return normalized

    for value in _walk_values(payload):
        normalized = _normalize_email(value)
        if normalized:
            return normalized

    return None


def _extract_payment_status(payload: dict[str, Any]) -> str | None:
    payment = _payment(payload)
    status = payment.get("status")
    return status.upper() if isinstance(status, str) else None


def _extract_provider_order_id(payload: dict[str, Any]) -> str | None:
    payment = _payment(payload)
    invoice = _invoice(payload)

    for value in (
        payment.get("order_id"),
        payment.get("orderId"),
        invoice.get("order_id"),
        invoice.get("orderId"),
    ):
        if isinstance(value, str) and value:
            return value

    return None


def _extract_provider_payment_id(payload: dict[str, Any]) -> str | None:
    payment = _payment(payload)

    for key in ("id", "payment_id"):
        value = payment.get(key)
        if isinstance(value, str) and value:
            return value

    data = payload.get("data")
    if isinstance(data, dict):
        value = data.get("id")
        if isinstance(value, str) and value:
            return value

    return None


def _extract_provider_subscription_id(payload: dict[str, Any]) -> str | None:
    invoice = _invoice(payload)

    for key in ("subscription_id", "id", "invoice_id"):
        value = invoice.get(key)
        if isinstance(value, str) and value:
            return value

    return None


def _extract_provider_customer_id(payload: dict[str, Any]) -> str | None:
    payment = _payment(payload)
    invoice = _invoice(payload)

    for value in (
        payment.get("customer_id"),
        invoice.get("customer_id"),
        _get_nested_str(invoice, ["primary_recipient", "customer_id"]),
    ):
        if isinstance(value, str) and value:
            return value

    return None


def _find_checkout_attempt(
    db: Session,
    *,
    payload: dict[str, Any],
) -> BillingPaymentAttempt | None:
    provider_order_id = _extract_provider_order_id(payload)
    provider_payment_id = _extract_provider_payment_id(payload)

    query = db.query(BillingPaymentAttempt).filter(
        BillingPaymentAttempt.provider == "square",
    )

    if provider_order_id:
        attempt = query.filter(
            BillingPaymentAttempt.provider_order_id == provider_order_id,
        ).first()
        if attempt is not None:
            return attempt

    if provider_payment_id:
        attempt = query.filter(
            BillingPaymentAttempt.provider_payment_id == provider_payment_id,
        ).first()
        if attempt is not None:
            return attempt

    return None


def _mark_checkout_attempt_captured(
    db: Session,
    *,
    attempt: BillingPaymentAttempt | None,
    provider_payment_id: str | None,
    payload: dict[str, Any],
) -> None:
    if attempt is None:
        return

    attempt.status = "captured"
    attempt.provider_payment_id = provider_payment_id or attempt.provider_payment_id
    attempt.payload_json = payload
    attempt.completed_at = attempt.completed_at or _utc_now()
    attempt.updated_at = _utc_now()
    db.add(attempt)
    db.commit()


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
    provider_event_id = str(payload.get("event_id") or payload.get("id") or "")
    event_type = str(payload.get("type") or payload.get("event_type") or "unknown")

    event = BillingEvent(
        provider="square",
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
    provider_order_id = _extract_provider_order_id(payload)
    provider_subscription_id = _extract_provider_subscription_id(payload)
    provider_payment_id = _extract_provider_payment_id(payload)
    provider_customer_id = _extract_provider_customer_id(payload)
    attempt = _find_checkout_attempt(db, payload=payload)
    plan_code = attempt.plan_code if attempt is not None else PAID_PRO_PLAN

    subscription = grant_square_paid_access(
        db,
        user=user,
        provider_order_id=provider_order_id or provider_subscription_id,
        provider_payment_id=provider_payment_id,
        provider_customer_id=provider_customer_id,
        plan_code=plan_code,
    )

    _mark_checkout_attempt_captured(
        db,
        attempt=attempt,
        provider_payment_id=provider_payment_id,
        payload=payload,
    )

    return subscription


def _cancel_square_subscription(
    db: Session,
    *,
    payload: dict[str, Any],
) -> bool:
    provider_subscription_id = _extract_provider_subscription_id(payload)
    provider_payment_id = _extract_provider_payment_id(payload)

    query = db.query(BillingSubscription).filter(BillingSubscription.provider == "square")

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


def process_square_webhook_event(
    db: Session,
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    provider_event_id = str(payload.get("event_id") or payload.get("id") or "")
    event_type = str(payload.get("type") or payload.get("event_type") or "")

    if not provider_event_id:
        return {"status": "ignored", "reason": "missing_event_id"}

    existing = (
        db.query(BillingEvent)
        .filter(
            BillingEvent.provider == "square",
            BillingEvent.provider_event_id == provider_event_id,
        )
        .first()
    )
    if existing is not None:
        return {
            "status": "duplicate",
            "provider": "square",
            "event_id": provider_event_id,
            "event_type": existing.event_type,
        }

    email = _extract_email(payload)
    user = _find_user_by_email(db, email)
    payment_status = _extract_payment_status(payload)

    is_active_payment = event_type == "payment.updated" and payment_status == "COMPLETED"
    is_active_invoice = event_type == "invoice.payment_made"

    if event_type in SQUARE_ACTIVE_EVENTS and (is_active_payment or is_active_invoice):
        if user is None:
            _record_event(
                db,
                payload=payload,
                status="failed",
                user=None,
                error_message=f"No MeetIQ user matched Square email: {email or 'unknown'}",
            )
            return {
                "status": "unmatched",
                "provider": "square",
                "event_id": provider_event_id,
                "event_type": event_type,
                "matched_email": email,
            }

        subscription = _activate_paid_subscription(db, user=user, payload=payload)
        _record_event(db, payload=payload, status="processed", user=user)

        return {
            "status": "processed",
            "provider": "square",
            "event_id": provider_event_id,
            "event_type": event_type,
            "user_id": user.id,
            "user_email": user.email,
            "plan_code": subscription.plan_code,
            "billing_status": subscription.status,
        }

    if event_type in SQUARE_CANCEL_EVENTS:
        canceled = _cancel_square_subscription(db, payload=payload)
        _record_event(db, payload=payload, status="processed", user=user)

        return {
            "status": "processed",
            "provider": "square",
            "event_id": provider_event_id,
            "event_type": event_type,
            "canceled": canceled,
        }

    if event_type in SQUARE_REVIEW_EVENTS:
        _record_event(
            db,
            payload=payload,
            status="received",
            user=user,
            error_message="Square event requires manual billing review.",
        )
        return {
            "status": "review",
            "provider": "square",
            "event_id": provider_event_id,
            "event_type": event_type,
        }

    _record_event(
        db,
        payload=payload,
        status="ignored",
        user=user,
        error_message="Unsupported or incomplete Square event type.",
    )
    return {
        "status": "ignored",
        "provider": "square",
        "event_id": provider_event_id,
        "event_type": event_type,
    }
