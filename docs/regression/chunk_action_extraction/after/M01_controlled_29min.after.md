# Chunk Action Regression After Output — M01_controlled_29min

- Capture type: exact-match scorer after-output capture
- Meeting ID: 1
- Status: DONE
- Source endpoint: /v1/meetings/1/notes/ai
- Source file: `/tmp/meetiq_capture_audio/M01_controlled_29min.mp3`

## Action Items

- Team - Review and finalize the landing page and outreach message
- Team - Prepare the short live-demo recording
- Team - Create the clean ten-minute audio test and run it through the product
- Team - Keep one backup meeting processed and ready before any live demo
- Team - Add stage timing logs to the worker output
- Team - Package the final demo commands into one short runbook

## Action Item Objects

- owner=Team; task=Review and finalize the landing page and outreach message; due=No deadline stated; source=; chunk=; confidence=0.7; context=
- owner=Team; task=Prepare the short live-demo recording; due=No deadline stated; source=transcript_action_recall; chunk=; confidence=0.84; context=
- owner=Team; task=Create the clean ten-minute audio test and run it through the product; due=No deadline stated; source=transcript_action_recall; chunk=; confidence=0.84; context=
- owner=Team; task=Keep one backup meeting processed and ready before any live demo; due=No deadline stated; source=transcript_action_recall; chunk=; confidence=0.84; context=
- owner=Team; task=Add stage timing logs to the worker output; due=No deadline stated; source=transcript_action_recall; chunk=; confidence=0.84; context=
- owner=Team; task=Package the final demo commands into one short runbook; due=No deadline stated; source=transcript_action_recall; chunk=; confidence=0.84; context=

## Summary next steps

- Review and finalize the landing page and outreach message.
- Prepare the short live-demo recording.
- Create the clean ten-minute audio test and run it through the product.
- Keep one backup meeting processed and ready before any live demo.
- Add stage timing logs to the worker output.

## Raw capture JSON

```json
{
  "action_item_objects": [
    {
      "confidence": 0.7,
      "due_date": null,
      "owner": "Team",
      "priority": "medium",
      "status": "open",
      "task": "Review and finalize the landing page and outreach message",
      "text": "Team: Review and finalize the landing page and outreach message"
    },
    {
      "confidence": 0.84,
      "due_date": null,
      "owner": "Team",
      "priority": "medium",
      "source": "transcript_action_recall",
      "status": "open",
      "task": "Prepare the short live-demo recording",
      "text": "Team: Prepare the short live-demo recording"
    },
    {
      "confidence": 0.84,
      "due_date": null,
      "owner": "Team",
      "priority": "medium",
      "source": "transcript_action_recall",
      "status": "open",
      "task": "Create the clean ten-minute audio test and run it through the product",
      "text": "Team: Create the clean ten-minute audio test and run it through the product"
    },
    {
      "confidence": 0.84,
      "due_date": null,
      "owner": "Team",
      "priority": "medium",
      "source": "transcript_action_recall",
      "status": "open",
      "task": "Keep one backup meeting processed and ready before any live demo",
      "text": "Team: Keep one backup meeting processed and ready before any live demo"
    },
    {
      "confidence": 0.84,
      "due_date": null,
      "owner": "Team",
      "priority": "medium",
      "source": "transcript_action_recall",
      "status": "open",
      "task": "Add stage timing logs to the worker output",
      "text": "Team: Add stage timing logs to the worker output"
    },
    {
      "confidence": 0.84,
      "due_date": null,
      "owner": "Team",
      "priority": "medium",
      "source": "transcript_action_recall",
      "status": "open",
      "task": "Package the final demo commands into one short runbook",
      "text": "Team: Package the final demo commands into one short runbook"
    }
  ],
  "action_items": [
    "Team - Review and finalize the landing page and outreach message",
    "Team - Prepare the short live-demo recording",
    "Team - Create the clean ten-minute audio test and run it through the product",
    "Team - Keep one backup meeting processed and ready before any live demo",
    "Team - Add stage timing logs to the worker output",
    "Team - Package the final demo commands into one short runbook"
  ],
  "decision_objects": [
    {
      "confidence": 0.86,
      "text": "meeting 17 as the primary backup demo example before the live client presentation"
    },
    {
      "confidence": 0.86,
      "text": "meeting 17 should be our backup demo artifact"
    },
    {
      "confidence": 0.86,
      "text": "the 10-minute realistic file remains the main proof of quality"
    },
    {
      "confidence": 0.86,
      "text": "we will lead with a practical positioning message instead of a broad platform pitch"
    },
    {
      "confidence": 0.86,
      "text": "the first pilot audience will be consultants, agencies, and small start-up teams"
    }
  ],
  "decisions": [
    "meeting 17 as the primary backup demo example before the live client presentation",
    "meeting 17 should be our backup demo artifact",
    "the 10-minute realistic file remains the main proof of quality",
    "we will lead with a practical positioning message instead of a broad platform pitch",
    "the first pilot audience will be consultants, agencies, and small start-up teams"
  ],
  "key_points": [
    "The more realistic 10-minute test also works and now produces a better summary, key points, and action items",
    "Lalita will prepare the short-lived demo file and keep one backup processed meeting ready",
    "Lalita will keep action item clean up in the current version and defer deeper summarization tuning until after the pilot",
    "One minimal smoke test, one realistic test before cleanup, and one realistic test after cleanup",
    "Meeting 17 should be our backup demo artifact",
    "We should confirm the pilot outreach approach, because once the demo flow is stable we should move quickly into a small pilot instead of waiting for a perfect product"
  ],
  "meeting_id": 1,
  "model_version": "local-summary-v3",
  "status": "DONE",
  "summary": "The meeting focused on reviewing current Meeting Notes Assistant progress, aligning demo planning and artifacts, refining pilot outreach and positioning, and reviewing current technical risks. Key outcomes: meeting 17 as the primary backup demo example before the live client presentation; the 10-minute realistic file remains the main proof of quality; we will lead with a practical positioning message instead of a broad platform pitch",
  "summary_slots": {
    "next_steps": [
      "Review and finalize the landing page and outreach message.",
      "Prepare the short live-demo recording.",
      "Create the clean ten-minute audio test and run it through the product.",
      "Keep one backup meeting processed and ready before any live demo.",
      "Add stage timing logs to the worker output."
    ],
    "outcome": "Key outcomes: meeting 17 as the primary backup demo example before the live client presentation; the 10-minute realistic file remains the main proof of quality; we will lead with a practical positioning message instead of a broad platform pitch",
    "purpose": "The meeting focused on reviewing current Meeting Notes Assistant progress, aligning demo planning and artifacts, refining pilot outreach and positioning, and reviewing current technical risks",
    "risks": []
  }
}
```
