# Demo Success Criteria

## Technical success

The demo is technically successful if:

- Backend health check passes
- Upload succeeds
- Worker processes the file
- Job reaches succeeded state
- AI notes endpoint returns structured JSON
- Markdown export is available
- No backend crash occurs
- No manual database fix is needed

## Output quality success

The output is successful if:

- Summary is relevant and concise
- Purpose is meaningful for a real meeting
- Outcome is meaningful for a real meeting
- Risks are not hallucinated
- Next steps are actionable
- Decisions are actual decisions
- Action items are real tasks
- Owner/due date fields are not invented when absent
- Greeting noise is not promoted as a key point
- Malformed transcript fragments are not shown as action items

## Safety success

The safety behavior is successful if:

- Non-meeting audio does not produce fake structured decisions
- Non-meeting audio does not produce fake action items
- Narrative audio does not produce fake next steps
- The system avoids overclaiming when audio is not a real meeting

## Current launch-safe claim

Use:

Best for short, structured business meetings.

Avoid:

- Works perfectly for every meeting.
- Fully replaces human review.
