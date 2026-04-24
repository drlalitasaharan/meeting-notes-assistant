# Demo Troubleshooting Guide

## Backend health check fails

~~~bash
./bin/dc ps
./bin/dc logs backend --tail=100
./bin/dc restart backend
http :8000/healthz
~~~

## Worker is not processing jobs

~~~bash
./bin/dc ps
./bin/dc logs worker --tail=100
./bin/dc restart worker
~~~

## Upload succeeds but notes are missing

Check job status:

~~~bash
http :8000/v1/jobs/$JOB_ID | jq
~~~

Check worker logs:

~~~bash
./bin/dc logs -f worker
~~~

## MinIO or storage issue

~~~bash
http :8000/healthz | jq
./bin/dc ps
./bin/dc restart minio backend worker
~~~

## Notes quality looks weak

Check:

- Is the audio a real meeting?
- Is it too long for the current demo?
- Is speech clear?
- Are there explicit decisions or action items?
- Is the file closer to narrative/casual audio than business-meeting audio?

For first demos, use a short structured meeting file.

## Narrative audio creates fake meeting notes

Run:

~~~bash
PYTHONPATH=backend pytest backend/tests/test_notes_quality_regression.py -q
~~~

Expected:

~~~text
2 passed
~~~

If this fails, do not use the branch for demos.

## Demo rule

Do not debug live in front of a pilot user unless the purpose of the call is technical validation.

For a polished pilot conversation, use a pre-tested input and pre-reviewed output.
