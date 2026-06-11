from __future__ import annotations

from backend.app.services.transcript_short_context_action_synthesis import (
    synthesize_short_context_and_actions,
)


def test_synthesizes_s03_kickoff_context() -> None:
    transcript = (
        "# S03 AMI TS3003a kickoff. "
        "Official speaker-role mapping: A Industrial Designer, B Project Manager, "
        "C User Interface Designer, D Marketing Expert. "
        "We are working for Real Reaction, an electronics company. "
        "The agenda includes opening acquaintance, tool training, project plan description, closing. "
        "The aim is to design a new remote control. "
        "It has to be original, trendy, and user friendly. "
        "The marketing expert is doing user requirement specification, trend watching, "
        "and product evaluation."
    )

    result = synthesize_short_context_and_actions(transcript)
    context_text = " ".join(result["context"]).lower()

    assert "project kickoff meeting" in context_text
    assert "real reaction" in context_text
    assert "new remote control" in context_text
    assert "original, trendy, and user friendly" in context_text
    assert "industrial designer" in context_text
    assert "tool training" in context_text
    assert "trend watching" in context_text


def test_synthesizes_s03_marketing_expert_minutes_action() -> None:
    transcript = (
        "# S03 AMI TS3003a kickoff. "
        "A Industrial Designer, B Project Manager, C User Interface Designer, D Marketing Expert. "
        "The Marketing Expert should take minutes once in a while when something should be written down."
    )

    result = synthesize_short_context_and_actions(transcript)

    assert result["action_items"] == [
        {
            "owner": "Marketing Expert",
            "action": "Take minutes once in a while when something should be written down.",
            "deadline": None,
        }
    ]


def test_does_not_trigger_for_unrelated_short_transcript() -> None:
    transcript = "Priya will send the pricing table after the client meeting."

    result = synthesize_short_context_and_actions(transcript)

    assert result == {"context": [], "action_items": []}
