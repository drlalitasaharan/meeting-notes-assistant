# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient

# Make sure imports resolve from repo root
import sys
sys.path.insert(0, os.path.abspath("."))

from backend.app.main import app  # uses your real app
from backend.app.db import SessionLocal
from backend.packages.shared.models import Meeting, Job, Base
from backend.app.db import engine

API_KEY = "dev-secret-123"
HEADERS = {"X-API-Key": API_KEY}

@pytest.fixture(scope="session", autouse=True)
def ensure_tables():
    # Your app already creates tables on startup, but this keeps CI predictable.
    Base.metadata.create_all(bind=engine)
    yield
    # Don’t drop tables; keep it simple for local CI runs.

@pytest.fixture(autouse=True)
def clean_db():
    # Clean rows between tests to avoid cross-test interference.
    db = SessionLocal()
    try:
        db.query(Job).delete()
        db.query(Meeting).delete()
        db.commit()
        yield
    finally:
        db.close()

@pytest.fixture()
def client():
    return TestClient(app)

@pytest.fixture()
def api_headers():
    return {"X-API-Key": API_KEY}

