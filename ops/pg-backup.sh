#!/usr/bin/env bash
set -euo pipefail

PGURL="${PGURL:-postgresql://app:app@db:5432/appdb}"
STAMP=$(date +"%Y-%m-%d_%H-%M-%S")
OUT="/backups/appdb_${STAMP}.dump"

mkdir -p /backups
# -F c = custom format; -Z 9 = max compression
pg_dump -F c -Z 9 "$PGURL" -f "$OUT"

# keep last 30 backups (BSD/macOS-safe: no -r)
TO_DELETE="$(ls -1t /backups/appdb_*.dump 2>/dev/null | tail -n +31 || true)"
if [ -n "${TO_DELETE}" ]; then
  echo "${TO_DELETE}" | xargs rm -f
fi

echo "Wrote: $OUT"

