# 30-60 Minute Audio Baseline QA

This directory is for local QA outputs from the 30-60 minute MP3 baseline pack.

Run one case at a time:

```bash
python scripts/run_30_60min_audio_baseline.py --case M01
```

The helper reads `qa_results/baseline_30_60min_before/manifest.csv` and writes:

- `M01_generated_notes.md`
- `M01_generated_notes.json`
- `M01_create_meeting.json`
- `M01_upload.json`
- `M01_job_latest.json`
- `run_summary.csv`

Local API requirements:

- Backend API running at `BASE_URL` or `MNA_API` (defaults to `http://127.0.0.1:8000`)
- Redis/RQ worker running so upload jobs are processed
- DB and storage configured for the local stack
- Transcription/model configuration available to the worker
- A QA account allowed to upload 30-60 minute recordings

Useful env vars:

```bash
BASE_URL=http://127.0.0.1:8000
MEETIQ_QA_EMAIL=meetiq-qa-baseline@example.com
MEETIQ_QA_PASSWORD='QaBaselinePassword123!'
MAX_POLL_ATTEMPTS=240
POLL_SLEEP_SECONDS=5
```

Because these recordings are longer than the default free-trial limit, the running
API must treat the QA user as pilot/paid or have local QA limits raised. For a
local pilot override, start the API with:

```bash
MEETIQ_PILOT_OVERRIDE_EMAILS=meetiq-qa-baseline@example.com
```

The script does not change production behavior, billing, auth policy, prompts, or
notes generation.
