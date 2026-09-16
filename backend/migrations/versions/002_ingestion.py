"""ingestion and attack sessions

Revision ID: 002
Revises: 001
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("source", sa.String(64), server_default="alerts_json"),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("byte_offset", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "attack_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("source_ip", sa.String(64), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0"),
        sa.Column("successful_attempt_count", sa.Integer(), server_default="0"),
        sa.Column("target_count", sa.Integer(), server_default="0"),
        sa.Column("target_hosts", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("target_ports", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("services", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("usernames", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("protocols", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("average_rate", sa.Float(), nullable=True),
        sa.Column("peak_rate", sa.Float(), nullable=True),
        sa.Column("attack_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("risk_score", sa.Integer(), server_default="0"),
        sa.Column("risk_level", sa.String(16), server_default="low"),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("attack_type", sa.String(64), server_default="authentication_bruteforce"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_sessions_org_status", "attack_sessions", ["organization_id", "status"])
    op.create_index("ix_sessions_source_ip", "attack_sessions", ["source_ip"])
    op.create_index("ix_sessions_risk", "attack_sessions", ["risk_score"])

    op.create_table(
        "normalized_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("wazuh_event_id", sa.String(128), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_ip", sa.String(64), nullable=True),
        sa.Column("destination_ip", sa.String(64), nullable=True),
        sa.Column("source_port", sa.Integer(), nullable=True),
        sa.Column("destination_port", sa.Integer(), nullable=True),
        sa.Column("protocol", sa.String(32), nullable=True),
        sa.Column("username", sa.String(256), nullable=True),
        sa.Column("target_host", sa.String(256), nullable=True),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("agent_name", sa.String(128), nullable=True),
        sa.Column("rule_id", sa.String(32), nullable=True),
        sa.Column("rule_level", sa.Integer(), nullable=True),
        sa.Column("rule_description", sa.String(512), nullable=True),
        sa.Column("authentication_result", sa.String(32), nullable=True),
        sa.Column("service", sa.String(64), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=True),
        sa.Column("attack_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attack_sessions.id"), nullable=True),
        sa.Column("raw_event", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_events_org_ts", "normalized_events", ["organization_id", "timestamp"])
    op.create_index("ix_events_source_ip", "normalized_events", ["source_ip"])
    op.create_index("ix_events_wazuh_id", "normalized_events", ["wazuh_event_id"], unique=True)
    op.create_index("ix_normalized_events_timestamp", "normalized_events", ["timestamp"])


def downgrade() -> None:
    op.drop_table("normalized_events")
    op.drop_table("attack_sessions")
    op.drop_table("ingestion_states")
