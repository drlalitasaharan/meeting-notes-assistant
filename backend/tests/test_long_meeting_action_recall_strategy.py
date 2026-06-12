from __future__ import annotations

from app.services.persisted_action_contract import _finalize_persisted_action_contract
from app.services.transcript_explicit_commitment_synthesis import (
    synthesize_explicit_commitments,
)


def test_long_meeting_finalizer_keeps_explicit_commitment_verbs() -> None:
    action_items, action_objects, _ = _finalize_persisted_action_contract(
        action_item_objects=[
            {
                "owner": "Priya",
                "task": "Circulate the approved pilot pricing table.",
                "due_date": "2026-06-18 17:00",
            },
            {
                "owner": "Alex",
                "task": "Complete the storage and access-control security review.",
                "due_date": "2026-06-22 12:00",
            },
            {
                "owner": "Alex",
                "task": "Verify recording deletion from storage after the retention test.",
                "due_date": None,
            },
        ],
        raw_transcript_text="",
    )

    joined_items = " ".join(action_items).lower()
    joined_tasks = " ".join(str(item.get("task") or "") for item in action_objects).lower()

    assert "circulate the approved pilot pricing table" in joined_items
    assert "complete the storage and access-control security review" in joined_items
    assert "verify recording deletion from storage after the retention test" in joined_items

    assert "circulate the approved pilot pricing table" in joined_tasks
    assert "complete the storage and access-control security review" in joined_tasks
    assert "verify recording deletion from storage after the retention test" in joined_tasks


def test_long_meeting_recap_actions_are_extracted_from_late_final_recap() -> None:
    transcript = """
    Priya: This commercial pilot review includes decision confirmed language
    and explicit action language so the controlled long-meeting extractor should run.

    Jordan: Decision confirmed: standard pilot recordings remain limited to thirty minutes.
    Morgan: The pilot support plan uses email as the primary pilot support channel.

    Priya: We discussed pricing, security review, support, and regional storage.
    These are context points only unless marked as actions.

    Jordan: Final recap for the long meeting.
    Jordan: Recap action: Circulate the approved pilot pricing table. Owner: Priya. Deadline: 2026-06-18 17:00.
    Jordan: Recap action: Complete the storage and access-control security review. Owner: Alex. Deadline: 2026-06-22 12:00.
    Jordan: Recap action: Verify recording deletion from storage after the retention test. Owner: Alex. Deadline: No deadline.
    """

    result = synthesize_explicit_commitments(transcript)
    actions = result["action_items"]
    joined = " ".join(str(action.get("action") or "") for action in actions).lower()

    assert "circulate the approved pilot pricing table" in joined
    assert "complete the storage and access-control security review" in joined
    assert "verify recording deletion from storage after the retention test" in joined

    owner_by_action = {
        str(action.get("action") or "").lower(): action.get("owner") for action in actions
    }

    assert owner_by_action["circulate the approved pilot pricing table."] == "Priya"
    assert owner_by_action["complete the storage and access-control security review."] == "Alex"
    assert (
        owner_by_action["verify recording deletion from storage after the retention test."]
        == "Alex"
    )
