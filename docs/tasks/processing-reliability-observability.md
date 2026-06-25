# Task: Processing reliability, timing, and progress visibility

## Goal

Improve MeetIQ processing reliability and user confidence for 30–60 minute recordings without interrupting the current production user experience.

This task must be additive, backward-compatible, and safe to deploy.

## Product scope

Target:
- 30–60 minute meetings
- Paid Starter / pilot users
- Better observability and reliability before expanding Pro Pilot / 2-hour support

Do not:
- Change billing logic
- Change plan limits
- Publicly promise 2+ hour support
- Break existing meeting upload, processing, notes, or markdown download flows

## Required implementation

### 1. Add processing observability

Track processing stages and timestamps.

Recommended user-facing stages:
- uploaded
- validating_media
- processing_audio
- transcribing
- generating_notes
- finalizing
- completed
- failed

Track timing for:
- upload_received_at
- media_validation_started_at
- media_validation_completed_at
- audio_conversion_started_at
- audio_conversion_completed_at
- transcription_started_at
- transcription_completed_at
- notes_generation_started_at
- notes_generation_completed_at
- processing_completed_at
- processing_failed_at

Use additive nullable DB fields or a JSONB timing object. Do not require backfilling existing meetings.

### 2. Keep existing status compatibility

Existing frontend and API behavior must continue working.

If current statuses are:
- uploaded
- processing
- completed
- failed

Keep those working.

Add richer processing stage information as an additional field, not as a breaking replacement.

Recommended API response:
- status: existing high-level status
- processing_stage: richer stage
- processing_progress_label: user-friendly label
- processing_error_message: safe user-facing message
- processing_timings: admin/debug timing metadata if already supported by admin routes

### 3. Add safe worker stage updates

Worker should update stage at major boundaries:
- validation start/end
- audio conversion start/end
- transcription start/end
- notes generation start/end
- finalizing
- completed
- failed

Stage updates should be idempotent and safe if called more than once.

### 4. Add failure hardening

On worker failure:
- mark meeting status failed
- set processing_stage failed
- store safe error code
- store safe user-facing error message
- store internal diagnostic detail only where appropriate
- avoid exposing secrets, stack traces, API keys, raw provider errors, or internal paths to users

Recommended safe user messages:
- "Processing took longer than expected. Please try again or contact support."
- "We could not process this recording. Please check the file format and try again."
- "Transcription failed. Please try a shorter or clearer recording."

### 5. Add retry-safe structure

Do not blindly retry all jobs.

Retries should be safe and bounded:
- max attempts should be limited
- duplicate jobs should not double-charge usage
- failed retry should preserve original meeting record
- successful retry should produce normal notes
- retry should not create duplicate notes or duplicate usage consumption

### 6. Add admin visibility

Admin view/API should show:
- current status
- current processing stage
- attempts
- started/completed/failed timestamps
- total processing time
- slow/failed meetings

Do not expose admin diagnostics to normal users.

### 7. Add tests

Add or update tests for:
- stage transition helper
- failed job stores safe error
- completed job stores completed timestamp
- API remains backward compatible
- existing upload/usage tests still pass
- retry does not double-count usage if relevant to current architecture

### 8. Production smoke test after merge

Use a 35–45 minute paid/pilot file.

Confirm:
- upload works
- stages update clearly
- processing completes
- notes generate
- markdown downloads
- usage increments correctly
- admin can see timing and status
- no current production flow is interrupted

## Definition of done

This task is complete when a 35–45 minute recording can be processed with:
- clear user-facing progress
- no silent failure
- safe failure messages
- timing visibility
- admin slow/failed job visibility
- no billing or usage regression
- no disruption to current users
