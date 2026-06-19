from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, NamedTuple

import httpx
from sqlalchemy.orm import Session

from app.models.billing import BillingPaymentAttempt
from app.models.user import User
from app.services.billing import (
    PAID_PRO_PLAN,
    PRO_PILOT_PLAN,
    STARTER_PLAN,
    grant_paypal_paid_access,
)

PAYPAL_SANDBOX_API_BASE = "https://api-m.sandbox.paypal.com"
PAYPAL_LIVE_API_BASE = "https://api-m.paypal.com"

DEFAULT_CURRENCY_CODE = "USD"
DEFAULT_PLAN_CODE = STARTER_PLAN


class PayPalCheckoutPlan(NamedTuple):
    plan_code: str
    amount_cents: int
    description: str


PAYPAL_CHECKOUT_PLANS: dict[str, PayPalCheckoutPlan] = {
    STARTER_PLAN: PayPalCheckoutPlan(
        plan_code=STARTER_PLAN,
        amount_cents=2300,
        description="MeetIQ Starter",
    ),
    # Legacy alias: keep paid_pro supported as Starter-equivalent.
    PAID_PRO_PLAN: PayPalCheckoutPlan(
        plan_code=PAID_PRO_PLAN,
        amount_cents=2300,
        description="MeetIQ Starter",
    ),
    PRO_PILOT_PLAN: PayPalCheckoutPlan(
        plan_code=PRO_PILOT_PLAN,
        amount_cents=4900,
        description="MeetIQ Pro Pilot",
    ),
}


class PayPalCheckoutConfigError(RuntimeError):
    pass


class PayPalCheckoutProviderError(RuntimeError):
    pass


class PayPalCheckoutPlanError(ValueError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _paypal_api_base() -> str:
    env = os.getenv("PAYPAL_ENV", "sandbox").strip().lower()
    return PAYPAL_LIVE_API_BASE if env == "live" else PAYPAL_SANDBOX_API_BASE


def _frontend_base_url() -> str:
    value = (
        os.getenv("MEETIQ_FRONTEND_BASE_URL")
        or os.getenv("FRONTEND_BASE_URL")
        or "http://localhost:3000"
    )
    return value.strip().rstrip("/")


def _format_amount(amount_cents: int) -> str:
    return f"{Decimal(amount_cents) / Decimal('100'):.2f}"


def resolve_paypal_checkout_plan(plan_code: str | None) -> PayPalCheckoutPlan:
    normalized_plan_code = (plan_code or DEFAULT_PLAN_CODE).strip().lower()

    plan = PAYPAL_CHECKOUT_PLANS.get(normalized_plan_code)
    if plan is None:
        supported = ", ".join(sorted(PAYPAL_CHECKOUT_PLANS))
        raise PayPalCheckoutPlanError(
            f"Unsupported PayPal checkout plan. Supported plans: {supported}."
        )

    return plan


def _get_paypal_access_token() -> str:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise PayPalCheckoutConfigError("PayPal client credentials are not configured.")

    try:
        response = httpx.post(
            f"{_paypal_api_base()}/v1/oauth2/token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise PayPalCheckoutProviderError("PayPal access token request failed.") from exc

    token = response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise PayPalCheckoutProviderError("PayPal access token response was invalid.")

    return token


def _extract_approval_url(order_payload: dict[str, Any]) -> str:
    links = order_payload.get("links")
    if not isinstance(links, list):
        raise PayPalCheckoutProviderError("PayPal order response did not include links.")

    for link in links:
        if not isinstance(link, dict):
            continue
        if link.get("rel") == "approve" and isinstance(link.get("href"), str):
            return link["href"]

    raise PayPalCheckoutProviderError("PayPal order response did not include approval URL.")


def _mark_attempt_failed(
    db: Session,
    *,
    attempt: BillingPaymentAttempt,
    error_message: str,
) -> None:
    attempt.status = "failed"
    attempt.error_message = error_message
    db.add(attempt)
    db.commit()


def create_paypal_checkout(
    *,
    db: Session,
    user: User,
    plan_code: str | None = None,
) -> BillingPaymentAttempt:
    checkout_plan = resolve_paypal_checkout_plan(plan_code)
    amount_cents = checkout_plan.amount_cents
    currency_code = DEFAULT_CURRENCY_CODE
    attempt_reference = f"meetiq-{uuid.uuid4().hex}"
    frontend_base_url = _frontend_base_url()

    attempt = BillingPaymentAttempt(
        user_id=user.id,
        provider="paypal",
        attempt_reference=attempt_reference,
        plan_code=checkout_plan.plan_code,
        amount_cents=amount_cents,
        currency_code=currency_code,
        status="creating",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    try:
        token = _get_paypal_access_token()

        order_request = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": attempt_reference,
                    "custom_id": attempt_reference,
                    "invoice_id": attempt_reference,
                    "description": checkout_plan.description,
                    "amount": {
                        "currency_code": currency_code,
                        "value": _format_amount(amount_cents),
                    },
                }
            ],
            "application_context": {
                "brand_name": "MeetIQ",
                "landing_page": "LOGIN",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "PAY_NOW",
                "return_url": f"{frontend_base_url}/billing/success",
                "cancel_url": f"{frontend_base_url}/billing/cancel",
            },
        }

        response = httpx.post(
            f"{_paypal_api_base()}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=order_request,
            timeout=15,
        )
        response.raise_for_status()
    except (PayPalCheckoutConfigError, PayPalCheckoutProviderError):
        _mark_attempt_failed(
            db,
            attempt=attempt,
            error_message="PayPal checkout configuration or provider request failed.",
        )
        raise
    except httpx.HTTPError as exc:
        _mark_attempt_failed(
            db,
            attempt=attempt,
            error_message="PayPal order creation request failed.",
        )
        raise PayPalCheckoutProviderError("PayPal order creation request failed.") from exc

    order_payload = response.json()
    order_id = order_payload.get("id")
    if not isinstance(order_id, str) or not order_id:
        _mark_attempt_failed(
            db,
            attempt=attempt,
            error_message="PayPal order response did not include order id.",
        )
        raise PayPalCheckoutProviderError("PayPal order response did not include order id.")

    approval_url = _extract_approval_url(order_payload)

    attempt.provider_order_id = order_id
    attempt.checkout_url = approval_url
    attempt.status = "created"
    attempt.payload_json = order_payload
    attempt.updated_at = _utc_now()

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


