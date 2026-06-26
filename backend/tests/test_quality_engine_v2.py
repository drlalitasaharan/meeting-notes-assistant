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


def test_quality_engine_v2_allowlist_parsing_ignores_empty_segments() -> None:
    from app.services.quality_engine_v2 import parse_quality_engine_v2_allowlist

    assert parse_quality_engine_v2_allowlist(" Admin@Example.com, , qa@example.com ") == {
        "admin@example.com",
        "qa@example.com",
    }


def test_quality_engine_v2_email_allowlist_matching_is_case_insensitive() -> None:
    from app.services.quality_engine_v2 import is_quality_engine_v2_email_allowlisted

    assert (
        is_quality_engine_v2_email_allowlisted(
            " ADMIN@example.COM ",
            "qa@example.com, admin@EXAMPLE.com",
        )
        is True
    )


def test_quality_engine_v2_email_allowlist_uses_env_when_value_not_supplied(
    monkeypatch,
) -> None:
    from app.services.quality_engine_v2 import is_quality_engine_v2_email_allowlisted

    monkeypatch.setenv("MEETIQ_QEV2_ALLOWLIST_EMAILS", "internal@example.com")

    assert is_quality_engine_v2_email_allowlisted("internal@example.com") is True
    assert is_quality_engine_v2_email_allowlisted("customer@example.com") is False


def test_resolve_notes_engine_mode_defaults_to_v1_when_env_unset(monkeypatch) -> None:
    from app.services.quality_engine_v2 import resolve_notes_engine_mode_for_user

    monkeypatch.delenv("MEETIQ_QEV2_ALLOWLIST_EMAILS", raising=False)

    assert resolve_notes_engine_mode_for_user(None, "admin@example.com") == "v1"


def test_resolve_notes_engine_mode_keeps_non_allowlisted_email_on_v1() -> None:
    from app.services.quality_engine_v2 import resolve_notes_engine_mode_for_user

    assert (
        resolve_notes_engine_mode_for_user(
            "v1",
            "customer@example.com",
            "admin@example.com",
        )
        == "v1"
    )


def test_resolve_notes_engine_mode_routes_allowlisted_email_to_v2() -> None:
    from app.services.quality_engine_v2 import resolve_notes_engine_mode_for_user

    assert (
        resolve_notes_engine_mode_for_user(
            "v1",
            "admin@example.com",
            "qa@example.com, admin@example.com",
        )
        == "v2"
    )


def test_resolve_notes_engine_mode_missing_email_stays_v1() -> None:
    from app.services.quality_engine_v2 import resolve_notes_engine_mode_for_user

    assert resolve_notes_engine_mode_for_user("v1", None, "admin@example.com") == "v1"


def test_resolve_notes_engine_mode_preserves_shadow_and_explicit_global_v2() -> None:
    from app.services.quality_engine_v2 import resolve_notes_engine_mode_for_user

    assert (
        resolve_notes_engine_mode_for_user(
            "shadow",
            "customer@example.com",
            "admin@example.com",
        )
        == "shadow"
    )
    assert (
        resolve_notes_engine_mode_for_user(
            "v2",
            "customer@example.com",
            "admin@example.com",
        )
        == "v2"
    )


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


