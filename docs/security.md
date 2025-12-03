# Security & hardening checklist

This is a pragmatic checklist for running Meeting Notes Assistant in a
production-like environment. It is not a full security review, but covers the
basics that “future me” or a collaborator should verify.

Use the checkboxes to track what’s done.

---

## API authentication & access

- [ ] API requests require an API key (e.g., `X-API-Key`) for all non-health endpoints.
- [ ] API keys are **not** hard-coded in the repo or Docker files.
- [ ] API keys are stored in environment variables / a secrets manager.
- [ ] There is a simple process to rotate API keys (update env + restart).
- [ ] Rate limiting or basic WAF is in place in front of the API
      (Traefik, nginx, cloud LB, etc.) or on the hosting platform.

## Transport security (TLS)

- [ ] External access is only over HTTPS.
- [ ] TLS termination (e.g., Traefik) is configured with valid certificates
      (Let’s Encrypt or equivalent).
- [ ] HTTP is redirected to HTTPS.
- [ ] Internal service URLs (Postgres, Redis, MinIO) are not exposed directly
      to the internet.

## Network boundaries

- [ ] Only the reverse proxy / API ports (80/443) are exposed to the public.
- [ ] Postgres, Redis, and MinIO ports are bound to the Docker network or localhost only.
- [ ] `/metrics-prom` is reachable only from trusted networks
      (Prometheus, ops VPN, etc.).
- [ ] `/healthz` is either:
  - Protected behind auth, or
  - Returns minimal information suitable for public exposure.

## Secrets management

- [ ] There is **no** `.env` file with production secrets committed to Git.
- [ ] Secrets (DB password, MinIO keys, API keys) are stored in:
  - Environment variables, or
  - A secrets manager (AWS SSM, Vault, etc.).
- [ ] Secrets are not printed in logs (check log formats for URLs, headers, bodies).
- [ ] A rotation schedule exists for:
  - DB passwords.
  - MinIO access keys.
  - API keys.

## Resource limits & abuse resistance

- [ ] There is a maximum allowed upload size for meeting media (MP4, etc.).
- [ ] There are reasonable request timeouts on the API and any reverse proxy.
- [ ] Worker concurrency is configured so that a burst of large jobs cannot
      exhaust memory/CPU on the host.
- [ ] External dependencies (e.g., transcription/summarisation providers, if any)
      have rate limits or safeguards documented.

## Observability & incident response

- [ ] The “MNA – Golden Flow” Grafana dashboard is imported in prod.
- [ ] The Prometheus alerts in `prometheus/alerts.yml` are enabled and verified to fire.
- [ ] There is a clear “first steps” doc for when alerts fire
      (see `docs/observability.md` and `docs/backups.md`).

## Backups & data protection

- [ ] Postgres backup procedure from `docs/backups.md` has been executed at least once.
- [ ] MinIO backup procedure from `docs/backups.md` has been executed at least once.
- [ ] Restore from backup has been tested end-to-end:
  - DB restore.
  - MinIO restore.
  - Real MVP smoke test against restored data.
- [ ] Backup storage location is:
  - Encrypted at rest.
  - Access-controlled (not world-readable).

## Operational hygiene

- [ ] Logs are retained for a reasonable timeframe (e.g., 7–30 days) and are
      accessible for debugging incidents.
- [ ] There is an upgrade process documented in `docs/production-deploy.md`.
- [ ] There is a minimal access control model (who can deploy, who can read logs,
      who can see production metrics).

Anything unchecked here is either a TODO or a conscious risk. Update this file
as you tighten security over time.
