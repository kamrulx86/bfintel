import httpx

from app.core.intel_config import IntelSettings, get_intel_settings
from app.integrations.intel.base import ProviderResult, ThreatIntelProvider


class AbuseIpDbProvider(ThreatIntelProvider):
    name = "abuseipdb"

    def __init__(self, settings: IntelSettings | None = None) -> None:
        self.settings = settings or get_intel_settings()

    def lookup(self, ip: str) -> ProviderResult:
        if not self.settings.abuseipdb_enabled or not self.settings.abuseipdb_api_key:
            return ProviderResult(provider=self.name, success=False, error="not_configured")

        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {"Key": self.settings.abuseipdb_api_key, "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": "90", "verbose": ""}
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                resp = client.get(url, headers=headers, params=params)
                if resp.status_code == 429:
                    return ProviderResult(provider=self.name, success=False, error="rate_limited", data={"status": 429})
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            return ProviderResult(provider=self.name, success=False, error=str(exc))

        data = payload.get("data") or {}
        return ProviderResult(
            provider=self.name,
            success=True,
            data={
                "abuse_confidence_score": data.get("abuseConfidenceScore"),
                "total_reports": data.get("totalReports"),
                "last_reported_at": data.get("lastReportedAt"),
                "is_whitelisted": data.get("isWhitelisted"),
                "usage_type": data.get("usageType"),
                "raw": data,
            },
        )
