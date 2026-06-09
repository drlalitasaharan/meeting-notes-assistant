from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.deps import get_current_user, require_admin
from app.main import app


def test_require_admin_allows_allowlisted_email(monkeypatch):
    monkeypatch.setenv(
        "ADMIN_EMAILS",
        "owner@example.com, second-admin@example.com",
    )
    user = SimpleNamespace(email="OWNER@example.com")

    assert require_admin(user) is user


def test_require_admin_rejects_non_admin(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "owner@example.com")
    user = SimpleNamespace(email="customer@example.com")

    with pytest.raises(HTTPException) as exc_info:
        require_admin(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin access required."


def test_require_admin_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ADMIN_EMAILS", raising=False)
    user = SimpleNamespace(email="owner@example.com")

    with pytest.raises(HTTPException) as exc_info:
        require_admin(user)

    assert exc_info.value.status_code == 403


def test_non_admin_cannot_access_admin_overview(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "owner@example.com")

    def override_current_user():
        return SimpleNamespace(email="customer@example.com")

    app.dependency_overrides[get_current_user] = override_current_user

    try:
        client = TestClient(app)
        response = client.get("/v1/admin/overview")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}


def test_admin_routes_are_registered():
    route_paths = {route.path for route in app.routes}

    assert "/v1/admin/overview" in route_paths
    assert "/v1/admin/meetings" in route_paths
    assert "/v1/admin/system-health" in route_paths
