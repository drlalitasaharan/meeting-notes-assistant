from app.services.note_strategies.local_summary import LocalSummaryStrategy


def test_owner_marker_recall_promotes_video_transcript_actions() -> None:
    transcript = """
    Priya. Action item for Priya. I will update the proposal language today, and send the edited version to Alex by 3pm.
    Jordan. Action item for Jordan. I will confirm pricing with finance by 11am tomorrow. If the number changes by more than 10%, I will alert Alex and Priya immediately.
    Morgan. Action item for Morgan. I will draft the client follow-up email by tomorrow afternoon with the pilot timeline, success criteria, and a proposed next meeting made.
    Priya. Action item for Priya. I will clean the demo account, and upload the approved sample meeting file by Monday morning.
    Alex. Action item for Alex. I will run the internal demo dry run on Monday afternoon, and check upload, processing, structured notes, markdown export, and non-meeting safety.
    """

    api = LocalSummaryStrategy().generate(transcript).to_api_dict()

    objects = api["action_item_objects"]
    owners = {item["owner"] for item in objects}
    tasks = " | ".join(item["task"] for item in objects).lower()

    assert "Priya" in owners
    assert "Jordan" in owners
    assert "Morgan" in owners
    assert "Alex" in owners
    assert "update the proposal language" in tasks
    assert "send the edited version to alex" in tasks
    assert "confirm pricing with finance" in tasks
    assert "draft the client follow-up email" in tasks
    assert "clean the demo account" in tasks
    assert "upload the approved sample meeting file" in tasks
    assert "run the internal demo dry run" in tasks
    assert "transcript i will" not in tasks
    assert len(objects) >= 7
