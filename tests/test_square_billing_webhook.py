from __future__ import annotations

import uuid

from app.core.db import SessionLocal
from app.models.billing import BillingEvent, BillingPaymentAttempt, BillingSubscription
from app.models.user import User


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Square",
            "last_name": "Tester",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def _square_payment_event(
    *,
    event_id: str,
    email: str,
    payment_id: str,
    status: str = "COMPLETED",
    order_id: str | None = None,
) -> dict:
    payment = {
        "id": payment_id,
        "status": status,
        "buyer_email_address": email,
        "note": f"meetiq:{email}",
    }
    if order_id:
        payment["order_id"] = order_id

    return {
        "event_id": event_id,
        "type": "payment.updated",
        "data": {
            "id": payment_id,
            "object": {
                "payment": payment,
            },
        },
    }


def _square_invoice_event(
    *,
    event_id: str,
    email: str,
    invoice_id: str,
    event_type: str = "invoice.payment_made",
) -> dict:
    return {
        "event_id": event_id,
        "type": event_type,
        "data": {
            "id": invoice_id,
            "object": {
                "invoice": {
                    "id": invoice_id,
                    "description": f"meetiq:{email}",
                    "primary_recipient": {
                        "email_address": email,
                    },
                }
            },
        },
    }


def test_square_payment_updated_activates_paid_access(client, monkeypatch):
    monkeypatch.setenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"square-paid-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)
    payment_id = f"pay-{uuid.uuid4().hex}"
    event_id = f"evt-{uuid.uuid4().hex}"

    response = client.post(
        "/v1/billing/square/webhook",
        json=_square_payment_event(
            event_id=event_id,
            email=email,
            payment_id=payment_id,
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
    assert billing_status.json()["provider"] == "square"

    db = SessionLocal()
    try:
        assert (
            db.query(BillingEvent).filter(BillingEvent.provider_event_id == event_id).count() == 1
        )
        assert (
            db.query(BillingSubscription)
            .filter(
                BillingSubscription.provider == "square",
                BillingSubscription.provider_payment_id == payment_id,
                BillingSubscription.status == "active",
            )
            .count()
            == 1
        )
    finally:
        db.close()


def test_square_webhook_is_idempotent(client, monkeypatch):
    monkeypatch.setenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"square-duplicate-{uuid.uuid4().hex}@example.com"
    _signup(client, email)

    payment_id = f"pay-{uuid.uuid4().hex}"
    event_id = f"evt-{uuid.uuid4().hex}"
    payload = _square_payment_event(
        event_id=event_id,
        email=email,
        payment_id=payment_id,
    )

    first = client.post("/v1/billing/square/webhook", json=payload)
    second = client.post("/v1/billing/square/webhook", json=payload)

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
            .filter(BillingSubscription.provider_payment_id == payment_id)
            .count()
            == 1
        )
    finally:
        db.close()


def test_square_unmatched_email_does_not_activate_access(client, monkeypatch):
    monkeypatch.setenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "true")

    event_id = f"evt-{uuid.uuid4().hex}"
    payment_id = f"pay-{uuid.uuid4().hex}"

    response = client.post(
        "/v1/billing/square/webhook",
        json=_square_payment_event(
            event_id=event_id,
            email=f"missing-{uuid.uuid4().hex}@example.com",
            payment_id=payment_id,
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
            .filter(BillingSubscription.provider_payment_id == payment_id)
            .count()
            == 0
        )
    finally:
        db.close()


def test_square_invoice_payment_made_activates_paid_access(client, monkeypatch):
    monkeypatch.setenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"square-invoice-{uuid.uuid4().hex}@example.com"
    _signup(client, email)
    invoice_id = f"inv-{uuid.uuid4().hex}"
    event_id = f"evt-{uuid.uuid4().hex}"

    response = client.post(
        "/v1/billing/square/webhook",
        json=_square_invoice_event(
            event_id=event_id,
            email=email,
            invoice_id=invoice_id,
        ),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "processed"
    assert response.json()["provider"] == "square"

    db = SessionLocal()
    try:
        assert (
            db.query(BillingSubscription)
            .filter(
                BillingSubscription.provider == "square",
                BillingSubscription.provider_subscription_id == invoice_id,
                BillingSubscription.status == "active",
            )
            .count()
            == 1
        )
    finally:
        db.close()


def test_square_invoice_cancel_event_cancels_matching_subscription(client, monkeypatch):
    monkeypatch.setenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"square-cancel-{uuid.uuid4().hex}@example.com"
    _signup(client, email)
    invoice_id = f"inv-{uuid.uuid4().hex}"

    active_response = client.post(
        "/v1/billing/square/webhook",
        json=_square_invoice_event(
            event_id=f"evt-{uuid.uuid4().hex}",
            email=email,
            invoice_id=invoice_id,
        ),
    )
    assert active_response.status_code == 200, active_response.text

    cancel_response = client.post(
        "/v1/billing/square/webhook",
        json=_square_invoice_event(
            event_id=f"evt-{uuid.uuid4().hex}",
            email=email,
            invoice_id=invoice_id,
            event_type="invoice.canceled",
        ),
    )

    assert cancel_response.status_code == 200, cancel_response.text
    assert cancel_response.json()["status"] == "processed"
    assert cancel_response.json()["canceled"] is True

    db = SessionLocal()
    try:
        subscription = (
            db.query(BillingSubscription)
            .filter(BillingSubscription.provider_subscription_id == invoice_id)
            .one()
        )
        assert subscription.status == "canceled"
    finally:
        db.close()


def test_square_webhook_preserves_checkout_attempt_plan_code(client, monkeypatch):
    monkeypatch.setenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "true")

    email = f"square-pro-pilot-webhook-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)
    order_id = f"ORDER-{uuid.uuid4().hex}"
    payment_id = f"pay-{uuid.uuid4().hex}"
    attempt_reference = f"meetiq-{uuid.uuid4().hex}"
    event_id = f"evt-{uuid.uuid4().hex}"

    db = SessionLocal()
    try:
        from app.models.user import User

        user = db.query(User).filter(User.email == email).one()
        attempt = BillingPaymentAttempt(
            user_id=user.id,
            provider="square",
            attempt_reference=attempt_reference,
            provider_order_id=order_id,
            checkout_url="https://square.link/u/test",
            plan_code="pro_pilot",
            amount_cents=4900,
            currency_code="USD",
            status="created",
            payload_json={"source": "test"},
        )
        db.add(attempt)
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/v1/billing/square/webhook",
        json=_square_payment_event(
            event_id=event_id,
            email=email,
            payment_id=payment_id,
            order_id=order_id,
        ),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "processed"
    assert response.json()["plan_code"] == "pro_pilot"

    billing_status = client.get(
        "/v1/billing/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert billing_status.status_code == 200
    assert billing_status.json()["plan_code"] == "pro_pilot"
    assert billing_status.json()["provider"] == "square"

    db = SessionLocal()
    try:
        subscription = (
            db.query(BillingSubscription)
            .filter(
                BillingSubscription.provider == "square",
                BillingSubscription.provider_subscription_id == order_id,
            )
            .one()
        )
        assert subscription.status == "active"
        assert subscription.plan_code == "pro_pilot"
        assert subscription.provider_payment_id == payment_id

        attempt = (
            db.query(BillingPaymentAttempt)
            .filter(BillingPaymentAttempt.provider_order_id == order_id)
            .one()
        )
        assert attempt.status == "captured"
        assert attempt.plan_code == "pro_pilot"
        assert attempt.provider_payment_id == payment_id
        assert attempt.completed_at is not None
    finally:
        db.close()


def test_square_payment_updated_prefers_meetiq_note_email_over_buyer_email(
    client,
    monkeypatch,
):
    monkeypatch.setenv("SQUARE_WEBHOOK_VERIFY_DISABLED", "true")

    meetiq_email = f"square-note-account-{uuid.uuid4().hex}@example.com"
    payer_email = f"square-payer-{uuid.uuid4().hex}@example.com"
    token = _signup(client, meetiq_email)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    payment_id = f"pay-{uuid.uuid4().hex}"
    event_id = f"evt-{uuid.uuid4().hex}"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == meetiq_email).one()
        attempt = BillingPaymentAttempt(
            user_id=user.id,
            provider="square",
            attempt_reference=f"meetiq-{uuid.uuid4().hex}",
            provider_order_id=order_id,
            plan_code="starter",
            amount_cents=2300,
            currency_code="USD",
            status="created",
        )
        db.add(attempt)
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/v1/billing/square/webhook",
        json={
            "event_id": event_id,
            "type": "payment.updated",
            "data": {
                "id": payment_id,
                "object": {
                    "payment": {
                        "id": payment_id,
                        "status": "COMPLETED",
                        "buyer_email_address": payer_email,
                        "note": f"meetiq:{meetiq_email}",
                        "order_id": order_id,
                    }
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "processed"
    assert response.json()["plan_code"] == "starter"

    billing_status = client.get(
        "/v1/billing/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert billing_status.status_code == 200
    assert billing_status.json()["plan_code"] == "starter"
    assert billing_status.json()["provider"] == "square"

    db = SessionLocal()
    try:
        assert (
            db.query(BillingSubscription)
            .filter(
                BillingSubscription.provider == "square",
                BillingSubscription.provider_subscription_id == order_id,
                BillingSubscription.provider_payment_id == payment_id,
                BillingSubscription.plan_code == "starter",
                BillingSubscription.status == "active",
            )
            .count()
            == 1
        )
        assert (
            db.query(BillingPaymentAttempt)
            .filter(
                BillingPaymentAttempt.provider == "square",
                BillingPaymentAttempt.provider_order_id == order_id,
                BillingPaymentAttempt.provider_payment_id == payment_id,
                BillingPaymentAttempt.status == "captured",
            )
            .count()
            == 1
        )
    finally:
        db.close()
