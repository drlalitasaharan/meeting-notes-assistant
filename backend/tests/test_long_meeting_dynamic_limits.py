from app.services.note_strategies.local_summary import _action_limits_for_transcript
from app.services.notes_quality_pass import _long_meeting_next_step_limit


def _words(count: int) -> str:
    return " ".join(["word"] * count)


def test_action_limits_stay_concise_for_short_meetings() -> None:
    assert _action_limits_for_transcript(_words(1000)) == (8, 3)
    assert _long_meeting_next_step_limit(_words(1000)) == 3


def test_action_limits_expand_for_30_minute_meetings() -> None:
    assert _action_limits_for_transcript(_words(3500)) == (12, 5)
    assert _long_meeting_next_step_limit(_words(3500)) == 5


def test_action_limits_expand_for_60_minute_meetings() -> None:
    assert _action_limits_for_transcript(_words(7500)) == (15, 6)
    assert _long_meeting_next_step_limit(_words(7500)) == 6


def test_action_limits_expand_for_two_hour_meetings() -> None:
    assert _action_limits_for_transcript(_words(15000)) == (20, 8)
    assert _long_meeting_next_step_limit(_words(15000)) == 8
