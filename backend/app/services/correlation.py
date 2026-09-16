from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.correlation_config import get_correlation_settings
from app.models.attack_session import AttackSession
from app.models.normalized_event import NormalizedEvent
from app.services.risk import compute_risk_score


def correlate_event(db: Session, event: NormalizedEvent, organization_id: UUID) -> None:
    settings = get_correlation_settings()
    if not event.source_ip:
        return

    window_start = event.timestamp - timedelta(minutes=settings.window_minutes)
    session = db.scalar(
        select(AttackSession)
        .where(
            AttackSession.organization_id == organization_id,
            AttackSession.source_ip == event.source_ip,
            AttackSession.status == "active",
            AttackSession.last_seen >= window_start,
        )
        .order_by(AttackSession.last_seen.desc())
        .limit(1)
    )

    if session is None:
        session = AttackSession(
            organization_id=organization_id,
            source_ip=event.source_ip,
            first_seen=event.timestamp,
            last_seen=event.timestamp,
            attempt_count=0,
            successful_attempt_count=0,
            target_hosts=[],
            target_ports=[],
            services=[],
            usernames=[],
            protocols=[],
            status="active",
        )
        db.add(session)
        db.flush()

    session.last_seen = max(session.last_seen, event.timestamp)
    if event.authentication_result == "failure":
        session.attempt_count += 1
    elif event.authentication_result == "success":
        session.successful_attempt_count += 1

    session.target_hosts = _uniq(session.target_hosts, event.target_host)
    session.services = _uniq(session.services, event.service)
    session.usernames = _uniq(session.usernames, event.username)
    session.protocols = _uniq(session.protocols, event.protocol)
    if event.destination_port:
        session.target_ports = _uniq_int(session.target_ports, event.destination_port)

    session.target_count = len(session.target_hosts or [])
    duration = (session.last_seen - session.first_seen).total_seconds()
    session.attack_duration_seconds = int(duration)
    if duration > 0:
        session.average_rate = session.attempt_count / (duration / 60.0)
    session.peak_rate = session.average_rate

    session.risk_score, session.risk_level = compute_risk_score(
        session.attempt_count,
        session.successful_attempt_count,
        session.target_count,
        len(session.services or []),
        settings,
    )

    if session.attempt_count >= settings.attempt_threshold:
        session.status = "active"
    event.attack_session_id = session.id


def _uniq(existing: list[str] | None, value: str | None) -> list[str]:
    items = list(existing or [])
    if value and value not in items:
        items.append(value)
    return items


def _uniq_int(existing: list[int] | None, value: int) -> list[int]:
    items = list(existing or [])
    if value not in items:
        items.append(value)
    return items
