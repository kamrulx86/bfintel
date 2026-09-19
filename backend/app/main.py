from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.hardening_config import get_hardening_settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.models.normalized_event import NormalizedEvent
from app.models.wazuh_connection import WazuhConnection
from app.services.ingest_alerts import ingest_initial_wazuh_logs

settings = get_settings()
hardening = get_hardening_settings()
_docs = None if hardening.disable_api_docs or settings.bfintel_env == "production" else "/api/docs"
_openapi = None if hardening.disable_api_docs or settings.bfintel_env == "production" else "/api/openapi.json"


def _bootstrap_wazuh_ingest_if_empty() -> None:
    db = SessionLocal()
    try:
        conn = db.scalar(select(WazuhConnection).where(WazuhConnection.is_active.is_(True)).limit(1))
        if not conn:
            return
        event_count = (
            db.scalar(
                select(func.count())
                .select_from(NormalizedEvent)
                .where(NormalizedEvent.organization_id == conn.organization_id)
            )
            or 0
        )
        if event_count > 0:
            return
        ingest_initial_wazuh_logs(db, conn.organization_id)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _bootstrap_wazuh_ingest_if_empty()
    yield


app = FastAPI(
    title="BFIntel API",
    description="Brute-force intelligence layer for Wazuh",
    version="0.1.0",
    docs_url=_docs,
    openapi_url=_openapi,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"product": "BFIntel", "status": "ok"}


app.include_router(api_router)
