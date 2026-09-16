from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.attack_session import AttackSession
from app.schemas.intelligence import AttackListResponse, AttackSessionOut

router = APIRouter(prefix="/attacks", tags=["attacks"])


@router.get("", response_model=AttackListResponse)
def list_attacks(
    db: DbSession,
    user: CurrentUser,
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    service: str | None = Query(default=None),
    source_ip: str | None = Query(default=None),
    host: str | None = Query(default=None),
    username: str | None = Query(default=None),
    hours: int | None = Query(default=None, ge=1, le=720),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AttackListResponse:
    filters = [AttackSession.organization_id == user.organization_id]
    if status:
        filters.append(AttackSession.status == status)
    if risk_level:
        filters.append(AttackSession.risk_level == risk_level)
    if service:
        filters.append(AttackSession.services.any(service))
    if source_ip:
        filters.append(AttackSession.source_ip.ilike(f"%{source_ip.strip()}%"))
    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        filters.append(AttackSession.last_seen >= since)
    if host:
        filters.append(AttackSession.target_hosts.any(host))
    if username:
        filters.append(AttackSession.usernames.any(username))

    total = db.scalar(select(func.count()).select_from(AttackSession).where(*filters)) or 0
    rows = db.scalars(
        select(AttackSession).where(*filters).order_by(AttackSession.last_seen.desc()).offset(offset).limit(limit)
    ).all()
    return AttackListResponse(items=[AttackSessionOut.model_validate(r) for r in rows], total=total)


@router.get("/{session_id}", response_model=AttackSessionOut)
def get_attack(db: DbSession, user: CurrentUser, session_id: UUID) -> AttackSessionOut:
    row = db.scalar(
        select(AttackSession).where(
            AttackSession.id == session_id,
            AttackSession.organization_id == user.organization_id,
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Attack session not found")
    return AttackSessionOut.model_validate(row)
