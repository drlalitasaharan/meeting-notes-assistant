from app.services.quality_engine_v3 import (
    apply_quality_engine_v3,
    render_quality_engine_v3_markdown,
    run_quality_engine_v3,
)

A10MINS_TRANSCRIPT = """
I'd like us to leave this meeting with a clear decision on the target audience.
The main purpose of today's meeting is to finalize the demo flow.
The first pilot audience will be consultants, agencies, founders, and small teams.
Lalita will create the clean 10-minute audio test and run it through the product today.
Lalita will prepare the short live demo file and keep one backup processed meeting ready.
If we say it's designed for consultants, we should be careful about the promise.
The live demo will use a short prepared recording.
Do we want to support 3-hour recordings now or later?
"""


def _base_notes() -> dict:
    return {
        "summary": "The team discussed target audience, demo flow, and pilot readiness.",
        "summary_slots": {
            "purpose": "",
            "outcome": "",
            "risks": [],
            "open_questions": [],
            "next_steps": [],
        },
        "action_item_objects": [],
        "decision_objects": [],
    }


def test_qev3_rejects_a10mins_fake_actions_and_keeps_real_actions() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)

    actions = improved["action_item_objects"]
    action_text = " ".join(action["task"] for action in actions).lower()

    assert "create the clean 10-minute audio test" in action_text
    assert "prepare the short live demo file" in action_text

    assert "leave this meeting" not in action_text
    assert "main purpose" not in action_text
    assert "if we say" not in action_text
    assert "live demo will use" not in action_text
    assert "first pilot audience" not in action_text


def test_qev3_places_a10mins_decisions_outside_actions() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)

    decisions = improved["decision_objects"]
    decision_text = " ".join(decision["text"] for decision in decisions).lower()
    action_text = " ".join(action["task"] for action in improved["action_item_objects"]).lower()

    assert "first pilot audience" in decision_text
    assert "live demo will use" in decision_text

    assert "first pilot audience" not in action_text
    assert "live demo will use" not in action_text


def test_qev3_extracts_risks_and_open_questions() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)
    slots = improved["summary_slots"]

    risks = " ".join(slots["risks"]).lower()
    open_questions = " ".join(slots["open_questions"]).lower()

    assert "careful about the promise" in risks
    assert "3-hour recordings" in open_questions


def test_qev3_owner_and_deadline_cleanup() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)

    actions = improved["action_item_objects"]

    create_action = next(
        action
        for action in actions
        if "create the clean 10-minute audio test" in action["task"].lower()
    )
    demo_action = next(
        action for action in actions if "prepare the short live demo file" in action["task"].lower()
    )

    assert create_action["owner"] == "Lalita"
    assert create_action["deadline"] == "today"
    assert demo_action["owner"] == "Lalita"


def test_qev3_removes_invalid_existing_actions() -> None:
    notes = _base_notes()
    notes["action_item_objects"] = [
        {
            "owner": "Team",
            "task": "I'd like us to leave this meeting with a clear decision on the target audience.",
        },
        {
            "owner": "Lalita",
            "task": "Create the clean 10-minute audio test today.",
        },
    ]

    improved = apply_quality_engine_v3(notes, A10MINS_TRANSCRIPT)

    action_text = " ".join(action["task"] for action in improved["action_item_objects"]).lower()

    assert "leave this meeting" not in action_text
    assert "create the clean 10-minute audio test" in action_text


def test_qev3_run_mode_is_safe_when_not_v3() -> None:
    notes = _base_notes()

    result = run_quality_engine_v3(notes, A10MINS_TRANSCRIPT, mode="v1")

    assert result["notes"] == notes
    assert result["metadata"]["applied"] is False
    assert result["metadata"]["engine"] == "qev3"


def test_qev3_run_mode_applies_v3() -> None:
    result = run_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT, mode="v3")

    assert result["metadata"]["applied"] is True
    assert result["metadata"]["mode"] == "v3"
    assert result["notes"]["action_item_objects"]


