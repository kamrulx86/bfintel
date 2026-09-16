"""source ip intelligence

Revision ID: 003
Revises: 002
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_ip_intel",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("source_ip", sa.String(64), nullable=False),
        sa.Column("country_code", sa.String(8), nullable=True),
        sa.Column("country_name", sa.String(128), nullable=True),
        sa.Column("region", sa.String(128), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("asn", sa.String(32), nullable=True),
        sa.Column("isp", sa.String(256), nullable=True),
        sa.Column("organization_name", sa.String(256), nullable=True),
        sa.Column("reverse_dns", sa.String(512), nullable=True),
        sa.Column("is_hosting", sa.Boolean(), nullable=True),
        sa.Column("network_scope", sa.String(32), nullable=True),
        sa.Column("last_enriched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enrichment_status", sa.String(32), server_default="pending"),
        sa.UniqueConstraint("organization_id", "source_ip", name="uq_org_source_ip_intel"),
    )
    op.create_index("ix_source_ip_intel_country", "source_ip_intel", ["country_code"])
    op.create_index("ix_source_ip_intel_asn", "source_ip_intel", ["asn"])

    op.create_table(
        "intel_provider_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("source_ip", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("success", sa.Boolean(), server_default="false"),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_intel_provider_ip", "intel_provider_results", ["source_ip"])


def downgrade() -> None:
    op.drop_table("intel_provider_results")
    op.drop_table("source_ip_intel")
