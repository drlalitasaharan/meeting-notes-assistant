# backend/app/db.py
import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

# Raw env default (dev/CI fallback)
_raw_url = os.getenv("DATABASE_URL", "sqlite:///./mna.db")

# Normalize driver: if Postgres DSN uses psycopg (v3) or no driver, force psycopg2
try:
    url = make_url(_raw_url)
    if url.get_backend_name() == "postgresql" and url.get_driver_name() in (None, "psycopg"):
        url = url.set(drivername="postgresql+psycopg2")
    DATABASE_URL = str(url)
except Exception:
    # If parsing fails for any reason, just keep the raw string
    DATABASE_URL = _raw_url

# Only pass SQLite-specific args for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Expose a session factory for request-scoped sessions
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def wait_for_db(timeout_seconds: int = 20) -> None:
    """Wait briefly for the DB to accept connections; don't raise on failure."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            time.sleep(1)
    # Give up silently; app should still boot so /healthz is reachable
