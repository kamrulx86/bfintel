import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.ip_lists import BlocklistEntry
from app.models.user import Role
from app.schemas.soc import BlocklistCreate, BlocklistOut
from app.services.audit import write_audit

router = APIRouter(prefix="/blocklist", tags=["blocklist"])


@router.get("", response_model=list[BlocklistOut])
def list_blocklist(db: DbSession, user: CurrentUser) -> list[BlocklistOut]:
    rows = db.scalars(
        select(BlocklistEntry)
        .where(BlocklistEntry.organization_id == user.organization_id)
        .order_by(BlocklistEntry.created_at.desc())
    ).all()
    return [BlocklistOut.model_validate(r) for r in rows]


@router.post("", response_model=BlocklistOut)
def add_blocklist(db: DbSession, user: CurrentUser, body: BlocklistCreate) -> BlocklistOut:
    if user.role not in (Role.admin.value, Role.analyst.value):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = BlocklistEntry(
        organization_id=user.organization_id,
        source_ip=body.source_ip.strip(),
        reason=body.reason,
        enforcement_status=body.enforcement_status,
        added_by=user.id,
    )
    db.add(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="blocklist.add", target=body.source_ip)
    db.commit()
    db.refresh(row)
    return BlocklistOut.model_validate(row)


@router.delete("/{entry_id}")
def remove_blocklist(db: DbSession, user: CurrentUser, entry_id: uuid.UUID) -> dict:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=403, detail="Admin only")
    row = db.scalar(
        select(BlocklistEntry).where(BlocklistEntry.id == entry_id, BlocklistEntry.organization_id == user.organization_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    ip = row.source_ip
    db.delete(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="blocklist.remove", target=ip)
    db.commit()
    return {"status": "deleted"}
