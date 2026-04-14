# Demo command checklist

## Health
http :8000/healthz

## Create meeting
http POST :8000/v1/meetings title="Demo meeting" tags:='["demo"]'

## Upload audio
http --form POST :8000/v1/meetings/$MEETING_ID/upload file@demo_media/meeting_10min_script.wav

## Check job
http :8000/v1/jobs/$JOB_ID

## AI notes JSON
http :8000/v1/meetings/$MEETING_ID/notes/ai

## Markdown notes
http :8000/v1/meetings/$MEETING_ID/notes.md
