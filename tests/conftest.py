# tests/conftest.py
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure repo-root imports work (e.g., "backend.*")
sys.path.insert(0, os.path.abspath("."))

# Provide a default API key for tests
os.environ.setdefault("API_KEY", "dev-secret-123")

from backend.app.core.db import engine
from backend.app.main import app
from backend.packages.shared.models import Base


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    # Don't drop tables; keep it simple for local CI runs.


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def api_headers():
    return {"X-API-Key": os.getenv("API_KEY", "dev-secret-123")}
