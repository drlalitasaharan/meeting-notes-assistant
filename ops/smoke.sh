#!/usr/bin/env bash
set -euo pipefail
KEY=$(docker compose exec -T api sh -lc 'printf "%s" "$API_KEY"')
curl -fsS http://127.0.0.1:8000/healthz >/dev/null
curl -fsS -H "X-API-KEY: $KEY" "http://127.0.0.1:8000/v1/meetings?limit=1" >/dev/null
echo "Smoke OK"
