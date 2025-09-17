# scripts/seed_demo.py
"""
Populate DB + MinIO with demo meetings/slides for Phase-1 testing.
Safe to re-run: deterministic IDs + upsert logic.

Run from repo root (where `backend/` and `scripts/` live):
    APP_ENV=demo python -m scripts.seed_demo
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict
from uuid import uuid4

# ---- Path bootstrap: ensure both repo root and backend/ are importable ----
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# --- Project imports (Option A: explicit package path via `backend.*`) ---
from backend.app.core.logger import get_logger
from backend.app.core.db import SessionLocal
from backend.app.services import minio_client as slides_minio
from backend.packages.shared.models import Meeting, Transcript, Summary

log = get_logger(__name__)

# Only allow seeding in non-prod environments
ALLOWED_ENVS = {"dev", "demo", "local", "test"}

# Deterministic demo fixtures (stable IDs => safe to re-run)
DEMO_MEETINGS: List[Dict] = [
    {
        "id": "demo_kickoff",
        "title": "Project Kickoff",
        "transcript": "Welcome to the kickoff. We aligned on scope, risks, and next steps.",
        "slide_filename": "kickoff.txt",
        "slide_bytes": b"Project Kickoff\nSlides placeholder",
        "created_at_offset_days": 1,
    },
    {
        "id": "demo_qbr",
        "title": "Quarterly Review",
        "transcript": "We reviewed KPIs, blockers, and planned actions.",
        "slide_filename": "qbr.txt",
        "slide_bytes": b"Quarterly Review\nSlides placeholder",
        "created_at_offset_days": 2,
    },
    {
        "id": "demo_design",
        "title": "Design Sync",
        "transcript": "Discussed slide deck structure and API polish.",
        "slide_filename": "design.txt",
        "slide_bytes": b"Design Sync\nSlides placeholder",
        "created_at_offset_days": 3,
    },
]


def _set_if_has(obj, field: str, value):
    """Set attribute if the SQLAlchemy model has it (schema-tolerant)."""
    if hasattr(obj, field):
        setattr(obj, field, value)


def upsert_meeting(db, mid: str, title: str, created_at_dt: datetime) -> bool:
    """
    Create or update a Meeting row with deterministic ID + safe defaults.
    Writes real datetime objects (not strings) to DateTime columns.
    Returns True if created, False if updated/no-op.
    """
    m = db.get(Meeting, mid)
    if m is None:
        m = Meeting(id=mid, title=title, status="processed", storage_key=f"raw/{mid}.bin")
        # Only set created_at if the model has it
        if hasattr(m, "created_at") and created_at_dt:
            setattr(m, "created_at", created_at_dt)
        db.add(m)
        log.info("Created meeting", extra={"id": mid, "title": title})
        return True
    else:
        changed = False
        if m.title != title:
            m.title = title
            changed = True
        if getattr(m, "status", None) != "processed":
            _set_if_has(m, "status", "processed")
            changed = True
        # If created_at exists and is currently NULL, set it to a datetime
        if hasattr(m, "created_at") and created_at_dt and getattr(m, "created_at", None) is None:
            setattr(m, "created_at", created_at_dt)
            changed = True
        if changed:
            log.info("Updated meeting", extra={"id": mid, "title": title})
        else:
            log.info("Meeting up-to-date", extra={"id": mid})
        return False


def upsert_transcript(db, mid: str, text: str) -> None:
    """Create or update Transcript with safe provider/language defaults."""
    t = db.query(Transcript).filter_by(meeting_id=mid).first()
    if t is None:
        kwargs = {"meeting_id": mid}
        if hasattr(Transcript, "id"):
            kwargs["id"] = str(uuid4())
        t = Transcript(**kwargs)
        _set_if_has(t, "provider", "demo")
        _set_if_has(t, "language", "en")
        _set_if_has(t, "text", text)
        db.add(t)
        log.info("Created transcript", extra={"meeting_id": mid})
    else:
        _set_if_has(t, "text", text)
        if getattr(t, "provider", None) in (None, ""):
            _set_if_has(t, "provider", "demo")
        if getattr(t, "language", None) in (None, ""):
            _set_if_has(t, "language", "en")
        log.info("Updated transcript", extra={"meeting_id": mid})


def upsert_summary(db, mid: str) -> None:
    """Create or update Summary, ensuring common NOT NULL fields and markdown body."""
    s = db.query(Summary).filter_by(meeting_id=mid).first()
    demo_md = "## (demo) summary\n\n- highlight 1\n- decision A\n- action X\n- risk R"
    if s is None:
        kwargs = {"meeting_id": mid}
        if hasattr(Summary, "id"):
            kwargs["id"] = str(uuid4())
        if hasattr(Summary, "provider"):
            kwargs["provider"] = "demo"
        if hasattr(Summary, "language"):
            kwargs["language"] = "en"
        # JSON-ish fields commonly NOT NULL
        if hasattr(Summary, "highlights"):
            kwargs["highlights"] = []
        if hasattr(Summary, "decisions"):
            kwargs["decisions"] = []
        if hasattr(Summary, "actions"):
            kwargs["actions"] = []
        if hasattr(Summary, "risks"):
            kwargs["risks"] = []
        s = Summary(**kwargs)
        db.add(s)
        log.info("Created summary", extra={"meeting_id": mid})
    _set_if_has(s, "raw_md", demo_md)


def ensure_slide_in_minio(mid: str, filename: str, data: bytes) -> bool:
    """
    Upload a tiny demo slide if it doesn't already exist in MinIO.
    Returns True if uploaded, False if already present or failed.
    """
    try:
        if slides_minio.slide_exists(mid, filename):
            log.info("Slide exists, skipping upload", extra={"meeting_id": mid, "filename": filename})
            return False
        slides_minio.put_slide_bytes(mid, data, filename, content_type="text/plain")
        log.info("Uploaded demo slide", extra={"meeting_id": mid, "filename": filename})
        return True
    except Exception as e:
        log.warning("Slide upload failed", extra={"meeting_id": mid, "filename": filename, "err": str(e)})
        return False


def main() -> None:
    app_env = os.getenv("APP_ENV", "dev")
    if app_env not in ALLOWED_ENVS:
        raise SystemExit(f"Refusing to seed in APP_ENV={app_env}. Allowed: {ALLOWED_ENVS}")

    # Ensure MinIO bucket exists
    slides_minio.ensure_bucket()

    now = datetime.utcnow()
    created_meetings = 0
    updated_meetings = 0
    uploaded_slides = 0

    with SessionLocal() as db:
        for item in DEMO_MEETINGS:
            mid = item["id"]
            title = item["title"]
            created_at_dt = now - timedelta(days=item["created_at_offset_days"])

            created = upsert_meeting(db, mid, title, created_at_dt)
            upsert_transcript(db, mid, item["transcript"])
            upsert_summary(db, mid)

            created_meetings += 1 if created else 0
            updated_meetings += 0 if created else 1

        db.commit()

    # Upload slides after DB commit (idempotent)
    for item in DEMO_MEETINGS:
        if ensure_slide_in_minio(item["id"], item["slide_filename"], item["slide_bytes"]):
            uploaded_slides += 1

    print(
        f"✅ Seed complete: created_meetings={created_meetings}, "
        f"updated_meetings={updated_meetings}, uploaded_slides={uploaded_slides}, "
        f"total_meetings={len(DEMO_MEETINGS)}"
    )


if __name__ == "__main__":
    main()