def test_qev3_markdown_renders_commercial_sections() -> None:
    improved = apply_quality_engine_v3(_base_notes(), A10MINS_TRANSCRIPT)
    markdown = render_quality_engine_v3_markdown(improved)

    assert "# Meeting Notes" in markdown
    assert "## Executive Summary" in markdown
    assert "## Key Decisions" in markdown
    assert "## Action Items" in markdown
    assert "## Risks / Concerns" in markdown
    assert "## Open Questions" in markdown
    assert "| Owner | Action | Deadline |" in markdown


def test_qev3_extracts_m01_numbered_decision_recap() -> None:
    from app.services.quality_engine_v3 import run_quality_engine_v3

    transcript = (
        "Lalitaa: Let's capture decisions explicitly. "
        "Decision one: meeting seventeen will be the current best backup demo example. "
        "Decision two: the ten-minute realistic file remains the main proof of quality. "
        "Decision three: the thirty-minute file will be used as a stress test rather than a live default. "
        "Decision four: we will improve logging visibility for stage durations in a later pass.\n"
        "Kevin: Decision five: we will lead with a practical positioning message instead of a broad platform pitch.\n"
        "John: Decision six: the first pilot audience will be consultants, agencies, and small startup teams."
    )

    result = run_quality_engine_v3({"summary_slots": {}}, transcript, mode="v3")
    decisions = [item["text"].lower() for item in result["notes"].get("decision_objects", [])]

    assert any(
        "meeting seventeen will be the current best backup demo example" in item
        for item in decisions
    )
    assert any(
        "ten-minute realistic file remains the main proof of quality" in item for item in decisions
    )
    assert any("thirty-minute file will be used as a stress test" in item for item in decisions)
    assert any("improve logging visibility for stage durations" in item for item in decisions)
    assert any(
        "practical positioning message instead of a broad platform pitch" in item
        for item in decisions
    )
    assert any(
        "first pilot audience will be consultants, agencies, and small startup teams" in item
        for item in decisions
    )


def test_qev3_extracts_m01_final_action_recap_items() -> None:
    from app.services.quality_engine_v3 import run_quality_engine_v3

    transcript = (
        "Lalitaa: Let's close with concrete actions. "
        "Team will review and finalize the landing page and outreach message by Friday. "
        "Team will add stage timing logs to the worker output. "
        "Lalita will create the clean ten-minute audio test and run it through the product today."
    )

    result = run_quality_engine_v3({"summary_slots": {}}, transcript, mode="v3")
    actions = result["notes"].get("action_item_objects", [])

    action_texts = [item["text"].lower() for item in actions]
    owners = {item["owner"] for item in actions}

    assert "Team" in owners
    assert "Lalita" in owners
    assert any(
        "review and finalize the landing page and outreach message" in item for item in action_texts
    )
    assert any("add stage timing logs to the worker output" in item for item in action_texts)
    assert any("create the clean ten-minute audio test" in item for item in action_texts)
    assert any(item["deadline"] == "today" for item in actions)
    assert any(item["deadline"] == "by Friday" for item in actions)


def test_quality_engine_v3_dedupes_semantic_action_subsets() -> None:
    from app.services.quality_engine_v3 import run_quality_engine_v3

    notes = {
        "summary": "",
        "key_points": [],
        "action_items": [],
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Prepare basic pilot outreach assets for the first pilot audience",
                "text": "Team: Prepare basic pilot outreach assets for the first pilot audience",
                "deadline": "Not specified",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "Prepare basic pilot outreach assets",
                "text": "Team: Prepare basic pilot outreach assets",
                "deadline": "Not specified",
                "status": "open",
                "priority": "medium",
            },
        ],
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "decisions": [],
        "decision_objects": [],
    }

    result = run_quality_engine_v3(notes, "", mode="v3")
    tasks = [
        item["task"]
        for item in result["notes"].get("action_item_objects", [])
        if isinstance(item, dict)
    ]

    assert "Prepare basic pilot outreach assets for the first pilot audience" in tasks
    assert "Prepare basic pilot outreach assets" not in tasks


