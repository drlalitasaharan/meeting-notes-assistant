from __future__ import annotations

import uuid
from datetime import datetime

from app.core.db import SessionLocal
from app.models.billing import BillingPaymentAttempt, BillingSubscription
from app.models.user import User


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Admin",
            "last_name": "Billing",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def test_admin_billing_overview_requires_admin(client, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "admin-only@example.com")
    user_email = f"billing-viewer-{uuid.uuid4().hex}@example.com"
    token = _signup(client, user_email)

    response = client.get(
        "/v1/admin/billing/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_billing_overview_returns_subscription_and_attempts(client, monkeypatch):
    admin_email = f"billing-admin-{uuid.uuid4().hex}@example.com"
    paid_user_email = f"paid-user-{uuid.uuid4().hex}@example.com"
    monkeypatch.setenv("ADMIN_EMAILS", admin_email)

    admin_token = _signup(client, admin_email)
    _signup(client, paid_user_email)

    db = SessionLocal()
    try:
        paid_user = db.query(User).filter(User.email == paid_user_email).first()
        assert paid_user is not None

        subscription = BillingSubscription(
            user_id=paid_user.id,
            provider="paypal",
            provider_subscription_id=f"ORDER-{uuid.uuid4().hex}",
            provider_payment_id=f"CAPTURE-{uuid.uuid4().hex}",
            plan_code="paid_pro",
            status="active",
        )
        attempt = BillingPaymentAttempt(
            user_id=paid_user.id,
            provider="paypal",
            attempt_reference=f"meetiq-{uuid.uuid4().hex}",
            provider_order_id=subscription.provider_subscription_id,
            provider_capture_id=subscription.provider_payment_id,
            plan_code="paid_pro",
            amount_cents=1000,
            currency_code="USD",
            status="captured",
            completed_at=datetime.utcnow(),
        )
        db.add_all([subscription, attempt])
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/v1/admin/billing/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["active_paid_users"] >= 1
    assert payload["active_subscriptions"] >= 1
    assert payload["total_payment_attempts"] >= 1
    assert payload["successful_payment_attempts"] >= 1
    assert any(item["user_email"] == paid_user_email for item in payload["recent_subscriptions"])
    assert any(item["user_email"] == paid_user_email for item in payload["recent_payment_attempts"])
