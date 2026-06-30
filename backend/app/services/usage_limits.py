from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.upload_ledger import UploadLedger
from app.models.user import User
from app.services.billing import (
    PAID_PRO_PLAN,
    PRO_PILOT_PLAN,
    STARTER_PLAN,
    get_effective_plan,
)

DEFAULT_FREE_TRIAL_UPLOAD_LIMIT = 1
DEFAULT_FREE_TRIAL_MAX_DURATION_SECONDS = 30 * 60
DEFAULT_PILOT_UPLOAD_LIMIT = 3
DEFAULT_PILOT_MAX_DURATION_SECONDS = 60 * 60
DEFAULT_STARTER_MONTHLY_UPLOAD_LIMIT = 20
DEFAULT_PRO_PILOT_MONTHLY_UPLOAD_LIMIT = 100
DEFAULT_STARTER_MAX_DURATION_SECONDS = 60 * 60
DEFAULT_PRO_PILOT_MAX_DURATION_SECONDS = 120 * 60

FREE_TRIAL_LIMIT_MESSAGE = "You have used your free-trial upload. Contact support to request pilot access or a higher limit."
PAID_MONTHLY_LIMIT_MESSAGE = "You have used your monthly upload allowance. Contact support to request a higher limit or Business / Team access."


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value.strip())
    except ValueError:
        return default

    return max(0, value)


def _csv_env(name: str) -> set[str]:
    return {item.strip().lower() for item in os.getenv(name, "").split(",") if item.strip()}


def _has_pilot_override(user: User) -> bool:
    pilot_override_emails = _csv_env("MEETIQ_PILOT_OVERRIDE_EMAILS")
    return user.email.strip().lower() in pilot_override_emails


def current_month_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def monthly_upload_limit_for_plan(plan_code: str) -> int | None:
    if plan_code in {PAID_PRO_PLAN, STARTER_PLAN}:
        return _int_env(
            "MEETIQ_STARTER_MONTHLY_UPLOAD_LIMIT",
            DEFAULT_STARTER_MONTHLY_UPLOAD_LIMIT,
        )

    if plan_code == PRO_PILOT_PLAN:
        return _int_env(
            "MEETIQ_PRO_PILOT_MONTHLY_UPLOAD_LIMIT",
            DEFAULT_PRO_PILOT_MONTHLY_UPLOAD_LIMIT,
        )

    return None


def max_duration_seconds_for_plan(plan_code: str) -> int | None:
    if plan_code in {PAID_PRO_PLAN, STARTER_PLAN}:
        return _int_env(
            "MEETIQ_STARTER_MAX_DURATION_SECONDS",
            DEFAULT_STARTER_MAX_DURATION_SECONDS,
        )

    if plan_code == PRO_PILOT_PLAN:
        return _int_env(
            "MEETIQ_PRO_PILOT_MAX_DURATION_SECONDS",
            DEFAULT_PRO_PILOT_MAX_DURATION_SECONDS,
        )

    return None


def upload_limit_for_user(user: User) -> int:
    if _has_pilot_override(user):
        return _int_env("MEETIQ_PILOT_UPLOAD_LIMIT", DEFAULT_PILOT_UPLOAD_LIMIT)

    return _int_env("MEETIQ_FREE_TRIAL_UPLOAD_LIMIT", DEFAULT_FREE_TRIAL_UPLOAD_LIMIT)


def max_duration_seconds_for_user(user: User) -> int:
    if _has_pilot_override(user):
        return _int_env("MEETIQ_PILOT_MAX_DURATION_SECONDS", DEFAULT_PILOT_MAX_DURATION_SECONDS)

    return _int_env(
        "MEETIQ_FREE_TRIAL_MAX_DURATION_SECONDS",
        DEFAULT_FREE_TRIAL_MAX_DURATION_SECONDS,
    )


def count_uploaded_meeting_slots(
    db: Session,
    *,
    user_id: int,
    exclude_meeting_id: int | None = None,
) -> int:
    query = db.query(func.count(UploadLedger.id)).filter(
        UploadLedger.user_id == str(user_id),
        UploadLedger.counted_at.isnot(None),
        UploadLedger.deleted_at.is_(None),
    )

    if exclude_meeting_id is not None:
        query = query.filter(UploadLedger.meeting_id != str(exclude_meeting_id))

    return int(query.scalar() or 0)


