from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.normalized_event import NormalizedEvent
from app.models.source_ip_intel import SourceIpIntel
from app.schemas.investigation import ChartPoint, DashboardCharts, NamedCount


def build_dashboard_charts(db: Session, organization_id, hours: int = 24) -> DashboardCharts:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    bucket = func.date_trunc("hour", NormalizedEvent.timestamp).label("bucket")
    timeline_rows = db.execute(
        select(bucket, func.count())
        .where(NormalizedEvent.organization_id == organization_id, NormalizedEvent.timestamp >= since)
        .group_by(bucket)
        .order_by(bucket)
    ).all()
    auth_failures_timeline = [
        ChartPoint(bucket=row[0].isoformat() if row[0] else "", count=int(row[1])) for row in timeline_rows
    ]

    by_service_rows = db.execute(
        select(NormalizedEvent.service, func.count())
        .where(
            NormalizedEvent.organization_id == organization_id,
            NormalizedEvent.timestamp >= since,
            NormalizedEvent.service.isnot(None),
        )
        .group_by(NormalizedEvent.service)
        .order_by(func.count().desc())
        .limit(10)
    ).all()
    by_service = [NamedCount(name=row[0] or "unknown", count=int(row[1])) for row in by_service_rows]

    host_rows = db.execute(
        select(NormalizedEvent.target_host, func.count())
        .where(
            NormalizedEvent.organization_id == organization_id,
            NormalizedEvent.timestamp >= since,
            NormalizedEvent.target_host.isnot(None),
        )
        .group_by(NormalizedEvent.target_host)
        .order_by(func.count().desc())
        .limit(10)
    ).all()
    top_target_hosts = [NamedCount(name=row[0] or "unknown", count=int(row[1])) for row in host_rows]

    user_rows = db.execute(
        select(NormalizedEvent.username, func.count())
        .where(
            NormalizedEvent.organization_id == organization_id,
            NormalizedEvent.timestamp >= since,
            NormalizedEvent.username.isnot(None),
        )
        .group_by(NormalizedEvent.username)
        .order_by(func.count().desc())
        .limit(10)
    ).all()
    top_usernames = [NamedCount(name=row[0] or "unknown", count=int(row[1])) for row in user_rows]

    unique_source_ips = db.scalar(
        select(func.count(func.distinct(NormalizedEvent.source_ip)))
        .select_from(NormalizedEvent)
        .where(
            NormalizedEvent.organization_id == organization_id,
            NormalizedEvent.timestamp >= since,
            NormalizedEvent.source_ip.isnot(None),
        )
    ) or 0

    country_rows = db.execute(
        select(SourceIpIntel.country_name, func.count(func.distinct(NormalizedEvent.source_ip)))
        .join(
            NormalizedEvent,
            (NormalizedEvent.source_ip == SourceIpIntel.source_ip)
            & (NormalizedEvent.organization_id == SourceIpIntel.organization_id),
        )
        .where(NormalizedEvent.organization_id == organization_id, NormalizedEvent.timestamp >= since)
        .group_by(SourceIpIntel.country_name)
        .order_by(func.count(func.distinct(NormalizedEvent.source_ip)).desc())
        .limit(10)
    ).all()
    by_country = [
        NamedCount(name=row[0] or "Unknown", count=int(row[1])) for row in country_rows if row[1]
    ]

    return DashboardCharts(
        hours=hours,
        auth_failures_timeline=auth_failures_timeline,
        by_service=by_service,
        by_country=by_country,
        top_target_hosts=top_target_hosts,
        top_usernames=top_usernames,
        unique_source_ips=int(unique_source_ips),
    )
