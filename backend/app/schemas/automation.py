from datetime import datetime
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    channel_type: Literal["telegram", "slack", "webhook"]
    config: dict
    is_active: bool = True


class ChannelOut(BaseModel):
    id: UUID
    name: str
    channel_type: str
    is_active: bool
    created_at: datetime
    configured: bool = True

    model_config = {"from_attributes": True}


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    enabled: bool = True
    conditions: dict
    actions: list[dict]
    cooldown_minutes: int = Field(default=15, ge=1, le=1440)


class RuleOut(BaseModel):
    id: UUID
    name: str
    enabled: bool
    conditions: dict
    actions: list[dict]
    cooldown_minutes: int
    last_triggered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RuleExecutionOut(BaseModel):
    id: UUID
    rule_id: UUID
    source_ip: str | None
    result: str
    detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
