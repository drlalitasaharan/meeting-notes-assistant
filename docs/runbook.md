# Runbook (Local)

- Launch infra:
  `docker compose -f infra/local/docker-compose.yml up -d`

- API:
  `uvicorn apps.api.main:app --reload --port 8000`

- Web:
  `cd apps/web && npm install && npm run dev -- -p 3000`

- Workers:
  Transcribe → `python apps/workers/transcribe/worker.py <MEETING_ID> raw/<MEETING_ID>.bin`
  Summarize → `python apps/workers/llm/summarize.py <MEETING_ID>`
  OCR PDF  → `python -c "from apps.workers.vision.ocr import ocr_pdf; ocr_pdf('<MEETING_ID>', '<S3_SLIDES_KEY>')"`
