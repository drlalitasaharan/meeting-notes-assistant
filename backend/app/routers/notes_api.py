# backend/app/routers/notes_api.py
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import MetaData, Table, create_engine, insert, inspect, select

# Prefer your settings if present; else fall back to the container path
try:
    from app.core.settings import settings

    DATABASE_URL = settings.DATABASE_URL
except Exception:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/backend/dev.db")

engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()
logger = logging.getLogger(__name__)

meetings: Optional[Table]
notes: Optional[Table]

try:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    has_meetings = "meetings" in table_names
    has_notes = "notes" in table_names

    if has_meetings and has_notes:
        meetings = Table("meetings", metadata, autoload_with=engine)
        notes = Table("notes", metadata, autoload_with=engine)
    else:
        logger.warning(
            "notes_api: required tables missing in DB; meetings=%s notes=%s available_tables=%s",
            has_meetings,
            has_notes,
            sorted(table_names),
        )
        meetings = None
        notes = None
except Exception as e:  # pragma: no cover
    logger.warning(
        "notes_api: DB reflection failed; notes endpoints will be disabled: %s",
        e,
    )
    meetings = None
    notes = None

router = APIRouter(prefix="/v1", tags=["notes"])


class NoteIn(BaseModel):
    content: str
    author: Optional[str] = None


def _ensure_schema() -> None:
    """Guard so that if the schema is missing (e.g. local sqlite tests)
    we don't crash at import time or on first request.
    """
    if meetings is None or notes is None:
        raise HTTPException(
            status_code=503,
            detail="Notes API is not available; database schema is not initialized.",
        )


@router.get("/meetings")
def list_meetings():
    _ensure_schema()
    assert meetings is not None  # for type checkers

    with engine.connect() as conn:
        rows = (
            conn.execute(
                select(
                    meetings.c.id,
                    meetings.c.title,
                    meetings.c.scheduled_at,
                    meetings.c.status,
                ).order_by(meetings.c.id)
            )
            .mappings()
            .all()
        )
        return list(rows)


@router.get("/meetings/{meeting_id}/notes")
def list_notes(meeting_id: int):
    _ensure_schema()
    assert notes is not None  # for type checkers

    with engine.connect() as conn:
        rows = (
            conn.execute(
                select(
                    notes.c.id,
                    notes.c.meeting_id,
                    notes.c.content,
                    notes.c.author,
                    notes.c.created_at,
                )
                .where(notes.c.meeting_id == meeting_id)
                .order_by(notes.c.id)
            )
            .mappings()
            .all()
        )
        return list(rows)


@router.post("/meetings/{meeting_id}/notes")
def create_note(meeting_id: int, payload: NoteIn):
    _ensure_schema()
    assert meetings is not None and notes is not None  # for type checkers

    with engine.begin() as conn:
        # sanity: meeting must exist
        m = conn.execute(select(meetings.c.id).where(meetings.c.id == meeting_id)).first()
        if not m:
            raise HTTPException(status_code=404, detail="meeting not found")

        res = conn.execute(
            insert(notes).values(
                meeting_id=meeting_id,
                content=payload.content,
                author=payload.author,
            )
        )
        new_id = res.inserted_primary_key[0]
        row = (
            conn.execute(
                select(
                    notes.c.id,
                    notes.c.meeting_id,
                    notes.c.content,
                    notes.c.author,
                    notes.c.created_at,
                ).where(notes.c.id == new_id)
            )
            .mappings()
            .one()
        )
        return dict(row)
