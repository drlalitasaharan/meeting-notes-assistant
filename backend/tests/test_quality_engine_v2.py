from app.services.quality_engine_v2 import apply_quality_engine_v2


def test_quality_engine_v2_adds_purpose_when_missing() -> None:
    notes = {
        "summary": "The team discussed pricing, onboarding, and launch readiness.",
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Today we need to confirm the pricing page, onboarding copy, and launch readiness.
    The goal is to make sure the Starter checkout and first-user experience are clear.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["purpose"]
    assert "pricing" in improved["summary_slots"]["purpose"].lower() or "launch" in improved["summary_slots"]["purpose"].lower()


def test_quality_engine_v2_syncs_next_steps_from_actions() -> None:
    notes = {
        "summary": "The team discussed launch follow-up.",
        "summary_slots": {"purpose": "Confirm launch follow-up.", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Lalita",
                "task": "Update the pricing page CTA before launch",
                "status": "open",
                "priority": "medium",
            }
        ],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "Lalita will update the pricing page CTA before launch.")

    next_steps = improved["summary_slots"]["next_steps"]
    assert next_steps
    assert any("pricing page CTA" in step for step in next_steps)


def test_quality_engine_v2_preserves_existing_decisions() -> None:
    notes = {
        "summary": "The team aligned on the launch scope.",
        "summary_slots": {"purpose": "Review launch scope.", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [
            {"text": "Keep launch scope focused on upload, processing, notes review, and Markdown export.", "confidence": 0.8}
        ],
    }

    improved = apply_quality_engine_v2(notes, "The team decided to keep the launch scope focused.")

    decisions = improved["decision_objects"]
    assert len(decisions) == 1
    assert "launch scope" in decisions[0]["text"].lower()


def test_quality_engine_v2_mode_defaults_to_v1() -> None:
    from app.services.quality_engine_v2 import normalize_notes_engine_mode

    assert normalize_notes_engine_mode(None) == "v1"
    assert normalize_notes_engine_mode("") == "v1"
    assert normalize_notes_engine_mode("unknown") == "v1"


def test_quality_engine_v2_mode_accepts_v1_v2_shadow() -> None:
    from app.services.quality_engine_v2 import normalize_notes_engine_mode

    assert normalize_notes_engine_mode("v1") == "v1"
    assert normalize_notes_engine_mode("v2") == "v2"
    assert normalize_notes_engine_mode("shadow") == "shadow"
    assert normalize_notes_engine_mode(" V2 ") == "v2"
    assert normalize_notes_engine_mode(" SHADOW ") == "shadow"


def test_quality_engine_v2_mode_decisions() -> None:
    from app.services.quality_engine_v2 import (
        should_apply_quality_engine_v2,
        should_run_quality_engine_v2_shadow,
    )

    assert should_apply_quality_engine_v2("v1") is False
    assert should_apply_quality_engine_v2("shadow") is False
    assert should_apply_quality_engine_v2("v2") is True

    assert should_run_quality_engine_v2_shadow("v1") is False
    assert should_run_quality_engine_v2_shadow("v2") is False
    assert should_run_quality_engine_v2_shadow("shadow") is True


def test_run_quality_engine_v2_preserves_v1_output_in_v1_mode() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team discussed launch readiness.",
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(notes, "The goal is to confirm launch readiness.", mode="v1")

    assert result["notes"] == notes
    assert result["metadata"]["applied"] is False
    assert result["metadata"]["mode"] == "v1"


def test_run_quality_engine_v2_applies_v2_in_v2_mode() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team discussed launch readiness.",
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(notes, "The goal is to confirm launch readiness.", mode="v2")

    assert result["metadata"]["applied"] is True
    assert result["metadata"]["mode"] == "v2"
    assert result["notes"]["summary_slots"]["purpose"]


def test_run_quality_engine_v2_shadow_keeps_v1_notes_user_facing() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team discussed launch readiness.",
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(notes, "The goal is to confirm launch readiness.", mode="shadow")

    assert result["notes"] == notes
    assert result["metadata"]["applied"] is False
    assert result["metadata"]["mode"] == "shadow"
    assert result["metadata"]["shadow_ran"] is True
    assert result["metadata"]["shadow_summary"]["purpose_added"] is True
