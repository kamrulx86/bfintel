from fastapi import APIRouter

from app.api.routes import (
    abuse_reports,
    allowlist,
    attacks,
    audit,
    auth,
    blocklist,
    cases,
    dashboard,
    health,
    ingestion,
    intel,
    ip_intelligence,
    notifications,
    rules,
    search,
    setup,
    sources,
    watchlist,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(setup.router)
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(attacks.router)
api_router.include_router(sources.router)
api_router.include_router(ingestion.router)
api_router.include_router(ip_intelligence.router)
api_router.include_router(search.router)
api_router.include_router(intel.router)
api_router.include_router(notifications.router)
api_router.include_router(rules.router)
api_router.include_router(cases.router)
api_router.include_router(watchlist.router)
api_router.include_router(allowlist.router)
api_router.include_router(blocklist.router)
api_router.include_router(audit.router)
api_router.include_router(abuse_reports.router)
