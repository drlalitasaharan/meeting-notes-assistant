from __future__ import annotations

import re
from typing import Dict, Iterable, List, TypeVar

from app.schemas.meeting_notes import ActionItem, MeetingNotesCanonical

T = TypeVar("T")


def _norm(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _dedupe_texts(values: Iterable[str], limit: int | None = None) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        key = _norm(value)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value.strip())
        if limit is not None and len(out) >= limit:
            break
    return out


def _dedupe_struct_items(items: Iterable[T]) -> List[T]:
    best_by_key: Dict[str, T] = {}

    for item in items:
        text = getattr(item, "text", "")
        key = _norm(text)
        if not key:
            continue

        current = best_by_key.get(key)
        if current is None:
            best_by_key[key] = item
            continue

        current_conf = float(getattr(current, "confidence", 0.0))
        new_conf = float(getattr(item, "confidence", 0.0))
        if new_conf > current_conf:
            best_by_key[key] = item

    return list(best_by_key.values())


def _merge_action_items(items: Iterable[ActionItem]) -> List[ActionItem]:
    grouped: Dict[str, ActionItem] = {}

    for item in items:
        key = _norm(item.text)
        if not key:
            continue

        current = grouped.get(key)
        if current is None:
            grouped[key] = item
            continue

        if item.confidence > current.confidence:
            current.confidence = item.confidence
        if not current.owner and item.owner:
            current.owner = item.owner
        if not current.due_date and item.due_date:
            current.due_date = item.due_date

        merged_sources = sorted(set(current.source_chunk_ids + item.source_chunk_ids))
        current.source_chunk_ids = merged_sources

    return list(grouped.values())


def merge_canonical(notes: MeetingNotesCanonical) -> MeetingNotesCanonical:
    notes.key_points = _dedupe_texts(notes.key_points, limit=8)
    notes.next_steps = _dedupe_texts(notes.next_steps, limit=8)
    notes.decisions = _dedupe_struct_items(notes.decisions)
    notes.risks = _dedupe_struct_items(notes.risks)
    notes.action_items = _merge_action_items(notes.action_items)

    notes.decisions = sorted(notes.decisions, key=lambda x: x.confidence, reverse=True)[:6]
    notes.risks = sorted(notes.risks, key=lambda x: x.confidence, reverse=True)[:6]
    notes.action_items = sorted(notes.action_items, key=lambda x: x.confidence, reverse=True)[:8]

    return notes
