# External-ready 10-minute demo rehearsal

Branch: demo/external-ready-rehearsal
Meeting ID: 181
Audio file: ./demo_media/client_weekly_sync_10min.m4a

## Goal

Re-run the same 10-minute demo audio after the markdown cleanup patch and confirm the external-facing markdown no longer contains:

1. "I'd us to leave..."
2. Extra spaces before periods

## Initial result

FAIL.

The first rehearsal still showed the malformed Key Points phrase and spaces before periods in Action Items.

## Final validation

PASS.

The refreshed external-facing markdown no longer contains the malformed phrase or extra spaces before periods.

## External-readiness checks

- Bad phrase check: PASS
- Curly apostrophe variant check: PASS
- Extra spaces before periods check: PASS

## Evidence

Validated files:

- test_outputs/demo_rehearsal/meeting_181_external_ready_notes.md
- test_outputs/demo_rehearsal/meeting_181_external_ready_notes_ai.json
- test_outputs/demo_rehearsal/meeting_181_external_ready_notes_after_cleanup_fix.md

## Decision

The previous conditional demo readiness can now be upgraded to a cleaner external-ready demo decision for this 10-minute rehearsal path.
