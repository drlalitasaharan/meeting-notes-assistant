from app.services.note_strategies.local_summary import LocalSummaryStrategy


def _payload_for(transcript: str) -> dict:
    result = LocalSummaryStrategy().generate(transcript, "")
    return result.to_api_dict()


def _decision_texts(payload: dict) -> list[str]:
    decision_objects = payload.get("decision_objects") or []
    if decision_objects:
        return [str(item.get("text") or "") for item in decision_objects]

    return [str(item or "") for item in payload.get("decisions") or []]


def _action_tasks(payload: dict) -> list[str]:
    action_objects = payload.get("action_item_objects") or []
    if action_objects:
        return [str(item.get("task") or "") for item in action_objects]

    return [str(item or "") for item in payload.get("action_items") or []]


def _slot_texts(payload: dict) -> list[str]:
    slots = payload.get("summary_slots") or {}

    texts: list[str] = []
    for key in ("purpose", "outcome"):
        value = str(slots.get(key) or "").strip()
        if value:
            texts.append(value)

    for key in ("risks", "next_steps"):
        values = slots.get(key) or []
        if isinstance(values, list):
            texts.extend(str(item or "").strip() for item in values if str(item or "").strip())

    return texts


def test_structured_meeting_decisions_are_short_and_publishable():
    transcript = """
    Speaker one, good morning everyone. The main purpose of today's meeting is to review
    where we are with the Meeting Notes Assistant demo, confirm the pilot outreach plan,
    discuss a few open issues, and align on next steps for this week.

    I'd like us to leave this meeting with a clear decision on the target audience, a
    finalized plan for the demo flow, and concrete owners for the follow-up actions.

    Speaker two, from a positioning standpoint, I still think the best first audience is
    consultants, small agencies, founders, and startup teams.

    Speaker one, all right, let's lock the decisions. Decision one, the first pilot
    audience will be consultants, agencies, founders, and small teams. Decision two, the
    live demo will use a short and clean file, while capability testing will use a
    separate 10 minute audio sample. Decision three, we will keep one backup meeting
    already processed before any live demo. Decision four, this week's priority is to
    validate the 10 minute audio flow and prepare basic pilot outreach assets.

    Speaker two, that sounds final to me. Let's assign owners. Lalita will create the
    clean 10 minute audio test and run it through the product today. Lalita will also
    prepare the short live demo file and keep one backup processed meeting ready. The demo
    command runbook will be updated after the successful test. The landing page and
    outreach message will be reviewed and finalized by Friday.
    """

    payload = _payload_for(transcript)
    decisions = _decision_texts(payload)

    assert len(decisions) >= 3

    joined = " ".join(decisions).lower()

    assert "first pilot audience" in joined
    assert "live demo will use a short and clean file" in joined
    assert "backup meeting already processed before any live demo" in joined
    assert "validate the 10 minute audio flow" in joined

    for decision in decisions:
        lowered = decision.lower()
        assert len(decision) <= 260
        assert "speaker one" not in lowered
        assert "speaker two" not in lowered
        assert "decision one" not in lowered
        assert "decision two" not in lowered


def test_structured_meeting_slots_do_not_contain_transcript_chunks():
    transcript = """
    Speaker one, let's talk about the user facing message for pilot outreach. My thought
    is to keep it very practical. Decision one, the first pilot audience will be
    consultants, agencies, founders, and small teams. Decision two, the live demo will use
    a short and clean file, while capability testing will use a separate 10 minute audio
    sample. Decision three, we will keep one backup meeting already processed before any
    live demo. Decision four, this week's priority is to validate the 10 minute audio flow
    and prepare basic pilot outreach assets. Speaker two, that sounds final to me.
    """

    payload = _payload_for(transcript)
    slot_texts = _slot_texts(payload)

    for text in slot_texts:
        lowered = text.lower()
        assert len(text) <= 300
        assert "speaker one" not in lowered
        assert "speaker two" not in lowered
        assert "decision one" not in lowered
        assert "decision two" not in lowered


def test_structured_meeting_actions_do_not_include_agenda_fragments():
    transcript = """
    Speaker one, I'd like us to leave this meeting with a clear decision on the target
    audience, a finalized plan for the demo flow, and concrete owners for the follow-up
    actions.

    Speaker two, let's assign owners. Lalita will create the clean 10 minute audio test
    and run it through the product today. Lalita will also prepare the short live demo file
    and keep one backup processed meeting ready. The demo command runbook will be updated
    after the successful test.
    """

    payload = _payload_for(transcript)
    actions = _action_tasks(payload)

    joined = " ".join(actions).lower()

    assert "concrete owners for the follow-up actions" not in joined


def test_non_meeting_content_does_not_create_business_decisions_or_actions():
    transcript = """
    The old story continued for several minutes. The character walked through the street,
    looked at the window, and wondered what might happen next. There was no meeting,
    no project update, no assigned owner, no business decision, and no follow-up task.
    """

    payload = _payload_for(transcript)

    decisions = _decision_texts(payload)
    actions = _action_tasks(payload)

    assert decisions == []
    assert actions == []
