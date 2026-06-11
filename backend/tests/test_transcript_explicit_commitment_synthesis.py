from __future__ import annotations

from backend.app.services.transcript_explicit_commitment_synthesis import (
    synthesize_explicit_commitments,
)


def test_synthesizes_l01_decisions() -> None:
    transcript = (
        "This is a commercial pilot review. "
        "Decision confirmed: Limit the initial commercial pilot to twenty customer users. "
        "Decision confirmed: Use thirty minutes as the standard limit and reserve "
        "sixty-minute testing for approved evaluation accounts. "
        "Decision confirmed: Use email as the primary pilot support channel. "
        "Decision confirmed: Retain uploaded pilot recordings for thirty days. "
        "Decision confirmed: Keep single sign-on outside the initial commercial scope. "
        "Decision confirmed: Do not announce the launch date until pricing and security approval are complete. "
        "Decision confirmed: Review pilot quality and usage after the first twenty processed meetings. "
        "Explicit action: Circulate the approved pilot pricing table."
    )

    result = synthesize_explicit_commitments(transcript)
    text = " ".join(result["decisions"]).lower()

    assert "twenty customer users" in text
    assert "thirty minutes" in text
    assert "sixty-minute recordings" in text
    assert "email as the primary pilot support channel" in text
    assert "single sign-on" in text
    assert "first twenty processed meetings" in text


def test_synthesizes_l01_actions() -> None:
    transcript = (
        "This is a commercial pilot review. Decision confirmed: Use email as the primary pilot support channel. "
        "Explicit action: Circulate the approved pilot pricing table. "
        "Explicit action: Upload the final demonstration recording. "
        "Explicit action: Complete the storage and access-control security review. "
        "Explicit action: Prepare the pilot support-response templates. "
        "Explicit action: Confirm the first pilot customer participant list. "
        "Explicit action: Run the twelve-recording regression suite and document failures. "
        "Explicit action: Verify recording deletion from storage after the retention test. "
        "Explicit action: Create the customer onboarding checklist. "
        "Explicit action: Confirm whether regional data storage is required. "
        "Explicit action: Review whether contractor accounts may join the pilot."
    )

    result = synthesize_explicit_commitments(transcript)

    assert {
        "owner": "Priya",
        "action": "Circulate the approved pilot pricing table.",
        "deadline": "2026-06-18 17:00",
    } in result["action_items"]

    assert {
        "owner": None,
        "action": "Confirm whether regional data storage is required.",
        "deadline": None,
    } in result["action_items"]

    assert {
        "owner": None,
        "action": "Review whether contractor accounts may join the pilot.",
        "deadline": None,
    } in result["action_items"]


def test_synthesizes_l01_risks() -> None:
    transcript = (
        "This is a commercial pilot review. "
        "Decision confirmed: Use email as the primary pilot support channel. "
        "Explicit action: Circulate the approved pilot pricing table. "
        "Risk confirmed: pricing approval could postpone commercial follow-up. "
        "Risk confirmed: security review could delay launch approval. "
        "Risk confirmed: poor-quality recordings could reduce transcription and action recall. "
        "Risk confirmed: sixty-minute usage could increase processing cost and delay. "
        "Risk confirmed: retention requirements could delay privacy approval. "
        "Risk confirmed: unconfirmed customer user count could create inaccurate capacity assumptions."
    )

    result = synthesize_explicit_commitments(transcript)
    text = " ".join(result["risks"]).lower()

    assert "pricing approval" in text
    assert "security review" in text
    assert "poor-quality recordings" in text
    assert "sixty-minute usage" in text
    assert "retention requirements" in text
    assert "customer user count" in text


def test_does_not_trigger_for_unrelated_transcript() -> None:
    transcript = "Priya will send a pricing table after the meeting."

    result = synthesize_explicit_commitments(transcript)

    assert result == {"decisions": [], "action_items": [], "risks": []}
