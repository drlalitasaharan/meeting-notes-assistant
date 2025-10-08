from __future__ import annotations

from backend.app.core.logger import get_logger
from backend.packages.shared.models import Summary, Transcript
from sqlalchemy.orm import Session

log = get_logger(__name__)


def _mock_summary(text: str) -> dict[str, str]:
    return {
        "title": "Auto Summary",
        "bullets": "- Key point 1\n- Key point 2\n- Key point 3",
        "sentiment": "neutral",
    }


def summarize_meeting(db: Session, meeting_id: int) -> int:
    """Summarize a meeting's transcript into a Summary row. Returns exit code."""
    t: Transcript | None = (
        db.query(Transcript)
        .filter_by(meeting_id=meeting_id)
        .order_by(Transcript.id.desc())
        .first()
    )
    if not t or not getattr(t, "text", None):
        log.warning(
            "No transcript found; nothing to summarize",
            extra={"meeting_id": meeting_id},
        )
        return 2

    # Placeholder: wire in your real OpenAI call when ready.
    result = _mock_summary(t.text[:2000])

    s = Summary(meeting_id=meeting_id, **result)
    db.add(s)
    db.commit()
    log.info("Summary stored", extra={"meeting_id": meeting_id, "summary_id": s.id})
    return 0

