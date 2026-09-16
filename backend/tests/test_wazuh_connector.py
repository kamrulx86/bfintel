import pytest

from app.integrations.wazuh.api_connector import WazuhApiConnector


@pytest.mark.asyncio
async def test_wazuh_connector_invalid_host():
    connector = WazuhApiConnector(
        api_url="https://127.0.0.1:59999",
        username="x",
        password="y",
        verify_tls=False,
    )
    diag = await connector.test_connection()
    assert diag.api_reachable is False
    assert diag.success is False
