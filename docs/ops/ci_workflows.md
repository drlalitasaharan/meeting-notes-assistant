# CI workflow index

This document summarizes the repository CI checks and what each one protects.

## Prodready Compose Config

Workflow file:

- `.github/workflows/prodready-compose-config.yml`

Purpose:

- Validates that `docker-compose.prodready.yml` renders correctly.
- Protects the prod-ready Docker Compose defaults from accidental regression.

Runs on:

- Pull requests that change `docker-compose.prodready.yml` or the workflow file.
- Pushes to `main` that change `docker-compose.prodready.yml` or the workflow file.

Protects:

- Postgres image remains `postgres:16-alpine`.
- Default database credentials remain aligned with the validated local/prodready setup.
- Backend `DATABASE_URL` remains aligned with the DB credentials.
- Backend healthcheck remains strict and checks `/healthz` JSON status.
- Older weaker defaults are rejected.

## Prodready Healthz Smoke Test

Workflow file:

- `.github/workflows/prodready-healthz-smoke-test.yml`

Purpose:

- Starts the prod-ready Docker Compose stack in GitHub Actions.
- Verifies that the backend runtime health contract works, not only that the compose file renders.

Runs on:

- Pull requests that change backend code, worker code, `docker-compose.prodready.yml`, or the workflow file.
- Pushes to `main` that change backend code, worker code, `docker-compose.prodready.yml`, or the workflow file.

Protects:

- Postgres, Redis, and MinIO can start as prod-ready dependencies.
- Backend can build and start.
- Backend Docker healthcheck becomes healthy.
- `/healthz` returns top-level `status: ok`.
- DB, Redis, and storage checks all return `status: ok`.

## Operational note

The config guard catches static compose regressions quickly.

The healthz smoke test catches runtime regressions where the backend process starts but dependencies or health semantics are broken.

Together, these checks protect the prod-ready baseline needed before external demos and pilot usage.
