from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    active_attacks: int
    suspicious_ips: int
    events_last_24h: int
    high_risk_sources: int
    open_cases: int = 0
    last_ingestion_at: datetime | None = None


class AttackSessionOut(BaseModel):
    id: UUID
    source_ip: str
    first_seen: datetime
    last_seen: datetime
    attempt_count: int
    successful_attempt_count: int
    target_count: int
    target_hosts: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    usernames: list[str] = Field(default_factory=list)
    risk_score: int
    risk_level: str
    status: str
    attack_type: str

    model_config = {"from_attributes": True}


class AttackListResponse(BaseModel):
    items: list[AttackSessionOut]
    total: int


class SourceIntelOut(BaseModel):
    source_ip: str
    session_count: int
    total_attempts: int
    max_risk_score: int
    max_risk_level: str
    last_seen: datetime
    services: list[str] = Field(default_factory=list)
    country_code: str | None = None
    country_name: str | None = None
    asn: str | None = None
    isp: str | None = None


class SourceListResponse(BaseModel):
    items: list[SourceIntelOut]
    total: int


class IngestionRunResponse(BaseModel):
    status: str
    lines: int = 0
    normalized: int = 0
    skipped: int = 0
    errors: int = 0
    detail: str | None = None
