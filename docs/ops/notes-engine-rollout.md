# MeetIQ Notes Engine Rollout / Rollback

This document records the production rollout switch for MeetIQ notes generation.

## Render services

Keep NOTES_ENGINE consistent in both Render services:

1. Backend web service
2. Worker service

## Rollout rule

Rollout = NOTES_ENGINE=v2

Meaning: use Quality Engine v2 globally.

## Rollback rule

Rollback = NOTES_ENGINE=v1

Meaning: use the old/stable v1 notes engine globally.

## Important

Do not change billing, database, Redis, S3, PayPal, Square, upload limits, or frontend env vars for notes-engine rollout.

Only change NOTES_ENGINE in both backend and worker.

## Allowlist

Keep MEETIQ_QEV2_ALLOWLIST_EMAILS unless intentionally changing allowlist behavior.

When NOTES_ENGINE=v2, QEv2 is global.

When NOTES_ENGINE=v1, v1 is global unless a selected account is allowlisted for QEv2.

## Post-rollout smoke test

After changing Render env vars and redeploying backend + worker:

1. Upload a new meeting.
2. Confirm notes reach ready.
3. Confirm model badge shows local-summary-v3+qev2.
4. Confirm Markdown download works.
5. Confirm usage increments.
6. Confirm backend health is ok.

Backend health command:

curl -s https://meeting-notes-assistant.onrender.com/healthz | python -m json.tool

## Simple rule

If good -> keep NOTES_ENGINE=v2
If bad  -> set NOTES_ENGINE=v1 in backend + worker
