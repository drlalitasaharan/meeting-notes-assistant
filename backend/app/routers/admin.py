from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import health as health_api
from app.deps import get_db, require_admin
from app.models.billing import BillingPaymentAttempt, BillingSubscription
from app.models.meeting import Meeting
from app.models.user import User
from app.services.processing_observability import serialize_admin_processing

router = APIRouter(prefix="/v1/admin", tags=["admin"])

COMPLETED_STATUSES = {
    "complete",
    "completed",
    "done",
    "success",
    "succeeded",
}
FAILED_STATUSES = {
    "error",
    "failed",
    "failure",
}
PROCESSING_STATUSES = {
    "in_progress",
    "processing",
    "summarizing",
    "transcribing",
}
QUEUED_STATUSES = {
    "queued",
}
STUCK_STATUSES = QUEUED_STATUSES | PROCESSING_STATUSES
STUCK_AFTER_MINUTES = 45


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    normalized = _as_utc(value)
    return normalized.isoformat() if normalized else None


def _normalized_status(value: str | None) -> str:
    return (value or "unknown").strip().lower()


def _sum_statuses(
    status_counts: dict[str, int],
    accepted_statuses: set[str],
) -> int:
    return sum(
        count for status_name, count in status_counts.items() if status_name in accepted_statuses
    )


def _is_stuck(meeting: Meeting, now: datetime) -> bool:
    updated_at = _as_utc(meeting.updated_at)

    if updated_at is None:
        return False

    return _normalized_status(meeting.status) in STUCK_STATUSES and updated_at < now - timedelta(
        minutes=STUCK_AFTER_MINUTES
    )


