from __future__ import annotations

import os

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.user import User

DEFAULT_FREE_TRIAL_UPLOAD_LIMIT = 1
DEFAULT_FREE_TRIAL_MAX_DURATION_SECONDS = 30 * 60
DEFAULT_PILOT_UPLOAD_LIMIT = 3
DEFAULT_PILOT_MAX_DURATION_SECONDS = 60 * 60


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
    query = db.query(func.count(Meeting.id)).filter(
        Meeting.user_id == user_id,
        Meeting.raw_media_path.isnot(None),
    )

    if exclude_meeting_id is not None:
        query = query.filter(Meeting.id != exclude_meeting_id)

    return int(query.scalar() or 0)


def enforce_free_trial_upload_limit(
    *,
    db: Session,
    current_user: User,
    meeting: Meeting,
) -> None:
    if meeting.raw_media_path:
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
            detail=(
                "Free trial limit reached. Your free trial includes 1 meeting upload "
                "up to 30 minutes. Please upgrade or contact support to continue."
            ),
        )


def enforce_free_trial_duration_limit(
    *,
    current_user: User,
    duration_seconds: float | None,
) -> None:
    if duration_seconds is None:
        return

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
