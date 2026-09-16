# Deployment

## Docker Compose (recommended)

```bash
cp .env.example .env
# Edit SECRET_KEY, FERNET_KEY, POSTGRES_PASSWORD
docker compose up -d --build
```

- UI: http://localhost:8080
- API: http://localhost:8000/api/docs

## Dev server (192.168.122.186)

- **BFIntel UI:** http://192.168.122.186:8888
- **Wazuh API (setup wizard):** `https://192.168.122.186:55000` — use your `wazuh-wui` API user (from Wazuh dashboard config), **verify TLS off** for default certs.
- Indexer from Docker may require `https://192.168.122.186:9200` or host-specific URL; test via **[Test Connection]** in wizard.

Indexer on same host is often `https://127.0.0.1:9200` from Wazuh host only — from Docker use host gateway or expose indexer carefully.

## Production checklist

- [ ] `BFINTEL_ENV=production` (disables public API docs)
- [ ] Strong `SECRET_KEY`, `FERNET_KEY`, `POSTGRES_PASSWORD`
- [ ] TLS in front of nginx (443 → proxy to `BFINTEL_HTTP_PORT`)
- [ ] `BF_TRUST_PROXY_HEADERS=true` when using a reverse proxy (for rate limits + audit IP)
- [ ] `SESSION_COOKIE_SECURE=true` if using cookie-based sessions later
- [ ] Restrict host firewall: only admin networks to UI/API ports
- [ ] Scheduled Postgres backups — [BACKUP.md](BACKUP.md)
- [ ] Set `BF_ABUSE_REPORTER_*` and notification channel secrets via UI

## GitHub

Push `WEB-EDGE` repo; clone on any VPS; configure `.env`; `docker compose up -d --build`.

CI runs `ruff` + `pytest` + frontend build on push (`.github/workflows/ci.yml`).
