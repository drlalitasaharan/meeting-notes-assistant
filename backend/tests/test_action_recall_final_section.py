from app.services.note_strategies.local_summary import LocalSummaryStrategy


def _action_tasks_for(transcript: str) -> list[str]:
    result = LocalSummaryStrategy().generate(transcript, "")
    payload = result.to_api_dict()
    objects = payload.get("action_item_objects") or []
    if objects:
        return [str(item.get("task") or "") for item in objects]
    return [str(item or "") for item in payload.get("action_items") or []]


def test_final_owner_section_recalls_multiple_valid_actions():
    transcript = """
    Speaker one, let's assign owners. Lalita will create the clean 10 minute audio test
    and run it through the product today. Lalita will also prepare the short live demo file
    and keep one backup processed meeting ready. The demo command runbook will be updated
    after the successful test. The landing page and outreach message will be reviewed and
    finalized by Friday. After that, the next step is to begin sending pilot outreach
    messages and collecting feedback from early users.
    """

    actions = _action_tasks_for(transcript)
    joined = " ".join(actions).lower()

    assert "concrete owners for the follow-up actions" not in joined

    assert any("create the clean 10 minute audio test" in action.lower() for action in actions)
    assert any("prepare the short live demo file" in action.lower() for action in actions)
    assert any("backup" in action.lower() for action in actions)
    assert any("demo command runbook" in action.lower() for action in actions)
    assert any("landing page and outreach message" in action.lower() for action in actions)
    assert any("pilot outreach messages" in action.lower() for action in actions)
