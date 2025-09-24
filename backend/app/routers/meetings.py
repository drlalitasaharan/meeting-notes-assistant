from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ...packages.shared.models import Meeting

router = APIRouter(prefix="/meetings", tags=["meetings"])

# --------- Schemas ---------
class MeetingOut(BaseModel):
    id: int
    title: str
    status: str
    tags: list[str] = []

    class Config:
        from_attributes = True


class MeetingsPage(BaseModel):
    items: list[MeetingOut]
    page: int
    limit: int
    total: int


# --------- List ---------
@router.get("", response_model=MeetingsPage)
def list_meetings(
    query: str | None = Query(None),
    status: str | None = Query(None),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Meeting)
    if query:
        q = q.filter(Meeting.title.ilike(f"%{query.lower()}%"))
    if status:
        q = q.filter(Meeting.status == status)
    if tag:
        q = q.filter(Meeting.tags.ilike(f"%{tag}%"))

    total = q.count()
    rows = (
        q.order_by(Meeting.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    items = [
        MeetingOut(id=m.id, title=m.title, status=m.status, tags=m.tags_list)
        for m in rows
    ]
    return MeetingsPage(items=items, page=page, limit=limit, total=total)


# --------- Create ---------
@router.post("", response_model=MeetingOut)
def create_meeting(
    title: str,
    tags: str | None = None,
    db: Session = Depends(get_db),
):
    m = Meeting(title=title, tags=tags or "")
    db.add(m)
    db.commit()
    db.refresh(m)
    return MeetingOut(id=m.id, title=m.title, status=m.status, tags=m.tags_list)


# --------- Update (PATCH) ---------
ALLOWED_STATUS = {"new", "processing", "done", "failed"}

@router.patch("/{meeting_id}", response_model=MeetingOut)
def update_meeting(
    meeting_id: int,
    title: str | None = None,
    status: str | None = None,
    tags: str | None = None,  # comma-separated string
    db: Session = Depends(get_db),
):
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if title is not None:
        m.title = title

    if status is not None:
        if status not in ALLOWED_STATUS:
            raise HTTPException(
                status_code=422,
                detail=f"status must be one of {sorted(ALLOWED_STATUS)}",
            )
        m.status = status

    if tags is not None:
        m.tags = tags

    db.add(m)
    db.commit()
    db.refresh(m)
    return MeetingOut(id=m.id, title=m.title, status=m.status, tags=m.tags_list)