def test_quality_engine_v2_extracts_speaker_accepted_actions_with_spoken_dates() -> None:
    notes = {
        "summary": "The team reviewed pilot actions.",
        "summary_slots": {"purpose": "Review pilot actions.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Priya: I accept the first action. I will obtain written pricing approval and circulate the approved pricing table to the team. by five PM on June eighteenth, twenty twenty-six.
    Alex: I accept the second action. I will send the completed security review summary covering storage access, administrator permissions, and deletion controls. by noon on June twenty-second, twenty twenty-six.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert {
        "owner": "Priya",
        "task": "Obtain written pricing approval and circulate the approved pricing table to the team",
        "deadline": "2026-06-18 17:00",
        "status": "open",
        "priority": "medium",
    } in improved["action_item_objects"]
    assert {
        "owner": "Alex",
        "task": "Send the completed security review summary covering storage access, administrator permissions, and deletion controls",
        "deadline": "2026-06-22 12:00",
        "status": "open",
        "priority": "medium",
    } in improved["action_item_objects"]


def test_quality_engine_v2_does_not_treat_policy_subjects_as_action_owners() -> None:
    notes = {
        "summary": "The team reviewed pilot policies.",
        "summary_slots": {"purpose": "Review pilot policies.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Decision confirmed: Email will be the standard support channel for the pilot.
    Decision confirmed: Pilot recordings will be limited to thirty minutes.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["action_item_objects"] == []


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


def test_quality_engine_v2_extracts_numbered_decisions_separately() -> None:
    notes = {
        "summary": "The team reviewed demo decisions.",
        "summary_slots": {"purpose": "Review demo decisions.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = (
        "Decision one: meeting seventeen will be the current best backup demo example. "
        "Decision two: the ten-minute realistic file remains the main proof of quality. "
        "Decision three: the thirty-minute file will be used as a stress test rather than a live default."
    )

    improved = apply_quality_engine_v2(notes, transcript)
    decision_text = [item["text"] for item in improved["decision_objects"]]

    assert decision_text == [
        "Meeting seventeen will be the current best backup demo example.",
        "The ten-minute realistic file remains the main proof of quality.",
        "The thirty-minute file will be used as a stress test rather than a live default.",
    ]


def test_quality_engine_v2_extracts_decision_confirmed_followed_by_sentence() -> None:
    notes = {
        "summary": "The team reviewed pilot launch constraints.",
        "summary_slots": {"purpose": "Review pilot launch constraints.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = (
        "Priya: Decision confirmed. "
        "Single sign-on will remain outside the pilot scope unless the client explicitly requests it."
    )

    improved = apply_quality_engine_v2(notes, transcript)

    assert {
        "text": "Single sign-on will remain outside the pilot scope unless the client explicitly requests it.",
        "confidence": 0.8,
    } in improved["decision_objects"]


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
        "decision_objects": [{"text": "Use Acjen.ai as the public URL.", "confidence": 0.7}],
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
            "Risk: pay pal checkout may delay launch. Open question: who owns sqare validation?"
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


def test_quality_engine_v2_action_dedupe_keeps_richer_owner_deadline_item() -> None:
    notes = {
        "summary": "The team reviewed launch copy.",
        "summary_slots": {"purpose": "Review launch copy.", "next_steps": []},
        "action_item_objects": [
            {
                "task": "Prepare BetaList copy",
                "status": "open",
            }
        ],
        "decision_objects": [],
    }
    transcript = "Priya will prepare BetaList copy by Friday morning."

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["action_item_objects"] == [
        {
            "owner": "Priya",
            "task": "Prepare BetaList copy",
            "deadline": "Friday morning",
            "status": "open",
            "priority": "medium",
        }
    ]


def test_quality_engine_v2_action_extraction_avoids_vague_review_check_items() -> None:
    notes = {
        "summary": "The team reviewed follow-up.",
        "summary_slots": {"purpose": "Review follow-up.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Priya will review this by Friday.
    Sam will check it by Monday.
    Jordan will follow up on the topic next week.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["action_item_objects"] == []


def test_quality_engine_v2_decision_extraction_avoids_generic_confirmed_status() -> None:
    notes = {
        "summary": "The team reviewed readiness.",
        "summary_slots": {"purpose": "Review readiness.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Decision confirmed: Sam owns weekend monitoring.
    Decision confirmed: backend is healthy.
    Decision confirmed: the demo is ready.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["decision_objects"] == []


def test_quality_engine_v2_decision_extraction_still_keeps_explicit_decisions() -> None:
    notes = {
        "summary": "The team reviewed launch decisions.",
        "summary_slots": {"purpose": "Review launch decisions.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Decision: we will launch Starter first.
    We agreed to keep PayPal and Square both enabled.
    The team decided to delay Pro Pilot testing.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    decision_text = [item["text"] for item in improved["decision_objects"]]
    assert "Launch Starter first." in decision_text
    assert "Keep PayPal and Square both enabled." in decision_text
    assert "Delay Pro Pilot testing." in decision_text


def test_quality_engine_v2_risk_extraction_avoids_action_like_items() -> None:
    notes = {
        "summary": "The team reviewed billing follow-up.",
        "summary_slots": {"purpose": "Review billing.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Risk: Sam will verify Square and PayPal webhook logs after the next test payment."

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["risks"] == []


def test_quality_engine_v2_open_questions_excludes_question_answered_later() -> None:
    notes = {
        "summary": "The team reviewed launch URL.",
        "summary_slots": {"purpose": "Review launch URL.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Open question: should the public URL be Acjen.ai or the Vercel app?
    Decision confirmed: use Acjen.ai as the public URL.
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["open_questions"] == []
    assert {
        "text": "Use Acjen.ai as the public URL.",
        "confidence": 0.8,
    } in improved["decision_objects"]


def test_quality_engine_v2_open_questions_keeps_explicit_unresolved_question() -> None:
    notes = {
        "summary": "The team reviewed support operations.",
        "summary_slots": {"purpose": "Review support.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Open question: who owns refunds when PayPal and Square results differ?"

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["open_questions"] == [
        "Who owns refunds when PayPal and Square results differ?"
    ]


def test_quality_engine_v2_open_questions_excludes_rhetorical_question() -> None:
    notes = {
        "summary": "The team reviewed checkout readiness.",
        "summary_slots": {"purpose": "Review checkout.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Open question: does that make sense?"

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["open_questions"] == []


def test_quality_engine_v2_open_question_section_keeps_multiple_real_questions() -> None:
    notes = {
        "summary": "The team reviewed support operations.",
        "summary_slots": {"purpose": "Review support.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = """
    Open questions:
    - Should the support page mention a typical processing-time range?
    - Should the admin page show queue depth or only recent failures?
    """

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["open_questions"] == [
        "Should the support page mention a typical processing-time range?",
        "Should the admin page show queue depth or only recent failures?",
    ]


def test_quality_engine_v2_risk_extraction_avoids_generic_concern_without_marker() -> None:
    notes = {
        "summary": "The team reviewed launch concerns.",
        "summary_slots": {"purpose": "Review launch.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Pricing approval could be a concern for launch timing."

    improved = apply_quality_engine_v2(notes, transcript)

    assert improved["summary_slots"]["risks"] == []


def test_quality_engine_v2_global_dedupe_preserves_distinct_items() -> None:
    notes = {
        "summary": "The team reviewed pricing.",
        "summary_slots": {"purpose": "Review pricing.", "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Alex",
                "task": "Update pricing copy",
                "status": "open",
            }
        ],
        "decision_objects": [{"text": "Use Acjen.ai as the public URL.", "confidence": 0.8}],
    }
    transcript = """
    Alex will approve the pricing table by Friday.
    Decision: we will keep Starter checkout primary.
    Risk: Pricing approval may delay launch.
    Open question: who approves the launch post?
    """

    improved = apply_quality_engine_v2(notes, transcript)

    action_tasks = [item["task"] for item in improved["action_item_objects"]]
    decision_text = [item["text"] for item in improved["decision_objects"]]
    assert "Update pricing copy" in action_tasks
    assert "Approve the pricing table" in action_tasks
    assert "Use Acjen.ai as the public URL." in decision_text
    assert "Keep Starter checkout primary." in decision_text
    assert improved["summary_slots"]["risks"] == ["Pricing approval may delay launch."]
    assert improved["summary_slots"]["open_questions"] == ["Who approves the launch post?"]


def test_quality_engine_v2_tuning_preserves_v1_and_shadow_behavior() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Decision: we will launch Starter first. Priya will prepare copy by Friday."

    v1_result = run_quality_engine_v2(notes, transcript, mode="v1")
    shadow_result = run_quality_engine_v2(notes, transcript, mode="shadow")

    assert v1_result["notes"] == original
    assert shadow_result["notes"] == original
    assert notes == original
    assert shadow_result["metadata"]["shadow_ran"] is True


def test_quality_engine_v2_tuning_keeps_known_entity_warnings_working() -> None:
    notes = {
        "summary": "Decision: we will keep pay pal and sqare support enabled.",
        "summary_slots": {"purpose": "Review checkout.", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    warnings = " ".join(improved["summary_slots"]["known_entity_warnings"])
    assert "PayPal" in warnings
    assert "Square" in warnings


def test_quality_engine_v2_markdown_renderer_renders_all_sections() -> None:
    from app.services.quality_engine_v2 import render_quality_engine_v2_markdown

    notes = {
        "summary": "The team aligned on launch readiness.",
        "summary_slots": {
            "purpose": "Review launch readiness.",
            "open_questions": ["Who monitors first weekend signups?"],
            "risks": ["Webhook activation failure may block paid upload limits."],
            "next_steps": ["Run production smoke test."],
        },
        "key_points": ["Starter checkout remains the primary public plan."],
        "decision_objects": [{"text": "Launch as controlled early access."}],
        "action_item_objects": [
            {
                "owner": "Sam",
                "task": "Run a production smoke test",
                "deadline": "noon tomorrow",
                "status": "open",
            }
        ],
    }

    markdown = render_quality_engine_v2_markdown(notes)

    assert "## Purpose\n\nReview launch readiness." in markdown
    assert "## Summary\n\nThe team aligned on launch readiness." in markdown
    assert "## Key Points\n\n- Starter checkout remains the primary public plan." in markdown
    assert "## Decisions\n\n- Launch as controlled early access." in markdown
    assert (
        "## Action Items\n\n"
        "- [ ] **Sam** — Run a production smoke test _(deadline: noon tomorrow, status: open)_"
    ) in markdown
    assert "## Open Questions\n\n- Who monitors first weekend signups?" in markdown
    assert (
        "## Risks / Blockers\n\n- Webhook activation failure may block paid upload limits."
    ) in markdown
    assert "## Next Steps\n\n- Run production smoke test." in markdown


def test_quality_engine_v2_markdown_renderer_skips_empty_sections_cleanly() -> None:
    from app.services.quality_engine_v2 import render_quality_engine_v2_markdown

    notes = {
        "summary": "The team aligned on launch readiness.",
        "summary_slots": {"purpose": "Review launch readiness."},
        "action_item_objects": [],
        "decision_objects": [],
    }

    markdown = render_quality_engine_v2_markdown(notes)

    assert markdown == (
        "## Purpose\n\nReview launch readiness.\n\n"
        "## Summary\n\nThe team aligned on launch readiness.\n"
    )
    assert "## Decisions" not in markdown
    assert "## Action Items" not in markdown
    assert "None" not in markdown


def test_quality_engine_v2_markdown_renderer_formats_action_without_optional_fields() -> None:
    from app.services.quality_engine_v2 import render_quality_engine_v2_markdown

    notes = {
        "summary_slots": {},
        "action_item_objects": [{"task": "Prepare launch copy"}],
        "decision_objects": [],
    }

    markdown = render_quality_engine_v2_markdown(notes)

    assert markdown == "## Action Items\n\n- [ ] Prepare launch copy _(status: open)_\n"


def test_quality_engine_v2_markdown_renderer_formats_decision_objects() -> None:
    from app.services.quality_engine_v2 import render_quality_engine_v2_markdown

    notes = {
        "summary_slots": {},
        "action_item_objects": [],
        "decision_objects": [
            {"text": "Use Acjen.ai as the public URL."},
            {"decision": "Keep Starter checkout primary."},
        ],
    }

    markdown = render_quality_engine_v2_markdown(notes)

    assert markdown == (
        "## Decisions\n\n- Use Acjen.ai as the public URL.\n- Keep Starter checkout primary.\n"
    )


def test_quality_engine_v2_markdown_renderer_preserves_v1_and_shadow_behavior() -> None:
    from app.services.quality_engine_v2 import (
        render_quality_engine_v2_markdown,
        run_quality_engine_v2,
    )

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    transcript = "Decision: we will launch Starter first."

    v1_result = run_quality_engine_v2(notes, transcript, mode="v1")
    shadow_result = run_quality_engine_v2(notes, transcript, mode="shadow")
    markdown = render_quality_engine_v2_markdown(
        {
            "summary": "The team reviewed launch.",
            "summary_slots": {"purpose": "Review launch."},
        }
    )

    assert v1_result["notes"] == notes
    assert shadow_result["notes"] == notes
    assert markdown.startswith("## Purpose")


def test_quality_engine_v2_renderer_does_not_enable_v2_by_default() -> None:
    from app.services.quality_engine_v2 import normalize_notes_engine_mode

    assert normalize_notes_engine_mode(None) == "v1"


def test_quality_engine_v2_admin_comparison_keeps_v1_default() -> None:
    from app.services.quality_engine_v2 import normalize_notes_engine_mode

    assert normalize_notes_engine_mode(None) == "v1"
    assert normalize_notes_engine_mode("") == "v1"


def test_quality_engine_v2_shadow_comparison_does_not_alter_user_notes() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "Decision: we will launch Starter first. Priya will prepare copy by Friday.",
        mode="shadow",
    )

    assert result["notes"] == original
    assert notes == original
    assert result["metadata"]["shadow_ran"] is True
    assert "v2_notes" not in result
    assert "v2_markdown" not in result


def test_quality_engine_v2_comparison_output_not_exposed_to_normal_users() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "Decision: we will launch Starter first.",
        mode="v1",
    )

    assert result == {
        "notes": notes,
        "metadata": {
            "applied": False,
            "mode": "v1",
            "fallback_used": False,
            "warnings": [],
        },
    }
    assert "comparison" not in result
    assert "v2_notes" not in result
    assert "v2_markdown" not in result


def test_quality_engine_v2_admin_comparison_path_is_explicit() -> None:
    from app.services.quality_engine_v2 import build_quality_engine_v2_admin_comparison

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = build_quality_engine_v2_admin_comparison(
        notes,
        "Decision: we will launch Starter first. Priya will prepare copy by Friday.",
    )

    assert result["admin_only"] is True
    assert result["user_notes"] == notes
    assert result["metadata"]["mode"] == "admin_comparison"
    assert result["metadata"]["applied_to_user_notes"] is False
    assert result["metadata"]["fallback_used"] is False
    assert "critic" in result["metadata"]
    assert result["v2_notes"] != notes
    assert "Launch Starter first." in result["v2_markdown"]
    assert result["comparison"]["improved_action_count"] == 1
    assert result["comparison"]["improved_decision_count"] == 1


def test_quality_engine_v2_cleans_transcript_like_key_points() -> None:
    notes = {
        "summary": "The team reviewed support operations.",
        "summary_slots": {"purpose": "Review support.", "next_steps": []},
        "key_points": [
            "Sophia says, Sophia will update the support page with review recommended language for long recordings before the launch post goes live",
            "Aaron says, I will listen for concrete actions, deadlines, because this recording is part of the 30-60 minute quality baseline",
            "Sophia says, open question, should the support page mention a typical processing time range?",
            "Meyer says, the goal today is to review support operations, and reliability review, and finish with exact decisions, risks, questions, and owners",
            "Maya says, I want to make sure the notes separate confirmed decisions from general discussion, because this is what a user will expect after a real meeting",
            "Support operations and reliability are being reviewed for launch readiness",
        ],
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    key_points_text = " ".join(improved["key_points"])
    assert "Sophia says" not in key_points_text
    assert "Aaron says" not in key_points_text
    assert "Meyer says" not in key_points_text
    assert "Maya says" not in key_points_text
    assert "30-60 minute quality baseline" not in key_points_text
    assert "separate confirmed decisions from general discussion" not in key_points_text
    assert improved["key_points"] == [
        "Support operations and reliability are being reviewed for launch readiness"
    ]


def test_quality_engine_v2_moves_open_question_key_point_to_open_questions() -> None:
    notes = {
        "summary": "The team reviewed support operations.",
        "summary_slots": {"purpose": "Review support.", "next_steps": []},
        "key_points": [
            "Sophia says, open question, should the support page mention a typical processing time range?"
        ],
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["key_points"] == []
    assert improved["summary_slots"]["open_questions"] == [
        "Should the support page mention a typical processing time range?"
    ]


def test_quality_engine_v2_support_page_key_point_remains_action_or_next_step() -> None:
    notes = {
        "summary": "The team reviewed support operations.",
        "summary_slots": {"purpose": "Review support.", "next_steps": []},
        "key_points": [
            "Sophia says, Sophia will update the support page with review recommended language for long recordings before the launch post goes live"
        ],
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["key_points"] == []
    assert any(
        item["owner"] == "Sophia" and "support page" in item["task"]
        for item in improved["action_item_objects"]
    )
    assert any("support page" in step for step in improved["summary_slots"]["next_steps"])


def test_quality_engine_v2_critic_warns_on_missing_purpose() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "The team reviewed launch readiness.",
            "summary_slots": {},
            "action_item_objects": [{"owner": "Sam", "task": "Run smoke test"}],
            "decision_objects": [],
        }
    )

    assert result["checks"]["purpose_present"] is False
    assert "Purpose is missing." in result["warnings"]
    assert result["passed"] is False


def test_quality_engine_v2_critic_warns_on_generic_summary() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "The meeting aligned on the main priorities and next steps",
            "summary_slots": {"purpose": "Review launch."},
            "action_item_objects": [{"owner": "Sam", "task": "Run smoke test"}],
            "decision_objects": [],
        }
    )

    assert result["checks"]["summary_specific"] is False
    assert "Summary appears too generic." in result["warnings"]


def test_quality_engine_v2_critic_warns_on_too_few_actions() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "The team reviewed launch readiness.",
            "summary_slots": {"purpose": "Review launch."},
            "action_item_objects": [],
            "decision_objects": [],
        }
    )

    assert result["checks"]["actions_present"] is False
    assert "Action items are missing or too few." in result["warnings"]


def test_quality_engine_v2_critic_allows_decisions_only_transcript_without_actions() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "The team confirmed pilot policy decisions.",
            "summary_slots": {"purpose": "Confirm pilot policy."},
            "action_item_objects": [],
            "decision_objects": [{"text": "The pilot will support ten users."}],
        },
        "This is a decisions-only meeting. No action items or next steps were assigned.",
    )

    assert result["checks"]["actions_present"] is True
    assert result["passed"] is True


def test_quality_engine_v2_critic_keeps_generic_summary_warning_non_blocking() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "The meeting aligned on the main priorities and next steps",
            "summary_slots": {"purpose": "Review launch."},
            "action_item_objects": [{"owner": "Sam", "task": "Run smoke test"}],
            "decision_objects": [],
        }
    )

    assert result["checks"]["summary_specific"] is False
    assert "Summary appears too generic." in result["warnings"]
    assert result["blocking_warnings"] == []
    assert result["passed"] is True


def test_quality_engine_v2_critic_warns_on_open_question_inside_key_points() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "The team reviewed support operations.",
            "summary_slots": {"purpose": "Review support."},
            "key_points": ["Sophia says, open question, should support show processing time?"],
            "action_item_objects": [{"owner": "Sofia", "task": "Update support page"}],
            "decision_objects": [],
        }
    )

    assert result["checks"]["open_questions_not_in_key_points"] is False
    assert "Open questions appear mixed into key points." in result["warnings"]


def test_quality_engine_v2_critic_warns_on_transcript_like_notes() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "The team reviewed support operations.",
            "summary_slots": {"purpose": "Review support."},
            "key_points": ["Maya says, the goal today is to review support operations."],
            "action_item_objects": [{"owner": "Sofia", "task": "Update support page"}],
            "decision_objects": [],
        }
    )

    assert result["checks"]["notes_not_transcript_like"] is False
    assert "Notes appear transcript-like." in result["warnings"]


def test_quality_engine_v2_critic_warns_on_suspicious_domain_or_email() -> None:
    from app.services.quality_engine_v2 import critic_quality_engine_v2_notes

    result = critic_quality_engine_v2_notes(
        {
            "summary": "Use support at acjen dot ai and the raw vercell URL.",
            "summary_slots": {"purpose": "Review support."},
            "action_item_objects": [{"owner": "Sofia", "task": "Update support page"}],
            "decision_objects": [],
        }
    )

    assert result["checks"]["emails_and_domains_not_suspicious"] is False
    assert "Possible suspicious email or domain text detected." in result["warnings"]


def test_quality_engine_v2_critic_failure_does_not_fail_job(monkeypatch) -> None:
    import app.services.quality_engine_v2 as quality_engine_v2

    def raise_critic(*args, **kwargs):
        raise RuntimeError("critic failed")

    monkeypatch.setattr(
        quality_engine_v2,
        "critic_quality_engine_v2_notes",
        raise_critic,
    )

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = quality_engine_v2.run_quality_engine_v2(
        notes,
        "Decision: we will launch Starter first.",
        mode="shadow",
    )

    assert result["notes"] == notes
    assert result["metadata"]["critic"]["passed"] is False
    assert result["metadata"]["critic"]["warnings"] == [
        "Quality Engine v2 critic failed: RuntimeError"
    ]


def test_quality_engine_v2_critic_keeps_v1_default_unchanged() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v2(
        notes,
        "Decision: we will launch Starter first.",
        mode=None,
    )

    assert result == {
        "notes": notes,
        "metadata": {
            "applied": False,
            "mode": "v1",
            "fallback_used": False,
            "warnings": [],
        },
    }


def test_quality_engine_v2_shadow_mode_includes_critic_without_changing_user_notes() -> None:
    from app.services.quality_engine_v2 import run_quality_engine_v2

    notes = {
        "summary": "The team reviewed launch.",
        "summary_slots": {"purpose": "", "next_steps": []},
        "action_item_objects": [],
        "decision_objects": [],
    }
    original = {
        "summary": "The team reviewed launch.",
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
    assert "critic" in result["metadata"]
    assert "v2_notes" not in result


def test_quality_engine_v2_meeting_44_style_duplicate_risks_are_collapsed() -> None:
    notes = {
        "summary": "The team reviewed demo readiness.",
        "summary_slots": {
            "purpose": "Review demo readiness.",
            "next_steps": [],
            "risks": [
                "Longer files may run into the current timeout.",
                "Longer files may run into the current time out.",
                "If a meeting is processed before the raw media path is attached, the work can throw an error because the meeting has no raw media path.",
                "If a meeting is processed before the raw media path is attached, the worker can throw an error because the meeting has no raw media path.",
            ],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["summary_slots"]["risks"] == [
        "Longer files may run into the current timeout.",
        "If a meeting is processed before the raw media path is attached, the worker can throw an error because the meeting has no raw media path.",
    ]


def test_quality_engine_v2_meeting_44_style_timing_log_actions_are_collapsed() -> None:
    notes = {
        "summary": "The team reviewed worker observability.",
        "summary_slots": {"purpose": "Review worker observability.", "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Add stage timing logs to the worker output",
                "status": "open",
            },
            {
                "owner": "Team",
                "task": "Add staged timing logs so that each major processing step has an elapsed duration in the worker logs",
                "status": "open",
            },
        ],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")
    timing_actions = [
        item for item in improved["action_item_objects"] if "timing logs" in item["task"].lower()
    ]

    assert len(timing_actions) == 1


def test_quality_engine_v2_meeting_44_style_backup_demo_actions_are_reduced() -> None:
    notes = {
        "summary": "The team reviewed demo readiness.",
        "summary_slots": {"purpose": "Review demo readiness.", "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Keep one backup meeting already processed before any live demo",
                "status": "open",
            },
            {
                "owner": "Team",
                "task": "Keep meeting seventeen as the primary backup demo example",
                "status": "open",
            },
            {
                "owner": "Lalita",
                "task": "Package the final demo commands into one short runbook",
                "status": "open",
            },
        ],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")
    backup_actions = [
        item
        for item in improved["action_item_objects"]
        if "backup" in item["task"].lower() and "demo" in item["task"].lower()
    ]

    assert len(backup_actions) == 1
    assert any(
        item["task"] == "Package the final demo commands into one short runbook"
        for item in improved["action_item_objects"]
    )


def test_quality_engine_v2_normalizes_lolita_owner_only_when_lalita_context_exists() -> None:
    notes = {
        "summary": "Lalita reviewed demo readiness.",
        "summary_slots": {"purpose": "Review demo readiness.", "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Lolita",
                "task": "Package the final demo commands into one short runbook",
                "status": "open",
            }
        ],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "Lalita will send a short recap.")

    assert improved["action_item_objects"][0]["owner"] == "Lalita"


def test_quality_engine_v2_does_not_normalize_lolita_without_lalita_context() -> None:
    notes = {
        "summary": "The team reviewed demo readiness.",
        "summary_slots": {"purpose": "Review demo readiness.", "next_steps": []},
        "action_item_objects": [
            {
                "owner": "Lolita",
                "task": "Package the final demo commands into one short runbook",
                "status": "open",
            }
        ],
        "decision_objects": [],
    }

    improved = apply_quality_engine_v2(notes, "")

    assert improved["action_item_objects"][0]["owner"] == "Lolita"
