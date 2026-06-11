from __future__ import annotations

from backend.app.services.transcript_m02_design_synthesis import (
    synthesize_m02_design_decisions_and_risks,
)


def test_synthesizes_m02_name_and_look_feel_decisions() -> None:
    transcript = (
        "This is the second meeting about the functional design for the remote control. "
        "The team discusses the project name Mando. "
        "Let's stick to Mando for the name and we will see the look and feel later."
    )

    result = synthesize_m02_design_decisions_and_risks(transcript)
    text = " ".join(result["decisions"]).lower()

    assert "use mando" in text
    assert "working project or product name" in text
    assert "defer detailed look-and-feel" in text


def test_synthesizes_m02_budget_and_speech_risks() -> None:
    transcript = (
        "This is the AMI IS1004b functional design meeting for the Mando remote control. "
        "The incorporation of an L_C_D_ or a speech recognition system could be interesting, "
        "but I do not know if the budget would be large enough. "
        "Speech recognition might be difficult because TV background noise might interfere "
        "and make speech recognition harder."
    )

    result = synthesize_m02_design_decisions_and_risks(transcript)
    text = " ".join(result["risks"]).lower()

    assert "speech-recognition features may exceed" in text
    assert "background noise can interfere" in text


def test_synthesizes_m02_market_and_button_risks() -> None:
    transcript = (
        "This is the second functional design meeting for the Mando remote control. "
        "It may be interesting to think in both prototypes, for right and left handed people, "
        "but unless targeting single people it could cut out a lot of the market. "
        "A remote without numbers may be very difficult to learn compared with traditional ones. "
        "If you have too many buttons it increases the difficulty, and the user has to "
        "understand that the same button is doing too many things."
    )

    result = synthesize_m02_design_decisions_and_risks(transcript)
    text = " ".join(result["risks"]).lower()

    assert "left-handed and right-handed prototypes" in text
    assert "traditional number buttons" in text
    assert "too many buttons" in text
    assert "harder to understand and use" in text


def test_does_not_trigger_for_unrelated_transcript() -> None:
    transcript = "Priya will send the pricing table after the client meeting."

    result = synthesize_m02_design_decisions_and_risks(transcript)

    assert result == {"decisions": [], "risks": []}
