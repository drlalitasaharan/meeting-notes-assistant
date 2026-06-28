from __future__ import annotations

from typing import Any

from app.jobs import process_meeting
from app.services.quality_engine_v2 import normalize_notes_engine_mode


def test_notes_engine_mode_accepts_v3() -> None:
    assert normalize_notes_engine_mode("v3") == "v3"


def test_selected_quality_engine_routes_v3(monkeypatch: Any) -> None:
    calls: dict[str, Any] = {}

    def fake_v3(
        notes: dict[str, Any],
        transcript_text: str | None,
        *,
        mode: str,
    ) -> dict[str, Any]:
        calls["v3"] = {
            "notes": notes,
            "transcript_text": transcript_text,
            "mode": mode,
        }
        return {"notes": {"engine": "v3"}, "metadata": {"mode": "v3"}}

    monkeypatch.setattr(process_meeting, "run_quality_engine_v3", fake_v3)

    result = process_meeting._run_selected_quality_engine(
        {"input": True},
        "hello transcript",
        mode="v3",
    )

    assert result["notes"] == {"engine": "v3"}
    assert result["metadata"]["mode"] == "v3"
    assert calls["v3"]["notes"] == {"input": True}
    assert calls["v3"]["transcript_text"] == "hello transcript"
    assert calls["v3"]["mode"] == "v3"


def test_selected_quality_engine_preserves_v2_route(monkeypatch: Any) -> None:
    calls: dict[str, Any] = {}

    def fake_v2(
        notes: dict[str, Any],
        transcript_text: str | None,
        *,
        mode: str,
    ) -> dict[str, Any]:
        calls["v2"] = {
            "notes": notes,
            "transcript_text": transcript_text,
            "mode": mode,
        }
        return {"notes": {"engine": "v2"}, "metadata": {"mode": "v2"}}

    monkeypatch.setattr(process_meeting, "run_quality_engine_v2", fake_v2)

    result = process_meeting._run_selected_quality_engine(
        {"input": True},
        "hello transcript",
        mode="v2",
    )

    assert result["notes"] == {"engine": "v2"}
    assert result["metadata"]["mode"] == "v2"
    assert calls["v2"]["notes"] == {"input": True}
    assert calls["v2"]["transcript_text"] == "hello transcript"
    assert calls["v2"]["mode"] == "v2"


def test_selected_quality_engine_preserves_v1_route(monkeypatch: Any) -> None:
    calls: dict[str, Any] = {}

    def fake_v2(
        notes: dict[str, Any],
        transcript_text: str | None,
        *,
        mode: str,
    ) -> dict[str, Any]:
        calls["v1"] = {
            "notes": notes,
            "transcript_text": transcript_text,
            "mode": mode,
        }
        return {"notes": {"engine": "v1"}, "metadata": {"mode": "v1"}}

    monkeypatch.setattr(process_meeting, "run_quality_engine_v2", fake_v2)

    result = process_meeting._run_selected_quality_engine(
        {"input": True},
        "hello transcript",
        mode="v1",
    )

    assert result["notes"] == {"engine": "v1"}
    assert result["metadata"]["mode"] == "v1"
    assert calls["v1"]["mode"] == "v1"
