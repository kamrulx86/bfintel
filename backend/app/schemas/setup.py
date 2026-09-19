from pydantic import BaseModel, EmailStr, Field


class SetupStatusResponse(BaseModel):
    setup_required: bool
    has_wazuh_connection: bool


class AdminCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    organization_name: str = Field(min_length=2, max_length=255)


class AdminCreateResponse(BaseModel):
    message: str
    access_token: str


class WazuhTestRequest(BaseModel):
    api_url: str
    api_username: str
    api_password: str
    indexer_url: str | None = None
    indexer_username: str | None = None
    indexer_password: str | None = None
    verify_tls: bool = True


class WazuhTestResponse(BaseModel):
    success: bool
    api_reachable: bool
    api_auth_ok: bool
    indexer_reachable: bool
    api_version: str | None = None
    permission_error: str | None = None
    tls_error: str | None = None
    connection_error: str | None = None
    details: list[str]


class WazuhSaveRequest(WazuhTestRequest):
    name: str = "Primary"


class WazuhSaveResponse(BaseModel):
    id: str
    message: str
    initial_ingest: dict | None = None
