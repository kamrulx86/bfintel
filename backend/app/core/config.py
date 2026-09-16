from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bfintel_env: str = Field(default="development", alias="BFINTEL_ENV")
    secret_key: str = Field(alias="SECRET_KEY")
    fernet_key: str = Field(alias="FERNET_KEY")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    backend_cors_origins: str = Field(
        default="http://localhost:5173",
        alias="BACKEND_CORS_ORIGINS",
    )
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    access_token_expire_minutes: int = 60 * 8

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
