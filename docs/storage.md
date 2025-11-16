# Storage Architecture – MinIO / S3

This document describes how Meeting Notes Assistant (MNA) uses object storage.

Current implementation:

- Local / self-hosted: MinIO
- Cloud: S3-compatible (can be swapped in via configuration)
- Accessed via `app.storage` abstraction in the backend.

---

## 1. Buckets and usage

> Adjust bucket names if your configuration uses different ones.

Recommended structure:

- `mna-raw`
  - Raw input files, such as uploaded audio or slide decks.
- `mna-processed`
  - Transcripts, OCR results, intermediate artifacts.
- `mna-exports`
  - Final summaries, PDFs, and documents exported to other tools.
- `mna-backups`
  - Database dumps and other backup artifacts.

You may choose to collapse these into fewer buckets (e.g., `mna-data`, `mna-backups`) depending on your environment.

For each bucket:

| Bucket         | Contents                         | Retention (recommended)              |
|----------------|----------------------------------|--------------------------------------|
| `mna-raw`      | Original uploads                 | 30–90 days                           |
| `mna-processed`| Transcripts / OCR outputs        | 6–12 months or as needed             |
| `mna-exports`  | Final user documents             | Long term (until user deletes)       |
| `mna-backups`  | DB and config backups            | 7 daily + 4 weekly + 1 monthly, etc. |

Document the **actual** retention you choose below:

- Raw uploads:
- Processed artifacts:
- Exports:
- Backups:

---

## 2. Access and endpoints

MinIO is typically exposed as:

- API endpoint (local): `http://127.0.0.1:9000` or similar.
- API endpoint (behind Traefik, local): `https://minio.mna.local`
- Console (if enabled): `https://console.minio.mna.local`

The backend uses:

- `S3_ENDPOINT` / `S3_PUBLIC_ENDPOINT`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_BUCKET_*` (per bucket) – names depending on your config

These are usually supplied via environment variables in the compose files.

---

## 3. Health checks

The storage abstraction exposes:

- `storage.health_check()`

This method should:

1. List a dedicated health bucket or prefix **or**
2. Perform a tiny put+get+delete for a “health” object (e.g., `healthcheck.txt` in `mna-raw` or a dedicated bucket).

If `health_check()` fails, the API `/healthz` endpoint should report:

- `checks.storage = "error: ..."`
- `status = "degraded"` or a non-200 HTTP status

This allows CI and ops to detect storage outages without relying on application errors.

---

## 4. Backups

### 4.1 Database backups to object store (recommended)

Use a script/job to:

1. Run `pg_dump` against the Postgres instance.
2. Compress the dump (e.g., gzip).
3. Upload to the `mna-backups` bucket with a timestamped key.

Example key format:

- `db/meetings-{YYYYMMDDTHHMMSSZ}.sql.gz`

### 4.2 Backup retention

Define a policy for the `mna-backups` bucket, for example:

- Keep last **7 daily** backups.
- Keep last **4 weekly** backups.
- Optionally keep **1 monthly** backup for longer.

If your object store supports lifecycle rules (S3/MinIO), configure them accordingly and document the rules here.

---

## 5. Operational notes

### 5.1 When storage is down

Symptoms:

- `/healthz` shows `storage` as `error`.
- Uploads or downloads fail.

Actions:

1. Check MinIO container status and logs (see runbook).
2. Verify MinIO console/API are reachable.
3. Avoid deleting or reinitializing buckets until data safety is confirmed.
4. Escalate to infra/DevOps if data loss is suspected.

### 5.2 Migrating to a different S3 provider

- Update endpoint and credentials (`S3_ENDPOINT`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`).
- Ensure buckets exist with the expected names.
- Run `storage.health_check()` and basic upload/download tests.
- If migrating existing data, perform a one-off migration and verify object counts and samples.

---

## 6. Future improvements (optional)

- Enable server-side encryption of buckets.
- Configure lifecycle rules for automatic archiving/deletion.
- Add more fine-grained buckets (e.g., per tenant) if multi-tenant support is added.
