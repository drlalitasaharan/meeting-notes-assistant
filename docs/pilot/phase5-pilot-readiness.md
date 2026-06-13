# Phase 5 Pilot Readiness Notes

## Current Status

MeetIQ is ready for controlled hosted pilot testing with known limitations documented.

Completed launch-hardening items:

- Production Render pre-deploy migration workflow is configured.
- Alembic migrations now run before backend API deploys.
- Production database reached latest migration head.
- `upload_ledger` database foundation has been added.
- Hosted backend deploy completed successfully after pre-deploy migration.

## Finding: Upload Usage Reset After Delete

Current behavior:

- A user can upload a meeting.
- Usage increases while the meeting is stored.
- If the user deletes the meeting, usage can return to available capacity.
- This means current usage enforcement is based on stored/active meetings, not lifetime uploads.

Pilot decision:

This is acceptable for controlled pilot testing because users are invited and monitored manually.

Public launch decision:

This must be hardened before public self-serve/free-trial launch.

Required future fix:

- Create an `upload_ledger` row when an upload is accepted.
- Set `counted_at` when the upload is confirmed or processing starts.
- Keep the ledger row even if the meeting is deleted.
- Calculate free-trial usage from `upload_ledger`, not active/stored meetings.

## Phase 5 Task Status

### M16. Add lifetime upload ledger

Status: Partial complete.

Completed:

- `upload_ledger` table migration added.
- Production migration workflow confirmed.
- Database foundation is ready.

Remaining before public/free-trial launch:

- App logic must create and count upload ledger records.
- Delete should not reset lifetime usage.

### M17. Add Render pre-deploy migration workflow

Status: Complete.

Confirmed:

- Render pre-deploy command runs before backend deploy.
- Alembic migration reaches head.
- Backend service goes live after migration succeeds.

### M18. Add pilot feedback form or support intake tracking

Status: Do now.

Recommended minimum version:

- Add a simple feedback/support intake path.
- Collect upload issues, note quality feedback, confusing UX areas, and pilot user comments.

### M19. Add basic admin view for user uploads/errors

Status: Soon, but not required before first controlled pilot.

### M20. Prepare first pilot onboarding email and instructions

Status: Do now.

## Pilot User Guidance

Recommended first pilot test:

- Use a structured 5–20 minute meeting recording first.
- Use clear audio where possible.
- Review summary, decisions, risks, action items, and next steps.
- Report any upload, processing, or output quality issues.

Current long-meeting guidance:

- 60-minute meetings are supported on a best-effort basis.
- Long-meeting quality should be evaluated further before broader public launch.

## Public Launch Gate

Before public self-serve/free-trial launch:

- Upload ledger app logic must be implemented.
- Free-trial usage must not reset after delete.
- Basic upload/error monitoring should exist.
- Support or feedback intake should be available.
- Billing should only be added after pilot validation.
