from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FeedbackUsefulness = Literal["yes", "somewhat", "no"]
FeedbackMostUseful = Literal["summary", "decisions", "action_items", "risks", "nothing_yet"]
FeedbackWouldUseAgain = Literal["yes", "maybe", "no"]
FeedbackMeetingType = Literal["internal", "client", "sales", "research", "project", "other"]


class MeetingFeedbackCreate(BaseModel):
    meeting_id: int
    usefulness: FeedbackUsefulness
    most_useful: FeedbackMostUseful
    improvement_text: str | None = Field(default=None, max_length=5000)
    would_use_again: FeedbackWouldUseAgain
    meeting_type: FeedbackMeetingType


class MeetingFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    meeting_id: int
    usefulness: str
    most_useful: str
    improvement_text: str | None = None
    would_use_again: str
    meeting_type: str
    created_at: datetime
    updated_at: datetime
