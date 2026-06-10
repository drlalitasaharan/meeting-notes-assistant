from backend.app.services.transcript_signal_extractor import (
    extract_actions_from_transcript,
    extract_decisions_from_transcript,
    extract_structured_signals_from_transcript,
)


def test_extract_decisions_from_explicit_decision_language() -> None:
    transcript = (
        "The team decided to limit the pilot to twenty users. "
        "We agreed to use email as the primary support channel. "
        "Priya will send the pricing table by 2026-06-18 17:00."
    )

    decisions = extract_decisions_from_transcript(transcript)

    assert any("limit the pilot to twenty users" in decision.lower() for decision in decisions)
    assert any("email as the primary support channel" in decision.lower() for decision in decisions)


def test_extract_actions_with_owner_and_deadline() -> None:
    transcript = (
        "Priya will send the pricing table by 2026-06-18 17:00. "
        "Jordan will upload the final demonstration recording by 2026-06-19 15:00."
    )

    actions = extract_actions_from_transcript(transcript)

    assert actions[0]["owner"] == "Priya"
    assert "pricing table" in actions[0]["action"].lower()
    assert actions[0]["deadline"] == "2026-06-18 17:00"
    assert any(action["owner"] == "Jordan" for action in actions)


def test_extract_structured_signals_handles_missing_transcript() -> None:
    signals = extract_structured_signals_from_transcript(None)

    assert signals["decisions"] == []
    assert signals["action_items"] == []
