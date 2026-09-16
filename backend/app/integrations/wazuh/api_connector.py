import asyncio
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

from app.integrations.wazuh.base import WazuhConnector, WazuhTestDiagnostics


class WazuhApiConnector(WazuhConnector):
    """Wazuh Manager REST API connector."""

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        indexer_url: Optional[str] = None,
        indexer_username: Optional[str] = None,
        indexer_password: Optional[str] = None,
        verify_tls: bool = True,
        timeout: float = 20.0,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.indexer_url = indexer_url.rstrip("/") if indexer_url else None
        self.indexer_username = indexer_username
        self.indexer_password = indexer_password
        self.verify_tls = verify_tls
        self.timeout = timeout
        self._token: Optional[str] = None

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(verify=self.verify_tls, timeout=self.timeout)

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        url = f"{self.api_url}/security/user/authenticate"
        resp = await client.post(url, auth=(self.username, self.password))
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, str):
            return data
        token = data.get("data", {}).get("token")
        if not token:
            raise httpx.HTTPStatusError("No token in response", request=resp.request, response=resp)
        return token

    async def test_connection(self) -> WazuhTestDiagnostics:
        diag = WazuhTestDiagnostics()
        try:
            async with self._client() as client:
                try:
                    ping = await client.get(f"{self.api_url}/")
                    diag.api_reachable = ping.status_code < 500
                    diag.details.append(f"API HTTP {ping.status_code} on root endpoint")
                except httpx.ConnectError as exc:
                    diag.connection_error = str(exc)
                    diag.details.append(f"API connection failed: {exc}")
                    return diag
                except httpx.SSLError as exc:
                    diag.tls_error = str(exc)
                    diag.details.append(f"TLS error: {exc}")
                    return diag

                try:
                    self._token = await self._authenticate(client)
                    diag.api_auth_ok = True
                    diag.details.append("API authentication successful")
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in (401, 403):
                        diag.permission_error = exc.response.text[:500]
                        diag.details.append("API authentication failed")
                    else:
                        diag.connection_error = str(exc)
                    return diag

                headers = {"Authorization": f"Bearer {self._token}"}
                info = await client.get(f"{self.api_url}/", headers=headers)
                if info.status_code == 200:
                    body = info.json()
                    diag.api_version = str(body.get("data", {}).get("api_version") or body.get("api_version") or "unknown")
                    diag.details.append(f"API version: {diag.api_version}")

                if self.indexer_url:
                    try:
                        auth = None
                        if self.indexer_username and self.indexer_password:
                            auth = (self.indexer_username, self.indexer_password)
                        idx = await client.get(self.indexer_url, auth=auth)
                        diag.indexer_reachable = idx.status_code < 500
                        diag.details.append(f"Indexer HTTP {idx.status_code}")
                    except Exception as exc:  # noqa: BLE001
                        diag.details.append(f"Indexer unreachable: {exc}")
        except httpx.SSLError as exc:
            diag.tls_error = str(exc)
        except Exception as exc:  # noqa: BLE001
            diag.connection_error = str(exc)
            diag.details.append(str(exc))
        return diag

    async def _authorized_get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        async with self._client() as client:
            if not self._token:
                self._token = await self._authenticate(client)
            headers = {"Authorization": f"Bearer {self._token}"}
            url = urljoin(self.api_url + "/", path.lstrip("/"))
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 401:
                self._token = await self._authenticate(client)
                headers = {"Authorization": f"Bearer {self._token}"}
                resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_agents(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        return await self._authorized_get("/agents", params={"limit": limit, "offset": offset})

    async def search_security_events(
        self,
        query: dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        # Phase 2: indexer-backed search; Phase 1 stub returns empty structure
        await asyncio.sleep(0)
        return {"data": {"items": [], "total": 0}, "query": query, "limit": limit, "offset": offset}
