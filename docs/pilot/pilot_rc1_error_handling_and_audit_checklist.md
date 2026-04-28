# Pilot RC1 Error Handling and Audit Checklist

## User-facing error states

| Scenario | Recommended message |
|---|---|
| Upload failed | Upload failed. Please try again. |
| Unsupported file | This file format is not supported. Please upload a supported audio file. |
| Processing delay | Processing is taking longer than expected. Please check again shortly. |
| Transcription failed | Audio could not be transcribed clearly. Please try a clearer recording. |
| Notes generation failed | Notes could not be generated for this meeting. |
| Non-meeting content | This recording did not contain enough meeting structure to generate decisions or action items. |
| Worker unavailable | Processing is temporarily unavailable. Please try again later. |

## Backend events to track

- meeting created
- upload started
- upload completed
- job queued
- job running
- job succeeded
- job failed
- transcription failed
- notes generation failed
- markdown generated
- safety downgrade triggered
- feedback submitted
- deletion requested

## Minimum audit fields

- meeting_id
- job_id
- created_at
- upload_status
- processing_status
- notes_status
- markdown_status
- safety_signal
- feedback_status
- review_status
- error_reason

## Acceptance criteria

- every failed meeting has a visible reason
- every completed meeting has generated notes or intentional safety downgrade
- every pilot meeting can be traced from upload to output
- user feedback can be linked to meeting output
