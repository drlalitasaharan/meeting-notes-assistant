from app.routers.meeting_notes_api import (
    _clean_publishable_markdown_text,
    _render_action_item_md,
)


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


def test_clean_publishable_markdown_fixes_known_30_60min_spacing_defects() -> None:
    text = "- Sophia will add reviewrecommended language tomake long recordings clearer ."
    cleaned = _clean_publishable_markdown_text(text)

    assert "reviewrecommended" not in cleaned
    assert "tomake" not in cleaned
    assert "clearer ." not in cleaned
    assert "review recommended language to make long recordings clearer." in cleaned


def test_render_action_item_md_formats_stringified_dict_action() -> None:
    item = (
        "{'owner': 'Priya', 'task': 'Create two versions of LinkedIn post, "
        "one founder style, and one product style', 'status': 'open', 'priority': 'medium'}"
    )

    rendered = _render_action_item_md(item)

    assert rendered == (
        "- [ ] **Priya** — Create two versions of LinkedIn post, one founder style, "
        "and one product style _(status: open, priority: medium)_"
    )
    assert "{'owner'" not in rendered
