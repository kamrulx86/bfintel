from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AbuseReportSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    reporter_org_name: str = Field(default="Security Operations", alias="BF_ABUSE_REPORTER_ORG")
    reporter_email: str = Field(default="soc@example.com", alias="BF_ABUSE_REPORTER_EMAIL")
    reporter_phone: str | None = Field(default=None, alias="BF_ABUSE_REPORTER_PHONE")


def get_abuse_report_settings() -> AbuseReportSettings:
    return AbuseReportSettings()
