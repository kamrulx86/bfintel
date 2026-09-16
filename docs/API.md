# API (Phase 1)

Base: `/api`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/setup/status` | Setup required / Wazuh configured |
| POST | `/setup/admin` | First admin (once) |
| POST | `/setup/wazuh/test` | Test Wazuh credentials |
| POST | `/setup/wazuh` | Save connection (auth) |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Current user |
| GET | `/health` | DB/Redis/backend health |

OpenAPI: `/api/docs`
