from __future__ import annotations

from backend.app.services.transcript_medium_case_synthesis import (
    synthesize_medium_case_decisions_and_risks,
)


def test_pilot_support_medium_signals() -> None:
    transcript = (
        "The team discussed a pilot for twenty users. "
        "They agreed email support should be the main support channel. "
        "Pilot feedback will guide the next improvement cycle."
    )

    result = synthesize_medium_case_decisions_and_risks(transcript)
    text = " ".join(result["decisions"] + result["risks"]).lower()

    assert "pilot" in text
    assert "support" in text
    assert "feedback" in text


def test_pricing_demo_medium_signals() -> None:
    transcript = (
        "The client demo needs a clean demo account, an approved sample file, "
        "pricing confirmation, and a backup processed meeting."
    )

    result = synthesize_medium_case_decisions_and_risks(transcript)
    text = " ".join(result["decisions"] + result["risks"]).lower()

    assert "pricing confirmation" in text
    assert "clean demo account" in text
    assert "backup processed meeting" in text
    assert "client" in text


def test_scope_reporting_medium_signals() -> None:
    transcript = (
        "The team aligned the proposal scope and decided custom reporting "
        "should stay phase 2 because over-promising could create expectations."
    )

    result = synthesize_medium_case_decisions_and_risks(transcript)
    text = " ".join(result["decisions"] + result["risks"]).lower()

    assert "proposal scope" in text
    assert "custom reporting" in text
    assert "phase 2" in text
    assert "expectations" in text
