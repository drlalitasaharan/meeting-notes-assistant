# Paid Account Upload Smoke Checklist

## Purpose

Confirm that a paid Starter account can use MeetIQ after successful billing activation.

## Test account

Use the Square Starter paid test account:

- Account: meetiq-test+square-live-starter-20260620@example.com
- Expected plan: Starter
- Expected provider: Square
- Expected upload limit: 20 meetings/month

## Pre-test expected state

Usage page should show:

- Plan: Starter
- Billing provider: Square
- Meetings used: 0 of 20
- Remaining uploads: 20

## Browser smoke test

1. Log in to MeetIQ.
2. Open Usage page.
3. Confirm paid access is active.
4. Click New Upload.
5. Upload a short known-good meeting file.
6. Confirm upload starts successfully.
7. Wait for processing to complete.
8. Open the meeting result.
9. Confirm notes are generated.
10. Confirm the notes contain:
    - Summary
    - Decisions
    - Risks or open questions if present
    - Action items if present
11. Download Markdown.
12. Confirm Markdown file downloads.
13. Return to Usage page.
14. Confirm usage increments from 0 of 20 to 1 of 20.

## Expected result

PASS if:

- Paid account can upload.
- Meeting processes successfully.
- Notes are generated.
- Markdown download works.
- Usage changes to 1 of 20.

## Failure handling

If upload is blocked:

- Capture screenshot of the error.
- Check Render logs for the upload request.
- Confirm billing status still shows Starter.

If processing fails:

- Capture meeting status.
- Check worker logs.
- Use retry processing only if available and appropriate.

If usage does not increment:

- Confirm meeting was created successfully.
- Check backend usage endpoint behavior.
- Do not change billing code unless root cause is confirmed.

## Result

Status: PASS

Confirmed:

- Paid Starter Square account could upload a meeting.
- Meeting processed successfully.
- Notes page opened successfully.
- Markdown download worked.
- Usage incremented from 0 of 20 to 1 of 20.

Conclusion:

Paid billing activation is connected to real product usage.

## Evidence

Observed production result:

- Paid account: meetiq-test+square-live-starter-20260620@example.com
- Plan: Starter
- Billing provider: Square
- Upload tested: meetiq_30min_sample_meeting_video.mp4
- Meeting title: V30mins
- Meeting ID: 40
- Notes status: Notes ready
- Markdown export downloaded: meeting-40-notes.md
- Usage before upload: 0 of 20
- Usage after upload: 1 of 20
- Remaining uploads after upload: 19

Final result: PASS
