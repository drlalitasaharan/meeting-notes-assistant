#!/usr/bin/env bash
set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
THRESHOLD="${THRESHOLD:-85}"
OUT="test_outputs/pilot_rc1_quality_gate"
mkdir -p "$OUT"

echo "Running Pilot RC1 quality gate..."
echo "Base URL: $BASE_URL"

AUDIO_FILE=""
for candidate in \
  "backend/storage/uploads/meeting_115.m4a" \
  "client_weekly_sync_10min.m4a" \
  "test_assets/client_weekly_sync_10min.m4a" \
  "test_outputs/client_weekly_sync_10min.m4a" \
  "meeting_30min_script.wav" \
  "test_assets/meeting_30min_script.wav" \
  "demo_upload_audio_2s.wav" \
  "test_assets/demo_upload_audio_2s.wav"
do
  if [ -f "$candidate" ]; then
    AUDIO_FILE="$candidate"
    break
  fi
done

if [ -z "$AUDIO_FILE" ]; then
  AUDIO_FILE="$(find . -maxdepth 5 \( -iname "*10min*.m4a" -o -iname "*10min*.wav" -o -iname "*demo*.wav" -o -iname "*meeting*.m4a" -o -iname "*meeting*.wav" \) | head -n 1)"
fi

if [ -z "$AUDIO_FILE" ]; then
  echo "No demo audio file found."
  exit 1
fi

echo "Audio file: $AUDIO_FILE"

score=0
check_lines=""

add_check() {
  name="$1"
  passed="$2"
  points="$3"
  if [ "$passed" = "yes" ]; then
    score=$((score + points))
    mark="PASS"
  else
    mark="FAIL"
  fi
  check_lines="${check_lines}- ${mark} ${name} (${points} pts)\n"
}

echo "Checking backend health..."
if curl -s "$BASE_URL/healthz" > "$OUT/healthz.json"; then
  health_ok="$(jq -r "if .status == \"ok\" and .checks.db.status == \"ok\" and .checks.redis.status == \"ok\" and .checks.storage.status == \"ok\" then \"yes\" else \"no\" end" "$OUT/healthz.json")"
else
  echo "{}" > "$OUT/healthz.json"
  health_ok="no"
fi
add_check "Backend health endpoint returned ok" "$health_ok" 10

echo "Creating meeting..."
MEETING_RESPONSE="$(http --body POST "$BASE_URL/v1/meetings" title="Pilot RC1 quality gate regression run" 2>/dev/null || true)"
printf "%s\n" "$MEETING_RESPONSE" > "$OUT/meeting_response.json"
MEETING_ID="$(printf "%s" "$MEETING_RESPONSE" | jq -r ".id // empty" 2>/dev/null || true)"
if [ -n "$MEETING_ID" ]; then meeting_ok="yes"; else meeting_ok="no"; fi
add_check "Meeting was created" "$meeting_ok" 10

echo "Uploading audio..."
UPLOAD_RESPONSE="$(http --form POST "$BASE_URL/v1/meetings/$MEETING_ID/upload" file@"$AUDIO_FILE" 2>/dev/null || true)"
printf "%s\n" "$UPLOAD_RESPONSE" > "$OUT/upload_response.json"
JOB_ID="$(printf "%s" "$UPLOAD_RESPONSE" | jq -r ".job_id // .id // empty" 2>/dev/null || true)"
if [ -n "$JOB_ID" ]; then upload_ok="yes"; else upload_ok="no"; fi
add_check "Audio upload returned a processing job" "$upload_ok" 10

echo "Polling job..."
FINAL_STATUS=""
for i in $(seq 1 90); do
  JOB_RESPONSE="$(http --body "$BASE_URL/v1/jobs/$JOB_ID" 2>/dev/null || true)"
  printf "%s\n" "$JOB_RESPONSE" > "$OUT/job_status_latest.json"
  FINAL_STATUS="$(printf "%s" "$JOB_RESPONSE" | jq -r ".status // empty" 2>/dev/null || true)"
  echo "Poll $i status: $FINAL_STATUS"
  if [ "$FINAL_STATUS" = "succeeded" ] || [ "$FINAL_STATUS" = "failed" ]; then
    break
  fi
  sleep 5
done

