from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HardeningSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rate_limit_enabled: bool = Field(default=True, alias="BF_RATE_LIMIT_ENABLED")
    login_rate_limit: int = Field(default=10, alias="BF_LOGIN_RATE_LIMIT")
    login_rate_window_seconds: int = Field(default=60, alias="BF_LOGIN_RATE_WINDOW_SECONDS")
    api_rate_limit: int = Field(default=300, alias="BF_API_RATE_LIMIT")
    api_rate_window_seconds: int = Field(default=60, alias="BF_API_RATE_WINDOW_SECONDS")
    trust_proxy_headers: bool = Field(default=False, alias="BF_TRUST_PROXY_HEADERS")
    disable_api_docs: bool = Field(default=False, alias="BF_DISABLE_API_DOCS")


@lru_cache
def get_hardening_settings() -> HardeningSettings:
    return HardeningSettings()
