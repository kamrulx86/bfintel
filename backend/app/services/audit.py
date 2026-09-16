import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    *,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    organization_id: Optional[uuid.UUID] = None,
    target: Optional[str] = None,
    result: str = "success",
    ip_address: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            target=target,
            result=result,
            ip_address=ip_address,
            metadata_json=metadata,
        )
    )
