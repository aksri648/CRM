"""initial communications schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS communications")

    op.create_table("communications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(50)), sa.Column("status", sa.String(50), default="queued"),
        sa.Column("subject_line", sa.String(500), nullable=True), sa.Column("message_body", sa.Text, nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text, nullable=True), sa.Column("retry_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="communications")
    op.create_index("ix_communications_status", "communications", ["status"], schema="communications")

    op.create_table("communication_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("communication_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("communications.communications.id")),
        sa.Column("event_type", sa.String(50)), sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="communications")

    op.create_table("delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("communication_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("communications.communications.id")),
        sa.Column("attempt_number", sa.Integer), sa.Column("status", sa.String(50)),
        sa.Column("response_code", sa.Integer, nullable=True), sa.Column("response_body", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="communications")

    op.create_table("callback_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("communication_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("communications.communications.id")),
        sa.Column("event_type", sa.String(50)), sa.Column("payload", postgresql.JSON),
        sa.Column("delivered_to_app", sa.Boolean, default=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="communications")

    op.create_table("queue_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(100)), sa.Column("payload", postgresql.JSON),
        sa.Column("status", sa.String(50), default="queued"), sa.Column("priority", sa.Integer, default=0),
        sa.Column("retry_count", sa.Integer, default=0), sa.Column("max_retries", sa.Integer, default=3),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="communications")


def downgrade() -> None:
    for tbl in ["queue_jobs", "callback_events", "delivery_attempts", "communication_events", "communications"]:
        op.drop_table(tbl, schema="communications", if_exists=True)
