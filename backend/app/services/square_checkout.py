from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import NamedTuple

import httpx
from sqlalchemy.orm import Session

from app.models.billing import BillingPaymentAttempt
from app.models.user import User
from app.services.billing import PAID_PRO_PLAN, PRO_PILOT_PLAN, STARTER_PLAN

SQUARE_SANDBOX_API_BASE = "https://connect.squareupsandbox.com"
SQUARE_LIVE_API_BASE = "https://connect.squareup.com"

DEFAULT_CURRENCY_CODE = "USD"
DEFAULT_PLAN_CODE = STARTER_PLAN


class SquareCheckoutPlan(NamedTuple):
    plan_code: str
    amount_cents: int
    name: str


SQUARE_CHECKOUT_PLANS: dict[str, SquareCheckoutPlan] = {
    STARTER_PLAN: SquareCheckoutPlan(
        plan_code=STARTER_PLAN,
        amount_cents=2300,
        name="MeetIQ Starter",
    ),
    PAID_PRO_PLAN: SquareCheckoutPlan(
        plan_code=PAID_PRO_PLAN,
        amount_cents=2300,
        name="MeetIQ Starter",
    ),
    PRO_PILOT_PLAN: SquareCheckoutPlan(
        plan_code=PRO_PILOT_PLAN,
        amount_cents=4900,
        name="MeetIQ Pro Pilot",
    ),
}


class SquareCheckoutConfigError(RuntimeError):
    pass


class SquareCheckoutProviderError(RuntimeError):
    pass


class SquareCheckoutPlanError(ValueError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _square_api_base() -> str:
    env = os.getenv("SQUARE_ENV", "sandbox").strip().lower()
    if env in {"production", "live"}:
        return SQUARE_LIVE_API_BASE
    if env in {"sandbox", "test"}:
        return SQUARE_SANDBOX_API_BASE
    raise SquareCheckoutConfigError("SQUARE_ENV must be one of: sandbox, test, production, live.")


def _frontend_base_url() -> str:
    value = (
        os.getenv("MEETIQ_FRONTEND_BASE_URL")
        or os.getenv("FRONTEND_BASE_URL")
        or "http://localhost:3000"
    )
    return value.strip().rstrip("/")


def resolve_square_checkout_plan(plan_code: str | None) -> SquareCheckoutPlan:
    normalized_plan_code = (plan_code or DEFAULT_PLAN_CODE).strip().lower()
    plan = SQUARE_CHECKOUT_PLANS.get(normalized_plan_code)

    if plan is None:
        supported = ", ".join(sorted(SQUARE_CHECKOUT_PLANS))
        raise SquareCheckoutPlanError(
            f"Unsupported Square checkout plan. Supported plans: {supported}."
        )

    return plan


def _square_access_token() -> str:
    token = os.getenv("SQUARE_ACCESS_TOKEN")
    if not token:
        raise SquareCheckoutConfigError("SQUARE_ACCESS_TOKEN is not configured.")
    return token


def _square_location_id() -> str:
    location_id = os.getenv("SQUARE_LOCATION_ID")
    if not location_id:
        raise SquareCheckoutConfigError("SQUARE_LOCATION_ID is not configured.")
    return location_id


def _mark_attempt_failed(
    db: Session,
    *,
    attempt: BillingPaymentAttempt,
    error_message: str,
) -> None:
    attempt.status = "failed"
    attempt.error_message = error_message
    attempt.updated_at = _utc_now()
    db.add(attempt)
    db.commit()


def create_square_checkout(
    *,
    db: Session,
    user: User,
    plan_code: str | None = None,
) -> BillingPaymentAttempt:
    checkout_plan = resolve_square_checkout_plan(plan_code)
    amount_cents = checkout_plan.amount_cents
    currency_code = DEFAULT_CURRENCY_CODE
    attempt_reference = f"meetiq-{uuid.uuid4().hex}"
    frontend_base_url = _frontend_base_url()

    attempt = BillingPaymentAttempt(
        user_id=user.id,
        provider="square",
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
        request_payload = {
            "idempotency_key": attempt_reference,
            "quick_pay": {
                "name": checkout_plan.name,
                "price_money": {
                    "amount": amount_cents,
                    "currency": currency_code,
                },
                "location_id": _square_location_id(),
            },
            "checkout_options": {
                "redirect_url": (
                    f"{frontend_base_url}/billing/square/success"
                    f"?attempt_reference={attempt_reference}"
                ),
            },
            "payment_note": f"meetiq:{user.email}",
        }

        response = httpx.post(
            f"{_square_api_base()}/v2/online-checkout/payment-links",
            headers={
                "Authorization": f"Bearer {_square_access_token()}",
                "Content-Type": "application/json",
                "Square-Version": "2026-05-20",
            },
            json=request_payload,
            timeout=15,
        )
        response.raise_for_status()
    except SquareCheckoutConfigError:
        _mark_attempt_failed(
            db,
            attempt=attempt,
            error_message="Square checkout configuration is incomplete.",
        )
        raise
    except httpx.HTTPError as exc:
        _mark_attempt_failed(
            db,
            attempt=attempt,
            error_message="Square payment link creation request failed.",
        )
        raise SquareCheckoutProviderError("Square payment link creation request failed.") from exc

    payload = response.json()
    payment_link = payload.get("payment_link")
    if not isinstance(payment_link, dict):
        _mark_attempt_failed(
            db,
            attempt=attempt,
            error_message="Square payment link response was invalid.",
        )
        raise SquareCheckoutProviderError("Square payment link response was invalid.")

    checkout_url = payment_link.get("url")
    if not isinstance(checkout_url, str) or not checkout_url:
        _mark_attempt_failed(
            db,
            attempt=attempt,
            error_message="Square payment link response did not include a checkout URL.",
        )
        raise SquareCheckoutProviderError(
            "Square payment link response did not include a checkout URL."
        )

    order_id = payment_link.get("order_id")
    payment_link_id = payment_link.get("id")

    attempt.provider_order_id = order_id if isinstance(order_id, str) else payment_link_id
    attempt.checkout_url = checkout_url
    attempt.status = "created"
    attempt.payload_json = payload
    attempt.updated_at = _utc_now()

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt
