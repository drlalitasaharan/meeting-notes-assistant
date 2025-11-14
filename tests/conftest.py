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
    Base.metadata.create_all(bind=engine)

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


@pytest.fixture()
def api_headers():
    return {"X-API-Key": os.getenv("API_KEY", "dev-secret-123")}
