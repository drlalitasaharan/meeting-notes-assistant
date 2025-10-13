# backend/app/routers/notes_api.py
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import MetaData, Table, create_engine, insert, select

# Prefer your settings if present; else fall back to the container path
try:
    from app.core.settings import settings

    DATABASE_URL = settings.DATABASE_URL
except Exception:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/backend/dev.db")

engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()
try:
    meetings = Table("meetings", metadata, autoload_with=engine)
    notes = Table("notes", metadata, autoload_with=engine)
except Exception as e:
    # Surface a clear error early if tables are missing
    raise RuntimeError(f"DB reflection failed: {e}")

router = APIRouter(prefix="/v1", tags=["notes"])


class NoteIn(BaseModel):
    content: str
    author: Optional[str] = None


@router.get("/meetings")
def list_meetings():
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
