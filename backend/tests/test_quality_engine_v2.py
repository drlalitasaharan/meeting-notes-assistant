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
    assert (
        "pricing" in improved["summary_slots"]["purpose"].lower()
        or "launch" in improved["summary_slots"]["purpose"].lower()
    )


def test_quality_engine_v2_syncs_next_steps_from_actions() -> None:
    notes = {
        "summary": "The team discussed launch follow-up.",
        "summary_slots": {
            "purpose": "Confirm launch follow-up.",
            "outcome": "",
            "risks": [],
            "next_steps": [],
        },
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

    improved = apply_quality_engine_v2(
        notes, "Lalita will update the pricing page CTA before launch."
    )

    next_steps = improved["summary_slots"]["next_steps"]
    assert next_steps
    assert any("pricing page CTA" in step for step in next_steps)


def test_quality_engine_v2_preserves_existing_decisions() -> None:
    notes = {
        "summary": "The team aligned on the launch scope.",
        "summary_slots": {
            "purpose": "Review launch scope.",
            "outcome": "",
            "risks": [],
            "next_steps": [],
        },
        "action_item_objects": [],
        "decision_objects": [
            {
                "text": "Keep launch scope focused on upload, processing, notes review, and Markdown export.",
                "confidence": 0.8,
            }
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


def test_quality_engine_v2_extracts_explicit_unresolved_questions_from_transcript() -> None:
    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "Review launch readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Open question: Who owns the support page update?
    The team still needs to confirm whether the launch post goes live Friday.
    """

    improved = apply_quality_engine_v2(notes, transcript)
    questions = improved["summary_slots"]["open_questions"]

    assert "Who owns the support page update?" in questions
    assert "Whether the launch post goes live Friday?" in questions


def test_quality_engine_v2_preserves_existing_open_questions() -> None:
    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {
            "purpose": "Review launch readiness.",
            "next_steps": [],
            "open_questions": ["Who confirms the PayPal test?"],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["summary_slots"]["open_questions"] == ["Who confirms the PayPal test?"]


def test_quality_engine_v2_deduplicates_repeated_open_questions() -> None:
    notes = {
        "summary": "Open question: Who owns onboarding copy?",
        "summary_slots": {
            "purpose": "Review onboarding.",
            "next_steps": [],
            "open_questions": ["Who owns onboarding copy?"],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Unresolved question: who owns onboarding copy?"

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["open_questions"] == ["Who owns onboarding copy?"]


def test_quality_engine_v2_does_not_extract_questions_when_none_are_present() -> None:
    notes = {
        "summary": "The team confirmed launch readiness and reviewed support ownership.",
        "summary_slots": {"purpose": "Review launch readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Does that make sense? Any questions? The support owner is confirmed."

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["open_questions"] == []


def test_quality_engine_v2_open_questions_preserve_existing_v1_and_shadow_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Open question: Who owns support routing?"

    v1_result = run_quality_engine_v2(notes, transcript, mode="v1")
    shadow_result = run_quality_engine_v2(notes, transcript, mode="shadow")

    assert v1_result["notes"] == original
    assert shadow_result["notes"] == original
    assert notes == original
    assert shadow_result["metadata"]["shadow_ran"] is True


def test_quality_engine_v2_open_questions_keep_known_entity_warnings_working() -> None:
    notes = {
        "summary": "Open question: who owns pay pal checkout validation?",
        "summary_slots": {"purpose": "Review checkout readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert "Who owns pay pal checkout validation?" in improved["summary_slots"]["open_questions"]
    assert any(
        "PayPal" in warning for warning in improved["summary_slots"]["known_entity_warnings"]
    )


def test_quality_engine_v2_extracts_explicit_risks_from_transcript() -> None:
    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "Review launch readiness.", "next_steps": [], "risks": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Risk: Pricing approval may delay the launch follow-up.
    Blocker: The support page owner is still waiting on review guidance.
    """

    improved = apply_quality_engine_v2(notes, transcript)
    risks = improved["summary_slots"]["risks"]

    assert "Pricing approval may delay the launch follow-up." in risks
    assert "The support page owner is still waiting on review guidance." in risks


def test_quality_engine_v2_preserves_existing_risks() -> None:
    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {
            "purpose": "Review launch readiness.",
            "next_steps": [],
            "risks": ["Long recordings need manual review before publication."],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["summary_slots"]["risks"] == [
        "Long recordings need manual review before publication."
    ]


def test_quality_engine_v2_deduplicates_repeated_risks() -> None:
    notes = {
        "summary": "Risk: Pricing approval may delay launch.",
        "summary_slots": {
            "purpose": "Review launch readiness.",
            "next_steps": [],
            "risks": ["Pricing approval may delay launch."],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Risk: pricing approval may delay launch."

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["risks"] == ["Pricing approval may delay launch."]


def test_quality_engine_v2_does_not_extract_risks_when_none_are_present() -> None:
    notes = {
        "summary": "The team reviewed risks and action items, then confirmed ownership.",
        "summary_slots": {"purpose": "Review launch readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "The prior blocker was resolved. No risks remain for launch."

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["risks"] == []


def test_quality_engine_v2_risks_preserve_existing_v1_and_shadow_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Risk: Pricing approval may delay launch."

    v1_result = run_quality_engine_v2(notes, transcript, mode="v1")
    shadow_result = run_quality_engine_v2(notes, transcript, mode="shadow")

    assert v1_result["notes"] == original
    assert shadow_result["notes"] == original
    assert notes == original
    assert shadow_result["metadata"]["shadow_ran"] is True


def test_quality_engine_v2_risks_keep_open_questions_and_known_entity_warnings_working() -> None:
    notes = {
        "summary": "Risk: pay pal checkout may delay launch. Open question: who owns sqare validation?",
        "summary_slots": {"purpose": "Review checkout readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert "Pay pal checkout may delay launch." in improved["summary_slots"]["risks"]
    assert "Who owns sqare validation?" in improved["summary_slots"]["open_questions"]
    warnings = " ".join(improved["summary_slots"]["known_entity_warnings"])
    assert "PayPal" in warnings
    assert "Square" in warnings


def test_quality_engine_v2_extracts_explicit_action_items_from_transcript() -> None:
    notes = {
        "summary": "The team reviewed onboarding.",
        "summary_slots": {"purpose": "Review onboarding.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Aisha will update the landing page onboarding copy by Friday morning.
    Action for Marco: add a sample recording link to the upload page before the next product review.
    """

    improved = apply_quality_engine_v2(notes, transcript)
    actions = improved["action_item_objects"]

    assert {
        "owner": "Aisha",
        "task": "Update the landing page onboarding copy",
        "deadline": "Friday morning",
        "status": "open",
        "priority": "medium",
    } in actions
    assert {
        "owner": "Marco",
        "task": "Add a sample recording link to the upload page",
        "deadline": "the next product review",
        "status": "open",
        "priority": "medium",
    } in actions


def test_quality_engine_v2_preserves_existing_action_item_objects() -> None:
    notes = {
        "summary": "The team reviewed support.",
        "summary_slots": {"purpose": "Review support.", "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Nora",
                "task": "Draft the first support macro",
                "deadline": "Wednesday",
                "status": "open",
                "priority": "high",
            }
        ],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["action_item_objects"] == notes["action_item_objects"]


def test_quality_engine_v2_deduplicates_repeated_action_items() -> None:
    notes = {
        "summary": "The team reviewed checkout.",
        "summary_slots": {"purpose": "Review checkout.", "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Sam",
                "task": "Verify Square and PayPal webhook logs",
                "status": "open",
            }
        ],
        "decision_objects": [],
    }
    transcript = "Sam will verify Square and PayPal webhook logs after the next test payment."

    improved = apply_quality_engine_v2(notes, transcript)

    matching = [
        item
        for item in improved["action_item_objects"]
        if item["owner"] == "Sam" and item["task"] == "Verify Square and PayPal webhook logs"
    ]
    assert len(matching) == 1


def test_quality_engine_v2_extracts_clear_action_owner_and_deadline() -> None:
    notes = {
        "summary": "The team reviewed pricing.",
        "summary_slots": {"purpose": "Review pricing.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(
        notes,
        "Priya, please prepare the BetaList submission using the Acjen AI URL by end of week.",
    )

    assert improved["action_item_objects"] == [
        {
            "owner": "Priya",
            "task": "Prepare the BetaList submission using the Acjen AI URL",
            "deadline": "end of week",
            "status": "open",
            "priority": "medium",
        }
    ]


def test_quality_engine_v2_does_not_extract_generic_discussion_points_as_actions() -> None:
    notes = {
        "summary": "The team reviewed risks and action items.",
        "summary_slots": {"purpose": "Review launch readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Marco says: I will listen for concrete actions and deadlines.
    Aisha says: I want to make sure the notes separate confirmed decisions from general discussion.
    The most important action items should include an owner and deadline.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["action_item_objects"] == []


def test_quality_engine_v2_action_extraction_preserves_v1_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed onboarding.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "Aisha will update the landing page onboarding copy by Friday morning.",
        mode="v1",
    )

    assert result["notes"] == notes
    assert result["metadata"]["applied"] is False


def test_quality_engine_v2_action_extraction_preserves_shadow_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed onboarding.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "The team reviewed onboarding.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "Aisha will update the landing page onboarding copy by Friday morning.",
        mode="shadow",
    )

    assert result["notes"] == original
    assert notes == original
    assert result["metadata"]["shadow_ran"] is True


def test_quality_engine_v2_actions_keep_risks_questions_and_entity_warnings_working() -> None:
    notes = {
        "summary": "Risk: pay pal checkout may delay launch. Open question: who owns sqare validation?",
        "summary_slots": {"purpose": "Review checkout.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Sam will verify Square and PayPal webhook logs after the next test payment."

    improved = apply_quality_engine_v2(notes, transcript)

    assert any(item["owner"] == "Sam" for item in improved["action_item_objects"])
    assert "Pay pal checkout may delay launch." in improved["summary_slots"]["risks"]
    assert "Who owns sqare validation?" in improved["summary_slots"]["open_questions"]
    warnings = " ".join(improved["summary_slots"]["known_entity_warnings"])
    assert "PayPal" in warnings
    assert "Square" in warnings


def test_quality_engine_v2_extracts_explicit_decisions_from_transcript() -> None:
    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "Review launch readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Decision: we will launch Starter first.
    We agreed to keep PayPal and Square both enabled.
    The team decided to delay Pro Pilot testing.
    Confirmed decision: use Acjen.ai as the public URL.
    """

    improved = apply_quality_engine_v2(notes, transcript)
    decisions = improved["decision_objects"]

    assert {"text": "Launch Starter first.", "confidence": 0.8} in decisions
    assert {"text": "Keep PayPal and Square both enabled.", "confidence": 0.8} in decisions
    assert {"text": "Delay Pro Pilot testing.", "confidence": 0.8} in decisions
    assert {"text": "Use Acjen.ai as the public URL.", "confidence": 0.8} in decisions


def test_quality_engine_v2_preserves_existing_decision_objects() -> None:
    notes = {
        "summary": "The team aligned on launch scope.",
        "summary_slots": {"purpose": "Review launch scope.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [
            {
                "text": "Keep launch scope focused on upload, processing, notes review, and Markdown export.",
                "confidence": 0.9,
            }
        ],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["decision_objects"] == notes["decision_objects"]


def test_quality_engine_v2_deduplicates_repeated_decisions() -> None:
    notes = {
        "summary": "Decision: use Acjen.ai as the public URL.",
        "summary_slots": {"purpose": "Review launch URL.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [
            {"text": "Use Acjen.ai as the public URL.", "confidence": 0.7}
        ],
    }
    transcript = "Confirmed decision: use Acjen.ai as the public URL."

    improved = apply_quality_engine_v2(notes, transcript)

    matching = [
        item
        for item in improved["decision_objects"]
        if item["text"] == "Use Acjen.ai as the public URL."
    ]
    assert len(matching) == 1


def test_quality_engine_v2_avoids_suggestions_options_and_questions_as_decisions() -> None:
    notes = {
        "summary": "The team discussed launch options.",
        "summary_slots": {"purpose": "Review launch options.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Maybe we should launch Starter first.
    One option is to keep PayPal and Square both enabled.
    Should we delay Pro Pilot testing?
    No decision yet on Business Team.
    We need to decide the public URL later.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["decision_objects"] == []


def test_quality_engine_v2_avoids_generic_discussion_points_as_decisions() -> None:
    notes = {
        "summary": "The team reviewed decisions.",
        "summary_slots": {"purpose": "Review notes quality.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Decisions discussed in this meeting are listed next as spoken meeting content.
    Aisha says: I want to make sure the notes separate confirmed decisions from general discussion.
    The goal is to finish with exact decisions, risks, questions, and owners.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["decision_objects"] == []


def test_quality_engine_v2_decision_extraction_preserves_v1_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "Decision: we will launch Starter first.",
        mode="v1",
    )

    assert result["notes"] == notes
    assert result["metadata"]["applied"] is False


def test_quality_engine_v2_decision_extraction_preserves_shadow_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "The team reviewed launch readiness.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "Decision: we will launch Starter first.",
        mode="shadow",
    )

    assert result["notes"] == original
    assert notes == original
    assert result["metadata"]["shadow_ran"] is True


def test_quality_engine_v2_decisions_keep_actions_risks_questions_and_entities_working() -> None:
    notes = {
        "summary": (
            "Risk: pay pal checkout may delay launch. "
            "Open question: who owns sqare validation?"
        ),
        "summary_slots": {"purpose": "Review checkout.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Decision: we will keep PayPal and Square both enabled.
    Sam will verify Square and PayPal webhook logs after the next test payment.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert {
        "text": "Keep PayPal and Square both enabled.",
        "confidence": 0.8,
    } in improved["decision_objects"]
    assert any(item["owner"] == "Sam" for item in improved["action_item_objects"])
    assert "Pay pal checkout may delay launch." in improved["summary_slots"]["risks"]
    assert "Who owns sqare validation?" in improved["summary_slots"]["open_questions"]
    warnings = " ".join(improved["summary_slots"]["known_entity_warnings"])
    assert "PayPal" in warnings
    assert "Square" in warnings
