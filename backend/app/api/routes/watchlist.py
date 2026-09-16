import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.ip_lists import WatchlistEntry
from app.models.user import Role
from app.schemas.soc import WatchlistCreate, WatchlistOut
from app.services.audit import write_audit

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistOut])
def list_watchlist(db: DbSession, user: CurrentUser) -> list[WatchlistOut]:
    rows = db.scalars(
        select(WatchlistEntry)
        .where(WatchlistEntry.organization_id == user.organization_id)
        .order_by(WatchlistEntry.created_at.desc())
    ).all()
    return [WatchlistOut.model_validate(r) for r in rows]


@router.post("", response_model=WatchlistOut)
def add_watchlist(db: DbSession, user: CurrentUser, body: WatchlistCreate) -> WatchlistOut:
    row = WatchlistEntry(
        organization_id=user.organization_id,
        source_ip=body.source_ip.strip(),
        reason=body.reason,
        risk_level=body.risk_level,
        notes=body.notes,
        added_by=user.id,
    )
    db.add(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="watchlist.add", target=body.source_ip)
    db.commit()
    db.refresh(row)
    return WatchlistOut.model_validate(row)


@router.delete("/{entry_id}")
def remove_watchlist(db: DbSession, user: CurrentUser, entry_id: uuid.UUID) -> dict:
    if user.role not in (Role.admin.value, Role.analyst.value):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = db.scalar(
        select(WatchlistEntry).where(WatchlistEntry.id == entry_id, WatchlistEntry.organization_id == user.organization_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    ip = row.source_ip
    db.delete(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="watchlist.remove", target=ip)
    db.commit()
    return {"status": "deleted"}
