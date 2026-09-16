from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.attack_session import AttackSession
from app.models.source_ip_intel import SourceIpIntel
from app.schemas.intelligence import SourceIntelOut, SourceListResponse

router = APIRouter(prefix="/sources", tags=["sources"])

_LEVEL_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _level_at_least(level: str, minimum: str) -> bool:
    return _LEVEL_RANK.get(level, 0) >= _LEVEL_RANK.get(minimum, 0)


@router.get("", response_model=SourceListResponse)
def list_sources(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    hours: int | None = Query(default=None, ge=1, le=720),
    risk_level: str | None = Query(default=None),
    service: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=64),
    country: str | None = Query(default=None, max_length=64),
) -> SourceListResponse:
    org_id = user.organization_id
    session_filters = [AttackSession.organization_id == org_id]
    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        session_filters.append(AttackSession.last_seen >= since)
    if q:
        session_filters.append(AttackSession.source_ip.ilike(f"%{q.strip()}%"))
    if service:
        session_filters.append(AttackSession.services.any(service))

    grouped = (
        select(
            AttackSession.source_ip.label("source_ip"),
            func.count(AttackSession.id).label("session_count"),
            func.sum(AttackSession.attempt_count).label("total_attempts"),
            func.max(AttackSession.risk_score).label("max_risk_score"),
            func.max(AttackSession.last_seen).label("last_seen"),
        )
        .where(*session_filters)
        .group_by(AttackSession.source_ip)
        .subquery()
    )

    total = db.scalar(select(func.count()).select_from(grouped)) or 0
    rows = db.execute(
        select(grouped).order_by(grouped.c.max_risk_score.desc(), grouped.c.last_seen.desc()).offset(offset).limit(limit)
    ).all()

    ip_list = [row.source_ip for row in rows]
    intel_rows = db.scalars(
        select(SourceIpIntel).where(
            SourceIpIntel.organization_id == org_id,
            SourceIpIntel.source_ip.in_(ip_list),
        )
    ).all() if ip_list else []
    intel_by_ip = {i.source_ip: i for i in intel_rows}

    items: list[SourceIntelOut] = []
    for row in rows:
        sessions = db.scalars(
            select(AttackSession)
            .where(AttackSession.organization_id == org_id, AttackSession.source_ip == row.source_ip)
            .order_by(AttackSession.risk_score.desc())
            .limit(5)
        ).all()
        services: list[str] = []
        max_level = "low"
        for s in sessions:
            for svc in s.services or []:
                if svc not in services:
                    services.append(svc)
            if _LEVEL_RANK.get(s.risk_level, 0) > _LEVEL_RANK.get(max_level, 0):
                max_level = s.risk_level

        if risk_level and not _level_at_least(max_level, risk_level):
            continue

        intel = intel_by_ip.get(row.source_ip)
        if country:
            c = (intel.country_name if intel else None) or ""
            cc = (intel.country_code if intel else None) or ""
            if country.lower() not in c.lower() and country.lower() not in cc.lower():
                continue

        items.append(
            SourceIntelOut(
                source_ip=row.source_ip,
                session_count=int(row.session_count),
                total_attempts=int(row.total_attempts or 0),
                max_risk_score=int(row.max_risk_score or 0),
                max_risk_level=max_level,
                last_seen=row.last_seen
                if isinstance(row.last_seen, datetime)
                else (sessions[0].last_seen if sessions else datetime.min.replace(tzinfo=timezone.utc)),
                services=services,
                country_code=intel.country_code if intel else None,
                country_name=intel.country_name if intel else None,
                asn=intel.asn if intel else None,
                isp=intel.isp if intel else None,
            )
        )

    if risk_level:
        total = len(items)

    return SourceListResponse(items=items, total=total)
