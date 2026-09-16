from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AbuseReportCreate(BaseModel):
    source_ip: str
    subject: str = Field(min_length=1, max_length=512)
    body: str = Field(min_length=1)
    recipient_email: str | None = None
    isp_name: str | None = None
    asn: str | None = None
    case_id: UUID | None = None
    template_key: str = "brute_force"


class AbuseReportUpdate(BaseModel):
    status: str | None = None
    subject: str | None = Field(default=None, max_length=512)
    body: str | None = None
    recipient_email: str | None = None


class AbuseReportOut(BaseModel):
    id: UUID
    source_ip: str
    case_id: UUID | None
    status: str
    subject: str
    body: str
    recipient_email: str | None
    isp_name: str | None
    asn: str | None
    template_key: str
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AbuseReportFromIpRequest(BaseModel):
    case_id: UUID | None = None
    template_key: str = "brute_force"
