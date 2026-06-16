from __future__ import annotations

import uuid

from app.core.db import SessionLocal
from app.models.billing import BillingEvent, BillingSubscription


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "PayPal",
            "last_name": "Tester",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def _paypal_event(
    *,
    event_id: str,
    event_type: str,
    email: str,
    subscription_id: str,
) -> dict:
    return {
        "id": event_id,
        "event_type": event_type,
        "resource": {
            "id": subscription_id,
            "custom_id": f"meetiq:{email}",
            "subscriber": {
                "email_address": email,
            },
            "billing_info": {
                "next_billing_time": "2026-07-16T00:00:00Z",
            },
        },
    }


def test_paypal_webhook_activates_paid_access(client, monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"paypal-paid-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)
    subscription_id = f"I-{uuid.uuid4().hex}"
    event_id = f"WH-{uuid.uuid4().hex}"

    response = client.post(
        "/v1/billing/paypal/webhook",
        json=_paypal_event(
            event_id=event_id,
            event_type="BILLING.SUBSCRIPTION.ACTIVATED",
            email=email,
            subscription_id=subscription_id,
        ),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "processed"
    assert response.json()["plan_code"] == "paid_pro"

    billing_status = client.get(
        "/v1/billing/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert billing_status.status_code == 200
    assert billing_status.json()["plan_code"] == "paid_pro"
    assert billing_status.json()["provider"] == "paypal"

    db = SessionLocal()
    try:
        assert (
            db.query(BillingEvent).filter(BillingEvent.provider_event_id == event_id).count() == 1
        )
        assert (
            db.query(BillingSubscription)
            .filter(
                BillingSubscription.provider == "paypal",
                BillingSubscription.provider_subscription_id == subscription_id,
                BillingSubscription.status == "active",
            )
            .count()
            == 1
        )
    finally:
        db.close()


def test_paypal_webhook_is_idempotent(client, monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"paypal-duplicate-{uuid.uuid4().hex}@example.com"
    _signup(client, email)

    event_id = f"WH-{uuid.uuid4().hex}"
    subscription_id = f"I-{uuid.uuid4().hex}"
    payload = _paypal_event(
        event_id=event_id,
        event_type="PAYMENT.SALE.COMPLETED",
        email=email,
        subscription_id=subscription_id,
    )

    first = client.post("/v1/billing/paypal/webhook", json=payload)
    second = client.post("/v1/billing/paypal/webhook", json=payload)

    assert first.status_code == 200, first.text
    assert first.json()["status"] == "processed"
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "duplicate"

    db = SessionLocal()
    try:
        assert (
            db.query(BillingEvent).filter(BillingEvent.provider_event_id == event_id).count() == 1
        )
        assert (
            db.query(BillingSubscription)
            .filter(BillingSubscription.provider_subscription_id == subscription_id)
            .count()
            == 1
        )
    finally:
        db.close()


def test_paypal_webhook_unmatched_email_does_not_activate_access(client, monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_VERIFY_DISABLED", "true")

    event_id = f"WH-{uuid.uuid4().hex}"
    subscription_id = f"I-{uuid.uuid4().hex}"

    response = client.post(
        "/v1/billing/paypal/webhook",
        json=_paypal_event(
            event_id=event_id,
            event_type="BILLING.SUBSCRIPTION.ACTIVATED",
            email=f"missing-{uuid.uuid4().hex}@example.com",
            subscription_id=subscription_id,
        ),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "unmatched"

    db = SessionLocal()
    try:
        assert (
            db.query(BillingEvent).filter(BillingEvent.provider_event_id == event_id).count() == 1
        )
        assert (
            db.query(BillingSubscription)
            .filter(BillingSubscription.provider_subscription_id == subscription_id)
            .count()
            == 0
        )
    finally:
        db.close()


def test_paypal_cancel_event_cancels_matching_subscription(client, monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"paypal-cancel-{uuid.uuid4().hex}@example.com"
    _signup(client, email)
    subscription_id = f"I-{uuid.uuid4().hex}"

    active_response = client.post(
        "/v1/billing/paypal/webhook",
        json=_paypal_event(
            event_id=f"WH-{uuid.uuid4().hex}",
            event_type="BILLING.SUBSCRIPTION.ACTIVATED",
            email=email,
            subscription_id=subscription_id,
        ),
    )
    assert active_response.status_code == 200, active_response.text

    cancel_response = client.post(
        "/v1/billing/paypal/webhook",
        json=_paypal_event(
            event_id=f"WH-{uuid.uuid4().hex}",
            event_type="BILLING.SUBSCRIPTION.CANCELLED",
            email=email,
            subscription_id=subscription_id,
        ),
    )

    assert cancel_response.status_code == 200, cancel_response.text
    assert cancel_response.json()["status"] == "processed"
    assert cancel_response.json()["canceled"] is True

    db = SessionLocal()
    try:
        subscription = (
            db.query(BillingSubscription)
            .filter(BillingSubscription.provider_subscription_id == subscription_id)
            .one()
        )
        assert subscription.status == "canceled"
    finally:
        db.close()
