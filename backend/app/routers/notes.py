from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Summary, Transcript

router = APIRouter(prefix="/v1/meetings", tags=["notes"])


class NotesOut(BaseModel):
    meeting_id: int
    transcript_snippet: str | None
    summary_bullets: str | None


@router.get("/{meeting_id}/notes", response_model=NotesOut)
def get_notes(meeting_id: int, db: Session = Depends(get_db)):
    t = (
        db.query(Transcript)
        .filter(Transcript.meeting_id == meeting_id)
        .order_by(desc(Transcript.created_at))
        .first()
    )
    s = db.query(Summary).filter(Summary.meeting_id == meeting_id).one_or_none()
    return NotesOut(
        meeting_id=meeting_id,
        transcript_snippet=(t.text[:800] + "…") if t else None,
        summary_bullets=s.bullets if s else None,
    )