@router.get("/overview")
def admin_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Return platform-wide operational counts.

    This endpoint is admin-only and intentionally excludes meeting content,
    transcripts, recording paths, and generated notes.
    """
    now = _utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    stuck_cutoff = now - timedelta(minutes=STUCK_AFTER_MINUTES)

    status_rows = db.query(Meeting.status, func.count(Meeting.id)).group_by(Meeting.status).all()

    status_counts: dict[str, int] = {}
    for raw_status, count in status_rows:
        normalized = _normalized_status(raw_status)
        status_counts[normalized] = status_counts.get(normalized, 0) + int(count)

    completed = _sum_statuses(status_counts, COMPLETED_STATUSES)
    failed = _sum_statuses(status_counts, FAILED_STATUSES)
    processing = _sum_statuses(status_counts, PROCESSING_STATUSES)
    queued = _sum_statuses(status_counts, QUEUED_STATUSES)

    finished = completed + failed
    success_rate = round((completed / finished) * 100, 1) if finished else None

    meetings_today = (
        db.query(func.count(Meeting.id)).filter(Meeting.created_at >= today_start).scalar() or 0
    )
    meetings_last_7_days = (
        db.query(func.count(Meeting.id)).filter(Meeting.created_at >= seven_days_ago).scalar() or 0
    )
    meetings_last_30_days = (
        db.query(func.count(Meeting.id)).filter(Meeting.created_at >= thirty_days_ago).scalar() or 0
    )
    stuck_meetings = (
        db.query(func.count(Meeting.id))
        .filter(
            func.lower(Meeting.status).in_(STUCK_STATUSES),
            Meeting.updated_at < stuck_cutoff,
        )
        .scalar()
        or 0
    )
    total_users = db.query(func.count(User.id)).scalar() or 0

    return {
        "generated_at": now.isoformat(),
        "total_users": int(total_users),
        "total_meetings": sum(status_counts.values()),
        "meetings_today": int(meetings_today),
        "meetings_last_7_days": int(meetings_last_7_days),
        "meetings_last_30_days": int(meetings_last_30_days),
        "completed": completed,
        "failed": failed,
        "processing": processing,
        "queued": queued,
        "stuck": int(stuck_meetings),
        "success_rate_percent": success_rate,
        "status_counts": status_counts,
        "stuck_after_minutes": STUCK_AFTER_MINUTES,
    }


@router.get("/meetings")
def admin_list_meetings(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=200),
) -> dict[str, Any]:
    """
    Return meetings across all users for operational troubleshooting.

    Raw media paths, transcripts, notes, password data, and storage
    credentials are never returned.
    """
    query = db.query(Meeting, User.email).outerjoin(
        User,
        Meeting.user_id == User.id,
    )

    if status_filter:
        query = query.filter(func.lower(Meeting.status) == status_filter.strip().lower())

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Meeting.title.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    total = query.count()
    rows = (
        query.order_by(Meeting.created_at.desc(), Meeting.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    now = _utc_now()
    items = []

    for meeting, user_email in rows:
        items.append(
            {
                "id": meeting.id,
                "title": meeting.title,
                "status": meeting.status,
                "user_id": meeting.user_id,
                "user_email": user_email,
                "created_at": _iso(meeting.created_at),
                "updated_at": _iso(meeting.updated_at),
                "last_error": meeting.last_error,
                "is_stuck": _is_stuck(meeting, now),
                **serialize_admin_processing(meeting),
            }
        )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/billing/overview")
def admin_billing_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Return billing state for admin monitoring.

    This endpoint intentionally returns payment metadata only. It does not
    return raw provider payloads, card/bank details, transcripts, recordings,
    notes, or secrets.
    """
    active_statuses = ("active", "trialing", "paid")
    successful_attempt_statuses = ("captured", "succeeded", "completed", "paid")
    failed_attempt_statuses = ("failed", "canceled", "cancelled", "error")

    active_paid_users = (
        db.query(func.count(func.distinct(BillingSubscription.user_id)))
        .filter(BillingSubscription.status.in_(active_statuses))
        .scalar()
        or 0
    )
    active_subscriptions = (
        db.query(func.count(BillingSubscription.id))
        .filter(BillingSubscription.status.in_(active_statuses))
        .scalar()
        or 0
    )
    total_subscriptions = db.query(func.count(BillingSubscription.id)).scalar() or 0
    total_payment_attempts = db.query(func.count(BillingPaymentAttempt.id)).scalar() or 0
    successful_payment_attempts = (
        db.query(func.count(BillingPaymentAttempt.id))
        .filter(BillingPaymentAttempt.status.in_(successful_attempt_statuses))
        .scalar()
        or 0
    )
    failed_payment_attempts = (
        db.query(func.count(BillingPaymentAttempt.id))
        .filter(BillingPaymentAttempt.status.in_(failed_attempt_statuses))
        .scalar()
        or 0
    )

    subscription_rows = (
        db.query(BillingSubscription, User.email)
        .outerjoin(User, BillingSubscription.user_id == User.id)
        .order_by(BillingSubscription.created_at.desc(), BillingSubscription.id.desc())
        .limit(10)
        .all()
    )

    attempt_rows = (
        db.query(BillingPaymentAttempt, User.email)
        .outerjoin(User, BillingPaymentAttempt.user_id == User.id)
        .order_by(BillingPaymentAttempt.created_at.desc(), BillingPaymentAttempt.id.desc())
        .limit(10)
        .all()
    )

    recent_subscriptions = []
    for subscription, user_email in subscription_rows:
        recent_subscriptions.append(
            {
                "id": subscription.id,
                "user_id": subscription.user_id,
                "user_email": user_email,
                "provider": subscription.provider,
                "plan_code": subscription.plan_code,
                "status": subscription.status,
                "provider_subscription_id": subscription.provider_subscription_id,
                "provider_payment_id": subscription.provider_payment_id,
                "current_period_end": _iso(subscription.current_period_end),
                "created_at": _iso(subscription.created_at),
                "updated_at": _iso(subscription.updated_at),
            }
        )

    recent_payment_attempts = []
    for attempt, user_email in attempt_rows:
        recent_payment_attempts.append(
            {
                "id": attempt.id,
                "user_id": attempt.user_id,
                "user_email": user_email,
                "provider": attempt.provider,
                "plan_code": attempt.plan_code,
                "status": attempt.status,
                "amount_cents": attempt.amount_cents,
                "currency_code": attempt.currency_code,
                "provider_order_id": attempt.provider_order_id,
                "provider_capture_id": attempt.provider_capture_id,
                "provider_payment_id": attempt.provider_payment_id,
                "completed_at": _iso(attempt.completed_at),
                "created_at": _iso(attempt.created_at),
                "updated_at": _iso(attempt.updated_at),
                "error_message": attempt.error_message,
            }
        )

    return {
        "generated_at": _utc_now().isoformat(),
        "active_paid_users": int(active_paid_users),
        "active_subscriptions": int(active_subscriptions),
        "total_subscriptions": int(total_subscriptions),
        "total_payment_attempts": int(total_payment_attempts),
        "successful_payment_attempts": int(successful_payment_attempts),
        "failed_payment_attempts": int(failed_payment_attempts),
        "recent_subscriptions": recent_subscriptions,
        "recent_payment_attempts": recent_payment_attempts,
    }


@router.get("/system-health")
def admin_system_health(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Return the existing DB, Redis, and storage health checks to admins.
    """
    return {
        "generated_at": _utc_now().isoformat(),
        **health_api.healthz(),
    }
