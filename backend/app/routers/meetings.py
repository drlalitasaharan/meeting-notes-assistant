from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/meetings", tags=["meetings"])

class MeetingOut(BaseModel):
    id: int
    title: str
    status: str
    tags: list[str] = []

class MeetingsPage(BaseModel):
    items: list[MeetingOut]
    page: int
    limit: int
    total: int

_FAKE = [
    MeetingOut(id=1, title="Sprint Planning", status="new", tags=["sprint","planning"]),
    MeetingOut(id=2, title="Design Review",  status="done", tags=["design"]),
]

@router.get("", response_model=MeetingsPage)
def list_meetings(
    query: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    rows = _FAKE
    if query:
        q = query.lower()
        rows = [m for m in rows if q in m.title.lower()]
    if status:
        rows = [m for m in rows if m.status == status]
    total = len(rows)
    start = (page-1)*limit
    end = start + limit
    return MeetingsPage(items=rows[start:end], page=page, limit=limit, total=total)
