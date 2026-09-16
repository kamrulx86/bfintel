from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.intel_config import get_intel_settings
from app.integrations.intel.abuseipdb import AbuseIpDbProvider
from app.integrations.intel.ip_api import IpApiProvider
from app.models.attack_session import AttackSession
from app.models.intel_provider_result import IntelProviderResult
from app.models.source_ip_intel import SourceIpIntel
from app.services.ip_utils import classify_ip_scope


def _needs_refresh(intel: SourceIpIntel | None, ttl_hours: int) -> bool:
    if intel is None:
        return True
    if intel.enrichment_status == "private":
        return False
    if not intel.last_enriched_at:
        return True
    return intel.last_enriched_at < datetime.now(timezone.utc) - timedelta(hours=ttl_hours)


def _save_provider_result(db: Session, org_id: UUID, ip: str, result) -> None:
    db.add(
        IntelProviderResult(
            organization_id=org_id,
            source_ip=ip,
            provider=result.provider,
            success=result.success,
            data=result.data if result.success else None,
            error_message=result.error,
        )
    )


def enrich_source_ip(db: Session, organization_id: UUID, source_ip: str, *, force: bool = False) -> str:
    settings = get_intel_settings()
    scope = classify_ip_scope(source_ip)

    intel = db.scalar(
        select(SourceIpIntel).where(
            SourceIpIntel.organization_id == organization_id,
            SourceIpIntel.source_ip == source_ip,
        )
    )
    if not force and not _needs_refresh(intel, settings.enrichment_ttl_hours):
        return "cached"

    if intel is None:
        intel = SourceIpIntel(organization_id=organization_id, source_ip=source_ip)
        db.add(intel)
        db.flush()

    intel.network_scope = scope
    if scope != "public":
        intel.enrichment_status = "private"
        intel.country_name = "Private / non-routable"
        intel.last_enriched_at = datetime.now(timezone.utc)
        return "private"

    geo = IpApiProvider(settings).lookup(source_ip)
    _save_provider_result(db, organization_id, source_ip, geo)
    if geo.success:
        d = geo.data
        intel.country_code = d.get("country_code")
        intel.country_name = d.get("country_name")
        intel.region = d.get("region")
        intel.city = d.get("city")
        intel.latitude = d.get("latitude")
        intel.longitude = d.get("longitude")
        intel.asn = d.get("asn")
        intel.isp = d.get("isp")
        intel.organization_name = d.get("organization")
        intel.reverse_dns = d.get("reverse_dns")
        intel.is_hosting = d.get("hosting")
        intel.enrichment_status = "ok"
    else:
        intel.enrichment_status = "geo_failed"

    abuse = AbuseIpDbProvider(settings).lookup(source_ip)
    _save_provider_result(db, organization_id, source_ip, abuse)
    if abuse.success:
        score = abuse.data.get("abuse_confidence_score") or 0
        _apply_abuse_risk_boost(db, organization_id, source_ip, int(score))

    intel.last_enriched_at = datetime.now(timezone.utc)
    if intel.enrichment_status != "ok" and abuse.success:
        intel.enrichment_status = "partial"
    return intel.enrichment_status


def _apply_abuse_risk_boost(db: Session, organization_id: UUID, source_ip: str, abuse_score: int) -> None:
    if abuse_score < 25:
        return
    bump = 10 if abuse_score < 50 else 15 if abuse_score < 75 else 20
    sessions = db.scalars(
        select(AttackSession).where(
            AttackSession.organization_id == organization_id,
            AttackSession.source_ip == source_ip,
        )
    ).all()
    for session in sessions:
        session.risk_score = min(100, session.risk_score + bump)
        if session.risk_score >= 80:
            session.risk_level = "critical"
        elif session.risk_score >= 60:
            session.risk_level = "high"
        elif session.risk_score >= 30:
            session.risk_level = "medium"


def enrich_pending_ips(db: Session, organization_id: UUID, limit: int = 25) -> dict[str, int]:
    settings = get_intel_settings()
    stale_before = datetime.now(timezone.utc) - timedelta(hours=settings.enrichment_ttl_hours)

    ips = db.scalars(
        select(AttackSession.source_ip)
        .where(AttackSession.organization_id == organization_id)
        .distinct()
        .limit(limit * 3)
    ).all()

    stats = {"processed": 0, "enriched": 0, "skipped": 0, "errors": 0}
    for ip in ips:
        if stats["processed"] >= limit:
            break
        stats["processed"] += 1
        intel = db.scalar(
            select(SourceIpIntel).where(SourceIpIntel.organization_id == organization_id, SourceIpIntel.source_ip == ip)
        )
        if intel and intel.last_enriched_at and intel.last_enriched_at > stale_before:
            stats["skipped"] += 1
            continue
        try:
            status = enrich_source_ip(db, organization_id, ip)
            if status in ("cached", "skipped"):
                stats["skipped"] += 1
            else:
                stats["enriched"] += 1
        except Exception:  # noqa: BLE001
            stats["errors"] += 1
    return stats
