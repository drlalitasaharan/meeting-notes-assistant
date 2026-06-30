from __future__ import annotations

import os
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.deps import get_current_user
from app.models.user import User
from app.services.billing import get_effective_plan
from app.services.usage_limits import (
    count_monthly_uploaded_meeting_slots,
    count_uploaded_meeting_slots,
    max_duration_seconds_for_plan,
    max_duration_seconds_for_user,
    monthly_upload_limit_for_plan,
    upload_limit_for_user,
)

router = APIRouter(prefix="/v1/usage", tags=["usage"])


class UsageRead(BaseModel):
    plan: str
    is_pilot_override: bool
    meetings_used: int
    meeting_upload_limit: int
    remaining_uploads: int
    max_duration_seconds: int
    max_duration_minutes: int


def _get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _pilot_override_emails() -> set[str]:
    return {
        item.strip().lower()
        for item in os.getenv("MEETIQ_PILOT_OVERRIDE_EMAILS", "").split(",")
        if item.strip()
    }


def _is_pilot_user(user: User) -> bool:
    return user.email.strip().lower() in _pilot_override_emails()


@router.get("/me", response_model=UsageRead)
def get_my_usage(
    db: Session = Depends(_get_db),
    current_user: User = Depends(get_current_user),
) -> UsageRead:
    effective_plan = get_effective_plan(db=db, user=current_user)
    monthly_limit = monthly_upload_limit_for_plan(effective_plan)
    is_pilot = _is_pilot_user(current_user)

    if monthly_limit is not None:
        upload_limit = monthly_limit
        meetings_used = count_monthly_uploaded_meeting_slots(db, user_id=current_user.id)
        plan = effective_plan
    else:
        upload_limit = upload_limit_for_user(current_user)
        meetings_used = count_uploaded_meeting_slots(db, user_id=current_user.id)
        plan = "pilot" if is_pilot else "free_trial"

    remaining_uploads = max(0, upload_limit - meetings_used)
    plan_max_duration_seconds = max_duration_seconds_for_plan(effective_plan)
    max_duration_seconds = (
        plan_max_duration_seconds
        if plan_max_duration_seconds is not None
        else max_duration_seconds_for_user(current_user)
    )

    return UsageRead(
        plan=plan,
        is_pilot_override=is_pilot,
        meetings_used=meetings_used,
        meeting_upload_limit=upload_limit,
        remaining_uploads=remaining_uploads,
        max_duration_seconds=max_duration_seconds,
        max_duration_minutes=max_duration_seconds // 60,
    )
