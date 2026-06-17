from __future__ import annotations

import uuid

from app.core.db import SessionLocal
from app.models.billing import BillingPaymentAttempt
from app.models.user import User


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Billing",
            "last_name": "Attempt",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def test_billing_payment_attempt_can_be_stored(client):
    email = f"billing-attempt-{uuid.uuid4().hex}@example.com"
    _signup(client, email)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        attempt_reference = f"meetiq-{uuid.uuid4().hex}"
        provider_order_id = f"ORDER-{uuid.uuid4().hex}"

        attempt = BillingPaymentAttempt(
            user_id=user.id,
            provider="paypal",
            attempt_reference=attempt_reference,
            provider_order_id=provider_order_id,
            checkout_url="https://www.sandbox.paypal.com/checkoutnow?token=test",
            plan_code="paid_pro",
            amount_cents=1000,
            currency_code="USD",
            status="created",
            payload_json={"source": "test"},
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        saved = (
            db.query(BillingPaymentAttempt)
            .filter(BillingPaymentAttempt.attempt_reference == attempt_reference)
            .one()
        )

        assert saved.user_id == user.id
        assert saved.provider == "paypal"
        assert saved.provider_order_id == provider_order_id
        assert saved.plan_code == "paid_pro"
        assert saved.amount_cents == 1000
        assert saved.currency_code == "USD"
        assert saved.status == "created"
    finally:
        db.close()
