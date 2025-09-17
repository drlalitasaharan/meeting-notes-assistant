# backend/app/workers/integrations/push.py
"""
Push integrations for Meeting Notes:
- Slack: posts a compact text summary
- Notion: creates a page with summary content

Replaces all print() with structured logging.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from app.core.logger import get_logger
from app.core.db import SessionLocal
from packages.shared.env import settings
from packages.shared.models import Summary, Meeting

log = get_logger(__name__)


# ----------------------------
# Helpers
# ----------------------------
def _coerce_text(val: Any) -> str:
    """Turn lists/dicts into compact JSON; pass strings through."""
    if val is None:
        return ""
    if isinstance(val, (list, dict)):
        try:
            return json.dumps(val, ensure_ascii=False)
        except Exception:
            return str(val)
    return str(val)


def _load_meeting_and_summary(meeting_id: str) -> tuple[Optional[Meeting], Optional[Summary]]:
    with SessionLocal() as db:
        s = db.query(Summary).filter_by(meeting_id=meeting_id).first()
        m = db.get(Meeting, meeting_id)
        return m, s


# ----------------------------
# Slack
# ----------------------------
def to_slack(meeting_id: str, channel: str = "#meeting-notes") -> dict:
    """
    Post a short message to Slack for the given meeting.
    Returns a dict with {"ok": bool, "status": int, "body": <text or json>}.
    """
    if not settings.SLACK_BOT_TOKEN:
        log.warning("SLACK_BOT_TOKEN not set; skipping Slack push")
        return {"ok": False, "status": 0, "body": "missing token"}

    m, s = _load_meeting_and_summary(meeting_id)
    if not (m and s):
        log.warning("Missing summary or meeting; skipping Slack push", extra={"meeting_id": meeting_id})
        return {"ok": False, "status": 0, "body": "missing data"}

    title = m.title or "Meeting"
    text = (
        f"*{title}*\n"
        f"*Highlights:* {_coerce_text(getattr(s, 'highlights', None))}\n"
        f"*Decisions:* {_coerce_text(getattr(s, 'decisions', None))}\n"
        f"*Actions:* {_coerce_text(getattr(s, 'actions', None))}"
    )

    headers = {
        "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"channel": channel, "text": text}

    try:
        r = httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload,
            timeout=15,
        )
        body = r.text
        ok = r.is_success and (r.headers.get("content-type", "").startswith("application/json"))
        # Slack returns JSON {"ok": true/false, ...}; try to reflect that in logs
        try:
            parsed = r.json()
            ok = bool(parsed.get("ok", ok))
            body = parsed
        except Exception:
            pass

        level = log.info if ok else log.warning
        level("Slack push result", extra={"meeting_id": meeting_id, "status": r.status_code, "ok": ok})
        return {"ok": ok, "status": r.status_code, "body": body}
    except Exception:
        log.exception("Slack push failed", extra={"meeting_id": meeting_id})
        return {"ok": False, "status": 0, "body": "exception"}


# ----------------------------
# Notion
# ----------------------------
def to_notion(meeting_id: str) -> dict:
    """
    Create a Notion page in the configured database for the given meeting.
    Returns a dict with {"ok": bool, "status": int, "body": <text or json>}.
    """
    if not (settings.NOTION_TOKEN and settings.NOTION_DB_ID):
        log.warning("Notion env vars not set; skipping Notion push")
        return {"ok": False, "status": 0, "body": "missing env"}

    m, s = _load_meeting_and_summary(meeting_id)
    if not (m and s):
        log.warning("Missing summary or meeting; skipping Notion push", extra={"meeting_id": meeting_id})
        return {"ok": False, "status": 0, "body": "missing data"}

    title = m.title or "Meeting"
    # Prefer raw_md if available; otherwise compose a simple body
    raw_md = getattr(s, "raw_md", None) or (
        f"# {title}\n\n"
        f"**Highlights**\n{_coerce_text(getattr(s, 'highlights', None))}\n\n"
        f"**Decisions**\n{_coerce_text(getattr(s, 'decisions', None))}\n\n"
        f"**Actions**\n{_coerce_text(getattr(s, 'actions', None))}\n"
    )
    # Notion block text has ~2000 char soft limits; clip conservatively
    notion_text = str(raw_md)[:1900]

    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    page = {
        "parent": {"database_id": settings.NOTION_DB_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Completed"}},
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": notion_text}}]},
            }
        ],
    }

    try:
        r = httpx.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=page,
            timeout=20,
        )
        body = r.text
        ok = r.is_success
        try:
            body = r.json()
        except Exception:
            pass

        level = log.info if ok else log.warning
        level("Notion push result", extra={"meeting_id": meeting_id, "status": r.status_code, "ok": ok})
        return {"ok": ok, "status": r.status_code, "body": body}
    except Exception:
        log.exception("Notion push failed", extra={"meeting_id": meeting_id})
        return {"ok": False, "status": 0, "body": "exception"}