def _extract_capture_id(capture_payload: dict[str, Any]) -> str | None:
    purchase_units = capture_payload.get("purchase_units")
    if not isinstance(purchase_units, list):
        return None

    for unit in purchase_units:
        if not isinstance(unit, dict):
            continue

        payments = unit.get("payments")
        if not isinstance(payments, dict):
            continue

        captures = payments.get("captures")
        if not isinstance(captures, list):
            continue

        for capture in captures:
            if isinstance(capture, dict) and isinstance(capture.get("id"), str):
                return capture["id"]

    return None


def capture_paypal_checkout(
    *,
    db: Session,
    user: User,
    provider_order_id: str,
) -> BillingPaymentAttempt:
    order_id = provider_order_id.strip()
    if not order_id:
        raise PayPalCheckoutProviderError("PayPal order id is required.")

    attempt = (
        db.query(BillingPaymentAttempt)
        .filter(
            BillingPaymentAttempt.provider == "paypal",
            BillingPaymentAttempt.provider_order_id == order_id,
        )
        .first()
    )

    if attempt is None:
        raise PayPalCheckoutProviderError("PayPal payment attempt was not found.")

    if attempt.user_id != user.id:
        raise PayPalCheckoutProviderError("PayPal payment attempt does not belong to this user.")

    if attempt.status in {"captured", "completed", "paid"}:
        return attempt

    try:
        token = _get_paypal_access_token()

        response = httpx.post(
            f"{_paypal_api_base()}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        attempt.status = "capture_failed"
        attempt.error_message = "PayPal order capture request failed."
        attempt.updated_at = _utc_now()
        db.add(attempt)
        db.commit()
        raise PayPalCheckoutProviderError("PayPal order capture request failed.") from exc

    capture_payload = response.json()
    capture_id = _extract_capture_id(capture_payload)

    attempt.provider_capture_id = capture_id
    attempt.provider_payment_id = capture_id
    attempt.status = "captured"
    attempt.payload_json = capture_payload
    attempt.completed_at = _utc_now()
    attempt.updated_at = _utc_now()

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    grant_paypal_paid_access(
        db,
        user=user,
        provider_order_id=order_id,
        provider_capture_id=capture_id,
        plan_code=attempt.plan_code,
    )

    return attempt
