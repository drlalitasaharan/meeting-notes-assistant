from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

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
    processing_stage: Optional[str] = None
    processing_progress_label: Optional[str] = None
    processing_error_message: Optional[str] = None
    processing_timings: Optional[dict[str, Any]] = None
    confidential_mode: bool = False
    recording_retention_policy: Optional[str] = None
    recording_deleted_at: Optional[datetime] = None
    recording_delete_status: str = "not_required"
    created_at: datetime
    updated_at: datetime


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    agenda: Optional[str] = None
    status: Optional[Literal["new", "in_progress", "done"]] = None
