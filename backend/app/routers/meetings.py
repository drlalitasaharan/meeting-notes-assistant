from typing import Optional

from app.schemas.note import NoteCreate, NoteRead
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models.meeting import Meeting
from backend.app.models.note import Note
from backend.app.schemas.meetings import MeetingCreate, MeetingRead, MeetingUpdate

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])


# Create (supports with/without trailing slash)
@router.post("", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
@router.post(
    "/", response_model=MeetingRead, status_code=status.HTTP_201_CREATED, include_in_schema=False
)
def create_meeting(payload: MeetingCreate, response: Response, db: Session = Depends(get_db)):
    m = Meeting(title=payload.title, scheduled_at=payload.scheduled_at, agenda=payload.agenda)
    if payload.status is not None:
        m.status = payload.status
    db.add(m)
    db.commit()
    db.refresh(m)
    response.headers["Location"] = f"/v1/meetings/{m.id}"
    return m


# List with pagination + optional status filter + sort
@router.get("", response_model=list[MeetingRead], summary="List Meetings")
def list_meetings(
    response: Response,
    db: Session = Depends(get_db),
    limit: int = 20,  # 1..100
    offset: int = 0,  # >=0
    status: Optional[str] = None,  # e.g. new, in_progress, done
    sort: str = "desc",  # "asc" | "desc"
):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    q = db.query(Meeting)
    if status:
        q = q.filter(Meeting.status == status)

    total = q.count()
    order_col = Meeting.id.desc() if sort.lower() == "desc" else Meeting.id.asc()

    items = q.order_by(order_col).limit(limit).offset(offset).all()
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{meeting_id}", response_model=MeetingRead)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    return m


@router.patch("/{meeting_id}", response_model=MeetingRead)
def update_meeting(meeting_id: int, payload: MeetingUpdate, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(m)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{meeting_id}/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(meeting_id: int, payload: NoteCreate, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    n = Note(meeting_id=meeting_id, content=payload.content, author=payload.author)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


@router.get("/{meeting_id}/notes", response_model=list[NoteRead])
def list_notes(meeting_id: int, db: Session = Depends(get_db)):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return db.query(Note).filter(Note.meeting_id == meeting_id).order_by(Note.id.asc()).all()
