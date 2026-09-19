# Deployment

## Docker Compose (recommended)

```bash
cp .env.example .env
# Edit SECRET_KEY, FERNET_KEY, POSTGRES_PASSWORD
docker compose up -d --build
```

- UI: http://localhost:8080 (or `BFINTEL_HTTP_PORT` from `.env`)
- API: http://localhost:8000/api/health

## Remote / lab host

1. Clone the repo on the target server (e.g. `~/bfintel`).
2. Configure `.env` (never commit it).
3. On a **co-located Wazuh manager**, mount alerts for ingest:

   `WAZUH_ALERTS_HOST_DIR=/var/ossec/logs/alerts`

4. Run `docker compose up -d --build`.
5. Complete the setup wizard (admin + Wazuh API URL, typically `https://<manager>:55000`, TLS verify off for default certs).

On first Wazuh connection, BFIntel **backfills** `alerts.json` and enriches source IPs so the dashboard is populated immediately.

If BFIntel runs in Docker on the same host as Wazuh, allow the compose bridge subnet to reach **55000** and **9200** on the host firewall (bridge CIDR varies; check `docker network inspect`).

### Sync from your workstation

```bash
export LAB_HOST=your.server.example
export LAB_USER=deploy
export SSH_PORT=22
export DEPLOY_COMPOSE=1
./scripts/deploy-lab.sh
```

Store admin credentials only in a local gitignored file (see `lab-setup.credentials.example`).

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

Clone on any VPS; configure `.env`; `docker compose up -d --build`.

CI runs `ruff` + `pytest` + frontend build on push (`.github/workflows/ci.yml`).
