import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class CustomerResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    tags: list[str] | None = None
    total_orders: int = 0
    total_spent: float = 0
    average_order_value: float = 0
    lifecycle_stage: str | None = None
    rfm_score: str | None = None
    days_since_last_order: int | None = None
    is_active: bool = True
    created_at: datetime | None = None
    name: str | None = None
    ltv: float | None = None
    orders: int | None = None
    last_order_date: str | None = None

    @model_validator(mode='after')
    def alias_fields(self):
        if not self.name:
            self.name = f'{self.first_name or ""} {self.last_name or ""}'.strip() or None
        if self.ltv is None:
            self.ltv = float(self.total_spent) if self.total_spent is not None else None
        if self.orders is None:
            self.orders = self.total_orders
        if self.days_since_last_order is not None and self.last_order_date is None:
            self.last_order_date = f'{self.days_since_last_order}d ago'
        return self

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    customers: list[CustomerResponse]
    total: int
    page: int
    page_size: int


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    sku: str
    category: str
    subcategory: str | None = None
    price: float
    is_active: bool = True

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    order_date: datetime
    total_amount: float
    status: str
    product_id: uuid.UUID | None = None
    quantity: int = 1
    channel: str | None = None

    class Config:
        from_attributes = True


class SegmentCreate(BaseModel):
    name: str
    description: str | None = None
    criteria: dict = Field(default_factory=dict)
    is_dynamic: bool = True


class SegmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    criteria: dict
    customer_count: int = 0
    is_dynamic: bool = True
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class CampaignVariantCreate(BaseModel):
    name: str
    variant_type: str = "A"
    subject_line: str | None = None
    message_body: str
    cta_text: str | None = None
    style: str | None = None
    traffic_allocation: int | None = None


class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    goal_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    channel: str = "email"
    variants: list[CampaignVariantCreate] = Field(default_factory=list)
    scheduled_at: datetime | None = None


class CampaignVariantResponse(BaseModel):
    id: uuid.UUID
    name: str
    variant_type: str
    subject_line: str | None = None
    message_body: str
    cta_text: str | None = None
    style: str | None = None
    traffic_allocation: int | None = None
    is_winner: bool = False

    class Config:
        from_attributes = True


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    goal_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    channel: str
    status: str
    ai_generated: bool = False
    reasoning: dict | str | None = None
    expected_reach: int | None = None
    expected_ctr: float | None = None
    expected_revenue: float | None = None
    approval_status: str = "pending"
    scheduled_at: datetime | None = None
    launched_at: datetime | None = None
    completed_at: datetime | None = None
    variants: list[CampaignVariantResponse] = Field(default_factory=list)
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    campaigns: list[CampaignResponse]
    total: int
    page: int
    page_size: int


class CallbackEvent(BaseModel):
    communication_id: uuid.UUID
    campaign_id: uuid.UUID
    customer_id: uuid.UUID
    event_type: str
    timestamp: datetime | None = None
    metadata: dict | None = None


class ABTestCreate(BaseModel):
    name: str
    campaign_id: uuid.UUID
    hypothesis: str | None = None
    audience_split: dict = Field(default_factory=dict)
    success_metric: str = "conversion_rate"
    min_confidence: float = 0.95


class ABTestResponse(BaseModel):
    id: uuid.UUID
    name: str
    campaign_id: uuid.UUID
    hypothesis: str | None = None
    audience_split: dict
    success_metric: str
    min_confidence: float
    status: str
    winner_variant_id: uuid.UUID | None = None
    confidence_level: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: list = Field(default_factory=list)

    class Config:
        from_attributes = True


class CampaignPerformanceResponse(BaseModel):
    sent_count: int = 0
    delivered_count: int = 0
    open_count: int = 0
    read_count: int = 0
    click_count: int = 0
    conversion_count: int = 0
    revenue: float = 0
    delivery_rate: float | None = None
    open_rate: float | None = None
    read_rate: float | None = None
    click_through_rate: float | None = None
    conversion_rate: float | None = None

    class Config:
        from_attributes = True


class ChannelPerformanceResponse(BaseModel):
    channel: str
    sent_count: int = 0
    delivered_count: int = 0
    open_count: int = 0
    click_count: int = 0
    conversion_count: int = 0
    revenue: float = 0
    delivery_rate: float | None = None
    open_rate: float | None = None
    click_through_rate: float | None = None
    conversion_rate: float | None = None

    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    campaign_name: str | None = None
    request_type: str
    status: str
    requested_by: str | None = None
    reasoning: dict | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    approved_by: str | None = None


class DashboardStatsResponse(BaseModel):
    total_customers: int = 0
    active_campaigns: int = 0
    total_sent: int = 0
    total_revenue: float = 0
    avg_open_rate: float = 0
    avg_ctr: float = 0
    avg_conversion_rate: float = 0
    channel_breakdown: list[ChannelPerformanceResponse] = Field(default_factory=list)
    recent_campaigns: list[CampaignResponse] = Field(default_factory=list)


class OpportunityResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    opportunity_type: str
    expected_revenue: float | None = None
    expected_reach: int | None = None
    recommended_channel: str | None = None
    rationale: dict | None = None
    status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ProposalResponse(BaseModel):
    run_id: uuid.UUID
    campaign: CampaignResponse | None = None
    reasoning: dict | None = None
    agent_trace: list[dict] = Field(default_factory=list)
    approval: ApprovalResponse | None = None
    created_at: datetime | None = None


class MarketingGoalCreate(BaseModel):
    description: str
    objective: str
    target_metric: str | None = None
    target_value: float | None = None


class MarketingGoalResponse(BaseModel):
    id: uuid.UUID
    description: str
    objective: str
    target_metric: str | None = None
    target_value: float | None = None
    status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PipelineStatusResponse(BaseModel):
    queue_depth: int = 0
    processing_rate: float = 0
    recent_events: list[dict] = Field(default_factory=list)
    retry_queue_size: int = 0
    dlq_size: int = 0
    worker_status: str = "healthy"
