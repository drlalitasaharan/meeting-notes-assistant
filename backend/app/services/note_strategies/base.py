from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class ActionItem:
    owner: Optional[str]
    task: str
    due: Optional[str] = None
    confidence: float = 0.0

    def to_legacy_string(self) -> str:
        parts: list[str] = []
        if self.owner:
            parts.append(self.owner)
        parts.append(self.task)

        text = " — ".join(parts)
        if self.due:
            text += f" (due: {self.due})"
        return text


@dataclass
class NotesResult:
    summary: str
    key_points: List[str] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    model_version: str = "unknown"

    def to_api_dict(self) -> dict:
        return {
            "summary": self.summary,
            "key_points": self.key_points,
            "action_items": [item.to_legacy_string() for item in self.action_items],
            "action_item_objects": [asdict(item) for item in self.action_items],
            "decisions": self.decisions,
            "model_version": self.model_version,
        }


class NotesStrategy:
    def generate(self, transcript_text: str, slide_text: str = "") -> NotesResult:
        raise NotImplementedError
