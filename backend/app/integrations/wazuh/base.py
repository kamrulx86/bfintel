from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WazuhTestDiagnostics:
    api_reachable: bool = False
    api_auth_ok: bool = False
    indexer_reachable: bool = False
    api_version: Optional[str] = None
    permission_error: Optional[str] = None
    tls_error: Optional[str] = None
    connection_error: Optional[str] = None
    details: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.api_reachable and self.api_auth_ok


class WazuhConnector(ABC):
    @abstractmethod
    async def test_connection(self) -> WazuhTestDiagnostics:
        ...

    @abstractmethod
    async def get_agents(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        ...

    @abstractmethod
    async def search_security_events(
        self,
        query: dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        ...
