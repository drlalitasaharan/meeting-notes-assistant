from __future__ import annotations

import copy
from typing import Any

from app.services.llm_polish import apply_llm_polish_to_notes


def _base_notes() -> dict[str, Any]:
    return {
        "summary": "The meeting reviewed demo planning, pilot outreach, and technical risks.",
        "summary_slots": {
            "purpose": "Review current progress and align on demo planning.",
            "outcome": "The team aligned on demo assets and pilot positioning.",
            "risks": ["Longer files may run into the current timeout."],
            "next_steps": [
                "Review and finalize the landing page and outreach message.",
                "Prepare the short live-demo recording.",
            ],
        },
        "key_points": [
            "The realistic 10-minute test now produces a better summary.",
            "The team should move into a small pilot once the demo flow is stable.",
        ],
        "decisions": [
            "Use meeting 17 as the primary backup demo example.",
            "Lead with a practical positioning message.",
        ],
        "action_items": [
            "Team — Review and finalize the landing page and outreach message",
            "Team — Prepare the short live-demo recording",
        ],
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Review and finalize the landing page and outreach message",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "Prepare the short live-demo recording",
                "status": "open",
                "priority": "medium",
            },
        ],
    }


def test_llm_polish_disabled_returns_original_without_calling_client(monkeypatch) -> None:
    monkeypatch.setenv("MEETIQ_LLM_POLISH_ENABLED", "false")
    notes = _base_notes()
    calls: list[dict[str, Any]] = []

    def fake_client(payload: dict[str, Any]) -> dict[str, Any]:
        calls.append(payload)
        return {"summary": "Changed"}

    result = apply_llm_polish_to_notes(notes, polish_client=fake_client)

    assert result == notes
    assert calls == []


def test_llm_polish_applies_safe_polished_fields_and_preserves_actions(monkeypatch) -> None:
    monkeypatch.setenv("MEETIQ_LLM_POLISH_ENABLED", "true")
    monkeypatch.setenv("MEETIQ_LLM_PROVIDER", "groq")

    notes = _base_notes()
    original_actions = copy.deepcopy(notes["action_item_objects"])
    original_next_steps = copy.deepcopy(notes["summary_slots"]["next_steps"])

    def fake_client(payload: dict[str, Any]) -> dict[str, Any]:
        assert "action_items_context_only" in payload
        return {
            "summary": (
                "The meeting aligned demo planning, pilot outreach, and current technical risks, "
                "with a focus on preparing a reliable client-ready demo."
            ),
            "summary_slots": {
                "purpose": "Review MeetIQ progress, demo planning, pilot outreach, and current risks.",
                "outcome": "The team aligned on demo assets, pilot positioning, and backup planning.",
                "risks": ["Longer recordings may hit the current processing timeout."],
            },
            "key_points": [
                "The realistic 10-minute test now produces stronger structured notes.",
                "The team should move into a small pilot once the demo flow is stable.",
            ],
            "decisions": [
                "Use meeting 17 as the primary backup demo example.",
                "Lead with a practical positioning message.",
            ],
        }

    result = apply_llm_polish_to_notes(notes, polish_client=fake_client)

    assert result["summary"].startswith("The meeting aligned demo planning")
    assert result["summary_slots"]["purpose"].startswith("Review MeetIQ progress")
    assert result["summary_slots"]["risks"] == [
        "Longer recordings may hit the current processing timeout."
    ]
    assert result["key_points"][0] == (
        "The realistic 10-minute test now produces stronger structured notes."
    )
    assert result["_llm_polish_applied"] is True

    assert result["action_item_objects"] == original_actions
    assert result["action_items"] == notes["action_items"]
    assert result["summary_slots"]["next_steps"] == original_next_steps


def test_llm_polish_rejects_list_length_changes(monkeypatch) -> None:
    monkeypatch.setenv("MEETIQ_LLM_POLISH_ENABLED", "true")
    notes = _base_notes()

    def fake_client(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": (
                "The meeting aligned demo planning, pilot outreach, and current technical risks, "
                "with a focus on preparing a reliable client-ready demo."
            ),
            "summary_slots": {
                "purpose": "Review MeetIQ progress, demo planning, pilot outreach, and current risks.",
                "outcome": "The team aligned on demo assets, pilot positioning, and backup planning.",
                "risks": [
                    "Longer recordings may hit the current processing timeout.",
                    "Invented second risk should be rejected.",
                ],
            },
            "key_points": ["Only one key point should be rejected."],
            "decisions": ["Only one decision should be rejected."],
        }

    result = apply_llm_polish_to_notes(notes, polish_client=fake_client)

    assert result["key_points"] == notes["key_points"]
    assert result["decisions"] == notes["decisions"]
    assert result["summary_slots"]["risks"] == notes["summary_slots"]["risks"]


def test_llm_polish_invalid_response_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("MEETIQ_LLM_POLISH_ENABLED", "true")
    notes = _base_notes()

    def fake_client(_: dict[str, Any]) -> dict[str, Any] | None:
        return None

    result = apply_llm_polish_to_notes(notes, polish_client=fake_client)

    assert result == notes
