from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.hardening_config import get_hardening_settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

settings = get_settings()
hardening = get_hardening_settings()
_docs = None if hardening.disable_api_docs or settings.bfintel_env == "production" else "/api/docs"
_openapi = None if hardening.disable_api_docs or settings.bfintel_env == "production" else "/api/openapi.json"

app = FastAPI(
    title="BFIntel API",
    description="Brute-force intelligence layer for Wazuh",
    version="0.1.0",
    docs_url=_docs,
    openapi_url=_openapi,
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
