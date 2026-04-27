# Pilot RC1 Release Hardening Checklist

## Purpose

Freeze Pilot RC1 into a demo-ready and pilot-ready release candidate.

Recent completed quality work:
- Structured decision/action recall improved.
- Precision cleanup completed for duplicate decisions/actions.
- Embedded action owners normalized.
- Summary-like false action items filtered.
- Pilot RC1 benchmark reached 100/100 with 5/5 decisions and 5/5 actions.

## Release hardening goals

1. Confirm app health
   - Backend health endpoint passes.
   - DB, Redis, and storage checks pass.
   - Worker is running and processing jobs.

2. Confirm demo flow
   - Create meeting.
   - Upload short pilot demo audio.
   - Confirm job succeeds.
   - Confirm `/notes/ai` output is structured.
   - Confirm `/notes.md` export is readable.

3. Confirm quality gates
   - Pilot RC1 benchmark still passes.
   - Non-meeting safety benchmark still behaves safely.
   - No large local test artifacts are committed.

4. Confirm packaging
   - Demo script is ready.
   - Pilot outreach notes are ready.
   - Known limitations are documented.
   - Launch readiness score is updated.

## Acceptance criteria

- Health endpoint returns status ok.
- A fresh demo upload completes successfully.
- Notes contain summary, decisions, and action items.
- Markdown export is readable and client-facing.
- Code checks pass.
- Working tree is clean before PR.
- Pilot RC1 can be tagged or documented as release-ready.

## Status

Final demo-output polish in progress.
