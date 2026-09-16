import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AttackSession(Base):
    __tablename__ = "attack_sessions"
    __table_args__ = (
        Index("ix_sessions_org_status", "organization_id", "status"),
        Index("ix_sessions_source_ip", "source_ip"),
        Index("ix_sessions_risk", "risk_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    source_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    successful_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    target_count: Mapped[int] = mapped_column(Integer, default=0)
    target_hosts: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    target_ports: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    services: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    usernames: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    protocols: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    average_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    attack_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    status: Mapped[str] = mapped_column(String(32), default="active")
    attack_type: Mapped[str] = mapped_column(String(64), default="authentication_bruteforce")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
