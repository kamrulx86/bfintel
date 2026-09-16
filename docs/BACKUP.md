# Backup and restore

BFIntel state lives in **PostgreSQL** (cases, intel, rules, audit) and **`.env`** (secrets). Wazuh alerts are read from the host path configured as `WAZUH_ALERTS_HOST_DIR` — back up Wazuh separately.

## PostgreSQL (Docker Compose)

```bash
# On the host where compose runs
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "bfintel-$(date +%F).sql.gz"
```

Restore into a fresh volume (destructive — stop app first):

```bash
docker compose stop backend worker beat
gunzip -c bfintel-YYYY-MM-DD.sql.gz | docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose up -d backend worker beat
```

## Environment secrets

- Copy `.env` to a **password manager** or encrypted backup store — never commit it.
- After restore, confirm `DATABASE_URL`, `FERNET_KEY`, and `SECRET_KEY` match the backup era or re-enter Wazuh/notification credentials in the UI.

## Redis

Ephemeral (Celery broker). No backup required for BFIntel MVP.

## Lab disk hygiene

On Wazuh co-located hosts, monitor `/var/ossec/queue/vd_updater/tmp` and root filesystem — full disks break Postgres and ingestion.
