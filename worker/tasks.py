from __future__ import annotations
from sqlalchemy import text

# Import DB session safely (no heavy deps at import time)
try:
    from app.db import SessionLocal
except Exception:
    SessionLocal = None  # type: ignore


def demo_job(job_id: str, job_type: str, payload: dict):
    from app.db import SessionLocal

    artifact_key = None
    try:
        from app.storage import choose_storage

        storage = choose_storage()
        key = f"jobs/{job_id}.json"
        if hasattr(storage, "put_json"):
            storage.put_json(key, {"echo": payload, "ok": True})
            artifact_key = key
    except Exception:
        artifact_key = None
    db = SessionLocal()
    try:
        if artifact_key:
            db.execute(
                text("UPDATE jobs SET status='succeeded', artifact_key=:k WHERE id=:id"),
                {"id": job_id, "k": artifact_key},
            )
        else:
            db.execute(text("UPDATE jobs SET status='succeeded' WHERE id=:id"), {"id": job_id})
        db.commit()
    finally:
        db.close()


def generic_job(job_id: str, job_type: str, payload: dict):
    return demo_job(job_id, job_type, payload)
