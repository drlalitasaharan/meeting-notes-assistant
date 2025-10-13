from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    author: Optional[str] = Field(default=None, max_length=120)


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    meeting_id: int
    content: str
    author: Optional[str] = None
    created_at: datetime
