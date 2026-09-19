import re

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.crypto import encrypt_secret
from app.core.security import create_access_token, hash_password
from app.integrations.wazuh.api_connector import WazuhApiConnector
from app.models.organization import Organization
from app.models.user import Role, User
from app.models.wazuh_connection import WazuhConnection
from app.schemas.setup import (
    AdminCreateRequest,
    AdminCreateResponse,
    SetupStatusResponse,
    WazuhSaveRequest,
    WazuhSaveResponse,
    WazuhTestRequest,
    WazuhTestResponse,
)
from app.services.audit import write_audit
from app.services.ingest_alerts import ingest_initial_wazuh_logs

router = APIRouter(prefix="/setup", tags=["setup"])


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:48] or "org"


@router.get("/status", response_model=SetupStatusResponse)
def setup_status(db: DbSession) -> SetupStatusResponse:
    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    wazuh_count = db.scalar(select(func.count()).select_from(WazuhConnection)) or 0
    return SetupStatusResponse(
        setup_required=user_count == 0,
        has_wazuh_connection=wazuh_count > 0,
    )


@router.post("/admin", response_model=AdminCreateResponse)
def create_admin(body: AdminCreateRequest, db: DbSession, request: Request) -> AdminCreateResponse:
    existing = db.scalar(select(func.count()).select_from(User)) or 0
    if existing > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Setup already completed")

    org = Organization(name=body.organization_name, slug=_slugify(body.organization_name))
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email=body.email.lower(),
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role=Role.admin.value,
    )
    db.add(user)
    write_audit(
        db,
        action="setup.admin_created",
        user_id=user.id,
        organization_id=org.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    token = create_access_token(str(user.id), {"role": user.role, "org": str(org.id)})
    return AdminCreateResponse(message="Administrator created", access_token=token)


@router.post("/wazuh/test", response_model=WazuhTestResponse)
async def test_wazuh(body: WazuhTestRequest) -> WazuhTestResponse:
    connector = WazuhApiConnector(
        api_url=body.api_url,
        username=body.api_username,
        password=body.api_password,
        indexer_url=body.indexer_url,
        indexer_username=body.indexer_username,
        indexer_password=body.indexer_password,
        verify_tls=body.verify_tls,
    )
    diag = await connector.test_connection()
    return WazuhTestResponse(
        success=diag.success,
        api_reachable=diag.api_reachable,
        api_auth_ok=diag.api_auth_ok,
        indexer_reachable=diag.indexer_reachable,
        api_version=diag.api_version,
        permission_error=diag.permission_error,
        tls_error=diag.tls_error,
        connection_error=diag.connection_error,
        details=diag.details,
    )


@router.post("/wazuh", response_model=WazuhSaveResponse)
async def save_wazuh(
    body: WazuhSaveRequest,
    db: DbSession,
    user: CurrentUser,
    request: Request,
) -> WazuhSaveResponse:
    connector = WazuhApiConnector(
        api_url=body.api_url,
        username=body.api_username,
        password=body.api_password,
        indexer_url=body.indexer_url,
        indexer_username=body.indexer_username,
        indexer_password=body.indexer_password,
        verify_tls=body.verify_tls,
    )
    diag = await connector.test_connection()
    if not diag.success:
        raise HTTPException(status_code=400, detail="Wazuh connection test failed")

    conn = WazuhConnection(
        organization_id=user.organization_id,
        name=body.name,
        api_url=body.api_url.rstrip("/"),
        api_username_enc=encrypt_secret(body.api_username),
        api_secret_enc=encrypt_secret(body.api_password),
        indexer_url=body.indexer_url.rstrip("/") if body.indexer_url else None,
        indexer_username_enc=encrypt_secret(body.indexer_username) if body.indexer_username else None,
        indexer_secret_enc=encrypt_secret(body.indexer_password) if body.indexer_password else None,
        verify_tls=body.verify_tls,
        last_health_status="connected",
    )
    db.add(conn)
    db.flush()

    initial_ingest: dict | None = None
    try:
        initial_ingest = ingest_initial_wazuh_logs(db, user.organization_id)
    except OSError as exc:
        initial_ingest = {"error": "ingest_failed", "detail": str(exc)[:500]}

    write_audit(
        db,
        action="wazuh.connection_created",
        user_id=user.id,
        organization_id=user.organization_id,
        target=body.api_url,
        ip_address=request.client.host if request.client else None,
        metadata={"verify_tls": body.verify_tls, "initial_ingest": initial_ingest},
    )
    db.commit()

    return WazuhSaveResponse(
        id=str(conn.id),
        message="Wazuh connection saved",
        initial_ingest=initial_ingest,
    )
