from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attack_session import AttackSession
from app.models.intel_provider_result import IntelProviderResult
from app.models.normalized_event import NormalizedEvent
from app.models.source_ip_intel import SourceIpIntel
from app.schemas.intelligence import AttackSessionOut
from app.schemas.intel import GeoIntelOut, ProviderSnapshot
from app.schemas.investigation import IpInvestigationProfile, TimelineEventOut, TimelineResponse
from app.services.ip_utils import classify_ip_scope
from app.services.risk_explain import explain_attack_session


def get_ip_profile(db: Session, organization_id: UUID, source_ip: str) -> IpInvestigationProfile | None:
    has_events = db.scalar(
        select(func.count())
        .select_from(NormalizedEvent)
        .where(NormalizedEvent.organization_id == organization_id, NormalizedEvent.source_ip == source_ip)
    )
    has_sessions = db.scalar(
        select(func.count())
        .select_from(AttackSession)
        .where(AttackSession.organization_id == organization_id, AttackSession.source_ip == source_ip)
    )
    if not has_events and not has_sessions:
        return None

    first_seen = db.scalar(
        select(func.min(NormalizedEvent.timestamp)).where(
            NormalizedEvent.organization_id == organization_id, NormalizedEvent.source_ip == source_ip
        )
    )
    last_seen = db.scalar(
        select(func.max(NormalizedEvent.timestamp)).where(
            NormalizedEvent.organization_id == organization_id, NormalizedEvent.source_ip == source_ip
        )
    )

    total_events = int(has_events or 0)
    failure_count = db.scalar(
        select(func.count())
        .select_from(NormalizedEvent)
        .where(
            NormalizedEvent.organization_id == organization_id,
            NormalizedEvent.source_ip == source_ip,
            NormalizedEvent.authentication_result == "failure",
        )
    ) or 0
    success_count = db.scalar(
        select(func.count())
        .select_from(NormalizedEvent)
        .where(
            NormalizedEvent.organization_id == organization_id,
            NormalizedEvent.source_ip == source_ip,
            NormalizedEvent.authentication_result == "success",
        )
    ) or 0

    sessions = db.scalars(
        select(AttackSession)
        .where(AttackSession.organization_id == organization_id, AttackSession.source_ip == source_ip)
        .order_by(AttackSession.last_seen.desc())
    ).all()

    target_hosts: list[str] = []
    services: list[str] = []
    usernames: list[str] = []
    max_score = 0
    max_level = "low"
    level_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    reasons: list[str] = []

    for s in sessions:
        for h in s.target_hosts or []:
            if h not in target_hosts:
                target_hosts.append(h)
        for svc in s.services or []:
            if svc not in services:
                services.append(svc)
        for u in s.usernames or []:
            if u not in usernames:
                usernames.append(u)
        if s.risk_score > max_score:
            max_score = s.risk_score
        if level_rank.get(s.risk_level, 0) > level_rank.get(max_level, 0):
            max_level = s.risk_level
        for r in explain_attack_session(s):
            if r not in reasons:
                reasons.append(r)

    geo_row = db.scalar(
        select(SourceIpIntel).where(
            SourceIpIntel.organization_id == organization_id,
            SourceIpIntel.source_ip == source_ip,
        )
    )
    geo = GeoIntelOut.model_validate(geo_row) if geo_row else None

    provider_rows = db.scalars(
        select(IntelProviderResult)
        .where(
            IntelProviderResult.organization_id == organization_id,
            IntelProviderResult.source_ip == source_ip,
        )
        .order_by(IntelProviderResult.fetched_at.desc())
        .limit(10)
    ).all()
    threat_intel = [
        ProviderSnapshot(
            provider=r.provider,
            success=r.success,
            fetched_at=r.fetched_at,
            data=r.data or {},
            error=r.error_message,
        )
        for r in provider_rows
    ]
    for snap in threat_intel:
        if snap.provider == "abuseipdb" and snap.success:
            score = snap.data.get("abuse_confidence_score")
            if score is not None and int(score) >= 25:
                msg = f"+ AbuseIPDB community score {score} (third-party reports)"
                if msg not in reasons:
                    reasons.append(msg)
        if snap.provider == "ip-api" and snap.success and snap.data.get("hosting"):
            msg = "+ Network classified as hosting/datacenter (ip-api)"
            if msg not in reasons:
                reasons.append(msg)

    scope = geo_row.network_scope if geo_row and geo_row.network_scope else classify_ip_scope(source_ip)

    return IpInvestigationProfile(
        source_ip=source_ip,
        network_scope=scope,
        first_seen=first_seen,
        last_seen=last_seen,
        total_events=total_events,
        failure_count=int(failure_count),
        success_count=int(success_count),
        session_count=len(sessions),
        max_risk_score=max_score,
        max_risk_level=max_level,
        target_hosts=target_hosts,
        services=services,
        usernames=usernames,
        risk_reasons=reasons[:12],
        sessions=[AttackSessionOut.model_validate(s) for s in sessions],
        geo=geo,
        threat_intel=threat_intel,
        geo_placeholder=geo is None,
    )


def get_ip_timeline(
    db: Session,
    organization_id: UUID,
    source_ip: str,
    *,
    hours: int = 168,
    limit: int = 100,
    offset: int = 0,
) -> TimelineResponse:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    filters = [
        NormalizedEvent.organization_id == organization_id,
        NormalizedEvent.source_ip == source_ip,
        NormalizedEvent.timestamp >= since,
    ]
    total = db.scalar(select(func.count()).select_from(NormalizedEvent).where(*filters)) or 0
    rows = db.scalars(
        select(NormalizedEvent).where(*filters).order_by(NormalizedEvent.timestamp.desc()).offset(offset).limit(limit)
    ).all()
    return TimelineResponse(
        items=[TimelineEventOut.model_validate(r) for r in rows],
        total=int(total),
    )
