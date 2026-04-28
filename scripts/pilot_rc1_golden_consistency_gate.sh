#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
MAX_POLL_ATTEMPTS="${MAX_POLL_ATTEMPTS:-240}"
POLL_SLEEP_SECONDS="${POLL_SLEEP_SECONDS:-2}"
OUT_DIR="test_outputs/pilot_rc1_golden_consistency_gate_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT_DIR"

echo "Pilot RC1 Golden Consistency Gate"
echo "Base URL: $BASE_URL"
echo "Max poll attempts: $MAX_POLL_ATTEMPTS"
echo "Poll sleep seconds: $POLL_SLEEP_SECONDS"
echo "Output directory: $OUT_DIR"
echo

echo "1) Backend health check"
curl -fsS "$BASE_URL/healthz" | tee "$OUT_DIR/healthz.json"
echo
echo

declare -a SAMPLE_FILES=(
  "demo_media/client_weekly_sync_10min.m4a"
  "demo_media/meeting_30min_script.wav"
  "backend/storage/uploads/meeting_81.m4a"
  "backend/storage/uploads/meeting_86.mp3"
)

RUN_CSV="$OUT_DIR/run_manifest.csv"
echo "sample,status,meeting_id,job_id,notes_json,markdown" > "$RUN_CSV"

for SAMPLE in "${SAMPLE_FILES[@]}"; do
  echo "=================================================="
  echo "Sample: $SAMPLE"

  SAFE_NAME="$(basename "$SAMPLE" | tr ' ./' '___')"
  SAMPLE_OUT="$OUT_DIR/$SAFE_NAME"
  mkdir -p "$SAMPLE_OUT"

  if [ ! -f "$SAMPLE" ]; then
    echo "SKIP: missing file $SAMPLE"
    echo "$SAMPLE,missing,,,,," >> "$RUN_CSV"
    continue
  fi

  echo
  echo "Create meeting"
  CREATE_RESP="$(curl -fsS -X POST "$BASE_URL/v1/meetings" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Pilot RC1 golden gate - $(basename "$SAMPLE")\"}")"

  echo "$CREATE_RESP" | tee "$SAMPLE_OUT/create_meeting.json"
  MEETING_ID="$(echo "$CREATE_RESP" | jq -r '.id // .meeting_id // empty')"

  if [ -z "$MEETING_ID" ]; then
    echo "FAIL: could not read meeting id"
    echo "$SAMPLE,create_failed,,,,," >> "$RUN_CSV"
    continue
  fi

  echo
  echo "Upload file"
  UPLOAD_RESP="$(curl -fsS -X POST "$BASE_URL/v1/meetings/$MEETING_ID/upload" \
    -F "file=@$SAMPLE")"

  echo "$UPLOAD_RESP" | tee "$SAMPLE_OUT/upload.json"
  JOB_ID="$(echo "$UPLOAD_RESP" | jq -r '.job_id // .jobId // .id // empty')"

  if [ -z "$JOB_ID" ]; then
    echo "FAIL: could not read job id"
    echo "$SAMPLE,upload_failed,$MEETING_ID,,,," >> "$RUN_CSV"
    continue
  fi

  echo
  echo "Poll job"
  JOB_STATUS="unknown"

  for i in $(seq 1 "$MAX_POLL_ATTEMPTS"); do
    JOB_RESP="$(curl -fsS "$BASE_URL/v1/jobs/$JOB_ID")"
    echo "$JOB_RESP" > "$SAMPLE_OUT/job_latest.json"

    JOB_STATUS="$(echo "$JOB_RESP" | jq -r '.status // empty')"
    echo "Attempt $i: $JOB_STATUS"

    if [ "$JOB_STATUS" = "succeeded" ] || [ "$JOB_STATUS" = "failed" ]; then
      break
    fi

    sleep "$POLL_SLEEP_SECONDS"
  done

  if [ "$JOB_STATUS" != "succeeded" ]; then
    echo "FAIL: job did not succeed"
    echo "$SAMPLE,job_failed,$MEETING_ID,$JOB_ID,,," >> "$RUN_CSV"
    continue
  fi

  echo
  echo "Fetch AI notes JSON"
  curl -fsS "$BASE_URL/v1/meetings/$MEETING_ID/notes/ai" \
    | tee "$SAMPLE_OUT/notes_ai.json" >/dev/null

  echo
  echo "Fetch markdown"
  if curl -fsS "$BASE_URL/v1/meetings/$MEETING_ID/notes.md" \
    | tee "$SAMPLE_OUT/notes.md" >/dev/null; then
    MARKDOWN_PATH="$SAMPLE_OUT/notes.md"
  else
    MARKDOWN_PATH=""
  fi

  echo "$SAMPLE,completed,$MEETING_ID,$JOB_ID,$SAMPLE_OUT/notes_ai.json,$MARKDOWN_PATH" >> "$RUN_CSV"

  echo
  echo "Completed sample: $SAMPLE"
done

echo
echo "=================================================="
echo "Score outputs"
python scripts/pilot_rc1_score_notes.py \
  --out-dir "$OUT_DIR" \
  --csv "$OUT_DIR/scorecard.csv" \
  --markdown "$OUT_DIR/scorecard.md"

echo
echo "Run manifest:"
column -s, -t "$RUN_CSV" || cat "$RUN_CSV"

echo
echo "Saved outputs:"
echo "$OUT_DIR"

echo
echo "Key files:"
echo "$OUT_DIR/run_manifest.csv"
echo "$OUT_DIR/scorecard.csv"
echo "$OUT_DIR/scorecard.md"
