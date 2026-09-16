from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class IntelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    enrichment_ttl_hours: int = Field(default=168, alias="BF_INTEL_ENRICHMENT_TTL_HOURS")
    ip_api_enabled: bool = Field(default=True, alias="BF_INTEL_IP_API_ENABLED")
    ip_api_base_url: str = Field(default="http://ip-api.com", alias="BF_INTEL_IP_API_BASE_URL")
    abuseipdb_api_key: str | None = Field(default=None, alias="ABUSEIPDB_API_KEY")
    abuseipdb_enabled: bool = Field(default=True, alias="BF_INTEL_ABUSEIPDB_ENABLED")
    request_timeout_seconds: float = Field(default=8.0, alias="BF_INTEL_REQUEST_TIMEOUT")


def get_intel_settings() -> IntelSettings:
    return IntelSettings()
