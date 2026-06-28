from __future__ import annotations

from app.jobs.process_meeting import (
    _is_successful_selected_qev3_output,
    _should_apply_quality_engine_result,
)


def test_selected_qev3_applies_even_when_metadata_mode_is_missing() -> None:
    metadata: dict[str, object] = {}

    assert _is_successful_selected_qev3_output("v3", metadata)
    assert _should_apply_quality_engine_result("v3", metadata)


def test_selected_qev3_does_not_apply_when_fallback_was_used() -> None:
    metadata: dict[str, object] = {"fallback_used": True}

    assert not _is_successful_selected_qev3_output("v3", metadata)


def test_qev2_still_uses_metadata_mode() -> None:
    assert _should_apply_quality_engine_result("v2", {"mode": "v2"})
    assert not _should_apply_quality_engine_result("v2", {})
