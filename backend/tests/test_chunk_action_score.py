from backend.app.services.chunk_action_score import (
    ActualAction,
    ExpectedAction,
    load_expected_actions,
    score_actions,
)


def test_load_expected_actions_skips_placeholders(tmp_path):
    expected_file = tmp_path / "expected.md"
    expected_file.write_text(
        """
# Expected Actions

| must_capture | owner | action | deadline | source/evidence | notes |
|---|---|---|---|---|---|
| yes | Speaker C | Create files from delimited segments. | No deadline stated | transcript | keep |
| yes | TBD after transcript review | TBD after transcript review | No deadline stated | transcript | skip |
| no | Speaker A | Optional action. | Friday | transcript | skip |
""",
        encoding="utf-8",
    )

    expected = load_expected_actions(expected_file)

    assert len(expected) == 1
    assert expected[0].owner == "Speaker C"
    assert expected[0].action == "Create files from delimited segments."


def test_score_actions_calculates_recall_owner_and_deadline_accuracy():
    expected = [
        ExpectedAction(
            owner="Speaker B",
            action="Provide a vocabulary dictionary with entropy scores.",
            deadline="Friday",
            source_evidence="transcript",
        ),
        ExpectedAction(
            owner="Speaker C",
            action="Create files from delimited segments.",
            deadline="No deadline stated",
            source_evidence="transcript",
        ),
    ]
    actual = [
        ActualAction(
            action="Provide vocabulary or dictionary with entropy score for each word.",
            owner="Speaker B",
            deadline="Friday",
        ),
        ActualAction(
            action="Create files from delimited segments for annotation.",
            owner="Speaker C",
            deadline="",
        ),
    ]

    score = score_actions(expected, actual)

    assert score.expected_count == 2
    assert score.found_count == 2
    assert score.recall == 1.0
    assert score.owner_accuracy == 1.0
    assert score.deadline_accuracy == 1.0


def test_score_actions_reports_partial_recall():
    expected = [
        ExpectedAction(
            owner="Speaker B",
            action="Provide a vocabulary dictionary with entropy scores.",
            deadline="No deadline stated",
            source_evidence="transcript",
        ),
        ExpectedAction(
            owner="Speaker C",
            action="Create files from delimited segments.",
            deadline="No deadline stated",
            source_evidence="transcript",
        ),
    ]
    actual = [
        ActualAction(
            action="Create files from delimited segments for annotation.",
            owner="Speaker C",
        ),
    ]

    score = score_actions(expected, actual)

    assert score.expected_count == 2
    assert score.found_count == 1
    assert score.recall == 0.5