if [ "$FINAL_STATUS" = "succeeded" ]; then job_ok="yes"; else job_ok="no"; fi
add_check "Processing job succeeded" "$job_ok" 20

if [ "$job_ok" = "yes" ]; then
  http --body "$BASE_URL/v1/meetings/$MEETING_ID/notes/ai" > "$OUT/notes_ai.json"
  curl -s "$BASE_URL/v1/meetings/$MEETING_ID/notes.md" > "$OUT/notes.md"
else
  echo "{}" > "$OUT/notes_ai.json"
  : > "$OUT/notes.md"
fi

summary_len="$(jq -r "(.summary // \"\") | length" "$OUT/notes_ai.json")"
purpose_len="$(jq -r "(.summary_slots.purpose // \"\") | length" "$OUT/notes_ai.json")"
outcome_len="$(jq -r "(.summary_slots.outcome // \"\") | length" "$OUT/notes_ai.json")"
key_count="$(jq -r "(.key_points // []) | length" "$OUT/notes_ai.json")"
decision_count="$(jq -r "((.decisions // []) | length) + ((.decision_objects // []) | length)" "$OUT/notes_ai.json")"
action_count="$(jq -r "((.action_items // []) | length) + ((.action_item_objects // []) | length)" "$OUT/notes_ai.json")"

if [ "$summary_len" -gt 0 ]; then summary_ok="yes"; else summary_ok="no"; fi
if [ "$purpose_len" -gt 0 ] && [ "$outcome_len" -gt 0 ]; then slots_ok="yes"; else slots_ok="no"; fi
if [ "$key_count" -gt 0 ]; then key_ok="yes"; else key_ok="no"; fi
if [ "$decision_count" -gt 0 ]; then decision_ok="yes"; else decision_ok="no"; fi
if [ "$action_count" -gt 0 ]; then action_ok="yes"; else action_ok="no"; fi

add_check "Summary was generated" "$summary_ok" 10
add_check "Purpose and outcome slots were generated" "$slots_ok" 10
add_check "Key points were generated" "$key_ok" 10
add_check "Decisions were generated" "$decision_ok" 10
add_check "Action items were generated" "$action_ok" 10

if [ "$score" -ge "$THRESHOLD" ]; then status="PASS"; passed_json="true"; else status="FAIL"; passed_json="false"; fi

printf "{\"score\":%s,\"threshold\":%s,\"passed\":%s,\"meeting_id\":\"%s\",\"job_id\":\"%s\",\"audio_file\":\"%s\"}\n" "$score" "$THRESHOLD" "$passed_json" "$MEETING_ID" "$JOB_ID" "$AUDIO_FILE" > "$OUT/quality_gate_summary.json"

{
  echo "# Pilot RC1 Quality Gate Regression Report"
  echo ""
  echo "## Result"
  echo ""
  echo "**Score:** $score/100"
  echo "**Threshold:** $THRESHOLD/100"
  echo "**Status:** $status"
  echo ""
  echo "## Run Evidence"
  echo ""
  echo "- Meeting ID: $MEETING_ID"
  echo "- Job ID: $JOB_ID"
  echo "- Audio file: $AUDIO_FILE"
  echo "- Final job status: $FINAL_STATUS"
  echo ""
  echo "## Checks"
  echo ""
  printf "%b" "$check_lines"
  echo ""
  echo "## Evidence Files"
  echo ""
  echo "- test_outputs/pilot_rc1_quality_gate/healthz.json"
  echo "- test_outputs/pilot_rc1_quality_gate/meeting_response.json"
  echo "- test_outputs/pilot_rc1_quality_gate/upload_response.json"
  echo "- test_outputs/pilot_rc1_quality_gate/job_status_latest.json"
  echo "- test_outputs/pilot_rc1_quality_gate/notes_ai.json"
  echo "- test_outputs/pilot_rc1_quality_gate/notes.md"
  echo "- test_outputs/pilot_rc1_quality_gate/quality_gate_summary.json"
} > "$OUT/quality_gate_report.md"

echo ""
echo "Pilot RC1 quality gate score: $score/100"
echo "Status: $status"
echo "Report: $OUT/quality_gate_report.md"

if [ "$score" -ge "$THRESHOLD" ]; then exit 0; else exit 1; fi
