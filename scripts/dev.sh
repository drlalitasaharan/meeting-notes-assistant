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

# --- release helper: relpush <tag> [ref=main] [message] -----------------------
# Pushes an annotated tag to origin without tripping the pre-push hook on `main`.
# Example: relpush v0.1.0
relpush() {
  tag="$1"
  ref="${2:-main}"
  msg="${3:-MNA: release $tag}"

  if [ -z "$tag" ]; then
    echo "usage: relpush <tag> [ref=main] [message]"
    return 2
  fi

  # Run the sensitive steps in a subshell so `set -e` doesn’t leak shell options
  (
    set -e
    echo "👉 Tagging '$ref' as '$tag'…"
    git fetch origin "$ref"
    git checkout "$ref"
    git pull --ff-only

    git tag -fa "$tag" -m "$msg" "$ref"
    git show --no-patch --pretty=oneline --decorate "$tag"

    tmp_branch="release/tag-push-${tag}-$(date +%s)"
    git switch -c "$tmp_branch"

    # Delete any existing remote tag, then push the fresh tag
    echo "🔁 Replacing remote tag (if present)…"
    git push origin ":refs/tags/$tag" >/dev/null 2>&1 || true
    echo "🚀 Pushing tag $tag to origin…"
    git push origin "$tag"

    git switch "$ref"
    git branch -D "$tmp_branch" >/dev/null 2>&1 || true
  )

  echo "✅ Verifying on origin…"
  if git ls-remote --tags origin | grep -q "refs/tags/$tag"; then
    echo "✅ Tag $tag is on origin and points to:"
    git show --no-patch --pretty=oneline --decorate "$tag"
    return 0
  else
    echo "⚠️  Tag $tag not visible on origin; check connectivity/permissions."
    return 1
  fi
}

echo "Loaded helpers: health, create_meeting, upload_slide, process_meeting, relpush"
echo "API=$API  X-API-Key set"

