from app.services.note_strategies.local_summary import (
    LocalSummaryStrategy,
    _is_long_meeting_records,
    build_sentence_records,
    chunk_records,
)


def _text_action_items(result) -> str:
    parts: list[str] = []
    for item in result.action_items or []:
        owner = getattr(item, "owner", "") or ""
        task = getattr(item, "task", "") or str(item)
        due = getattr(item, "due", "") or ""
        parts.append(f"{owner} {task} {due}")
    return " ".join(parts).lower()


def _long_filler(label: str, count: int = 900) -> str:
    sentence = (
        f"{label} discussion reviewed customer feedback, upload reliability, "
        "support operations, meeting notes quality, and product readiness. "
    )
    return sentence * count


def test_long_meeting_mode_triggers_for_large_transcript():
    transcript = _long_filler("Opening", count=1100)

    records = build_sentence_records(transcript, "")
    chunks = chunk_records(records, max_chars=1800)

    assert _is_long_meeting_records(records, chunks)


def test_long_meeting_preserves_beginning_middle_and_end_quality_signals():
    transcript = " ".join(
        [
            "The goal is to review long meeting quality, support reliability, and customer readiness.",
            "We decided that three hour recordings will use the long meeting quality path.",
            _long_filler("Early section", count=450),
            "Meyer will update the long recording quality checklist by Friday.",
            "There is a risk that users may miss details if the middle of a long meeting is not preserved.",
            _long_filler("Middle section", count=450),
            "Sophia will update support guidance for long recordings by next week.",
            "We decided that quality should be prioritized before processing speed.",
            "There is a risk that unclear usage guidance could confuse users.",
            _long_filler("Late section", count=450),
            "Aaron will finalize the customer-facing long recording review note by Friday.",
        ]
    )

    result = LocalSummaryStrategy().generate(transcript)

    joined_purpose = str((result.summary_slots or {}).get("purpose") or "").lower()
    joined_key_points = " ".join(result.key_points or []).lower()
    joined_decisions = " ".join(result.decisions or []).lower()
    joined_actions = _text_action_items(result)
    joined_risks = " ".join((result.summary_slots or {}).get("risks") or []).lower()

    assert "three hour recordings" in joined_decisions
    assert "quality should be prioritized before processing speed" in joined_decisions

    assert "meyer" in joined_actions
    assert "quality checklist" in joined_actions
    assert "sophia" in joined_actions
    assert "support guidance" in joined_actions
    assert "aaron" in joined_actions
    assert "customer-facing long recording review note" in joined_actions

    assert "middle of a long meeting" in joined_risks
    assert "unclear usage guidance" in joined_risks

    assert (
        "support reliability" in joined_purpose
        or "customer readiness" in joined_purpose
        or "support reliability" in joined_key_points
        or "customer readiness" in joined_key_points
    )
