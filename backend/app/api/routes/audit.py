from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.audit_log import AuditLog
from app.models.user import Role
from app.schemas.soc import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLogOut]:
    if user.role not in (Role.admin.value, Role.analyst.value):
        limit = min(limit, 50)
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == user.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    return [AuditLogOut.model_validate(r) for r in rows]
