from app.services.note_strategies.local_summary import LocalSummaryStrategy


def test_local_summary_promotes_pricing_followup_actions_and_risk():
    transcript = """
    The next client follow-up should be scheduled for next Tuesday after finance confirms pricing.
    The goal today is to confirm the revised proposal, pricing review, and next steps before Friday.
    I will confirm pricing with finance by tomorrow morning and flag any change above 10%.
    We will send the revised proposal with setup, training, and one dashboard review included and custom reporting listed as phase 2.
    We will confirm pricing, and we will send the client follow-up after finance review.
    The success criteria for the pilot are weekly active usage, fewer missed follow-ups, and client approval on the structured notes.
    """

    api = LocalSummaryStrategy().generate(transcript).to_api_dict()

    assert api["model_version"] == "local-summary-v3"
    assert api["action_items"]
    assert api["action_item_objects"]
    assert api["summary_slots"]["risks"]

    owners = [item.get("owner") for item in api["action_item_objects"]]
    assert "The Next Client Follow-Up" not in owners

    joined_actions = " ".join(api["action_items"]).lower()
    assert "client follow-up" in joined_actions or "confirm pricing" in joined_actions


def test_local_summary_promotes_explicit_action_item_markers():
    from app.services.note_strategies.local_summary import LocalSummaryStrategy

    transcript = """
    Today we need to confirm proposal scope, pricing status, demo readiness, client follow-up, risks, and action items.
    Action item for Priya. I will update the proposal language today and send the edited version to Alex by 3pm.
    Action item for Jordan. I will confirm pricing with finance by 11am tomorrow.
    Action item for Morgan. I will draft the client follow-up email tomorrow afternoon with the pilot timeline and success criteria.
    Action item for Priya. I will clean the demo account and upload the approved sample meeting file by Monday morning.
    Action item for Alex. I will run the internal demo dry run before the client call.
    """

    api = LocalSummaryStrategy().generate(transcript).to_api_dict()

    tasks = [str(item.get("task") or "") for item in api.get("action_item_objects", [])]
    owners = [str(item.get("owner") or "") for item in api.get("action_item_objects", [])]

    joined_tasks = " | ".join(tasks).lower()

    assert api["action_items"], api
    assert api["action_item_objects"], api
    assert "Jordan" in owners
    assert "Priya" in owners
    assert "Morgan" in owners
    assert "confirm pricing with finance" in joined_tasks
    assert "update the proposal language" in joined_tasks
    assert "send the edited version to alex" in joined_tasks
    assert "draft the client follow-up email" in joined_tasks


def test_local_summary_strips_transcript_label_from_marker_actions():
    from app.services.note_strategies.local_summary import LocalSummaryStrategy

    transcript = """
    Today we need to confirm proposal scope, pricing status, demo readiness, client follow-up, risks, and action items.
    Action item for Priya. Transcript I will update the proposal language today.
    Action item for Jordan. I will confirm pricing with finance by 11am tomorrow.
    """

    api = LocalSummaryStrategy().generate(transcript).to_api_dict()

    tasks = [str(item.get("task") or "") for item in api.get("action_item_objects", [])]

    assert "Update the proposal language today" in tasks
    assert "Confirm pricing with finance by 11am tomorrow" in tasks
    assert not any(task.lower().startswith("transcript ") for task in tasks)
