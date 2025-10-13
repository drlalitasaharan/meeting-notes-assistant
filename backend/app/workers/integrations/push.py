# backend/app/workers/integrations/push.py
from __future__ import annotations

from contextlib import suppress
from typing import Any

import httpx

from app.core.db import SessionLocal
from app.core.logger import get_logger
from packages.shared.env import settings
from packages.shared.models import Meeting, Summary

log = get_logger(__name__)


def _load_meeting_and_summary(meeting_id: int | str) -> tuple[Meeting | None, Summary | None]:
    with SessionLocal() as db:
        m = db.query(Meeting).filter_by(id=meeting_id).first()
        s = db.query(Summary).filter_by(meeting_id=meeting_id).first()
        return m, s


def _build_payload(meeting: Meeting | None, summary: Summary | None) -> dict[str, Any]:
    """Build a generic JSON payload suitable for webhooks (Slack/Notion/Teams adapters can map it)."""
    title = getattr(meeting, "title", f"Meeting {getattr(meeting, 'id', 'unknown')}")
    tags = getattr(meeting, "tags", "")
    status = getattr(meeting, "status", "")

    # Prefer structured fields if present on Summary, else fall back to raw_md
    actions = getattr(summary, "actions", None)
    risks = getattr(summary, "risks", None)
    raw_md = getattr(summary, "raw_md", None)
    synopsis = getattr(summary, "synopsis", None)

    notion_text = (
        synopsis or (raw_md[:1800] + "…") if raw_md and len(raw_md) > 1800 else raw_md or ""
    )

    # Example, Notion-style-ish block for consumers that expect a text block
    notion_block = {
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": notion_text}}]},
    }

    return {
        "meeting": {
            "id": getattr(meeting, "id", None),
            "title": title,
            "tags": tags,
            "status": status,
        },
        "summary": {
            "synopsis": synopsis,
            "actions": actions,
            "risks": risks,
            "raw_md": raw_md,
        },
        "blocks": [
            notion_block,
        ],
    }


def push_summary(meeting_id: int | str) -> dict[str, Any]:
    """
    Push the meeting summary to an external webhook endpoint.
    Set `PUSH_WEBHOOK_URL` in environment (see packages.shared.env.Settings).
    """
    endpoint = getattr(settings, "PUSH_WEBHOOK_URL", None)
    if not endpoint:
        msg = "Push disabled: no PUSH_WEBHOOK_URL configured"
        log.info(msg, extra={"meeting_id": meeting_id})
        return {"ok": False, "reason": msg}

    meeting, summary = _load_meeting_and_summary(meeting_id)
    if meeting is None:
        msg = "Meeting not found"
        log.warning(msg, extra={"meeting_id": meeting_id})
        return {"ok": False, "reason": msg}

    payload = _build_payload(meeting, summary)

    with httpx.Client(timeout=30) as client:
        r = client.post(endpoint, json=payload)
        ok = r.is_success
        body: Any = r.text
        with suppress(Exception):
            body = r.json()

    level = log.info if ok else log.warning
    level(
        "Pushed meeting summary",
        extra={
            "meeting_id": meeting_id,
            "status_code": r.status_code,
            "ok": ok,
        },
    )

    return {"ok": ok, "status": r.status_code, "response": body}


__all__ = ["push_summary"]