def test_qev3_persists_plain_text_decisions_and_filters_false_positives() -> None:
    from app.services.quality_engine_v3 import run_quality_engine_v3

    notes = {
        "summary": "",
        "key_points": [],
        "action_items": [],
        "action_item_objects": [],
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "decisions": [],
        "decision_objects": [],
    }

    transcript = """
    Decision 1, the first pilot audience will be consultants, agencies, founders, and small teams.
    Decision 2, the live demo will use a short and clean file, while capability testing will use a separate 10-minute audio sample.
    Decision 3, we will keep one backup meeting already processed before any live demo.
    So for the pilot, I suggest we keep the message very focused.
    My thought is to keep it very practical.
    Lalita will also prepare the short live demo file and keep one backup processed meeting ready.
    The demo command runbook will be updated after the successful test.
    If the live run feels slow, we should also have a backup meeting already processed.
    Keep a written runbook of the demo commands.
    """

    result = run_quality_engine_v3(notes, transcript, mode="v3")
    output = result["notes"]

    decisions = output.get("decisions", [])
    decision_objects = output.get("decision_objects", [])

    assert decisions
    assert all(isinstance(item, str) for item in decisions)
    assert all(isinstance(item, dict) for item in decision_objects)

    joined = " ".join(decisions).lower()

    assert "the first pilot audience will be consultants" in joined
    assert "the live demo will use a short and clean file" in joined
    assert "we will keep one backup meeting already processed" in joined

    assert "i suggest" not in joined
    assert "my thought is" not in joined
    assert "lalita will also prepare" not in joined
    assert "runbook will be updated" not in joined
    assert "if the live run feels slow" not in joined
    assert "keep a written runbook" not in joined
    assert "{" not in " ".join(str(item) for item in decisions)


def test_qev3_medium_meeting_cleans_action_like_decisions_and_dedupes_actions() -> None:
    from app.services.quality_engine_v3 import run_quality_engine_v3

    notes = {
        "summary": "",
        "key_points": [],
        "action_items": [],
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "Add stage timing logs to the worker output",
                "text": "Team: Add stage timing logs to the worker output",
                "deadline": "Not specified",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Team",
                "task": "add stage timing logs so that each major processing step has an elapsed duration in the worker logs",
                "text": "Team: add stage timing logs so that each major processing step has an elapsed duration in the worker logs",
                "deadline": "Not specified",
                "status": "open",
                "priority": "medium",
            },
        ],
        "summary_slots": {"purpose": "", "outcome": "", "risks": [], "next_steps": []},
        "decisions": [],
        "decision_objects": [],
    }

    transcript = """
    Decision one, meeting 17 will be the current best backup demo example.
    Decision two, the 10-minute realistic file remains the main proof of quality.
    Decision three, the 30-minute file will be used as a stress test rather than a live default.
    Decision four, we will improve logging visibility for stage durations in a later pass.
    Kevin, decision five, we will lead with a practical positioning message instead of a broad platform pitch.
    John, decision six, the first pilot audience will be consultants, agencies, and small startup teams.
    Keep one processed meeting ready.
    Keep one short live file ready.
    Keep the commands in a single note.
    Kevin, Lalita will prepare the short-lived demo file and keep one backup processed meeting ready.
    John, team will keep a short command checklist for create, upload, logs, notes JSON, and notes markdown.
    """

    result = run_quality_engine_v3(notes, transcript, mode="v3")
    output = result["notes"]

    decisions = output.get("decisions", [])
    joined_decisions = " ".join(decisions).lower()

    assert all(isinstance(item, str) for item in decisions)
    assert "meeting 17 will be the current best backup demo example" in joined_decisions
    assert "the 10-minute realistic file remains the main proof of quality" in joined_decisions
    assert "the 30-minute file will be used as a stress test" in joined_decisions
    assert "we will improve logging visibility" in joined_decisions
    assert "we will lead with a practical positioning message" in joined_decisions
    assert "the first pilot audience will be consultants" in joined_decisions

    assert "keep one processed meeting ready" not in joined_decisions
    assert "keep one short live file ready" not in joined_decisions
    assert "keep the commands in a single note" not in joined_decisions
    assert "lalita will prepare" not in joined_decisions
    assert "team will keep a short command checklist" not in joined_decisions

    action_tasks = [
        item.get("task", "")
        for item in output.get("action_item_objects", [])
        if isinstance(item, dict)
    ]
    stage_timing_actions = [task for task in action_tasks if "stage timing logs" in task.lower()]

    assert len(stage_timing_actions) == 1


