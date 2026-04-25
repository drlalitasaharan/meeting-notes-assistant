# Pilot-ready user flow rehearsal

Branch: demo/pilot-ready-user-flow-rehearsal
Meeting ID: 182
Audio file: ./demo_media/client_weekly_sync_10min.m4a

## Goal

Validate the full pilot-ready user flow using the 10-minute demo audio:

1. Start the local stack.
2. Confirm backend health.
3. Create a meeting.
4. Upload demo audio.
5. Wait for processing to finish.
6. Export markdown and AI JSON notes.
7. Run publishability checks.

## Result

PASS.

The full pilot-ready rehearsal completed successfully.

## Evidence

Generated files:

- test_outputs/pilot_rehearsal/meeting_182_pilot_ready_notes.md
- test_outputs/pilot_rehearsal/meeting_182_pilot_ready_notes_ai.json

Job ID:

- 03869a08-0d1f-4126-8b20-510cb719abd6

## Validation checks

The rehearsal passed the pilot-ready checks:

- Required markdown sections were present.
- Malformed phrase checks passed.
- Extra spaces before periods check passed.
- AI JSON included summary output.
- Job completed successfully.
- Exported markdown was readable and client-facing.

## Decision

The 10-minute pilot-ready user flow is validated.

This gives enough confidence to use the current demo path for a controlled pilot with real users, while keeping expectations focused on short, structured business meetings.

## Follow-up

The Docker build transferred a large build context during this run. This is not a demo blocker, but a future infrastructure cleanup should reduce the Docker build context using `.dockerignore` and build optimization.
