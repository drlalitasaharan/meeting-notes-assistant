# backend/app/workers/llm/summarize.py
"""
LLM-based meeting summarizer (scriptable worker).

- Uses structured logging (no prints).
- Works with/without OpenAI (falls back to a mock summary).
- Safe upsert: creates or updates Summary row, filling optional columns only
  if they exist on your model (provider, language, raw_md, highlights, etc.).
"""

import json
import sys
import argparse
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.db import SessionLocal
from packages.shared.env import settings
from packages.shared.models import Transcript, Summary, Meeting

log = get_logger(__name__)

# Optional OpenAI client
try:
    from openai import OpenAI
    _OPENAI = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception:
    _OPENAI = None
    log.warning("OPENAI client unavailable; using mock summary")

SYSTEM_PROMPT = """You are a structured meeting analyst. Output strict JSON with keys:
highlights[], decisions[], actions[], risks[], raw_md (markdown summary).
For actions include: task, owner(if heard), due(null if not stated)."""

MODEL_NAME = "gpt-4o-mini"


def _build_summary_payload(transcript_text: str) -> dict:
    """
    Returns a dict with keys: highlights, decisions, actions, risks, raw_md.
    Uses OpenAI if available; otherwise returns a mock payload.
    """
    content = (transcript_text or "")[:30000]  # naive truncate MVP

    if _OPENAI is None:
        return {
            "highlights": ["Mock highlight"],
            "decisions": [{"what": "Mock decision", "rationale": "Mock rationale"}],
            "actions": [{"task": "Mock task", "owner": "Speaker 1", "due": None}],
            "risks": [{"risk": "Mock risk", "mitigation": "Mock mitigation"}],
            "raw_md": "# Mock Summary\n- This is a placeholder."
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Transcript:\n{content}"}
    ]
    resp = _OPENAI.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"},
    )
    data = resp.choices[0].message.content
    return json.loads(data)


def _upsert_summary(db: Session, meeting_id: str, j: dict) -> None:
    """
    Create or update the Summary row for a meeting.
    Fills only attributes that exist on your model (handles JSON/Text schemas).
    """
    s = db.query(Summary).filter_by(meeting_id=meeting_id).first()

    # Prepare base kwargs respecting your schema
    kwargs = {"meeting_id": meeting_id}
    if not s and hasattr(Summary, "id"):
        kwargs["id"] = str(uuid4())
    if hasattr(Summary, "provider"):
        kwargs["provider"] = f"llm:{MODEL_NAME}" if _OPENAI else "mock"
    if hasattr(Summary, "language"):
        kwargs["language"] = "en"

    # Structured fields if present on your model
    if hasattr(Summary, "highlights"):
        kwargs["highlights"] = j.get("highlights", [])
    if hasattr(Summary, "decisions"):
        kwargs["decisions"] = j.get("decisions", [])
    if hasattr(Summary, "actions"):
        kwargs["actions"] = j.get("actions", [])
    if hasattr(Summary, "risks"):
        kwargs["risks"] = j.get("risks", [])

    # Markdown/raw field if present
    if hasattr(Summary, "raw_md"):
        kwargs["raw_md"] = j.get("raw_md", "")

    if s is None:
        s = Summary(**kwargs)
        db.add(s)
    else:
        for k, v in kwargs.items():
            setattr(s, k, v)


def summarize_meeting(meeting_id: str) -> int:
    """
    Summarize a meeting's transcript and persist a Summary row.
    Returns process exit code (0 = success, non-zero on failure).
    """
    log.info("Summarize requested", extra={"meeting_id": meeting_id})
    with SessionLocal() as db:
        try:
            t = db.query(Transcript).filter_by(meeting_id=meeting_id).first()
            if not t or not getattr(t, "text", None):
                log.warning("No transcript found; nothing to summarize", extra={"meeting_id": meeting_id})
                return 2

            payload = _build_summary_payload(t.text)

            _upsert_summary(db, meeting_id, payload)

            # Best-effort meeting status update
            m = db.get(Meeting, meeting_id)
            if m and hasattr(m, "status"):
                m.status = "summarized"

            db.commit()
            log.info("Summarize complete", extra={"meeting_id": meeting_id})
            return 0

        except Exception:
            db.rollback()
            log.exception("Summarize failed", extra={"meeting_id": meeting_id})
            return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Meeting LLM summarizer worker")
    parser.add_argument("meeting_id", help="Meeting ID to summarize")
    args = parser.parse_args(argv)
    return summarize_meeting(args.meeting_id)


if __name__ == "__main__":
    sys.exit(main())

