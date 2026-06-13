# ES2006c Stuck Processing Repro

Branch: fix/es2006c-stuck-processing
Date: Sat 13 Jun 2026 23:16:01 BST

## Meeting
- Meeting ID: 352
- Title: ES2006c repro v2
- File: ES2006c.mp3
- Duration: 2181.78 seconds / 36:21
- Job ID: e2344570-cf9c-48de-90d6-49f116b5d4a7

## Worker log excerpt
worker-1  | {"ts": "2026-06-13 22:10:36,708", "level": "INFO", "logger": "rq.worker", "message": "default: process_meeting[352] (e2344570-cf9c-48de-90d6-49f116b5d4a7)"}
worker-1  | {"ts": "2026-06-13 22:10:36,710", "level": "INFO", "logger": "__main__", "message": "job starting", "job_id": "e2344570-cf9c-48de-90d6-49f116b5d4a7", "queue": "default"}
worker-1  | {"ts": "2026-06-13 22:10:38,238", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: job started", "job_id": "e2344570-cf9c-48de-90d6-49f116b5d4a7", "meeting_id": "352"}
worker-1  | {"ts": "2026-06-13 22:10:38,308", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: loading audio", "job_id": "e2344570-cf9c-48de-90d6-49f116b5d4a7", "meeting_id": "352", "raw_media_path": "s3://mna-artifacts/raw_media/meeting_352.mp3"}
worker-1  | {"ts": "2026-06-13 22:10:38,704", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: transcribing audio", "job_id": "e2344570-cf9c-48de-90d6-49f116b5d4a7", "meeting_id": "352"}
worker-1  | {"ts": "2026-06-13 22:10:39,949", "level": "INFO", "logger": "httpx", "message": "HTTP Request: GET https://huggingface.co/api/models/Systran/faster-whisper-base/revision/main \"HTTP/1.1 200 OK\"", "job_id": "e2344570-cf9c-48de-90d6-49f116b5d4a7"}
worker-1  | {"ts": "2026-06-13 22:11:05,924", "level": "INFO", "logger": "faster_whisper", "message": "Processing audio with duration 36:21.685", "job_id": "e2344570-cf9c-48de-90d6-49f116b5d4a7"}
worker-1  | {"ts": "2026-06-13 22:11:12,107", "level": "INFO", "logger": "faster_whisper", "message": "Detected language 'cy' with probability 0.54", "job_id": "e2344570-cf9c-48de-90d6-49f116b5d4a7"}

## DB status
 id  |                 email                 |      title       | media_filename | duration_seconds |   status   | last_error |          created_at           |          updated_at
-----+---------------------------------------+------------------+----------------+------------------+------------+------------+-------------------------------+-------------------------------
 352 | qa-es2006c+20260613231035@example.com | ES2006c repro v2 | ES2006c.mp3    |          2181.78 | PROCESSING |            | 2026-06-13 22:10:35.604123+00 | 2026-06-13 22:10:35.915611+00
(1 row)
