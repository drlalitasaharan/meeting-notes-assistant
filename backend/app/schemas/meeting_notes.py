from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    text: str
    owner: Optional[str] = None
    due_date: Optional[str] = None
    confidence: float = 0.0
    source_chunk_ids: List[int] = Field(default_factory=list)


class DecisionItem(BaseModel):
    text: str
    confidence: float = 0.0
    source_chunk_ids: List[int] = Field(default_factory=list)


class RiskItem(BaseModel):
    text: str
    confidence: float = 0.0
    source_chunk_ids: List[int] = Field(default_factory=list)


class NotesMetadata(BaseModel):
    transcript_quality: float = 0.0
    transcript_normalizer_version: str = "v1"
    chunking_version: str = "v1"
    extractor_version: str = "slot-extractor-v1"
    validator_version: str = "action-validator-v1"
    formatter_version: str = "formatter-v1"


class MeetingNotesCanonical(BaseModel):
    meeting_id: int
    purpose: str = ""
    outcome: str = ""
    decisions: List[DecisionItem] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    summary: str = ""
    metadata: NotesMetadata = Field(default_factory=NotesMetadata)
