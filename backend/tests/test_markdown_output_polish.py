from app.routers.meeting_notes_api import _clean_publishable_markdown_text


def test_clean_publishable_markdown_removes_spaces_before_punctuation() -> None:
    text = "- Validate the pilot demo .\n- Share the backup output ."
    cleaned = _clean_publishable_markdown_text(text)

    assert "demo ." not in cleaned
    assert "output ." not in cleaned
    assert "demo." in cleaned
    assert "output." in cleaned


def test_clean_publishable_markdown_fixes_known_demo_phrase() -> None:
    text = "I'd us to leave this meeting with a clear demo plan."
    cleaned = _clean_publishable_markdown_text(text)

    assert "I'd us to leave" not in cleaned
    assert "I'd like us to leave" in cleaned
