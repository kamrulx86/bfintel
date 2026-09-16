# Security

- Wazuh credentials encrypted at rest (Fernet + `FERNET_KEY`).
- Passwords hashed with Argon2id.
- Secrets never returned by API; not logged.
- RBAC roles: admin, analyst, viewer (Phase 1: admin).
- Audit log for setup, auth, Wazuh config changes.
- SSRF: Wazuh URLs validated; no arbitrary URL fetch from user input beyond configured connectors.
- **Rate limiting** (in-memory, per instance): stricter on `/api/auth/login` and `/api/setup/*`; general cap on `/api/*`. Tune via `BF_LOGIN_RATE_LIMIT`, `BF_API_RATE_LIMIT`, `BF_RATE_LIMIT_ENABLED`.
- **Security headers** on API responses and nginx (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, API `Cache-Control: no-store`).
- **Production**: set `BFINTEL_ENV=production` or `BF_DISABLE_API_DOCS=true` to hide OpenAPI/Swagger; terminate TLS at nginx or a reverse proxy; set `BF_TRUST_PROXY_HEADERS=true` only behind a trusted proxy.
- **Backups**: see [BACKUP.md](BACKUP.md).