def count_monthly_uploaded_meeting_slots(
    db: Session,
    *,
    user_id: int,
    exclude_meeting_id: int | None = None,
) -> int:
    query = db.query(func.count(UploadLedger.id)).filter(
        UploadLedger.user_id == str(user_id),
        UploadLedger.counted_at.isnot(None),
        UploadLedger.counted_at >= current_month_start_utc(),
        UploadLedger.deleted_at.is_(None),
    )

    if exclude_meeting_id is not None:
        query = query.filter(UploadLedger.meeting_id != str(exclude_meeting_id))

    return int(query.scalar() or 0)


def enforce_can_create_meeting(
    *,
    db: Session,
    current_user: User,
) -> None:
    plan_code = get_effective_plan(db=db, user=current_user)
    monthly_limit = monthly_upload_limit_for_plan(plan_code)

    if monthly_limit is not None:
        used_slots = count_monthly_uploaded_meeting_slots(db, user_id=current_user.id)
        if used_slots >= monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=PAID_MONTHLY_LIMIT_MESSAGE,
            )
        return

    limit = upload_limit_for_user(current_user)
    used_slots = count_uploaded_meeting_slots(db, user_id=current_user.id)

    if used_slots >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=FREE_TRIAL_LIMIT_MESSAGE,
        )


def enforce_free_trial_upload_limit(
    *,
    db: Session,
    current_user: User,
    meeting: Meeting,
) -> None:
    if meeting.raw_media_path:
        return

    plan_code = get_effective_plan(db=db, user=current_user)
    monthly_limit = monthly_upload_limit_for_plan(plan_code)

    if monthly_limit is not None:
        used_slots = count_monthly_uploaded_meeting_slots(
            db,
            user_id=current_user.id,
            exclude_meeting_id=meeting.id,
        )
        if used_slots >= monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=PAID_MONTHLY_LIMIT_MESSAGE,
            )
        return

    limit = upload_limit_for_user(current_user)
    used_slots = count_uploaded_meeting_slots(
        db,
        user_id=current_user.id,
        exclude_meeting_id=meeting.id,
    )

    if used_slots >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=FREE_TRIAL_LIMIT_MESSAGE,
        )


def record_upload_ledger_entry(
    *,
    db: Session,
    current_user: User,
    meeting: Meeting,
    original_filename: str | None,
    file_size_bytes: int | None,
    content_type: str | None,
    storage_key: str | None,
) -> UploadLedger:
    existing = (
        db.query(UploadLedger)
        .filter(
            UploadLedger.user_id == str(current_user.id),
            UploadLedger.meeting_id == str(meeting.id),
            UploadLedger.counted_at.isnot(None),
            UploadLedger.deleted_at.is_(None),
        )
        .first()
    )
    if existing is not None:
        return existing

    now = datetime.now(timezone.utc)
    ledger = UploadLedger(
        id=uuid.uuid4().hex,
        user_id=str(current_user.id),
        account_id=None,
        meeting_id=str(meeting.id),
        original_filename=original_filename,
        file_size_bytes=file_size_bytes,
        content_type=content_type,
        storage_key=storage_key,
        status="counted",
        counted_at=now,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )
    db.add(ledger)
    return ledger


def enforce_free_trial_duration_limit(
    *,
    db: Session | None = None,
    current_user: User,
    duration_seconds: float | None,
) -> None:
    if duration_seconds is None:
        return

    max_seconds = None
    if db is not None:
        plan_code = get_effective_plan(db=db, user=current_user)
        max_seconds = max_duration_seconds_for_plan(plan_code)

    if max_seconds is None:
        max_seconds = max_duration_seconds_for_user(current_user)

    if duration_seconds <= max_seconds:
        return

    max_minutes = max_seconds // 60
    detected_minutes = round(duration_seconds / 60, 1)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"This recording is about {detected_minutes} minutes. "
            f"Your current limit is {max_minutes} minutes. "
            "Please upload a shorter recording, upgrade, or contact support."
        ),
    )


CONFIDENTIAL_MODE_PLAN_CODES = {
    "pro_pilot",
    "business",
    "team",
    "premium",
    "custom",
    "enterprise",
}


def can_use_confidential_mode(*, db: Session, current_user: User) -> bool:
    """Return whether the current user can enable Confidential Mode.

    Confidential Mode is a premium feature. Normal uploads remain available
    to all users; this helper only gates confidential_mode=true.
    """

    plan_code = get_effective_plan(db=db, user=current_user)
    return str(plan_code or "").strip().lower() in CONFIDENTIAL_MODE_PLAN_CODES
