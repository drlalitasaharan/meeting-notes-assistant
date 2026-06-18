from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.db import SessionLocal
from app.models.upload_ledger import UploadLedger
from app.models.user import User
from app.services.billing import grant_manual_paid_access


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Paid",
            "last_name": "Limit",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def _get_user(email: str) -> User:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).one()
    finally:
        db.close()


def _grant_plan(email: str, plan_code: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        grant_manual_paid_access(
            db=db,
            user=user,
            granted_by_admin_email="admin@example.com",
            reason="paid monthly upload limit test",
            plan_code=plan_code,
        )
    finally:
        db.close()


def _add_counted_uploads(user: User, count: int) -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        for index in range(count):
            db.add(
                UploadLedger(
                    id=uuid.uuid4().hex,
                    user_id=str(user.id),
                    account_id=None,
                    meeting_id=f"paid-limit-{uuid.uuid4().hex}-{index}",
                    original_filename="test.mp3",
                    file_size_bytes=123,
                    content_type="audio/mpeg",
                    storage_key=f"test/{uuid.uuid4().hex}.mp3",
                    status="counted",
                    counted_at=now,
                    created_at=now,
                    updated_at=now,
                    deleted_at=None,
                )
            )
        db.commit()
    finally:
        db.close()


def test_paid_pro_reports_starter_monthly_limit(client):
    email = f"paid-pro-usage-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)
    _grant_plan(email, "paid_pro")

    user = _get_user(email)
    _add_counted_uploads(user, 19)

    response = client.get(
        "/v1/usage/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan"] == "paid_pro"
    assert payload["meetings_used"] == 19
    assert payload["meeting_upload_limit"] == 20
    assert payload["remaining_uploads"] == 1


def test_paid_pro_blocks_after_twenty_monthly_uploads(client):
    email = f"paid-pro-block-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)
    _grant_plan(email, "paid_pro")

    user = _get_user(email)
    _add_counted_uploads(user, 20)

    response = client.post(
        "/v1/meetings",
        json={"title": "Blocked paid upload", "tags": "billing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 402
    assert "monthly upload allowance" in response.json()["detail"]


def test_pro_pilot_blocks_after_one_hundred_monthly_uploads(client):
    email = f"pro-pilot-block-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)
    _grant_plan(email, "pro_pilot")

    user = _get_user(email)
    _add_counted_uploads(user, 100)

    usage_response = client.get(
        "/v1/usage/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert usage_response.status_code == 200, usage_response.text
    usage = usage_response.json()
    assert usage["plan"] == "pro_pilot"
    assert usage["meeting_upload_limit"] == 100
    assert usage["remaining_uploads"] == 0

    response = client.post(
        "/v1/meetings",
        json={"title": "Blocked pro pilot upload", "tags": "billing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 402
    assert "monthly upload allowance" in response.json()["detail"]
