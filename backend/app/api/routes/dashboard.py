from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.correlation_config import get_correlation_settings
from app.models.attack_session import AttackSession
from app.models.case import Case
from app.models.ingestion_state import IngestionState
from app.models.normalized_event import NormalizedEvent
from app.schemas.intelligence import DashboardMetrics
from app.schemas.investigation import DashboardCharts
from app.services.dashboard_agg import build_dashboard_charts

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def dashboard_metrics(db: DbSession, user: CurrentUser) -> DashboardMetrics:
    settings = get_correlation_settings()
    org_id = user.organization_id
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    active_attacks = db.scalar(
        select(func.count())
        .select_from(AttackSession)
        .where(
            AttackSession.organization_id == org_id,
            AttackSession.status == "active",
            AttackSession.attempt_count >= settings.attempt_threshold,
        )
    ) or 0

    suspicious_ips = db.scalar(
        select(func.count(func.distinct(AttackSession.source_ip)))
        .select_from(AttackSession)
        .where(
            AttackSession.organization_id == org_id,
            AttackSession.status == "active",
            AttackSession.attempt_count > 0,
        )
    ) or 0

    events_last_24h = db.scalar(
        select(func.count())
        .select_from(NormalizedEvent)
        .where(NormalizedEvent.organization_id == org_id, NormalizedEvent.timestamp >= since)
    ) or 0

    high_risk_sources = db.scalar(
        select(func.count())
        .select_from(AttackSession)
        .where(
            AttackSession.organization_id == org_id,
            AttackSession.risk_level.in_(("high", "critical")),
            AttackSession.last_seen >= since,
        )
    ) or 0

    last_ingestion_at = db.scalar(
        select(func.max(IngestionState.updated_at)).where(IngestionState.organization_id == org_id)
    )

    open_cases = db.scalar(
        select(func.count())
        .select_from(Case)
        .where(
            Case.organization_id == org_id,
            Case.status.notin_(("closed", "resolved")),
        )
    ) or 0

    return DashboardMetrics(
        active_attacks=active_attacks,
        suspicious_ips=suspicious_ips,
        events_last_24h=events_last_24h,
        high_risk_sources=high_risk_sources,
        open_cases=int(open_cases),
        last_ingestion_at=last_ingestion_at,
    )


@router.get("/charts", response_model=DashboardCharts)
def dashboard_charts(
    db: DbSession,
    user: CurrentUser,
    hours: int = Query(default=24, ge=1, le=168),
) -> DashboardCharts:
    return build_dashboard_charts(db, user.organization_id, hours=hours)
