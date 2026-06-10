from operator import add
from typing import Optional
from typing_extensions import Annotated, TypedDict


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
    errors: Annotated[list[str], add]
    agent_trace: Annotated[list, add]
    current_agent: str
