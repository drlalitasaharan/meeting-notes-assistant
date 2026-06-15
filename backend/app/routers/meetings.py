from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import get_current_user
from app.models.meeting import Meeting
from app.models.meeting_notes import MeetingNotes
from app.models.note import Note
from app.models.user import User
from app.schemas.meetings import MeetingCreate, MeetingRead, MeetingUpdate
from app.schemas.notes import NoteCreate, NoteRead
from app.services.data_controls import delete_raw_media_best_effort
from app.services.usage_limits import enforce_can_create_meeting

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])


# Create (supports with/without trailing slash)
@router.post("", response_model=MeetingRead, status_code=status.HTTP_200_OK)
@router.post(
    "/", response_model=MeetingRead, status_code=status.HTTP_200_OK, include_in_schema=False
)
def create_meeting(
    payload: MeetingCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enforce_can_create_meeting(db=db, current_user=current_user)

    m = Meeting(
        title=payload.title,
        scheduled_at=payload.scheduled_at,
        agenda=payload.agenda,
        user_id=current_user.id,
    )
    # Ensure new meetings always have a status; default to "new"
    if getattr(payload, "status", None):
        m.status = payload.status
    else:
        m.status = "new"
    db.add(m)
    db.commit()
    db.refresh(m)
    response.headers["Location"] = f"/v1/meetings/{m.id}"
    return m


# List with pagination + optional status filter + sort
@router.get("", response_model=dict[str, Any], summary="List Meetings")
def list_meetings(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,  # 1..100
    offset: int = 0,  # >=0
    status: Optional[str] = None,  # e.g. new, in_progress, done
    sort: str = "desc",  # "asc" | "desc"
):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    q = db.query(Meeting).filter(Meeting.user_id == current_user.id)
    if status:
        q = q.filter(Meeting.status == status)

    total = q.count()
    order_col = Meeting.id.desc() if sort.lower() == "desc" else Meeting.id.asc()

    items_orm = q.order_by(order_col).limit(limit).offset(offset).all()
    items = [MeetingRead.model_validate(m).model_dump() for m in items_orm]
    response.headers["X-Total-Count"] = str(total)
    return {"items": items, "total": total}


@router.get("/{meeting_id}", response_model=MeetingRead)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.get(Meeting, meeting_id)
    if not m or m.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return m


@router.patch("/{meeting_id}", response_model=MeetingRead)
def update_meeting(
    meeting_id: int,
    payload: MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.get(Meeting, meeting_id)
    if not m or m.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.get(Meeting, meeting_id)
    if not m or m.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")

    raw_media_path = m.raw_media_path

    db.query(MeetingNotes).filter(MeetingNotes.meeting_id == meeting_id).delete(
        synchronize_session=False
    )
    db.query(Note).filter(Note.meeting_id == meeting_id).delete(synchronize_session=False)
    db.delete(m)
    db.commit()

    delete_raw_media_best_effort(raw_media_path)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{meeting_id}/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(
    meeting_id: int,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.get(Meeting, meeting_id)
    if not m or m.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    n = Note(meeting_id=meeting_id, content=payload.content, author=payload.author)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


@router.get("/{meeting_id}/notes", response_model=list[NoteRead])
def list_notes(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.get(Meeting, meeting_id)
    if not m or m.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return db.query(Note).filter(Note.meeting_id == meeting_id).order_by(Note.id.asc()).all()
