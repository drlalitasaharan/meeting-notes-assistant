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


def test_run_quality_engine_v2_shadow_does_not_mutate_original_notes() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team discussed onboarding.",
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    original_copy = {
        "summary": "The team discussed onboarding.",
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "The goal is to confirm onboarding readiness.",
        mode="shadow",
    )

    assert notes == original_copy
    assert result["notes"] == original_copy
    assert result["metadata"]["shadow_ran"] is True
    assert result["metadata"]["shadow_summary"]["purpose_added"] is True


def test_run_quality_engine_v2_unknown_mode_safely_uses_v1() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team discussed launch readiness.",
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "The goal is to confirm launch readiness.",
        mode="bad-mode",
    )

    assert result["notes"] == notes
    assert result["metadata"]["mode"] == "v1"
    assert result["metadata"]["applied"] is False


def test_quality_engine_v2_correct_known_entities_produce_no_warning() -> None:
    notes = {
        "summary": (
            "MeetIQ uses Acjen AI, support@acjen.ai, PayPal, Square, Render, "
            "Vercel, GoDaddy, BetaList, Indie Hackers, Product Hunt, GitHub, "
            "Markdown, Starter, and Pro Pilot."
        ),
        "summary_slots": {"purpose": "Review MeetIQ launch readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, None)

    assert improved["summary_slots"]["known_entity_warnings"] == []


def test_quality_engine_v2_warns_on_obvious_known_entity_variants() -> None:
    notes = {
        "summary": "The team mentioned a gen.ai, meet iq, git hub, and producthunt.",
        "summary_slots": {"purpose": "Review launch readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, None)
    warnings = " ".join(improved["summary_slots"]["known_entity_warnings"])

    assert "Acjen AI" in warnings
    assert "MeetIQ" in warnings
    assert "GitHub" in warnings
    assert "Product Hunt" in warnings
    assert improved["summary"] == notes["summary"]


def test_quality_engine_v2_warns_on_support_email_variants() -> None:
    notes = {
        "summary": "Use support at Acjen AI until support@acjen.com is ready.",
        "summary_slots": {"purpose": "Review support routing.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, None)
    warnings = improved["summary_slots"]["known_entity_warnings"]

    assert any("support@acjen.ai" in warning for warning in warnings)


def test_quality_engine_v2_warns_on_paypal_and_square_variants() -> None:
    notes = {
        "summary": "Check pay pal checkout and the sqare fallback link.",
        "summary_slots": {"purpose": "Review checkout readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, None)
    warnings = " ".join(improved["summary_slots"]["known_entity_warnings"])

    assert "PayPal" in warnings
    assert "Square" in warnings


def test_quality_engine_v2_known_entity_warnings_preserve_existing_v1_and_shadow_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "Check pay pal checkout before launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "Check pay pal checkout before launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    v1_result = run_quality_engine_v2(notes, "The goal is to review checkout.", mode="v1")
    shadow_result = run_quality_engine_v2(notes, "The goal is to review checkout.", mode="shadow")

    assert v1_result["notes"] == original
    assert shadow_result["notes"] == original
    assert notes == original
    assert shadow_result["metadata"]["shadow_ran"] is True
