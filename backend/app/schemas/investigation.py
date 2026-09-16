from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.intelligence import AttackSessionOut
from app.schemas.intel import GeoIntelOut, ProviderSnapshot


class ChartPoint(BaseModel):
    bucket: str
    count: int


class NamedCount(BaseModel):
    name: str
    count: int


class DashboardCharts(BaseModel):
    hours: int
    auth_failures_timeline: list[ChartPoint]
    by_service: list[NamedCount]
    by_country: list[NamedCount]
    top_target_hosts: list[NamedCount]
    top_usernames: list[NamedCount]
    unique_source_ips: int


class TimelineEventOut(BaseModel):
    id: UUID
    timestamp: datetime
    username: str | None
    service: str | None
    target_host: str | None
    authentication_result: str | None
    rule_id: str | None
    rule_description: str | None
    wazuh_event_id: str

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    items: list[TimelineEventOut]
    total: int


class IpInvestigationProfile(BaseModel):
    source_ip: str
    network_scope: str
    first_seen: datetime | None
    last_seen: datetime | None
    total_events: int
    failure_count: int
    success_count: int
    session_count: int
    max_risk_score: int
    max_risk_level: str
    target_hosts: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    usernames: list[str] = Field(default_factory=list)
    risk_reasons: list[str] = Field(default_factory=list)
    sessions: list[AttackSessionOut] = Field(default_factory=list)
    geo: GeoIntelOut | None = None
    threat_intel: list[ProviderSnapshot] = Field(default_factory=list)
    geo_placeholder: bool = False


class SearchHit(BaseModel):
    type: str
    label: str
    href: str
    meta: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHit]
