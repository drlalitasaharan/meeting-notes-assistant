from app.services.note_strategies.local_summary import LocalSummaryStrategy


def _long_filler(label: str, count: int = 450) -> str:
    return (
        f"{label} section reviewed upload reliability, transcript completeness, "
        "worker timeout behavior, support expectations, and long recording quality. "
    ) * count


def test_long_meeting_purpose_and_outcome_are_specific_for_3_hour_support():
    transcript = " ".join(
        [
            "The goal is to review 3-hour recording support, processing reliability, upload expectations, and long-recording QA readiness.",
            "We decided that 3-hour support should remain limited to Pro Pilot while quality is reviewed.",
            _long_filler("Opening"),
            "Nina will update front-end upload messaging for Pro Pilot users by Monday.",
            _long_filler("Middle"),
            "There is a risk that exposing 3-hour support publicly too early creates failure, cost, and expectation risk.",
            "There is a risk that exposing 3-hour support publicly creates failure, cost, and expectation risk.",
            _long_filler("Late"),
            "Omar will document the 3-hour job lifecycle by Wednesday.",
        ]
    )

    result = LocalSummaryStrategy().generate(transcript)
    slots = result.summary_slots or {}

    purpose = str(slots.get("purpose") or "").lower()
    outcome = str(slots.get("outcome") or "").lower()

    assert "3-hour" in purpose or "3 hour" in purpose
    assert "processing reliability" in purpose
    assert "upload expectations" in purpose

    assert "pro pilot" in outcome
    assert "quality" in outcome


def test_long_meeting_risks_are_deduped_and_cleaned():
    transcript = " ".join(
        [
            "The goal is to review 3-hour recording support and long-recording quality.",
            _long_filler("Opening"),
            "There is a risk that exposing 3-hour support publicly too early creates failure, cost, and expectation risk.",
            "There is a risk that exposing 3-hour support publicly creates failure, cost, and expectation risk.",
            "A partial transcript may look complete, but mislaid decisions and actions.",
            _long_filler("Middle"),
            "Marco will confirm transcript completion logging by Thursday.",
        ]
    )

    result = LocalSummaryStrategy().generate(transcript)
    risks = [str(item).lower() for item in (result.summary_slots or {}).get("risks") or []]
    joined = " ".join(risks)

    assert joined.count("exposing 3-hour support publicly") <= 1
    assert "mislaid decisions" not in joined
    assert "miss decisions and actions" in joined


def test_long_meeting_decision_recall_for_pilot_only_support():
    transcript = " ".join(
        [
            "The goal is to review 3-hour recording support and launch expectations.",
            "We decided that 3-hour support should remain limited to Pro Pilot while quality is reviewed.",
            _long_filler("Opening"),
            "There is a risk that public 3-hour support could confuse users if expectations are unclear.",
            _long_filler("Late"),
        ]
    )

    result = LocalSummaryStrategy().generate(transcript)
    decisions = " ".join(result.decisions or []).lower()

    assert "3-hour support" in decisions or "3 hour support" in decisions
    assert "pro pilot" in decisions


def test_long_meeting_risk_only_language_does_not_create_fake_decision():
    transcript = " ".join(
        [
            "The goal is to review 3-hour recording support and launch expectations.",
            _long_filler("Opening"),
            "There is a risk that public 3-hour support could confuse users if expectations are unclear.",
            _long_filler("Late"),
        ]
    )

    result = LocalSummaryStrategy().generate(transcript)
    decisions = " ".join(result.decisions or []).lower()

    assert "public 3-hour support could confuse users" not in decisions
