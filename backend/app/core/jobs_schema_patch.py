from __future__ import annotations

import os

from sqlalchemy import create_engine


def patch_jobs_table() -> None:
    """Ensure the SQLite jobs table matches the current Job model schema.

    This is ONLY for the test SQLite database (.test.db) to avoid migrations.
    For any non-SQLite or non-test DB, we do nothing.
    """
    url = os.getenv("DATABASE_URL")
    if not url or not url.startswith("sqlite"):
        return

    # Be extra safe: only touch the ephemeral test DB
    if ".test.db" not in url:
        return

    engine = create_engine(url, future=True)

    with engine.begin() as conn:
        # Check if jobs table even exists
        res = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
        )
        row = res.first()
        if not row:
            # No jobs table yet; let normal metadata.create_all handle it
            print("[pytest] jobs table does not exist yet; no patch needed.")
            return

        print("[pytest] Dropping and recreating jobs table for test schema")

        # Drop the legacy table
        conn.exec_driver_sql("DROP TABLE jobs")

        # Recreate using the current SQLAlchemy Job model
        from app.models.job import Job  # local import to avoid circular deps

        Job.__table__.create(bind=conn)

        # Show final schema for debugging
        cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info('jobs')").fetchall()]
        print("[pytest] jobs columns AFTER recreate:", cols)
