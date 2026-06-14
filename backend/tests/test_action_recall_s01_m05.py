from __future__ import annotations

from pathlib import Path

from backend.app.services.note_strategies.local_summary import LocalSummaryStrategy

ROOT = Path(__file__).resolve().parents[2]


def _summary_for_fixture(name: str):
    transcript = (ROOT / "backend" / "tests" / "fixtures" / "meeting_regression" / name).read_text()
    return LocalSummaryStrategy().generate(transcript)


def _actions(summary) -> list[str]:
    values: list[str] = []

    for item in getattr(summary, "action_items", []) or []:
        values.append(str(item))

    for item in getattr(summary, "action_item_objects", []) or []:
        if isinstance(item, dict):
            values.append(str(item.get("task") or item.get("text") or ""))
        else:
            task = getattr(item, "task", None) or getattr(item, "text", None) or str(item)
            values.append(str(task))

    return values


def _joined(actions: list[str]) -> str:
    text = "\n".join(actions).lower()
    return text.replace("-", " ").replace("–", " ").replace("—", " ")


def test_s01_captures_three_true_actions_without_known_false_positives():
    summary = _summary_for_fixture("S01_controlled_short.txt")
    text = _joined(_actions(summary))

    assert "upload the final sample recording" in text
    assert "send the approved pricing table" in text
    assert "finish the remaining storage and access control checks" in text

    assert "confirm score, pricing" not in text
    assert "create owns the pricing table" not in text


def test_m05_captures_two_explicit_actions_without_risk_open_question_invention():
    summary = _summary_for_fixture("M05_risks_open_questions.txt")
    text = _joined(_actions(summary))

    assert "obtain written pricing approval" in text
    assert "circulate the approved pricing table" in text
    assert "send the completed security review summary" in text
    assert "storage access" in text
    assert "administrator permissions" in text
    assert "deletion controls" in text

    assert "whether the client requires single sign" not in text
    assert "whether recordings must remain in a specific geographic region" not in text
    assert "whether external contractors" not in text
    assert "whether sixty-minute recordings" not in text
