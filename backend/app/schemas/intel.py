from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IntelProviderStatus(BaseModel):
    name: str
    enabled: bool
    configured: bool
    description: str


class GeoIntelOut(BaseModel):
    country_code: str | None = None
    country_name: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    asn: str | None = None
    isp: str | None = None
    organization_name: str | None = None
    reverse_dns: str | None = None
    is_hosting: bool | None = None
    network_scope: str | None = None
    last_enriched_at: datetime | None = None
    enrichment_status: str | None = None

    model_config = {"from_attributes": True}


class ProviderSnapshot(BaseModel):
    provider: str
    success: bool
    fetched_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ProviderResultsOut(BaseModel):
    source_ip: str
    results: list[ProviderSnapshot]
