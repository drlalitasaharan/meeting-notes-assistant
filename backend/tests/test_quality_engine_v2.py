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
