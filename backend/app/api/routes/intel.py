from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.intel_config import get_intel_settings
from app.models.intel_provider_result import IntelProviderResult
from app.models.user import Role
from app.schemas.intel import IntelProviderStatus, ProviderResultsOut, ProviderSnapshot
from app.services.enrichment import enrich_pending_ips, enrich_source_ip

router = APIRouter(prefix="/intel", tags=["intel"])


@router.get("/providers", response_model=list[IntelProviderStatus])
def provider_status(user: CurrentUser) -> list[IntelProviderStatus]:
    settings = get_intel_settings()
    return [
        IntelProviderStatus(
            name="ip-api",
            enabled=settings.ip_api_enabled,
            configured=True,
            description="GeoIP, ASN, ISP (ip-api.com)",
        ),
        IntelProviderStatus(
            name="abuseipdb",
            enabled=settings.abuseipdb_enabled,
            configured=bool(settings.abuseipdb_api_key),
            description="Community abuse reports (optional API key)",
        ),
    ]


@router.get("/{source_ip}/providers", response_model=ProviderResultsOut)
def provider_results(
    db: DbSession,
    user: CurrentUser,
    source_ip: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> ProviderResultsOut:
    rows = db.scalars(
        select(IntelProviderResult)
        .where(
            IntelProviderResult.organization_id == user.organization_id,
            IntelProviderResult.source_ip == source_ip.strip(),
        )
        .order_by(IntelProviderResult.fetched_at.desc())
        .limit(limit)
    ).all()
    return ProviderResultsOut(
        source_ip=source_ip,
        results=[
            ProviderSnapshot(
                provider=r.provider,
                success=r.success,
                fetched_at=r.fetched_at,
                data=r.data or {},
                error=r.error_message,
            )
            for r in rows
        ],
    )


@router.post("/enrich")
def run_enrichment(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=25, ge=1, le=100),
) -> dict:
    if user.role not in (Role.admin.value, Role.analyst.value):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    stats = enrich_pending_ips(db, user.organization_id, limit=limit)
    db.commit()
    return {"status": "ok", **stats}


@router.post("/{source_ip}/refresh")
def refresh_ip(db: DbSession, user: CurrentUser, source_ip: str) -> dict:
    if user.role not in (Role.admin.value, Role.analyst.value):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    status = enrich_source_ip(db, user.organization_id, source_ip.strip(), force=True)
    db.commit()
    return {"status": status}
