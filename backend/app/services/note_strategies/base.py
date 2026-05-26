from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def _action_item_to_legacy_string(item: object) -> str:
    """Return stable legacy action text for ActionItem-like objects."""
    if hasattr(item, "to_legacy_string"):
        try:
            return str(item.to_legacy_string())
        except TypeError:
            pass

    if isinstance(item, dict):
        owner = str(item.get("owner") or "Team").strip() or "Team"
        task = str(item.get("task") or item.get("text") or "").strip()
    else:
        owner = str(getattr(item, "owner", None) or "Team").strip() or "Team"
        task = str(getattr(item, "task", None) or getattr(item, "text", None) or item).strip()

    if not task:
        return owner

    if task.lower().startswith(owner.lower() + ":"):
        task = task.split(":", 1)[1].strip()

    return f"{owner} - {task}"


@dataclass
class ActionItem:
    owner: Optional[str]
    task: str
    due: Optional[str] = None
    confidence: float = 0.0

    def to_legacy_string(self) -> str:
        task = (self.task or "").strip()
        owner = (self.owner or "").strip() if self.owner else None

        if owner:
            if task.lower().startswith(owner.lower() + " "):
                text = task
            else:
                text = f"{owner} — {task}"
        else:
            text = task

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
    summary_slots: Optional[Dict[str, Any]] = None
    action_item_objects: List[Dict[str, Any]] = field(default_factory=list)
    decision_objects: List[Dict[str, Any]] = field(default_factory=list)

    def to_api_dict(self) -> dict:
        legacy_action_items = [_action_item_to_legacy_string(item) for item in self.action_items]

        if not legacy_action_items and self.action_item_objects:
            for item in self.action_item_objects:
                owner = str(item.get("owner") or "").strip()
                task = str(item.get("task") or item.get("text") or "").strip()
                if not task:
                    continue

                if owner and not task.lower().startswith(owner.lower()):
                    legacy_action_items.append(f"{owner} — {task}")
                else:
                    legacy_action_items.append(task)

        return {
            "summary": self.summary,
            "summary_slots": self.summary_slots,
            "key_points": self.key_points,
            "action_items": legacy_action_items,
            "action_item_objects": self.action_item_objects
            or [asdict(item) for item in self.action_items],
            "decisions": self.decisions,
            "decision_objects": self.decision_objects,
            "model_version": self.model_version,
        }


class NotesStrategy:
    def generate(self, transcript_text: str, slide_text: str = "") -> NotesResult:
        raise NotImplementedError
