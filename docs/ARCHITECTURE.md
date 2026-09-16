# BFIntel Architecture

## Layers

| Layer | Responsibility |
|-------|----------------|
| Frontend | React/Vite UI, setup wizard, SOC dashboards |
| API | FastAPI REST, auth, RBAC, OpenAPI |
| Workers | Celery — polling, normalization, correlation, enrichment |
| Integrations | Wazuh connectors, threat-intel providers (Phase 4+) |
| Data | PostgreSQL system of record, Redis cache/queue |

Wazuh remains the detection/SIEM source. BFIntel does not replace it.

## Key abstractions

- `WazuhConnector` — API / indexer / webhook implementations
- `GeoIPProvider`, `ThreatIntelProvider`, … — enrichment (Phase 4)
- `AttackSession` — correlated brute-force unit (Phase 2)

## Multi-tenant readiness

`organization_id` on users, connections, and future entities.

## Repository layout

See `/frontend`, `/backend`, `/infrastructure`, `/docs`, `/tests`.
