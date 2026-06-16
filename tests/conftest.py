from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure repo-root imports work (e.g., "backend.*")
sys.path.insert(0, os.path.abspath("."))

# -----------------------------------------------------------------------------
# Environment defaults for tests
# -----------------------------------------------------------------------------

# Provide default API key for tests
os.environ.setdefault("API_KEY", "dev-secret-123")

# Force a predictable SQLite test DB if not already set
os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.abspath('.test.db')}")

from sqlalchemy import inspect  # noqa: E402

from backend.app.core.db import engine  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.packages.shared.models import Base  # noqa: E402


# -----------------------------------------------------------------------------
# DB schema setup/teardown
# -----------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """
    For test runs, always ensure a schema that matches what the app expects.

    - Drop all tables and recreate from SQLAlchemy models
    - Ensure the `meetings` table has:
        - scheduled_at (DATETIME NULL)
        - agenda (TEXT NULL)
        - created_at (DATETIME NULL)
        - updated_at (DATETIME NULL)
      (ALTER TABLE if needed, for SQLite).
    """
    print("\n[pytest] Using engine URL:", engine.url)

    # Drop & recreate from metadata (whatever models are registered)
    Base.metadata.drop_all(bind=engine)
    # Billing models are new and must be present in the SQLite test DB.
    # Some older test setup paths only create the previously imported model tables.
    from app.models.billing import (  # noqa: F401
        BillingEvent,
        BillingSubscription,
        ManualBillingOverride,
    )

    Base.metadata.create_all(bind=engine)
    BillingSubscription.__table__.create(bind=engine, checkfirst=True)
    BillingEvent.__table__.create(bind=engine, checkfirst=True)
    ManualBillingOverride.__table__.create(bind=engine, checkfirst=True)

    insp = inspect(engine)
    tables = insp.get_table_names()
    print("[pytest] Tables AFTER create_all:", tables)

    if "meetings" in tables:
        cols = [c["name"] for c in insp.get_columns("meetings")]
        print("[pytest] meetings columns BEFORE fix:", cols)

        stmts: list[str] = []

        if "scheduled_at" not in cols:
            stmts.append("ALTER TABLE meetings ADD COLUMN scheduled_at DATETIME NULL")

        if "agenda" not in cols:
            stmts.append("ALTER TABLE meetings ADD COLUMN agenda TEXT NULL")

        if "created_at" not in cols:
            stmts.append("ALTER TABLE meetings ADD COLUMN created_at DATETIME NULL")

        if "updated_at" not in cols:
            stmts.append("ALTER TABLE meetings ADD COLUMN updated_at DATETIME NULL")

        if stmts:
            print("[pytest] Patching meetings table with:", stmts)
            with engine.begin() as conn:
                for sql in stmts:
                    conn.exec_driver_sql(sql)

            # Re-inspect to confirm
            insp = inspect(engine)
            cols_after = [c["name"] for c in insp.get_columns("meetings")]
            print("[pytest] meetings columns AFTER fix:", cols_after)
        else:
            print("[pytest] meetings table already has all expected columns")
    else:
        print("[pytest] WARNING: 'meetings' table not found after create_all()")

    yield
    # No teardown needed; tests share this schema.


# -----------------------------------------------------------------------------
# Test client + helpers
# -----------------------------------------------------------------------------


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def api_headers(client):
    """
    Return auth headers for tests that exercise authenticated API routes.

    User-owned meeting routes now require bearer-token auth. Keep X-API-Key as
    a compatibility header for legacy/system-test routes that still read it.
    """
    import importlib
    import os
    import uuid

    from app.models import Base

    try:
        from app.core.db import engine
    except ImportError:
        from app.db import engine

    for module_name in (
        "app.models.user",
        "app.models.meeting",
        "app.models.meeting_notes",
        "app.models.note",
        "app.models.upload_ledger",
        "app.models.billing",
    ):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            pass

    from sqlalchemy import inspect

    inspector = inspect(engine)
    if "meetings" in inspector.get_table_names():
        meeting_columns = {column["name"] for column in inspector.get_columns("meetings")}
        if "user_id" not in meeting_columns:
            Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    email = f"test-user-{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "organization_name": "MeetIQ Tests",
        },
    )
    assert response.status_code in (200, 201), response.text

    token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-API-Key": os.getenv("API_KEY") or os.getenv("X_API_KEY") or "dev-secret-123",
    }


# --- Golden-flow: ensure meeting_notes table exists for test DB ---------
from sqlalchemy import text  # type: ignore  # noqa: E402


def _ensure_meeting_notes_table() -> None:
    """Create meeting_notes table in the test SQLite DB if missing.

    We do this directly with SQL to keep tests independent from Alembic.
    """
    insp = inspect(engine)
    tables = insp.get_table_names()
    if "meeting_notes" in tables:
        return

    print("[pytest] Creating meeting_notes table for tests")
    create_sql = text(
        """
        CREATE TABLE meeting_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id VARCHAR NOT NULL,
            raw_transcript TEXT,
            summary TEXT,
            key_points TEXT,
            action_items TEXT,
            model_version VARCHAR,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    with engine.begin() as conn:
        conn.execute(create_sql)


# Call immediately so it's in place before tests that insert notes
_ensure_meeting_notes_table()
