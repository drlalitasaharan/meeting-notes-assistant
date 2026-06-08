from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = str(Path(__file__).resolve().parents[1] / "backend")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

os.environ.setdefault("API_KEY", "dev-secret-123")

from app.core.db import get_db as core_get_db  # noqa: E402
from app.deps import get_db as deps_get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.models import meeting as _meeting  # noqa: F401,E402
from app.models import user as _user  # noqa: F401,E402

TEST_AUTH_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestAuthSession = sessionmaker(
    bind=TEST_AUTH_ENGINE,
    autoflush=False,
    autocommit=False,
)


def override_auth_test_db():
    db = TestAuthSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=TEST_AUTH_ENGINE)
    Base.metadata.create_all(bind=TEST_AUTH_ENGINE)

    app.dependency_overrides[core_get_db] = override_auth_test_db
    app.dependency_overrides[deps_get_db] = override_auth_test_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(core_get_db, None)
        app.dependency_overrides.pop(deps_get_db, None)
        Base.metadata.drop_all(bind=TEST_AUTH_ENGINE)


def test_signup_missing_first_name_rejected(client):
    payload = {
        "email": "nobody@example.com",
        "password": "supersecret",
        "last_name": "Smith",
    }
    resp = client.post("/v1/auth/signup", json=payload)
    assert resp.status_code == 422


def test_signup_missing_last_name_rejected(client):
    payload = {
        "email": "nobody@example.com",
        "password": "supersecret",
        "first_name": "Jane",
    }
    resp = client.post("/v1/auth/signup", json=payload)
    assert resp.status_code == 422


def test_signup_rejects_whitespace_only_first_or_last(client):
    payload = {
        "email": "jane@example.com",
        "password": "supersecret",
        "first_name": "  ",
        "last_name": "  ",
    }
    resp = client.post("/v1/auth/signup", json=payload)
    assert resp.status_code == 400


def test_signup_accepts_optional_organization_and_me_returns_profile(client):
    payload = {
        "email": "alice@example.com",
        "password": "supersecret",
        "first_name": "Alice",
        "last_name": "Example",
        "organization_name": "ACME Corp",
    }

    resp = client.post("/v1/auth/signup", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/v1/auth/me", headers=headers)
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["email"] == "alice@example.com"
    assert me_data["first_name"] == "Alice"
    assert me_data["last_name"] == "Example"
    assert me_data["organization_name"] == "ACME Corp"


def test_signup_trims_organization_name_and_stores_blank_as_none(client):
    payload = {
        "email": "bob@example.com",
        "password": "supersecret",
        "first_name": "Bob",
        "last_name": "Example",
        "organization_name": "  Acjen AI  ",
    }

    resp = client.post("/v1/auth/signup", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/v1/auth/me", headers=headers)
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["organization_name"] == "Acjen AI"

    payload_blank_org = {
        "email": "nullorg@example.com",
        "password": "supersecret",
        "first_name": "Null",
        "last_name": "Org",
        "organization_name": "  ",
    }
    blank_resp = client.post("/v1/auth/signup", json=payload_blank_org)
    assert blank_resp.status_code == 200
    blank_data = blank_resp.json()
    assert "access_token" in blank_data

    token_blank = blank_data["access_token"]
    headers_blank = {"Authorization": f"Bearer {token_blank}"}
    me_blank = client.get("/v1/auth/me", headers=headers_blank)
    assert me_blank.status_code == 200
    me_blank_data = me_blank.json()
    assert me_blank_data["organization_name"] is None
