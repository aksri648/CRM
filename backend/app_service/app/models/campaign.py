import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Integer, Numeric, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class MarketingGoal(Base):
    __tablename__ = "marketing_goals"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description: Mapped[str] = mapped_column(Text)
    objective: Mapped[str] = mapped_column(String(100))
    target_metric: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="marketing_goal")


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.marketing_goals.id"), nullable=True)
    segment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.segments.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    reasoning: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_revenue: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="pending")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    launched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    marketing_goal = relationship("MarketingGoal", back_populates="campaigns")
    variants = relationship("CampaignVariant", back_populates="campaign")
    approval_request = relationship("ApprovalRequest", back_populates="campaign", uselist=False)
    performance = relationship("CampaignPerformance", back_populates="campaign", uselist=False)
    ab_tests = relationship("ABTest", back_populates="campaign")


class CampaignVariant(Base):
    __tablename__ = "campaign_variants"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.campaigns.id"))
    name: Mapped[str] = mapped_column(String(255))
    variant_type: Mapped[str] = mapped_column(String(50), default="A")
    subject_line: Mapped[str | None] = mapped_column(String(500), nullable=True)
    message_body: Mapped[str] = mapped_column(Text)
    cta_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    traffic_allocation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="variants")


class ABTest(Base):
    __tablename__ = "ab_tests"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.campaigns.id"))
    name: Mapped[str] = mapped_column(String(255))
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience_split: Mapped[dict] = mapped_column(JSON, default=dict)
    success_metric: Mapped[str] = mapped_column(String(100), default="conversion_rate")
    min_confidence: Mapped[float] = mapped_column(Float, default=0.95)
    status: Mapped[str] = mapped_column(String(50), default="running")
    winner_variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="ab_tests")
    results = relationship("ABTestResult", back_populates="ab_test")


class ABTestResult(Base):
    __tablename__ = "ab_test_results"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ab_test_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.ab_tests.id"))
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.campaign_variants.id"))
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    conversion_count: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    ab_test = relationship("ABTest", back_populates="results")


class CampaignOpportunity(Base):
    __tablename__ = "campaign_opportunities"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_type: Mapped[str] = mapped_column(String(100))
    expected_revenue: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    expected_reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rationale: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.campaigns.id"), unique=True)
    request_type: Mapped[str] = mapped_column(String(50), default="campaign_launch")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    requested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reasoning: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="approval_request")
