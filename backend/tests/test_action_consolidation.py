from backend.app.services.action_consolidation import consolidate_candidate_actions
from backend.app.services.chunk_action_extractor import CandidateAction


def _candidate(
    action: str,
    *,
    owner: str = "Speaker A",
    deadline: str = "No deadline stated",
    source_chunk: int = 1,
    confidence: str = "medium",
) -> CandidateAction:
    return CandidateAction(
        action=action,
        owner=owner,
        deadline=deadline,
        reason_context=action,
        related_decision="",
        related_risk="",
        source_chunk=source_chunk,
        confidence=confidence,
    )


def test_consolidates_duplicate_actions_and_keeps_specific_action():
    candidates = [
        _candidate("review pricing assumptions", source_chunk=1, confidence="medium"),
        _candidate(
            "review detailed pricing assumptions with finance",
            source_chunk=3,
            confidence="high",
        ),
    ]

    consolidated = consolidate_candidate_actions(candidates)

    assert len(consolidated) == 1
    assert consolidated[0].action == "review detailed pricing assumptions with finance"
    assert consolidated[0].source_chunk == 1
    assert consolidated[0].confidence == "high"


def test_does_not_merge_same_action_with_different_owner():
    candidates = [
        _candidate("review pricing assumptions", owner="Speaker A"),
        _candidate("review pricing assumptions", owner="Speaker B"),
    ]

    consolidated = consolidate_candidate_actions(candidates)

    assert len(consolidated) == 2


def test_does_not_merge_same_action_with_different_deadline():
    candidates = [
        _candidate("review pricing assumptions", deadline="Friday"),
        _candidate("review pricing assumptions", deadline="Monday"),
    ]

    consolidated = consolidate_candidate_actions(candidates)

    assert len(consolidated) == 2


def test_does_not_overmerge_different_deliverables():
    candidates = [
        _candidate("review pricing assumptions"),
        _candidate("review security assumptions"),
    ]

    consolidated = consolidate_candidate_actions(candidates)

    assert len(consolidated) == 2


def test_preserves_beginning_middle_and_end_actions():
    candidates = [
        _candidate("send launch notes", source_chunk=3),
        _candidate("create onboarding checklist", source_chunk=1),
        _candidate("validate billing limits", source_chunk=2),
    ]

    consolidated = consolidate_candidate_actions(candidates)

    assert [item.source_chunk for item in consolidated] == [1, 2, 3]
    assert [item.action for item in consolidated] == [
        "create onboarding checklist",
        "validate billing limits",
        "send launch notes",
    ]
