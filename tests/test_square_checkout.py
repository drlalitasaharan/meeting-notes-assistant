from __future__ import annotations

import uuid
from typing import Any

from app.core.db import SessionLocal
from app.models.billing import BillingPaymentAttempt


def _signup(client, email: str) -> str:
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Square",
            "last_name": "Checkout",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["access_token"]


def _configure_square_env(monkeypatch) -> None:
    monkeypatch.setenv("SQUARE_ENV", "sandbox")
    monkeypatch.setenv("SQUARE_ACCESS_TOKEN", "test-square-token")
    monkeypatch.setenv("SQUARE_LOCATION_ID", "test-location-id")
    monkeypatch.setenv("MEETIQ_FRONTEND_BASE_URL", "https://meetiq.example.com")


class FakeSquareResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"fake Square status {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


def test_square_create_checkout_requires_auth(client):
    response = client.post("/v1/billing/square/create-checkout")

    assert response.status_code in (401, 403)


def test_square_create_checkout_rejects_invalid_plan_code(client):
    email = f"square-invalid-plan-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/square/create-checkout",
        json={"plan_code": "business"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Unsupported Square checkout plan" in response.json()["detail"]


def test_square_create_checkout_returns_starter_checkout_and_records_attempt(
    client,
    monkeypatch,
):
    _configure_square_env(monkeypatch)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    payment_link_id = f"plink-{uuid.uuid4().hex}"
    checkout_url = f"https://square.link/u/{payment_link_id}"

    def fake_post(url: str, **kwargs: Any) -> FakeSquareResponse:
        assert url.endswith("/v2/online-checkout/payment-links")
        headers = kwargs.get("headers")
        assert isinstance(headers, dict)
        assert headers["Authorization"] == "Bearer test-square-token"

        request_payload = kwargs.get("json")
        assert isinstance(request_payload, dict)
        assert request_payload["quick_pay"]["name"] == "MeetIQ Starter"
        assert request_payload["quick_pay"]["price_money"] == {
            "amount": 2300,
            "currency": "USD",
        }
        assert request_payload["quick_pay"]["location_id"] == "test-location-id"
        assert request_payload["checkout_options"]["redirect_url"].startswith(
            "https://meetiq.example.com/billing/square/success?attempt_reference="
        )

        return FakeSquareResponse(
            {
                "payment_link": {
                    "id": payment_link_id,
                    "order_id": order_id,
                    "url": checkout_url,
                }
            }
        )

    monkeypatch.setattr("app.services.square_checkout.httpx.post", fake_post)

    email = f"square-starter-checkout-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/square/create-checkout",
        json={"plan_code": "starter"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "created"
    assert payload["provider"] == "square"
    assert payload["provider_order_id"] == order_id
    assert payload["checkout_url"] == checkout_url
    assert payload["approval_url"] == checkout_url
    assert payload["plan_code"] == "starter"
    assert payload["amount_cents"] == 2300
    assert payload["currency_code"] == "USD"

    db = SessionLocal()
    try:
        attempt = (
            db.query(BillingPaymentAttempt)
            .filter(BillingPaymentAttempt.provider_order_id == order_id)
            .one()
        )
        assert attempt.provider == "square"
        assert attempt.status == "created"
        assert attempt.checkout_url == checkout_url
        assert attempt.plan_code == "starter"
        assert attempt.amount_cents == 2300
        assert attempt.currency_code == "USD"
    finally:
        db.close()


def test_square_create_checkout_returns_pro_pilot_checkout_and_records_attempt(
    client,
    monkeypatch,
):
    _configure_square_env(monkeypatch)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    payment_link_id = f"plink-{uuid.uuid4().hex}"
    checkout_url = f"https://square.link/u/{payment_link_id}"

    def fake_post(url: str, **kwargs: Any) -> FakeSquareResponse:
        assert url.endswith("/v2/online-checkout/payment-links")

        request_payload = kwargs.get("json")
        assert isinstance(request_payload, dict)
        assert request_payload["quick_pay"]["name"] == "MeetIQ Pro Pilot"
        assert request_payload["quick_pay"]["price_money"] == {
            "amount": 4900,
            "currency": "USD",
        }

        return FakeSquareResponse(
            {
                "payment_link": {
                    "id": payment_link_id,
                    "order_id": order_id,
                    "url": checkout_url,
                }
            }
        )

    monkeypatch.setattr("app.services.square_checkout.httpx.post", fake_post)

    email = f"square-pro-pilot-checkout-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/square/create-checkout",
        json={"plan_code": "pro_pilot"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["provider"] == "square"
    assert payload["provider_order_id"] == order_id
    assert payload["checkout_url"] == checkout_url
    assert payload["plan_code"] == "pro_pilot"
    assert payload["amount_cents"] == 4900


def test_square_create_checkout_supports_legacy_paid_pro_as_starter_equivalent(
    client,
    monkeypatch,
):
    _configure_square_env(monkeypatch)

    order_id = f"ORDER-{uuid.uuid4().hex}"
    payment_link_id = f"plink-{uuid.uuid4().hex}"
    checkout_url = f"https://square.link/u/{payment_link_id}"

    def fake_post(url: str, **kwargs: Any) -> FakeSquareResponse:
        request_payload = kwargs.get("json")
        assert isinstance(request_payload, dict)
        assert request_payload["quick_pay"]["name"] == "MeetIQ Starter"
        assert request_payload["quick_pay"]["price_money"] == {
            "amount": 2300,
            "currency": "USD",
        }

        return FakeSquareResponse(
            {
                "payment_link": {
                    "id": payment_link_id,
                    "order_id": order_id,
                    "url": checkout_url,
                }
            }
        )

    monkeypatch.setattr("app.services.square_checkout.httpx.post", fake_post)

    email = f"square-paid-pro-checkout-{uuid.uuid4().hex}@example.com"
    token = _signup(client, email)

    response = client.post(
        "/v1/billing/square/create-checkout",
        json={"plan_code": "paid_pro"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan_code"] == "paid_pro"
    assert payload["amount_cents"] == 2300


def test_square_api_base_uses_production_url_for_production_env(monkeypatch) -> None:
    from app.services.square_checkout import _square_api_base

    monkeypatch.setenv("SQUARE_ENV", "production")

    assert _square_api_base() == "https://connect.squareup.com"


def test_square_api_base_uses_production_url_for_live_env(monkeypatch) -> None:
    from app.services.square_checkout import _square_api_base

    monkeypatch.setenv("SQUARE_ENV", "live")

    assert _square_api_base() == "https://connect.squareup.com"


def test_square_api_base_uses_sandbox_url_for_sandbox_env(monkeypatch) -> None:
    from app.services.square_checkout import _square_api_base

    monkeypatch.setenv("SQUARE_ENV", "sandbox")

    assert _square_api_base() == "https://connect.squareupsandbox.com"
