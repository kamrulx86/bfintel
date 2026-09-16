from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    severity: str = "medium"
    priority: str = "normal"
    source_ip: str | None = None
    attack_session_id: UUID | None = None


class CaseUpdate(BaseModel):
    status: str | None = None
    assignee: str | None = None
    severity: str | None = None
    priority: str | None = None


class CaseOut(BaseModel):
    id: UUID
    title: str
    severity: str
    priority: str
    status: str
    assignee: str | None
    source_ip: str | None
    attack_session_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class CaseNoteOut(BaseModel):
    id: UUID
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistCreate(BaseModel):
    source_ip: str
    reason: str | None = None
    risk_level: str = "medium"
    notes: str | None = None


class WatchlistOut(BaseModel):
    id: UUID
    source_ip: str
    reason: str | None
    risk_level: str
    notes: str | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AllowlistCreate(BaseModel):
    value: str
    entry_type: str = "ip"
    description: str | None = None


class AllowlistOut(BaseModel):
    id: UUID
    value: str
    entry_type: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BlocklistCreate(BaseModel):
    source_ip: str
    reason: str | None = None
    enforcement_status: str = "internal_only"


class BlocklistOut(BaseModel):
    id: UUID
    source_ip: str
    reason: str | None
    enforcement_status: str
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: UUID
    action: str
    target: str | None
    result: str
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
