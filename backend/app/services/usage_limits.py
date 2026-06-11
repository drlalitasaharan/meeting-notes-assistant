from __future__ import annotations

import os

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.user import User

DEFAULT_FREE_TRIAL_UPLOAD_LIMIT = 1
DEFAULT_PILOT_UPLOAD_LIMIT = 3


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


def upload_limit_for_user(user: User) -> int:
    """
    Early commercial-readiness limit.

    Public free trial users receive 1 uploaded meeting slot.
    Selected pilot users can be allowlisted by email without a database migration.
    """
    pilot_override_emails = _csv_env("MEETIQ_PILOT_OVERRIDE_EMAILS")
    if user.email.strip().lower() in pilot_override_emails:
        return _int_env("MEETIQ_PILOT_UPLOAD_LIMIT", DEFAULT_PILOT_UPLOAD_LIMIT)

    return _int_env("MEETIQ_FREE_TRIAL_UPLOAD_LIMIT", DEFAULT_FREE_TRIAL_UPLOAD_LIMIT)


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
    """
    Enforce the current public free-trial promise before upload/storage/processing.

    Current public promise:
    Free Trial = 1 meeting upload up to 30 minutes.

    This first implementation enforces the 1-meeting upload slot.
    Duration-specific enforcement should be added once reliable duration metadata exists.
    """
    # If this meeting already has media, treat it as the user's existing slot.
    # This avoids blocking a same-meeting retry/replacement during early access.
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
