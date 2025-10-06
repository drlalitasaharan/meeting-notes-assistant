
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure repo root importability before project imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.db import SessionLocal
from backend.app.core.logger import get_logger
from backend.app.services import minio_client as slides_minio
from backend.packages.shared.models import Meeting

log = get_logger(__name__)


def ensure_meeting(db, mid: str, title: str, created_at: datetime | None = None) -> Meeting:
    m = db.query(Meeting).filter_by(id=mid).first()
    if not m:
        m = Meeting(id=mid, title=title, tags="demo")
        if created_at:
            m.created_at = created_at
        db.add(m)
        log.info("Created meeting", extra={"id": mid, "title": title})
    else:
        changed = False
        if title and m.title != title:
            m.title = title
            changed = True
        if created_at and getattr(m, "created_at", None) is None:
            m.created_at = created_at
            changed = True
        if changed:
            log.info("Updated meeting", extra={"id": mid, "title": title})
    return m


def seed() -> None:
    with SessionLocal() as db:
        now = datetime.utcnow()
        demo_meetings = [
            {"id": "demo_kickoff", "title": "Demo Kickoff", "created_at": now - timedelta(days=10)},
            {"id": "demo_review", "title": "Demo Review", "created_at": now - timedelta(days=5)},
        ]

        uploaded_slides = 0

        for item in demo_meetings:
            m = ensure_meeting(db, item["id"], item["title"], item["created_at"])

            filename = "placeholder.txt"
            key = f"slides/{m.id}/{filename}"
            if slides_minio.object_exists(key, slides_minio.SLIDES_BUCKET):
                log.info(
                    "Slide exists, skipping upload",
                    extra={"meeting_id": m.id, "filename": filename},
                )
            else:
                try:
                    from io import BytesIO

                    slides_minio.upload_fileobj(
                        BytesIO(b"demo slide"),
                        key,
                        bucket=slides_minio.SLIDES_BUCKET,
                        content_type="text/plain",
                    )
                    uploaded_slides += 1
                except Exception as e:
                    log.warning(
                        "Slide upload failed",
                        extra={"meeting_id": m.id, "filename": filename, "err": str(e)},
                    )

        db.commit()
        log.info(
            f"✅ Seed complete: uploaded_slides={uploaded_slides}, total_meetings={len(demo_meetings)}",
        )


if __name__ == "__main__":
    seed()

