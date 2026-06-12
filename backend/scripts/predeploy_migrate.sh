#!/usr/bin/env bash
set -euo pipefail

echo "=== MeetIQ pre-deploy migration started ==="

cd "$(dirname "$0")/.."

echo "Current directory:"
pwd

echo "Checking Alembic config..."
test -f alembic.ini

echo "Running Alembic migrations..."
python -m alembic -c alembic.ini upgrade head

echo "Confirming Alembic current revision..."
python -m alembic -c alembic.ini current

echo "=== MeetIQ pre-deploy migration completed successfully ==="
