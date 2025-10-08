# backend/app/routers/meetings.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.core.logger import get_logger
from backend.packages.shared.models import Meeting

from ..deps import get_db, require_api_key

log = get_logger(__name__)

# NOTE: Keep routers version-agnostic; mount under /v1 in main.py.
router = APIRouter(
    prefix="/meetings",
    tags=["meetings"],
    dependencies=[Depends(require_api_key)],
)


def _tags_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [t for t in (value or "").split(",") if t]


@router.get("", response_model=dict)
def list_meetings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    query: str | None = Query(None, description="Simple search over title/tags"),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(Meeting)

    # Simple search on title/tags if provided (case-insensitive)
    if query:
        like = f"%{query}%"
        q = q.filter(or_(Meeting.title.ilike(like), Meeting.tags.ilike(like)))

    q = q.order_by(Meeting.id.desc())
    rows = q.offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": m.id,
            "title": m.title,
            "tags": _tags_list(m.tags),
            "status": getattr(m, "status", None),
        }
        for m in rows
    ]

    # Tests expect: r.json()["items"]
    return {"items": items}


@router.post("", status_code=status.HTTP_200_OK)
def create_meeting(
    title: str = Query(...),
    tags: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    m = Meeting(title=title, tags=tags or "")
    db.add(m)
    db.commit()
    db.refresh(m)
    log.info("Created meeting", extra={"meeting_id": m.id})
    return {
        "id": m.id,
        "title": m.title,
        "tags": _tags_list(m.tags),
        "status": getattr(m, "status", None),
    }


@router.get("/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)) -> dict:
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {
        "id": m.id,
        "title": m.title,
        "tags": _tags_list(m.tags),
        "status": getattr(m, "status", None),
    }


@router.patch("/{meeting_id}")
def update_meeting(
    meeting_id: int,
    *,
    title: str | None = None,
    status: str | None = None,
    tags: str | None = None,  # comma-separated string
    db: Session = Depends(get_db),
) -> dict:
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if title is not None:
        m.title = title
    if status is not None:
        m.status = status
    if tags is not None:
        m.tags = tags

    db.add(m)
    db.commit()
    db.refresh(m)

    log.info("Patched meeting", extra={"meeting_id": m.id})
    return {
        "id": m.id,
        "title": m.title,
        "tags": _tags_list(m.tags),
        "status": getattr(m, "status", None),
    }