def test_qev3_final_presentation_cleanup_removes_goal_decision_and_normalizes_actions() -> None:
    from app.services.quality_engine_v3 import finalize_quality_engine_v3_persisted_notes

    notes = {
        "summary": "The meeting discussed demo readiness.",
        "summary_slots": {
            "purpose": "Review demo readiness.",
            "outcome": "The team aligned on a practical demo plan.",
            "risks": [],
            "next_steps": [
                "review and finalize the landing page and outreach message by Friday.",
                "add stage timing logs so that each major processing step has an elapsed duration in the worker logs.",
                "Prepare the short-lived demo file and keep one backup processed meeting ready.",
            ],
        },
        "decision_objects": [
            {
                "text": "By the end of the meeting, we should leave with a final demo plan, a small list of action items, and a decision on which use case we will lead within conversations.",
                "evidence": "By the end of the meeting, we should leave with a final demo plan.",
                "confidence": 0.82,
            },
            {
                "text": "the 30-minute file will be used as a stress test rather than a live default",
                "evidence": "Decision three: the 30-minute file will be used as a stress test rather than a live default.",
                "confidence": 0.82,
            },
        ],
        "decisions": [],
        "action_item_objects": [
            {
                "owner": "Team",
                "task": "review and finalize the landing page and outreach message by Friday.",
                "text": "Team: review and finalize the landing page and outreach message by Friday.",
                "deadline": "by Friday",
                "status": "open",
                "priority": "medium",
            },
            {
                "owner": "Lalita",
                "task": "Prepare the short-lived demo file and keep one backup processed meeting ready",
                "text": "Lalita: Prepare the short-lived demo file and keep one backup processed meeting ready",
                "deadline": "Not specified",
                "status": "open",
                "priority": "medium",
            },
        ],
        "action_items": [
            "review and finalize the landing page and outreach message by Friday.",
            "Prepare the short-lived demo file and keep one backup processed meeting ready",
        ],
    }

    output = finalize_quality_engine_v3_persisted_notes(notes)

    decisions = output.get("decisions", [])
    joined_decisions = " ".join(decisions).lower()
    assert "by the end of the meeting" not in joined_decisions
    assert "final demo plan" not in joined_decisions
    assert "the 30-minute file will be used as a stress test" in joined_decisions

    action_objects = output.get("action_item_objects", [])
    assert action_objects[0]["task"].startswith("Review and finalize")
    assert action_objects[0]["text"].startswith("Team: Review and finalize")
    assert "short live-demo file" in action_objects[1]["task"]
    assert "short-lived" not in action_objects[1]["task"]

    next_steps = output.get("summary_slots", {}).get("next_steps", [])
    assert next_steps[0].startswith("Review and finalize")
    assert next_steps[1].startswith("Add stage timing logs")
    assert "short live-demo file" in next_steps[2]

    action_items = output.get("action_items", [])
    first_action = (
        action_items[0].get("task") or action_items[0].get("text")
        if isinstance(action_items[0], dict)
        else action_items[0]
    )
    second_action = (
        action_items[1].get("task") or action_items[1].get("text")
        if isinstance(action_items[1], dict)
        else action_items[1]
    )

    assert first_action.startswith("Review and finalize")
    assert "short live-demo file" in second_action
