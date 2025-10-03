# Developer helpers for Meeting Notes Assistant. Source with:  source scripts/dev.sh

# Repo root (prefer git)
if command -v git >/dev/null 2>&1; then
  ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
else
  ROOT_DIR="$(pwd)"
fi

: "${API:=http://127.0.0.1:8000}"

# Load API_KEY from env or .env; default if missing
if [ -z "${API_KEY:-}" ] && [ -f "$ROOT_DIR/.env" ]; then
  API_KEY="$(awk -F= '/^API_KEY=/{print $2}' "$ROOT_DIR/.env" | tail -1)"
fi
: "${API_KEY:=dev-123}"
H="X-API-Key: $API_KEY"

health() {
  curl -sS "$API/healthz" | jq .
}

create_meeting() {
  title="${1:-Kickoff}"
  curl -sS -X POST -H "$H" "$API/v1/meetings?title=$title"
}

upload_slide() {
  mid="$1"; file="$2"
  if [ -z "$mid" ] || [ -z "$file" ]; then
    echo "usage: upload_slide <meeting_id> <file>"; return 2
  fi
  curl -sS -X POST -H "$H" "$API/v1/meetings/$mid/slides" -F "files=@$file"
}

process_meeting() {
  mid="$1"
  if [ -z "$mid" ]; then echo "usage: process_meeting <meeting_id>"; return 2; fi

  job_json="$(curl -sS -X POST -H "$H" "$API/v1/jobs?type=process&meeting_id=$mid")" \
    || { echo "failed to create job"; return 1; }
  echo "$job_json" | jq .

  job_id="$(echo "$job_json" | jq -r .id)"
  if [ -z "$job_id" ] || [ "$job_id" = "null" ]; then
    echo "no job id returned"; return 1
  fi

  i=0
  while [ $i -lt 30 ]; do
    job_status="$(curl -sS -H "$H" "$API/v1/jobs/$job_id" | jq -r .status)"
    echo "job:$job_id status:$job_status"
    [ "$job_status" = "done" ] && return 0
    i=$((i+1)); sleep 1
  done
  echo "timed out waiting for job $job_id"; return 124
}

echo "Loaded helpers: health, create_meeting, upload_slide, process_meeting"
echo "API=$API  X-API-Key set"
