# Chunk Action Regression After Output — M05_risks_open_questions

- Capture type: exact-match scorer after-output capture
- Meeting ID: 1
- Status: DONE
- Source endpoint: /v1/meetings/1/notes/ai
- Source file: `/tmp/meetiq_capture_audio/M05_risks_open_questions.mp3`

## Action Items

- Team - Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026
- Team - Send the completed security review summary covering storage access, administrator permissions and deletion controls by noon on June 22nd, 2026

## Action Item Objects

- owner=Team; task=Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026; due=by 5pm; source=transcript_action_recall; chunk=; confidence=0.9; context=
- owner=Team; task=Send the completed security review summary covering storage access, administrator permissions and deletion controls by noon on June 22nd, 2026; due=No deadline stated; source=transcript_action_recall; chunk=; confidence=0.9; context=

## Summary next steps

- Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026.
- Send the completed security review summary covering storage access, administrator permissions and deletion controls by noon on June 22nd, 2026.

## Raw capture JSON

```json
{
  "action_item_objects": [
    {
      "confidence": 0.9,
      "due_date": "by 5pm",
      "owner": "Team",
      "priority": "medium",
      "source": "transcript_action_recall",
      "status": "open",
      "task": "Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026",
      "text": "Team: Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026"
    },
    {
      "confidence": 0.9,
      "due_date": null,
      "owner": "Team",
      "priority": "medium",
      "source": "transcript_action_recall",
      "status": "open",
      "task": "Send the completed security review summary covering storage access, administrator permissions and deletion controls by noon on June 22nd, 2026",
      "text": "Team: Send the completed security review summary covering storage access, administrator permissions and deletion controls by noon on June 22nd, 2026"
    }
  ],
  "action_items": [
    "Team - Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026",
    "Team - Send the completed security review summary covering storage access, administrator permissions and deletion controls by noon on June 22nd, 2026"
  ],
  "decision_objects": [
    {
      "confidence": 0.86,
      "text": "The product demonstration is ready, but the approved pricing table has not yet been issued"
    },
    {
      "confidence": 0.86,
      "text": "I accept the first action, I will obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026"
    },
    {
      "confidence": 0.86,
      "text": "That decision prevents the team from presenting an unapproved commercial date"
    },
    {
      "confidence": 0.86,
      "text": "Decision confirmed, do not promise single sign on or 60 minute meeting support until the client confirms the requirements and the additional scope is approved"
    },
    {
      "confidence": 0.86,
      "text": "confirmed, do not announce a final pilot launch date until pricing approval and the security review are complete"
    }
  ],
  "decisions": [
    "The product demonstration is ready, but the approved pricing table has not yet been issued",
    "I accept the first action, I will obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026",
    "That decision prevents the team from presenting an unapproved commercial date",
    "Decision confirmed, do not promise single sign on or 60 minute meeting support until the client confirms the requirements and the additional scope is approved",
    "confirmed, do not announce a final pilot launch date until pricing approval and the security review are complete"
  ],
  "key_points": [
    "Decision only the pricing action, Alex only the security review action",
    "Decision confirmed, do not announce a final pilot launch date until pricing approval and the security review are complete",
    "No owner or deadline is assigned to this open question during this meeting",
    "Question remains unresolved and should be recorded as open",
    "Decision preserves the current pilot scope while the client requirements remain unresolved",
    "The client has mentioned enterprise access controls but has not made single sign on a confirmed pilot requirement"
  ],
  "meeting_id": 1,
  "model_version": "local-summary-v3",
  "status": "DONE",
  "summary": "Risk number one, delayed pricing approval could postpone the client follow-up and prevent confirmation of the commercial pilot. The meeting aligned on the main priorities and next steps",
  "summary_slots": {
    "next_steps": [
      "Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026.",
      "Send the completed security review summary covering storage access, administrator permissions and deletion controls by noon on June 22nd, 2026."
    ],
    "outcome": "The meeting aligned on the main priorities and next steps",
    "purpose": "Risk number one, delayed pricing approval could postpone the client follow-up and prevent confirmation of the commercial pilot",
    "risks": [
      "Risk number one, delayed pricing approval could postpone the client follow-up and prevent confirmation of the commercial pilot"
    ]
  }
}
```
