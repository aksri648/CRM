"""initial schema

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
    for schema in ["crm", "analytics", "system"]:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    op.create_table("customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(255), unique=True, nullable=True),
        sa.Column("first_name", sa.String(255)), sa.Column("last_name", sa.String(255)),
        sa.Column("email", sa.String(255), unique=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("city", sa.String(255), nullable=True), sa.Column("state", sa.String(255), nullable=True),
        sa.Column("country", sa.String(255), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("total_orders", sa.Integer, default=0),
        sa.Column("total_spent", sa.Numeric(12, 2), default=0),
        sa.Column("average_order_value", sa.Numeric(12, 2), default=0),
        sa.Column("last_order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("days_since_last_order", sa.Integer, nullable=True),
        sa.Column("lifecycle_stage", sa.String(50)), sa.Column("rfm_score", sa.String(10)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")
    op.create_index("ix_customers_lifecycle", "customers", ["lifecycle_stage"], schema="crm")
    op.create_index("ix_customers_rfm", "customers", ["rfm_score"], schema="crm")

    op.create_table("products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255)), sa.Column("sku", sa.String(100), unique=True),
        sa.Column("category", sa.String(255)), sa.Column("subcategory", sa.String(255), nullable=True),
        sa.Column("price", sa.Numeric(10, 2)), sa.Column("cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.customers.id")),
        sa.Column("order_date", sa.DateTime(timezone=True)),
        sa.Column("total_amount", sa.Numeric(12, 2)), sa.Column("status", sa.String(50), default="completed"),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.products.id"), nullable=True),
        sa.Column("quantity", sa.Integer, default=1), sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")
    op.create_index("ix_orders_customer", "orders", ["customer_id"], schema="crm")

    op.create_table("segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255)), sa.Column("description", sa.Text, nullable=True),
        sa.Column("criteria", postgresql.JSON), sa.Column("customer_count", sa.Integer, default=0),
        sa.Column("is_dynamic", sa.Boolean, default=True), sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("segment_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.segments.id")),
        sa.Column("customer_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column("customer_count", sa.Integer),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("marketing_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("description", sa.Text), sa.Column("objective", sa.String(100)),
        sa.Column("target_metric", sa.String(100), nullable=True),
        sa.Column("target_value", sa.Float, nullable=True), sa.Column("status", sa.String(50), default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255)), sa.Column("description", sa.Text, nullable=True),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.marketing_goals.id"), nullable=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.segments.id"), nullable=True),
        sa.Column("channel", sa.String(50), default="email"), sa.Column("status", sa.String(50), default="draft"),
        sa.Column("ai_generated", sa.Boolean, default=False),
        sa.Column("reasoning", postgresql.JSON, nullable=True),
        sa.Column("expected_reach", sa.Integer, nullable=True), sa.Column("expected_ctr", sa.Float, nullable=True),
        sa.Column("expected_revenue", sa.Numeric(12, 2), nullable=True),
        sa.Column("approval_status", sa.String(50), default="pending"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("launched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")
    op.create_index("ix_campaigns_status", "campaigns", ["status"], schema="crm")

    op.create_table("campaign_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.campaigns.id")),
        sa.Column("name", sa.String(255)), sa.Column("variant_type", sa.String(50), default="A"),
        sa.Column("subject_line", sa.String(500), nullable=True), sa.Column("message_body", sa.Text),
        sa.Column("cta_text", sa.String(255), nullable=True), sa.Column("style", sa.String(50), nullable=True),
        sa.Column("traffic_allocation", sa.Integer, nullable=True), sa.Column("is_winner", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("ab_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.campaigns.id")),
        sa.Column("name", sa.String(255)), sa.Column("hypothesis", sa.Text, nullable=True),
        sa.Column("audience_split", postgresql.JSON), sa.Column("success_metric", sa.String(100), default="conversion_rate"),
        sa.Column("min_confidence", sa.Float, default=0.95), sa.Column("status", sa.String(50), default="running"),
        sa.Column("winner_variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confidence_level", sa.Float, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("ab_test_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ab_test_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.ab_tests.id")),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.campaign_variants.id")),
        sa.Column("sent_count", sa.Integer, default=0), sa.Column("delivered_count", sa.Integer, default=0),
        sa.Column("open_count", sa.Integer, default=0), sa.Column("click_count", sa.Integer, default=0),
        sa.Column("conversion_count", sa.Integer, default=0), sa.Column("revenue", sa.Numeric(12, 2), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("campaign_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255)), sa.Column("description", sa.Text, nullable=True),
        sa.Column("opportunity_type", sa.String(100)),
        sa.Column("expected_revenue", sa.Numeric(12, 2), nullable=True),
        sa.Column("expected_reach", sa.Integer, nullable=True),
        sa.Column("recommended_channel", sa.String(50), nullable=True),
        sa.Column("rationale", postgresql.JSON, nullable=True), sa.Column("status", sa.String(50), default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.campaigns.id"), unique=True),
        sa.Column("request_type", sa.String(50), default="campaign_launch"),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("requested_by", sa.String(255), nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reasoning", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm")

    op.create_table("campaign_performance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.campaigns.id"), unique=True),
        sa.Column("sent_count", sa.Integer, default=0), sa.Column("delivered_count", sa.Integer, default=0),
        sa.Column("open_count", sa.Integer, default=0), sa.Column("read_count", sa.Integer, default=0),
        sa.Column("click_count", sa.Integer, default=0), sa.Column("conversion_count", sa.Integer, default=0),
        sa.Column("revenue", sa.Numeric(12, 2), default=0),
        sa.Column("delivery_rate", sa.Float, nullable=True), sa.Column("open_rate", sa.Float, nullable=True),
        sa.Column("read_rate", sa.Float, nullable=True), sa.Column("click_through_rate", sa.Float, nullable=True),
        sa.Column("conversion_rate", sa.Float, nullable=True),
        sa.Column("unsubscribes", sa.Integer, default=0), sa.Column("complaints", sa.Integer, default=0),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="analytics")

    op.create_table("channel_performance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("channel", sa.String(50)), sa.Column("sent_count", sa.Integer, default=0),
        sa.Column("delivered_count", sa.Integer, default=0), sa.Column("open_count", sa.Integer, default=0),
        sa.Column("click_count", sa.Integer, default=0), sa.Column("conversion_count", sa.Integer, default=0),
        sa.Column("revenue", sa.Numeric(12, 2), default=0),
        sa.Column("delivery_rate", sa.Float, nullable=True), sa.Column("open_rate", sa.Float, nullable=True),
        sa.Column("click_through_rate", sa.Float, nullable=True), sa.Column("conversion_rate", sa.Float, nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True)), sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="analytics")

    op.create_table("audience_performance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.segments.id")),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.campaigns.id"), nullable=True),
        sa.Column("sent_count", sa.Integer, default=0), sa.Column("open_count", sa.Integer, default=0),
        sa.Column("click_count", sa.Integer, default=0), sa.Column("conversion_count", sa.Integer, default=0),
        sa.Column("revenue", sa.Numeric(12, 2), default=0),
        sa.Column("period_start", sa.DateTime(timezone=True)), sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="analytics")

    op.create_table("revenue_attribution",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.campaigns.id")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.orders.id")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm.customers.id")),
        sa.Column("revenue", sa.Numeric(12, 2)), sa.Column("attribution_model", sa.String(50), default="last_touch"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="analytics")

    op.create_table("agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_type", sa.String(100)), sa.Column("status", sa.String(50), default="running"),
        sa.Column("input_data", postgresql.JSON, nullable=True),
        sa.Column("output_data", postgresql.JSON, nullable=True),
        sa.Column("trace", postgresql.JSON, nullable=True), sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="system")

    op.create_table("agent_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("system.agent_runs.id")),
        sa.Column("agent_name", sa.String(100)),
        sa.Column("input_data", postgresql.JSON, nullable=True),
        sa.Column("output_data", postgresql.JSON, nullable=True),
        sa.Column("reasoning", sa.Text, nullable=True), sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("supporting_data", postgresql.JSON, nullable=True),
        sa.Column("predicted_outcome", postgresql.JSON, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True), sa.Column("tool_calls", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="system")

    op.create_table("trend_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("insight_type", sa.String(100)), sa.Column("title", sa.String(255)),
        sa.Column("description", sa.Text, nullable=True), sa.Column("data", postgresql.JSON, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("source_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("system.agent_runs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="system")

    op.create_table("scheduler_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(100)), sa.Column("status", sa.String(50), default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", postgresql.JSON, nullable=True), sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="system")

    op.create_table("telegram_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100)), sa.Column("payload", postgresql.JSON),
        sa.Column("status", sa.String(50), default="received"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="system")

    op.create_table("audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action", sa.String(255)), sa.Column("entity_type", sa.String(100)),
        sa.Column("entity_id", sa.String(255), nullable=True), sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("changes", postgresql.JSON, nullable=True), sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="system")


def downgrade() -> None:
    for tbl in ["audit_logs", "telegram_events", "scheduler_jobs", "trend_insights", "agent_decisions", "agent_runs",
                "revenue_attribution", "audience_performance", "channel_performance", "campaign_performance",
                "approval_requests", "campaign_opportunities", "ab_test_results", "ab_tests", "campaign_variants",
                "campaigns", "marketing_goals", "segment_snapshots", "segments", "orders", "products", "customers"]:
        op.drop_table(tbl, schema="analytics" if tbl in ["campaign_performance","channel_performance","audience_performance","revenue_attribution"] else "system" if tbl in ["agent_runs","agent_decisions","trend_insights","scheduler_jobs","telegram_events","audit_logs"] else "crm", if_exists=True)
