#!/usr/bin/env bash
set -euo pipefail

# --- Config (override via env) ---
MNA_API="${MNA_API:-http://127.0.0.1:8000}"
TEXT="${TEXT:-hello from smoke}"
DELAY="${DELAY:-0.2}"

# MinIO / mc settings (dev)
MC_ALIAS="${MC_ALIAS:-local}"
BUCKET="${BUCKET:-mna-dev}"
PUBLIC_BASE="${PUBLIC_BASE:-${S3_PUBLIC_ENDPOINT:-http://127.0.0.1:9000}}"

need() { command -v "$1" >/dev/null || { echo "Missing dependency: $1" >&2; exit 2; }; }
need curl; need jq; need mc

echo "== /healthz =="
curl -sS "$MNA_API/healthz" | jq .

echo "== create meeting (POST /v1/meetings) =="
MEETING_JSON="$(curl -sS -X POST "$MNA_API/v1/meetings" \
  -H 'content-type: application/json' \
  -d '{"title":"smoke test meeting"}')"
echo "$MEETING_JSON" | jq .
MEETING_ID="$(echo "$MEETING_JSON" | jq -r '.id')"

echo "== submit job (POST /v1/jobs) =="
curl -sS -X POST "$MNA_API/v1/jobs" \
  -H 'content-type: application/json' \
  -d "{\"type\":\"demo\",\"payload\":{\"text\":\"$TEXT\",\"delay\":$DELAY}}" \
  -o /tmp/resp.json -w '\nHTTP %{http_code}\n'
cat /tmp/resp.json

JOB_ID="$(jq -r '.job_id // .id // empty' /tmp/resp.json)"
[ -n "$JOB_ID" ] || { echo "No job id returned"; exit 1; }
echo "JOB_ID=$JOB_ID"

echo "== poll job status =="
for i in {1..80}; do
  curl -sS "$MNA_API/v1/jobs/$JOB_ID" -o /tmp/job.json
  STATUS="$(jq -r '.status' /tmp/job.json)"
  echo "$STATUS"
  [[ "$STATUS" =~ ^(finished|succeeded|failed)$ ]] && break
  sleep 0.5
done
echo "Final:" && jq . /tmp/job.json

# Create & upload a tiny artifact to MinIO using mc (public-read bucket)
echo "== upload artifact to MinIO via mc =="
ART="/tmp/smoke-${JOB_ID}.txt"
echo "artifact for job $JOB_ID (meeting $MEETING_ID) at $(date -u +%FT%TZ)" > "$ART"

# Ensure bucket exists (idempotent) and is public for download
mc mb "${MC_ALIAS}/${BUCKET}" >/dev/null 2>&1 || true
mc anonymous set download "${MC_ALIAS}/${BUCKET}" >/dev/null 2>&1 || true

KEY="smoke/${JOB_ID}.txt"
mc cp "$ART" "${MC_ALIAS}/${BUCKET}/${KEY}" >/dev/null

URL="${PUBLIC_BASE%/}/${BUCKET}/${KEY}"
echo "Artifact URL: $URL"

echo "== metrics head =="
curl -sS "$MNA_API/metrics" | sed -n '1,40p'
