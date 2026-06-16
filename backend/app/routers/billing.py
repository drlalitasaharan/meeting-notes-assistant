from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.services.billing import (
    cancel_manual_paid_access,
    get_billing_status,
    grant_manual_paid_access,
)

router = APIRouter(tags=["billing"])


class ManualUpgradeRequest(BaseModel):
    user_email: EmailStr
    plan_code: str = "paid_pro"
    reason: str | None = None
    ends_at: datetime | None = None


class ManualCancelRequest(BaseModel):
    user_email: EmailStr


@router.get("/v1/billing/status")
def billing_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return get_billing_status(db=db, user=current_user)


@router.post("/v1/admin/billing/manual-upgrade")
def admin_manual_billing_upgrade(
    payload: ManualUpgradeRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict[str, Any]:
    user = db.query(User).filter(User.email == payload.user_email.lower().strip()).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    override = grant_manual_paid_access(
        db=db,
        user=user,
        granted_by_admin_email=admin_user.email,
        reason=payload.reason,
        ends_at=payload.ends_at,
        plan_code=payload.plan_code,
    )

    return {
        "status": "ok",
        "user_id": user.id,
        "user_email": user.email,
        "plan_code": override.plan_code,
        "billing_status": override.status,
        "source": "manual_override",
    }


@router.post("/v1/admin/billing/manual-cancel")
def admin_manual_billing_cancel(
    payload: ManualCancelRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    user = db.query(User).filter(User.email == payload.user_email.lower().strip()).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    canceled = cancel_manual_paid_access(db=db, user=user)
    return {
        "status": "ok",
        "user_id": user.id,
        "user_email": user.email,
        "canceled": canceled,
    }
