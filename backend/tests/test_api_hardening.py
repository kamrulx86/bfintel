import pytest
from fastapi.testclient import TestClient

from app.core.hardening_config import get_hardening_settings
from app.main import app
from app.middleware.rate_limit import reset_rate_limit_store


@pytest.fixture
def client():
    reset_rate_limit_store()
    get_hardening_settings.cache_clear()
    with TestClient(app) as c:
        yield c
    reset_rate_limit_store()
    get_hardening_settings.cache_clear()


def test_security_headers_on_health(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "no-store" in res.headers.get("Cache-Control", "")


def test_protected_route_requires_auth(client: TestClient):
    res = client.get("/api/dashboard/metrics")
    assert res.status_code == 401
    assert res.headers.get("X-Content-Type-Options") == "nosniff"


