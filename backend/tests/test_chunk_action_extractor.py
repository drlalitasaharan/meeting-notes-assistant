from backend.app.services.chunk_action_extractor import (
    chunk_transcript,
    extract_candidate_actions,
)


def test_chunk_transcript_preserves_chunk_order():
    transcript = " ".join(f"word{i}" for i in range(25))

    chunks = chunk_transcript(transcript, max_words=10)

    assert len(chunks) == 3
    assert chunks[0].index == 1
    assert chunks[1].index == 2
    assert chunks[2].index == 3
    assert chunks[0].start_word == 0
    assert chunks[2].end_word == 25


def test_extract_candidate_actions_captures_owner_deadline_and_source_chunk():
    transcript = (
        "Speaker B: I will provide the vocabulary dictionary with entropy scores by Friday. "
        "Speaker C: We discussed annotation quality only."
    )

    actions = extract_candidate_actions(transcript)

    assert len(actions) == 1
    assert actions[0].owner == "Speaker B"
    assert actions[0].action == "provide the vocabulary dictionary with entropy scores by Friday"
    assert actions[0].deadline == "by Friday"
    assert actions[0].source_chunk == 1
    assert actions[0].confidence == "high"


def test_extract_candidate_actions_captures_named_owner():
    transcript = "Priya should review the pricing assumptions next week."

    actions = extract_candidate_actions(transcript)

    assert len(actions) == 1
    assert actions[0].owner == "Priya"
    assert actions[0].action == "review the pricing assumptions next week"
    assert actions[0].deadline == "next week"


def test_extract_candidate_actions_uses_unassigned_when_owner_unclear():
    transcript = "We need to create files from delimited segments for annotation."

    actions = extract_candidate_actions(transcript)

    assert len(actions) == 1
    assert actions[0].owner == "Unassigned"
    assert actions[0].action == "create files from delimited segments for annotation"
    assert actions[0].deadline == "No deadline stated"
    assert actions[0].confidence == "low"


def test_extract_candidate_actions_ignores_discussion_only_statements():
    transcript = "The team discussed entropy, annotation, and segmentation quality."

    actions = extract_candidate_actions(transcript)

    assert actions == []
