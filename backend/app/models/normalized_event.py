import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NormalizedEvent(Base):
    __tablename__ = "normalized_events"
    __table_args__ = (
        Index("ix_events_org_ts", "organization_id", "timestamp"),
        Index("ix_events_source_ip", "source_ip"),
        Index("ix_events_wazuh_id", "wazuh_event_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    wazuh_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    username: Mapped[str | None] = mapped_column(String(256), nullable=True)
    target_host: Mapped[str | None] = mapped_column(String(256), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rule_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rule_description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    authentication_result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    service: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attack_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("attack_sessions.id"), nullable=True)
    raw_event: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
