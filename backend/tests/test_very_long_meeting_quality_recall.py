from __future__ import annotations

from app.services.note_strategies.local_summary import LocalSummaryStrategy


def _very_long_records() -> list[dict[str, object]]:
    sections = [
        """
        Priya: We are reviewing 5-hour recording support, Pro Pilot limits, upload expectations, transcription reliability, and notes quality.
        Marco: Large files may fail if timeout, memory, or transcription chunking is not stable.
        Sarah: A partial transcript may look complete but miss decisions and action items.
        """,
        """
        Priya: Decision confirmed: 5-hour recordings remain internal stress-test only for now.
        Omar: Decision confirmed: public Pro Pilot messaging should stay conservative and not promise 5-hour support.
        Nina: Decision confirmed: long-recording notes must be reviewed before sharing externally.
        """,
        """
        Priya: I will update the internal 5-hour test checklist by Friday.
        Marco: I will review worker timeout and memory logs by Wednesday.
        Omar: I will document the long-recording processing lifecycle by Thursday.
        Nina: I will update the frontend upload messaging for Pro Pilot users by Monday.
        Sarah: I will write support copy for long recording expectations by Tuesday.
        Ben: I will create a simple issue tracker for upload, transcription, notes generation, and markdown issues by Friday.
        Aaron: I will verify usage counting after long-recording uploads by Wednesday.
        """,
        """
        Priya: Key point, 5-hour processing works but should remain internal validation.
        Marco: Key point, chunked transcription reduced provider failure risk.
        Omar: Key point, action and decision recall still need quality review.
        Sarah: Key point, users need clear expectations for long processing time.
        """,
    ]

    records: list[dict[str, object]] = []
    for repeat in range(80):
        for section in sections:
            records.append(
                {
                    "start": repeat * 60.0,
                    "end": repeat * 60.0 + 30.0,
                    "text": section.strip(),
                }
            )
    return records


def _records_to_transcript_text(records: list[dict[str, object]]) -> str:
    return "\n\n".join(str(record.get("text") or "") for record in records)


def _notes_field(result: object, field_name: str) -> object:
    if isinstance(result, dict):
        return result.get(field_name)

    if hasattr(result, field_name):
        return getattr(result, field_name)

    if hasattr(result, "model_dump"):
        dumped = result.model_dump()
        if isinstance(dumped, dict):
            return dumped.get(field_name)

    return getattr(result, "__dict__", {}).get(field_name)


def _action_item_text(item: object) -> str:
    if isinstance(item, dict):
        return " ".join(
            str(item.get(key) or "")
            for key in ("owner", "task", "text", "description")
        )

    return " ".join(
        str(getattr(item, key, "") or "")
        for key in ("owner", "task", "text", "description")
    )


def test_very_long_meeting_preserves_actions_decisions_and_wording() -> None:
    result = LocalSummaryStrategy().generate(
        _records_to_transcript_text(_very_long_records())
    )

    action_items = _notes_field(result, "action_items") or []
    decisions = _notes_field(result, "decisions") or []

    action_blob = " ".join(_action_item_text(item) for item in action_items).lower()
    decision_blob = " ".join(str(item) for item in decisions).lower()
    notes_blob = str(result).lower()

    assert len(action_items) >= 6
    assert "update the internal 5-hour test checklist" in action_blob
    assert "review worker timeout and memory logs" in action_blob
    assert "document the long-recording processing lifecycle" in action_blob
    assert "write support copy for long recording expectations" in action_blob
    assert "verify usage counting after long-recording uploads" in action_blob

    assert len(decisions) >= 3
    assert "5-hour recordings remain internal stress-test only" in decision_blob
    assert "public pro pilot messaging should stay conservative" in decision_blob
    assert "long-recording notes must be reviewed before sharing" in decision_blob

    assert "propilot" not in notes_blob
    assert "pro pilot" in notes_blob


def test_very_long_meeting_does_not_create_fake_decisions_from_risks() -> None:
    records = [
        {
            "start": 0.0,
            "end": 10.0,
            "text": (
                "Priya: Risk, exposing 5-hour support publicly too early creates expectation risk. "
                "Marco: Risk, large files may fail if worker timeout or memory limits are too low. "
                "Sarah: Risk, partial transcripts can miss action items."
            ),
        }
    ] * 100

    result = LocalSummaryStrategy().generate(_records_to_transcript_text(records))

    decisions = _notes_field(result, "decisions") or []
    assert decisions == [] or decisions == ["(none)"]
