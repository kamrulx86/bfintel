import httpx

from app.core.intel_config import IntelSettings, get_intel_settings
from app.integrations.intel.base import GeoAsnProvider, ProviderResult


class IpApiProvider(GeoAsnProvider):
    name = "ip-api"

    def __init__(self, settings: IntelSettings | None = None) -> None:
        self.settings = settings or get_intel_settings()

    def lookup(self, ip: str) -> ProviderResult:
        if not self.settings.ip_api_enabled:
            return ProviderResult(provider=self.name, success=False, error="disabled")

        url = (
            f"{self.settings.ip_api_base_url.rstrip('/')}/json/{ip}"
            "?fields=status,message,country,countryCode,regionName,city,lat,lon,isp,org,as,reverse,hosting,query"
        )
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                resp = client.get(url)
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            return ProviderResult(provider=self.name, success=False, error=str(exc))

        if payload.get("status") != "success":
            return ProviderResult(
                provider=self.name,
                success=False,
                error=payload.get("message", "lookup failed"),
                data=payload,
            )

        asn_raw = payload.get("as") or ""
        asn = asn_raw.split()[0] if asn_raw else None
        return ProviderResult(
            provider=self.name,
            success=True,
            data={
                "country_code": payload.get("countryCode"),
                "country_name": payload.get("country"),
                "region": payload.get("regionName"),
                "city": payload.get("city"),
                "latitude": payload.get("lat"),
                "longitude": payload.get("lon"),
                "asn": asn,
                "isp": payload.get("isp"),
                "organization": payload.get("org"),
                "reverse_dns": payload.get("reverse"),
                "hosting": payload.get("hosting"),
                "raw": payload,
            },
        )
