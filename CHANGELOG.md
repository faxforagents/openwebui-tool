# Changelog

## 0.1.0 (2026-11-04)

Initial Open WebUI tool package.

- Add seven REST methods for preparing, quoting, sending and reading faxes.
- Read credentials from the current user's UserValves on every call.
- Require a quote ID for sending and reuse its idempotency key on retries.
- Add fake HTTP tests for account isolation and request behavior.
- Document browser installation, Community sharing and sandbox checks.
