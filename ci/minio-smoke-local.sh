#!/usr/bin/env bash
set -euo pipefail

echo "== MinIO HTTPS smoke (local) =="

# --- Find mkcert root CA (macOS friendly) ---
ROOT="$(mkcert -CAROOT 2>/dev/null || true)"
if [[ -n "${ROOT}" && -r "${ROOT}/rootCA.pem" ]]; then
  ROOT="${ROOT}/rootCA.pem"
elif [[ -r "${HOME}/Library/Application Support/mkcert/rootCA.pem" ]]; then
  ROOT="${HOME}/Library/Application Support/mkcert/rootCA.pem"
elif [[ -r "${HOME}/.local/share/mkcert/rootCA.pem" ]]; then
  ROOT="${HOME}/.local/share/mkcert/rootCA.pem"
else
  echo "ERROR: mkcert root CA not found. Install mkcert (brew install mkcert) or set SSL_CERT_FILE." >&2
  exit 1
fi
export SSL_CERT_FILE="$ROOT"
export REQUESTS_CA_BUNDLE="$ROOT"

# --- Quick visibility of Traefik port binding ---
docker ps --filter name=meeting-notes-assistant-traefik-1 \
  --format 'table {{.Names}}\t{{.Ports}}' || true
echo

# --- Verify hosts are resolvable (macOS /etc/hosts entries) ---
for H in minio.mna.local console.minio.mna.local; do
  if ! grep -q "^[[:space:]]*127\.0\.0\.1[[:space:]]\+$H" /etc/hosts; then
    echo "WARNING: $H not found in /etc/hosts (TLS DNS-SNI may fail)." >&2
  fi
done

# --- MinIO API health (expects 200) ---
echo "[1/2] MinIO API /minio/health/ready (HTTPS)"
code=$(curl --retry 20 --retry-all-errors --retry-delay 2 \
  --cacert "$ROOT" -sS -w "%{http_code}" \
  https://minio.mna.local/minio/health/ready -o /dev/null)
echo "HTTP $code"
if [[ "$code" != "200" ]]; then
  echo "ERROR: MinIO API not healthy (expected 200)." >&2
  # brief hints
  echo "Hints: check Traefik logs and router wiring" >&2
  docker logs --since=2m meeting-notes-assistant-traefik-1 | tail -n +1 | sed 's/^/[traefik] /' >&2 || true
  exit 2
fi
echo

# --- MinIO Console landing (200/302 + HSTS header shown) ---
echo "[2/2] MinIO Console / (HTTPS + HSTS)"
curl --retry 10 --retry-all-errors --retry-delay 2 \
  --cacert "$ROOT" -sS -I https://console.minio.mna.local/ \
  | sed -n '1p;/^strict-transport-security:/Ip'

echo
echo "✅ MinIO HTTPS smoke finished."
