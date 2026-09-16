import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.ip_lists import AllowlistEntry
from app.models.user import Role
from app.schemas.soc import AllowlistCreate, AllowlistOut
from app.services.audit import write_audit

router = APIRouter(prefix="/allowlist", tags=["allowlist"])


@router.get("", response_model=list[AllowlistOut])
def list_allowlist(db: DbSession, user: CurrentUser) -> list[AllowlistOut]:
    rows = db.scalars(
        select(AllowlistEntry)
        .where(AllowlistEntry.organization_id == user.organization_id)
        .order_by(AllowlistEntry.created_at.desc())
    ).all()
    return [AllowlistOut.model_validate(r) for r in rows]


@router.post("", response_model=AllowlistOut)
def add_allowlist(db: DbSession, user: CurrentUser, body: AllowlistCreate) -> AllowlistOut:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=403, detail="Admin only")
    row = AllowlistEntry(
        organization_id=user.organization_id,
        value=body.value.strip(),
        entry_type=body.entry_type,
        description=body.description,
        added_by=user.id,
    )
    db.add(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="allowlist.add", target=body.value)
    db.commit()
    db.refresh(row)
    return AllowlistOut.model_validate(row)


@router.delete("/{entry_id}")
def remove_allowlist(db: DbSession, user: CurrentUser, entry_id: uuid.UUID) -> dict:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=403, detail="Admin only")
    row = db.scalar(
        select(AllowlistEntry).where(AllowlistEntry.id == entry_id, AllowlistEntry.organization_id == user.organization_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="allowlist.remove", target=row.value)
    db.commit()
    return {"status": "deleted"}
