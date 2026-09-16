import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SourceIpIntel(Base):
    __tablename__ = "source_ip_intel"
    __table_args__ = (UniqueConstraint("organization_id", "source_ip", name="uq_org_source_ip_intel"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    source_ip: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    country_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    asn: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    isp: Mapped[str | None] = mapped_column(String(256), nullable=True)
    organization_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    reverse_dns: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_hosting: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    network_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enrichment_status: Mapped[str] = mapped_column(String(32), default="pending")
