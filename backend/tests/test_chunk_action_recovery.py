from backend.app.services.chunk_action_recovery import (
    recover_chunk_level_action_dicts,
    recover_chunk_level_actions,
)


def test_recover_chunk_level_actions_extracts_and_consolidates_actions():
    transcript = (
        "Speaker B: I will provide the vocabulary dictionary with entropy scores by Friday. "
        "Later we talked about unrelated segmentation details. "
        "Speaker B: I will provide the vocabulary dictionary with entropy scores by Friday. "
        "Speaker C: I will create files from delimited segments for annotation."
    )

    actions = recover_chunk_level_actions(transcript)

    assert len(actions) == 2
    assert actions[0].owner == "Speaker B"
    assert "vocabulary dictionary" in actions[0].action
    assert actions[0].deadline == "by Friday"
    assert actions[1].owner == "Speaker C"
    assert "create files from delimited segments" in actions[1].action


def test_recover_chunk_level_actions_respects_max_actions():
    transcript = (
        "Speaker A: I will send launch notes. "
        "Speaker B: I will validate billing limits. "
        "Speaker C: I will create onboarding checklist."
    )

    actions = recover_chunk_level_actions(transcript, max_actions=2)

    assert len(actions) == 2


def test_recover_chunk_level_action_dicts_are_serializable():
    transcript = "Speaker C: I will create files from delimited segments for annotation."

    actions = recover_chunk_level_action_dicts(transcript)

    assert len(actions) == 1
    assert actions[0]["owner"] == "Speaker C"
    assert actions[0]["deadline"] == "No deadline stated"
    assert actions[0]["source_chunk"] == 1
    assert actions[0]["confidence"] in {"low", "medium", "high"}
