# Local Demo Runbook

## 1. Start clean

~~~bash
cd /Users/lalitasaharan/Code/AJENCEL/meeting-notes-assistant || exit 1
git checkout main
git pull origin main
git status
~~~

Expected:

~~~text
nothing to commit, working tree clean
~~~

## 2. Start services

~~~bash
./bin/dc up -d
./bin/dc ps
~~~

Expected services:

- backend
- worker
- postgres
- redis
- minio

## 3. Check backend health

~~~bash
http :8000/healthz
~~~

Expected health status:

~~~text
status: ok
~~~

## 4. Create demo meeting

~~~bash
MEETING_ID=$(http --body POST :8000/v1/meetings title="Pilot Demo Meeting" | jq -r '.id')
echo "$MEETING_ID"
~~~

## 5. Upload short demo audio

Use a short, structured business-meeting file first.

~~~bash
http --form POST :8000/v1/meetings/$MEETING_ID/upload file@client_weekly_sync_10min.m4a
~~~

## 6. Watch worker logs

~~~bash
./bin/dc logs -f worker
~~~

Look for:

- audio loaded
- transcription completed
- notes generated
- job succeeded

## 7. Check AI notes

~~~bash
http :8000/v1/meetings/$MEETING_ID/notes/ai | jq
~~~

Review:

- summary
- summary_slots
- key_points
- decisions
- decision_objects
- action_items
- action_item_objects

## 8. Check markdown export

~~~bash
http :8000/v1/meetings/$MEETING_ID/notes.md
~~~

## 9. Save latest demo output

~~~bash
mkdir -p test_outputs/demo
http --body :8000/v1/meetings/$MEETING_ID/notes/ai > test_outputs/demo/latest_demo_notes_ai.json
http --body :8000/v1/meetings/$MEETING_ID/notes.md > test_outputs/demo/latest_demo_notes.md
~~~

## 10. Readiness check

Before showing externally, confirm:

- Summary is concise and relevant
- Purpose and outcome are present for real meetings
- Decisions are real decisions
- Action items are publishable tasks
- Narrative/non-meeting content does not create fake actions
- Greeting noise is not promoted into key points or action items
