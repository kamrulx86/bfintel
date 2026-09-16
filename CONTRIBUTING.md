# Contributing

1. Phased delivery — see product spec (Phases 1–8).
2. Run backend tests: `cd backend && pytest`
3. Run ruff: `ruff check backend`
4. Migrations: `alembic revision --autogenerate` / `alembic upgrade head`
5. No secrets in commits.
