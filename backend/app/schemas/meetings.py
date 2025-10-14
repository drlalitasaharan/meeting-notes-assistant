from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class MeetingCreate(BaseModel):
    status: Optional[Literal["new", "in_progress", "done"]] = None
    title: str = Field(..., min_length=1, max_length=200)
    scheduled_at: Optional[datetime] = None
    agenda: Optional[str] = None


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    scheduled_at: Optional[datetime] = None
    agenda: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    agenda: Optional[str] = None
    status: Optional[Literal["new", "in_progress", "done"]] = None
