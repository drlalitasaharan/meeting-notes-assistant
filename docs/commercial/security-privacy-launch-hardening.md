# Security and privacy launch hardening

## Scope

This hardening pass adds launch-safe security and privacy improvements without
changing billing behavior, upload limits, authentication policy, storage
architecture, or processing behavior.

## Included

- Added conservative backend HTTP security headers.
- Limited backend CORS methods and headers to the methods/headers used by the app.
- Avoided browser caching for authenticated frontend API helper requests.
- Clarified privacy-page language around security practices and user controls.
- Clarified retention-page language around logs, backups, support metadata, and
  deleted meeting copies.

## Not included

- No database migration.
- No billing or free-trial logic change.
- No storage provider change.
- No authentication model change.
- No account deletion automation.

## Validation notes

The full local pytest suite currently has known unrelated backend failures from
legacy test-auth expectations and `_save_raw_media_stub` E2E test assumptions.
