# Chunk Action Regression After Output — L01_controlled_long_business_50min

- Capture type: exact-match scorer after-output capture
- Meeting ID: 1
- Status: DONE
- Source endpoint: /v1/meetings/1/notes/ai
- Source file: `/tmp/meetiq_capture_audio/L01_controlled_long_business_50min.mp3`

## Action Items

- The Working Recommendation Is This, Use The Approved Sample Recording And Retain One Processed Backup Meeting For Demonstration Continuity, Before Confirming Anything, We - Test that recommendation against the pilot objective and current evidence
- Unassigned - Use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected

## Action Item Objects

- owner=The Working Recommendation Is This, Use The Approved Sample Recording And Retain One Processed Backup Meeting For Demonstration Continuity, Before Confirming Anything, We; task=Test that recommendation against the pilot objective and current evidence; due=No deadline stated; source=chunk_action_recovery; chunk=1; confidence=0.68; context=The working recommendation is this, do not infer contractor eligibility, record the issue as unresolved and review it when the customer provides the participant list, before confirming anything, we should test that recommendation against the pilot objective and current evidence.
- owner=Unassigned; task=Use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected; due=No deadline stated; source=chunk_action_recovery; chunk=1; confidence=0.55; context=Likewise, a proposed option is not a decision, we will use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected.

## Summary next steps

- Test that recommendation against the pilot objective and current evidence.

## Raw capture JSON

```json
{
  "action_item_objects": [
    {
      "confidence": 0.68,
      "due_date": null,
      "owner": "The Working Recommendation Is This, Use The Approved Sample Recording And Retain One Processed Backup Meeting For Demonstration Continuity, Before Confirming Anything, We",
      "priority": "medium",
      "reason_context": "The working recommendation is this, do not infer contractor eligibility, record the issue as unresolved and review it when the customer provides the participant list, before confirming anything, we should test that recommendation against the pilot objective and current evidence.",
      "source": "chunk_action_recovery",
      "source_chunk": 1,
      "status": "open",
      "task": "Test that recommendation against the pilot objective and current evidence",
      "text": "The Working Recommendation Is This, Use The Approved Sample Recording And Retain One Processed Backup Meeting For Demonstration Continuity, Before Confirming Anything, We: Test that recommendation against the pilot objective and current evidence"
    },
    {
      "confidence": 0.55,
      "due_date": null,
      "owner": "Unassigned",
      "priority": "medium",
      "reason_context": "Likewise, a proposed option is not a decision, we will use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected.",
      "source": "chunk_action_recovery",
      "source_chunk": 1,
      "status": "open",
      "task": "Use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected",
      "text": "Unassigned: Use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected"
    }
  ],
  "action_items": [
    "The Working Recommendation Is This, Use The Approved Sample Recording And Retain One Processed Backup Meeting For Demonstration Continuity, Before Confirming Anything, We - Test that recommendation against the pilot objective and current evidence",
    "Unassigned - Use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected"
  ],
  "decision_objects": [
    {
      "confidence": 0.86,
      "text": "No new owner, deadline, decision, risk, or customer promise may be introduced during the recap, anything not confirmed in the main discussion remains outside the approved record"
    },
    {
      "confidence": 0.86,
      "text": "A proposed option is not a decision, we will use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected"
    },
    {
      "confidence": 0.86,
      "text": "The purpose is to define a launch safe commercial pilot and preserve a reliable record of what the team actually approved"
    },
    {
      "confidence": 0.86,
      "text": "We will also distinguish product readiness from commercial readiness, a pricing delay is not the same as a processing failure, and an open enterprise requirement is not the same as an approved feature"
    },
    {
      "confidence": 0.86,
      "text": "The decision is approved exactly as stated, related alternatives or future possibilities are not part of the approved decision"
    }
  ],
  "decisions": [
    "No new owner, deadline, decision, risk, or customer promise may be introduced during the recap, anything not confirmed in the main discussion remains outside the approved record",
    "A proposed option is not a decision, we will use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected",
    "The purpose is to define a launch safe commercial pilot and preserve a reliable record of what the team actually approved",
    "We will also distinguish product readiness from commercial readiness, a pricing delay is not the same as a processing failure, and an open enterprise requirement is not the same as an approved feature",
    "The decision is approved exactly as stated, related alternatives or future possibilities are not part of the approved decision"
  ],
  "key_points": [
    "From an operational and technical perspective, the boundary must remain clear, the team could improvise with an unverified recording or use of final approved sample that has already passed a smoke test, each option has different cost, reliability, security, or support consequences",
    "The working recommendation is this, use the approved sample recording and retain one processed backup meeting for demonstration continuity, before confirming anything, we should test that recommendation against the pilot objective and current evidence",
    "The recommendation fits a controlled pilot because it limits unnecessary variation while still giving the customer enough access to evaluate the core workflow and generated meeting notes",
    "An idea or possible future feature is not an action item, an action exists only when the owner is explicit or when the record deliberately states that the action remains unassigned",
    "A proposed option is not a decision, we will use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected",
    "The current evidence is as follows, previous controlled demonstrations showed stable processing when the number of participants and meeting types remained limited, that evidence informs the recommendation but does not create an automatic commitment"
  ],
  "meeting_id": 1,
  "model_version": "local-summary-v3",
  "status": "DONE",
  "summary": "The meeting focused on reviewing current Meeting Notes Assistant progress, aligning demo planning and artifacts, refining pilot outreach and positioning, and reviewing current technical risks. The team aligned on: No new owner, deadline, decision, risk, or customer promise may be introduced during the recap, anything not confirmed in the main discussion remains outside the approved record; A proposed option is not a decision, we will use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected",
  "summary_slots": {
    "next_steps": [
      "Test that recommendation against the pilot objective and current evidence."
    ],
    "outcome": "The team aligned on: No new owner, deadline, decision, risk, or customer promise may be introduced during the recap, anything not confirmed in the main discussion remains outside the approved record; A proposed option is not a decision, we will use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected.",
    "purpose": "The meeting focused on reviewing current Meeting Notes Assistant progress, aligning demo planning and artifacts, refining pilot outreach and positioning, and reviewing current technical risks",
    "risks": [
      "No new owner, deadline, decision, risk, or customer promise may be introduced during the recap, anything not confirmed in the main discussion remains outside the approved record"
    ]
  }
}
```
