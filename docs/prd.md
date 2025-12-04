# PRD: Meeting Notes Assistant MVP

## Overview
Automate meeting note-taking: ingest audio/video + slides, transcribe, summarize (decisions, actions, owners), push to Slack/Notion, and keep a searchable history.

## MVP Scope
- Upload/ingest recording (<2 hrs)
- Transcription (with diarization if provider supports)
- LLM summary to structured JSON
- Slides OCR (PDF/images)
- Integrations: Slack + Notion (basic)
- Searchable history (to be completed post-MVP with embeddings)
- Guardrails: consent banner, retention (30/90 days)

## Acceptance Criteria
- <10 min processing for a 1-hr meeting
- ≥90% explicit action items captured with owners
- Slides OCR searchable
- Slack/Notion push succeeds

## feat/prod-ready-100pc (merged 2025-12-03)

- Locked in `/metrics-prom` as the Prometheus metrics endpoint and documented how to curl it.
- Added `docs/production-deploy.md` with a concrete Docker Compose deployment recipe and first-boot smoke tests.
- Added `docs/backups.md` with a Postgres + MinIO backup/restore runbook tailored to `DB_USER=mna`, `DB_NAME=meetings`.
- Added `docs/security.md` with a pragmatic security and hardening checklist.
- Confirmed local health + metrics:
  - `curl -f http://localhost:8000/healthz`
  - `curl -s http://localhost:8000/metrics-prom | head`
- Took a real logical backup of the `meetings` database using `pg_dump` and checked the `.sql` file into `backups/postgres/`.

## `feat/obs-golden-flow-dashboard` (merged 2025-12-04)
  - Added Grafana “MNA – Golden Flow” dashboard JSON (`docs/grafana/mna-golden-flow.json`)
    to visualize the Real MVP path (HTTP traffic, latency, RQ job throughput, queue depth,
    backlog proxy, and service health).
  - Added `docs/grafana.md` with import instructions and panel-by-panel guidance for
    debugging “Real MVP is slow”, “jobs are stuck”, and “lots of 5xx errors”.
  - Added Prometheus alert rules (`prometheus/alerts.yml`) and local Prometheus config
    (`prometheus/prometheus.yml` + `docker-compose.prometheus.yml`), validated via
    `promtool check rules` inside the container.
  - Extended `docs/observability.md` with an “Alerts and runbooks” section documenting
    where rules live and first-response steps for API errors/latency, RQ job failures/backlog,
    and worker down situations.
