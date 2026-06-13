# ES2006c After-Fix Output

Branch: fix/es2006c-stuck-processing
Date: Sat 13 Jun 2026 23:46:56 BST

## Meeting
- Meeting ID: 353
- Title: ES2006c after fix v1
- File: ES2006c.mp3
- Duration: 2181.78 seconds / 36:21
- Job ID: fb65a54b-217f-4205-ae34-d5e4e241dac7

## Result
- Status: DONE
- Reached slide OCR: yes
- Reached notes generation: yes
- Finished: yes
- RQ Job OK: yes

## Worker log excerpt
worker-1  | {"ts": "2026-06-13 22:38:36,232", "level": "INFO", "logger": "rq.worker", "message": "default: process_meeting[353] (fb65a54b-217f-4205-ae34-d5e4e241dac7)"}
worker-1  | {"ts": "2026-06-13 22:38:36,233", "level": "INFO", "logger": "__main__", "message": "job starting", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "queue": "default"}
worker-1  | {"ts": "2026-06-13 22:38:37,051", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: job started", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "meeting_id": "353"}
worker-1  | {"ts": "2026-06-13 22:38:37,087", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: loading audio", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "meeting_id": "353", "raw_media_path": "s3://mna-artifacts/raw_media/meeting_353.mp3"}
worker-1  | {"ts": "2026-06-13 22:38:37,328", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: transcribing audio", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "meeting_id": "353"}
worker-1  | {"ts": "2026-06-13 22:38:38,235", "level": "INFO", "logger": "httpx", "message": "HTTP Request: GET https://huggingface.co/api/models/Systran/faster-whisper-base/revision/main \"HTTP/1.1 200 OK\"", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7"}
worker-1  | {"ts": "2026-06-13 22:39:10,535", "level": "INFO", "logger": "faster_whisper", "message": "Processing audio with duration 36:21.685", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7"}
worker-1  | {"ts": "2026-06-13 22:41:31,645", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: running slide OCR", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "meeting_id": "353"}
worker-1  | {"ts": "2026-06-13 22:41:31,646", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: generating notes", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "meeting_id": "353"}
worker-1  | {"ts": "2026-06-13 22:41:31,995", "level": "INFO", "logger": "app.jobs.process_meeting", "message": "process_meeting: finished", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "meeting_id": "353", "summary_preview": "Review progress, confirm the next demo path, and align on pilot outreach and ope"}
worker-1  | {"ts": "2026-06-13 22:41:32,007", "level": "INFO", "logger": "rq.worker", "message": "default: Job OK (fb65a54b-217f-4205-ae34-d5e4e241dac7)", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7"}
worker-1  | {"ts": "2026-06-13 22:41:32,007", "level": "INFO", "logger": "rq.worker", "message": "Result is kept for 500 seconds", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7"}
worker-1  | {"ts": "2026-06-13 22:41:32,037", "level": "INFO", "logger": "__main__", "message": "job completed", "job_id": "fb65a54b-217f-4205-ae34-d5e4e241dac7", "queue": "default"}

## DB status
 id  |        title         | media_filename | duration_seconds | status | last_error |          created_at           |          updated_at
-----+----------------------+----------------+------------------+--------+------------+-------------------------------+-------------------------------
 353 | ES2006c after fix v1 | ES2006c.mp3    |          2181.78 | DONE   |            | 2026-06-13 22:38:35.631013+00 | 2026-06-13 22:38:37.085612+00
(1 row)
