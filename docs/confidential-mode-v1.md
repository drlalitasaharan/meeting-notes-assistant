# MeetIQ Confidential Mode V1

## Purpose

Confidential Mode V1 gives users a safer hosted-cloud processing option for sensitive meetings.

When enabled, MeetIQ processes the uploaded recording using the existing hosted cloud workflow, generates structured meeting notes, and then automatically deletes the original uploaded recording after notes are successfully generated.

Generated notes remain available in the user account for review, editing, copy, export, and manual deletion.

## What Confidential Mode does

- Lets the user enable Confidential Mode before upload.
- Stores a `confidential_mode` flag on the meeting.
- Sets recording retention policy to `delete_after_notes`.
- Marks recording deletion as `pending` during processing.
- Deletes the original uploaded recording after notes are generated and saved.
- Marks recording deletion as `deleted` when successful.
- Marks recording deletion as `failed` if deletion does not complete.
- Does not fail the completed notes job if recording deletion fails.
- Shows Confidential Mode status on the meeting detail page.
- Keeps generated notes available for review and Markdown export.
- Keeps existing manual meeting deletion control.

## What Confidential Mode does not claim

Confidential Mode V1 does not claim:

- Fully local processing
- Offline processing
- End-to-end encryption
- HIPAA compliance
- SOC 2 compliance
- Dedicated private deployment
- Zero-retention processing for all derived data

MeetIQ should describe this as hosted-cloud Confidential Mode, not fully private or offline processing.

## User-facing wording

Recommended upload-page wording:

> MeetIQ still uses hosted cloud processing. When enabled, the original recording is automatically deleted after notes are generated. Generated notes remain available in your account.

Recommended meeting-page wording:

> Confidential Mode enabled. Original recording deleted after notes generation. Generated notes remain available for review and export.

## Data lifecycle

### Normal upload

1. User creates meeting.
2. User uploads recording.
3. Recording is stored.
4. Worker processes recording.
5. Notes are generated and stored.
6. Recording follows standard retention behavior.
7. User can manually delete the meeting.

### Confidential Mode upload

1. User creates meeting.
2. User enables Confidential Mode.
3. User uploads recording.
4. Recording is stored temporarily.
5. Worker processes recording.
6. Notes are generated and stored.
7. Meeting is marked completed.
8. Original recording is deleted best-effort.
9. Recording deletion status is shown to the user.
10. Notes remain available until the user deletes the meeting.

## Recording deletion statuses

- `not_required`: Confidential Mode was not enabled.
- `pending`: Confidential Mode was enabled and deletion has not completed yet.
- `deleted`: Original recording was deleted after notes generation.
- `failed`: Recording deletion did not complete. Notes remain available.

## Manual deletion

The existing meeting delete endpoint removes:

- Meeting record
- Generated meeting notes
- Regular notes
- Uploaded recording best-effort

This supports user-controlled deletion for both standard and Confidential Mode meetings.

## Current implementation files

Backend:

- `backend/app/models/meeting.py`
- `backend/app/schemas/meetings.py`
- `backend/app/routers/meeting_notes_api.py`
- `backend/app/jobs/process_meeting.py`
- `backend/app/services/data_controls.py`
- `backend/migrations/versions/20260630_confidential_mode_v1.py`
- `backend/tests/test_confidential_mode_worker.py`

Frontend:

- `frontend/app/upload/page.tsx`
- `frontend/components/UploadForm.tsx`
- `frontend/app/meetings/[id]/page.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/types.ts`

## Future roadmap

Recommended future privacy improvements:

1. S3 lifecycle rule for confidential recordings
   - Delete objects under a confidential prefix after 1 day as a safety net.

2. Retention controls
   - Delete recording after notes.
   - Delete recording after 24 hours.
   - Delete notes after 30 days.
   - Manual-only deletion.

3. Admin/support access restrictions
   - Hide recording URLs for confidential meetings.
   - Avoid exposing raw transcript/notes in admin views unless necessary.

4. Audit log
   - Track upload, processing, deletion attempt, deletion success/failure.

5. Support access approval
   - Require user approval before support can inspect confidential meeting output.

6. Private deployment
   - Dedicated storage, database, and worker for enterprise clients.

7. Local/offline processing
   - Longer-term option for clients requiring stronger confidentiality guarantees.
