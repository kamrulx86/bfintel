from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CorrelationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    window_minutes: int = Field(default=10, alias="BF_CORRELATION_WINDOW_MINUTES")
    attempt_threshold: int = Field(default=5, alias="BF_ATTEMPT_THRESHOLD")
    cooldown_minutes: int = Field(default=15, alias="BF_CORRELATION_COOLDOWN_MINUTES")
    alerts_json_path: str = Field(default="/wazuh-alerts/alerts.json", alias="WAZUH_ALERTS_JSON_PATH")


def get_correlation_settings() -> CorrelationSettings:
    return CorrelationSettings()
