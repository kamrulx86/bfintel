from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.models.user import Role
from app.schemas.intelligence import IngestionRunResponse
from app.services.ingest_alerts import ingest_alerts_file

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/poll", response_model=IngestionRunResponse)
def poll_alerts_now(db: DbSession, user: CurrentUser) -> IngestionRunResponse:
    if user.role not in (Role.admin.value, Role.analyst.value):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    stats = ingest_alerts_file(db, user.organization_id)
    if stats.get("error") == "file_missing":
        db.commit()
        return IngestionRunResponse(status="file_missing", detail="Wazuh alerts.json not mounted or path wrong")

    db.commit()
    return IngestionRunResponse(
        status="ok",
        lines=stats.get("lines", 0),
        normalized=stats.get("normalized", 0),
        skipped=stats.get("skipped", 0),
        errors=stats.get("errors", 0),
    )
