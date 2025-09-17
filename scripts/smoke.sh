#!/usr/bin/env bash
set -euo pipefail

API="${API_BASE_URL:-http://127.0.0.1:8000/v1}"

echo "== /healthz =="
curl -sS http://127.0.0.1:8000/healthz | jq .

echo "== start meeting =="
CREATE_RES=$(curl -sS -X POST "$API/meetings/start" -H "Content-Type: application/json" -d '{"name":"Smoke Test"}')
echo "$CREATE_RES" | jq .
MID=$(jq -r '.meetingId' <<<"$CREATE_RES")
PUT_URL=$(jq -r '.uploadUrl' <<<"$CREATE_RES")

[[ "$PUT_URL" == *"X-Amz-Algorithm=AWS4-HMAC-SHA256"* ]] || { echo "Missing SigV4 params"; exit 1; }

echo "== upload raw to MinIO (presigned PUT) =="
echo "hello audio" > /tmp/audio.bin
curl -sS -f --upload-file /tmp/audio.bin "$PUT_URL" > /dev/null
echo "PUT OK"

echo "== list meetings =="
curl -sS "$API/meetings" | jq .

echo "== attach slides =="
echo "slide text" > /tmp/slide1.txt
curl -sS -X POST "$API/meetings/$MID/attach-slides" -F "file=@/tmp/slide1.txt" | jq .

echo "== list slides (presigned GET) =="
SLIDES=$(curl -sS "$API/meetings/$MID/slides")
echo "$SLIDES" | jq .
DL=$(jq -r '.[0].url' <<<"$SLIDES")
[[ -n "$DL" && "$DL" != "null" ]] || { echo "No presigned GET url"; exit 1; }

echo "== GET presigned download headers =="
curl -sS -D - -o /dev/null "$DL" | grep -i '^Content-Type:' || true

echo "== process meeting =="
curl -sS -X POST "$API/meetings/$MID/process" | jq .

echo "== get meeting =="
curl -sS "$API/meetings/$MID" | jq .
echo "Smoke OK ✅ (MID=$MID)"
