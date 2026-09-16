from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeoAsnSnapshot:
    country_code: str | None = None
    country_name: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    asn: str | None = None
    isp: str | None = None
    organization: str | None = None
    reverse_dns: str | None = None
    hosting: bool | None = None


@dataclass
class ProviderResult:
    provider: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class GeoAsnProvider(ABC):
    name: str

    @abstractmethod
    def lookup(self, ip: str) -> ProviderResult:
        ...


class ThreatIntelProvider(ABC):
    name: str

    @abstractmethod
    def lookup(self, ip: str) -> ProviderResult:
        ...
