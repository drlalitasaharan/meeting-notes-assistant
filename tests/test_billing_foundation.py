from __future__ import annotations

import os
import uuid

from app.core.db import SessionLocal
from app.models.user import User
from app.services.billing import get_effective_plan, grant_manual_paid_access


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Billing",
            "last_name": "Tester",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def test_billing_status_defaults_to_free_trial(client):
    email = f"billing-free-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.get(
        "/v1/billing/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["plan_code"] == "free_trial"
    assert response.json()["billing_status"] == "free_trial"


def test_manual_paid_access_changes_effective_plan(client):
    email = f"billing-paid-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        grant_manual_paid_access(
            db=db,
            user=user,
            granted_by_admin_email="admin@example.com",
            reason="test paid access",
        )
        assert get_effective_plan(db=db, user=user) == "paid_pro"
    finally:
        db.close()

    response = client.get(
        "/v1/billing/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["plan_code"] == "paid_pro"
    assert response.json()["provider"] == "manual"


def test_admin_manual_upgrade_endpoint_requires_admin(client, monkeypatch):
    admin_email = f"billing-admin-{uuid.uuid4().hex}@example.com"
    target_email = f"billing-target-{uuid.uuid4().hex}@example.com"

    monkeypatch.setenv("ADMIN_EMAILS", admin_email)

    admin_token = _signup(client, admin_email)
    _signup(client, target_email)

    response = client.post(
        "/v1/admin/billing/manual-upgrade",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "user_email": target_email,
            "reason": "paid by invoice",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["plan_code"] == "paid_pro"

    # Avoid leaking this admin setting into later tests.
    monkeypatch.setenv("ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", ""))
