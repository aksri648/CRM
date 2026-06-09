from typing import Optional
from typing_extensions import TypedDict


class MarketingState(TypedDict):
    goal: str
    audience: Optional[dict]
    segment: Optional[dict]
    campaign_strategy: Optional[dict]
    channel: Optional[dict]
    message_variants: Optional[list]
    ab_test: Optional[dict]
    proposal: Optional[dict]
    approval_status: str
    analytics: Optional[dict]
    reasoning: Optional[str]
    confidence: Optional[float]
    metadata: dict
    errors: list[str]
    agent_trace: list
    current_agent: str
