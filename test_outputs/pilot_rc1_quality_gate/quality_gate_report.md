# Pilot RC1 Quality Gate Regression Report

## Result

**Score:** 100/100
**Threshold:** 85/100
**Status:** PASS

## Run Evidence

- Meeting ID: 184
- Job ID: 21bc0305-7b45-45da-abc2-5886d1495c99
- Audio file: backend/storage/uploads/meeting_115.m4a
- Final job status: succeeded

## Checks

- PASS Backend health endpoint returned ok (10 pts)
- PASS Meeting was created (10 pts)
- PASS Audio upload returned a processing job (10 pts)
- PASS Processing job succeeded (20 pts)
- PASS Summary was generated (10 pts)
- PASS Purpose and outcome slots were generated (10 pts)
- PASS Key points were generated (10 pts)
- PASS Decisions were generated (10 pts)
- PASS Action items were generated (10 pts)

## Evidence Files

- test_outputs/pilot_rc1_quality_gate/healthz.json
- test_outputs/pilot_rc1_quality_gate/meeting_response.json
- test_outputs/pilot_rc1_quality_gate/upload_response.json
- test_outputs/pilot_rc1_quality_gate/job_status_latest.json
- test_outputs/pilot_rc1_quality_gate/notes_ai.json
- test_outputs/pilot_rc1_quality_gate/notes.md
- test_outputs/pilot_rc1_quality_gate/quality_gate_summary.json
