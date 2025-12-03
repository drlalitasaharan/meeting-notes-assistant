# Backups & restore

This document describes how to back up and restore the two stateful parts of
Meeting Notes Assistant:

- **Postgres** – meetings, notes, and metadata.
- **MinIO** – uploaded media (e.g., MP4s) and derived artefacts.

Examples below assume Docker Compose via `./bin/dc` in this repo and the
default dev/prod-like configuration where:

- `DB_USER = mna`
- `DB_NAME = meetings`
- Postgres host is `db` on the Docker network.

Adjust names as needed if your environment differs.

---

## Postgres backups

We use `pg_dump` from inside the `db` container to create logical backups.

### Ad-hoc backup (manual)

Run this from the repo root:

```bash
DB_USER=mna
DB_NAME=meetings

mkdir -p backups/postgres

./bin/dc exec db pg_dump \
  -U "$DB_USER" \
  "$DB_NAME" \
  > "backups/postgres/${DB_NAME}-$(date +%Y%m%d-%H%M%S).sql"

ls -lh backups/postgres
