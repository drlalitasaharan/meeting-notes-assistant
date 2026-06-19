from __future__ import annotations

import uuid
from typing import Any

from app.core.db import SessionLocal
from app.models.billing import BillingPaymentAttempt, BillingSubscription


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "PayPal",
            "last_name": "Checkout",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def _configure_paypal_env(monkeypatch) -> None:
    monkeypatch.setenv("PAYPAL_ENV", "sandbox")
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("MEETIQ_FRONTEND_BASE_URL", "https://meetiq.example.com")


class FakePayPalResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"fake PayPal status {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


def test_paypal_create_checkout_requires_auth(client):
    response = client.post("/v1/billing/paypal/create-checkout")

    assert response.status_code in (401, 403)


def test_paypal_create_checkout_rejects_invalid_plan_code(client):
    email = f"paypal-invalid-plan-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/paypal/create-checkout",
        json={"plan_code": "business"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Unsupported PayPal checkout plan" in response.json()["detail"]


def test_paypal_create_checkout_returns_starter_checkout_and_records_attempt(
    client,
    monkeypatch,
):
    _configure_paypal_env(monkeypatch)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    approval_url = f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_post(url: str, **kwargs: Any) -> FakePayPalResponse:
        calls.append((url, kwargs))

        if url.endswith("/v1/oauth2/token"):
            return FakePayPalResponse({"access_token": "test-access-token"})

        if url.endswith("/v2/checkout/orders"):
            headers = kwargs.get("headers")
            assert isinstance(headers, dict)
            assert headers["Authorization"] == "Bearer test-access-token"

            order_request = kwargs.get("json")
            assert isinstance(order_request, dict)
            assert order_request["intent"] == "CAPTURE"
            assert (
                order_request["application_context"]["return_url"]
                == "https://meetiq.example.com/billing/success"
            )
            assert (
                order_request["application_context"]["cancel_url"]
                == "https://meetiq.example.com/billing/cancel"
            )

            purchase_unit = order_request["purchase_units"][0]
            assert purchase_unit["description"] == "MeetIQ Starter"
            assert purchase_unit["amount"] == {"currency_code": "USD", "value": "23.00"}
            assert purchase_unit["custom_id"].startswith("meetiq-")
            assert purchase_unit["reference_id"] == purchase_unit["custom_id"]

            return FakePayPalResponse(
                {
                    "id": order_id,
                    "status": "PAYER_ACTION_REQUIRED",
                    "links": [
                        {
                            "rel": "approve",
                            "href": approval_url,
                            "method": "GET",
                        }
                    ],
                }
            )

        raise AssertionError(f"Unexpected PayPal URL: {url}")

    monkeypatch.setattr("app.services.paypal_checkout.httpx.post", fake_post)

    email = f"paypal-starter-checkout-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/paypal/create-checkout",
        json={"plan_code": "starter"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "created"
    assert payload["provider"] == "paypal"
    assert payload["provider_order_id"] == order_id
    assert payload["approval_url"] == approval_url
    assert payload["plan_code"] == "starter"
    assert payload["amount_cents"] == 2300
    assert payload["currency_code"] == "USD"

    assert len(calls) == 2

    db = SessionLocal()
    try:
        attempt = (
            db.query(BillingPaymentAttempt)
            .filter(BillingPaymentAttempt.provider_order_id == order_id)
            .one()
        )
        assert attempt.provider == "paypal"
        assert attempt.status == "created"
        assert attempt.checkout_url == approval_url
        assert attempt.plan_code == "starter"
        assert attempt.amount_cents == 2300
        assert attempt.currency_code == "USD"
        assert attempt.attempt_reference == payload["attempt_reference"]
    finally:
        db.close()


def test_paypal_create_checkout_supports_legacy_paid_pro_as_starter_equivalent(
    client,
    monkeypatch,
):
    _configure_paypal_env(monkeypatch)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    approval_url = f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"

    def fake_post(url: str, **kwargs: Any) -> FakePayPalResponse:
        if url.endswith("/v1/oauth2/token"):
            return FakePayPalResponse({"access_token": "test-access-token"})

        if url.endswith("/v2/checkout/orders"):
            order_request = kwargs.get("json")
            assert isinstance(order_request, dict)
            purchase_unit = order_request["purchase_units"][0]
            assert purchase_unit["description"] == "MeetIQ Starter"
            assert purchase_unit["amount"] == {"currency_code": "USD", "value": "23.00"}

            return FakePayPalResponse(
                {
                    "id": order_id,
                    "status": "PAYER_ACTION_REQUIRED",
                    "links": [
                        {
                            "rel": "approve",
                            "href": approval_url,
                            "method": "GET",
                        }
                    ],
                }
            )

        raise AssertionError(f"Unexpected PayPal URL: {url}")

    monkeypatch.setattr("app.services.paypal_checkout.httpx.post", fake_post)

    email = f"paypal-paid-pro-checkout-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/paypal/create-checkout",
        json={"plan_code": "paid_pro"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan_code"] == "paid_pro"
    assert payload["amount_cents"] == 2300


def test_paypal_create_checkout_returns_pro_pilot_checkout_and_records_attempt(
    client,
    monkeypatch,
):
    _configure_paypal_env(monkeypatch)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    approval_url = f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"

    def fake_post(url: str, **kwargs: Any) -> FakePayPalResponse:
        if url.endswith("/v1/oauth2/token"):
            return FakePayPalResponse({"access_token": "test-access-token"})

        if url.endswith("/v2/checkout/orders"):
            order_request = kwargs.get("json")
            assert isinstance(order_request, dict)
            purchase_unit = order_request["purchase_units"][0]
            assert purchase_unit["description"] == "MeetIQ Pro Pilot"
            assert purchase_unit["amount"] == {"currency_code": "USD", "value": "49.00"}

            return FakePayPalResponse(
                {
                    "id": order_id,
                    "status": "PAYER_ACTION_REQUIRED",
                    "links": [
                        {
                            "rel": "approve",
                            "href": approval_url,
                            "method": "GET",
                        }
                    ],
                }
            )

        raise AssertionError(f"Unexpected PayPal URL: {url}")

    monkeypatch.setattr("app.services.paypal_checkout.httpx.post", fake_post)

    email = f"paypal-pro-pilot-checkout-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/paypal/create-checkout",
        json={"plan_code": "pro_pilot"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "created"
    assert payload["provider"] == "paypal"
    assert payload["provider_order_id"] == order_id
    assert payload["approval_url"] == approval_url
    assert payload["plan_code"] == "pro_pilot"
    assert payload["amount_cents"] == 4900
    assert payload["currency_code"] == "USD"

    db = SessionLocal()
    try:
        attempt = (
            db.query(BillingPaymentAttempt)
            .filter(BillingPaymentAttempt.provider_order_id == order_id)
            .one()
        )
        assert attempt.provider == "paypal"
        assert attempt.status == "created"
        assert attempt.checkout_url == approval_url
        assert attempt.plan_code == "pro_pilot"
        assert attempt.amount_cents == 4900
        assert attempt.currency_code == "USD"
        assert attempt.attempt_reference == payload["attempt_reference"]
    finally:
        db.close()


def test_paypal_capture_checkout_captures_order_and_activates_selected_plan(
    client,
    monkeypatch,
):
    _configure_paypal_env(monkeypatch)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    capture_id = f"CAPTURE-{uuid.uuid4().hex}"
    approval_url = f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"
    calls: list[str] = []

    def fake_post(url: str, **kwargs: Any) -> FakePayPalResponse:
        calls.append(url)

        if url.endswith("/v1/oauth2/token"):
            return FakePayPalResponse({"access_token": "test-access-token"})

        if url.endswith("/v2/checkout/orders"):
            return FakePayPalResponse(
                {
                    "id": order_id,
                    "status": "PAYER_ACTION_REQUIRED",
                    "links": [
                        {
                            "rel": "approve",
                            "href": approval_url,
                            "method": "GET",
                        }
                    ],
                },
                status_code=201,
            )

        if url.endswith(f"/v2/checkout/orders/{order_id}/capture"):
            headers = kwargs.get("headers")
            assert isinstance(headers, dict)
            assert headers["Authorization"] == "Bearer test-access-token"

            return FakePayPalResponse(
                {
                    "id": order_id,
                    "status": "COMPLETED",
                    "purchase_units": [
                        {
                            "payments": {
                                "captures": [
                                    {
                                        "id": capture_id,
                                        "status": "COMPLETED",
                                    }
                                ]
                            }
                        }
                    ],
                },
                status_code=201,
            )

        raise AssertionError(f"Unexpected PayPal URL: {url}")

    monkeypatch.setattr("app.services.paypal_checkout.httpx.post", fake_post)

    email = f"paypal-capture-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    checkout_response = client.post(
        "/v1/billing/paypal/create-checkout",
        json={"plan_code": "pro_pilot"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert checkout_response.status_code == 200, checkout_response.text
    assert checkout_response.json()["provider_order_id"] == order_id
    assert checkout_response.json()["plan_code"] == "pro_pilot"
    assert checkout_response.json()["amount_cents"] == 4900

    capture_response = client.post(
        "/v1/billing/paypal/capture",
        json={"provider_order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert capture_response.status_code == 200, capture_response.text
    payload = capture_response.json()
    assert payload["status"] == "captured"
    assert payload["provider_order_id"] == order_id
    assert payload["provider_capture_id"] == capture_id
    assert payload["plan_code"] == "pro_pilot"
    assert payload["amount_cents"] == 4900
    assert payload["billing"]["plan_code"] == "pro_pilot"
    assert payload["billing"]["provider"] == "paypal"

    billing_status = client.get(
        "/v1/billing/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert billing_status.status_code == 200
    assert billing_status.json()["plan_code"] == "pro_pilot"
    assert billing_status.json()["provider"] == "paypal"

    # Idempotent second capture should not call PayPal capture again.
    calls_before_second_capture = len(calls)
    second_capture = client.post(
        "/v1/billing/paypal/capture",
        json={"provider_order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second_capture.status_code == 200, second_capture.text
    assert len(calls) == calls_before_second_capture

    db = SessionLocal()
    try:
        attempt = (
            db.query(BillingPaymentAttempt)
            .filter(BillingPaymentAttempt.provider_order_id == order_id)
            .one()
        )
        assert attempt.status == "captured"
        assert attempt.plan_code == "pro_pilot"
        assert attempt.amount_cents == 4900
        assert attempt.provider_capture_id == capture_id
        assert attempt.provider_payment_id == capture_id
        assert attempt.completed_at is not None

        subscription = (
            db.query(BillingSubscription)
            .filter(
                BillingSubscription.provider == "paypal",
                BillingSubscription.provider_subscription_id == order_id,
            )
            .one()
        )
        assert subscription.status == "active"
        assert subscription.plan_code == "pro_pilot"
        assert subscription.provider_payment_id == capture_id
    finally:
        db.close()
