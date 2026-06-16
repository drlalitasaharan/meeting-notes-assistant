from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.billing import BillingEvent, BillingSubscription, ManualBillingOverride
from app.models.user import User

FREE_TRIAL_PLAN = "free_trial"
PAID_PRO_PLAN = "paid_pro"
ACTIVE_BILLING_STATUSES = {"active", "trialing", "paid"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _is_current(end_value: datetime | None) -> bool:
    normalized = _as_utc(end_value)
    return normalized is None or normalized >= _utc_now()


def _iso_or_none(value: datetime | None) -> str | None:
    normalized = _as_utc(value)
    return normalized.isoformat() if normalized is not None else None


def get_active_subscription(
    db: Session,
    user: User,
) -> BillingSubscription | None:
    rows = (
        db.query(BillingSubscription)
        .filter(
            BillingSubscription.user_id == user.id,
            BillingSubscription.status.in_(ACTIVE_BILLING_STATUSES),
        )
        .order_by(BillingSubscription.id.desc())
        .all()
    )

    for row in rows:
        if _is_current(row.current_period_end):
            return row

    return None


def get_active_manual_override(
    db: Session,
    user: User,
) -> ManualBillingOverride | None:
    rows = (
        db.query(ManualBillingOverride)
        .filter(
            ManualBillingOverride.user_id == user.id,
            ManualBillingOverride.status == "active",
        )
        .order_by(ManualBillingOverride.id.desc())
        .all()
    )

    for row in rows:
        if _is_current(row.ends_at):
            return row

    return None


def get_effective_plan(
    db: Session,
    user: User,
) -> str:
    manual_override = get_active_manual_override(db=db, user=user)
    if manual_override is not None:
        return manual_override.plan_code

    subscription = get_active_subscription(db=db, user=user)
    if subscription is not None:
        return subscription.plan_code

    return FREE_TRIAL_PLAN


def has_paid_access(
    db: Session,
    user: User,
) -> bool:
    return get_effective_plan(db=db, user=user) == PAID_PRO_PLAN


def get_billing_status(
    db: Session,
    user: User,
) -> dict[str, Any]:
    manual_override = get_active_manual_override(db=db, user=user)
    subscription = get_active_subscription(db=db, user=user)

    if manual_override is not None:
        return {
            "plan_code": manual_override.plan_code,
            "billing_status": manual_override.status,
            "provider": "manual",
            "current_period_end": _iso_or_none(manual_override.ends_at),
            "source": "manual_override",
        }

    if subscription is not None:
        return {
            "plan_code": subscription.plan_code,
            "billing_status": subscription.status,
            "provider": subscription.provider,
            "current_period_end": _iso_or_none(subscription.current_period_end),
            "source": "subscription",
        }

    return {
        "plan_code": FREE_TRIAL_PLAN,
        "billing_status": "free_trial",
        "provider": None,
        "current_period_end": None,
        "source": "default",
    }


def record_billing_event(
    db: Session,
    *,
    provider: str,
    provider_event_id: str,
    event_type: str,
    payload_json: dict[str, Any] | None = None,
    user: User | None = None,
    processing_status: str = "received",
    error_message: str | None = None,
) -> BillingEvent:
    existing = (
        db.query(BillingEvent)
        .filter(
            BillingEvent.provider == provider,
            BillingEvent.provider_event_id == provider_event_id,
        )
        .first()
    )
    if existing is not None:
        return existing

    event = BillingEvent(
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload_json=payload_json,
        user_id=user.id if user else None,
        processing_status=processing_status,
        error_message=error_message,
        processed_at=_utc_now() if processing_status == "processed" else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def grant_manual_paid_access(
    db: Session,
    *,
    user: User,
    granted_by_admin_email: str,
    reason: str | None = None,
    ends_at: datetime | None = None,
    plan_code: str = PAID_PRO_PLAN,
) -> ManualBillingOverride:
    override = ManualBillingOverride(
        user_id=user.id,
        plan_code=plan_code,
        status="active",
        reason=reason,
        granted_by_admin_email=granted_by_admin_email,
        starts_at=_utc_now(),
        ends_at=ends_at,
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


def cancel_manual_paid_access(
    db: Session,
    *,
    user: User,
) -> bool:
    override = get_active_manual_override(db=db, user=user)
    if override is None:
        return False

    override.status = "canceled"
    db.add(override)
    db.commit()
    return True
