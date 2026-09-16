from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import get_settings
from app.core.intel_config import get_intel_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health(db: DbSession) -> dict:
    settings = get_settings()
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False

    redis_ok = False
    try:
        import redis

        r = redis.from_url(settings.redis_url)
        redis_ok = bool(r.ping())
    except Exception:  # noqa: BLE001
        redis_ok = False

    intel = get_intel_settings()
    return {
        "status": "healthy" if db_ok else "degraded",
        "components": {
            "database": "healthy" if db_ok else "unhealthy",
            "redis": "healthy" if redis_ok else "unhealthy",
            "backend": "healthy",
            "intel_ip_api": "enabled" if intel.ip_api_enabled else "disabled",
            "intel_abuseipdb": "configured" if intel.abuseipdb_api_key else "not_configured",
        },
    }
