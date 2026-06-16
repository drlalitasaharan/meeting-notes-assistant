from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.services.billing import (
    cancel_manual_paid_access,
    get_billing_status,
    grant_manual_paid_access,
)
from app.services.paypal_webhooks import (
    PayPalWebhookVerificationError,
    process_paypal_webhook_event,
    verify_paypal_webhook_signature,
)
from app.services.square_webhooks import (
    SquareWebhookVerificationError,
    process_square_webhook_event,
    verify_square_webhook_signature,
)

router = APIRouter(tags=["billing"])


class ManualUpgradeRequest(BaseModel):
    user_email: EmailStr
    plan_code: str = "paid_pro"
    reason: str | None = None
    ends_at: datetime | None = None


class ManualCancelRequest(BaseModel):
    user_email: EmailStr


@router.post("/v1/billing/square/webhook")
async def square_billing_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    raw_body = await request.body()

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Square webhook JSON payload.",
        ) from None

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Square webhook payload.",
        )

    try:
        verified = verify_square_webhook_signature(
            headers=request.headers,
            raw_body=raw_body,
        )
    except SquareWebhookVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Square webhook signature verification failed.",
        )

    return process_square_webhook_event(db=db, payload=payload)


@router.post("/v1/billing/paypal/webhook")
async def paypal_billing_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    raw_body = await request.body()

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PayPal webhook JSON payload.",
        ) from None

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PayPal webhook payload.",
        )

    try:
        verified = verify_paypal_webhook_signature(
            headers=request.headers,
            webhook_event=payload,
        )
    except PayPalWebhookVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PayPal webhook signature verification failed.",
        )

    return process_paypal_webhook_event(db=db, payload=payload)


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
