# Demo fallback plan

## Purpose

Keep the client-facing demo controlled and professional even if live processing is slow or interrupted.

## Primary demo path

Use a short, clean live demo file for upload and processing.

## Backup path

If live processing is slow, use the already validated 10-minute markdown artifact:

- `test_outputs/demo_rehearsal/meeting_181_external_ready_notes_after_cleanup_fix.md`

## Fallback script

Use this wording:

> I am going to switch to the already processed demo output so we can focus on the quality of the generated notes instead of waiting on processing time.

## What not to say

Avoid saying:

- The system failed.
- The product is broken.
- The model is unreliable.

## What to say instead

Say:

- Processing time can vary depending on file length and environment.
- For the demo, we keep a validated backup output ready.
- The important part is the structure and quality of the generated notes.

## Recovery steps

```bash
./bin/dc ps
./bin/dc logs --tail=120 backend
./bin/dc logs --tail=120 worker
./bin/dc restart backend worker
curl -fsS http://localhost:8000/healthz | jq
```
