from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SummarySlots(BaseModel):
    purpose: str = ""
    outcome: str = ""
    risks: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class DecisionItem(BaseModel):
    text: str
    confidence: float = 0.0


class ActionItem(BaseModel):
    owner: str = ""
    task: str
    due_date: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    confidence: float = 0.0


class MeetingNotesResult(BaseModel):
    meeting_id: int
    status: str
    model_version: str
    summary: SummarySlots
    key_points: List[str] = Field(default_factory=list)
    decisions: List[DecisionItem] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
