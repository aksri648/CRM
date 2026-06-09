from app.models.crm import Customer, Order, Product, Segment, SegmentSnapshot
from app.models.campaign import Campaign, CampaignVariant, ABTest, ABTestResult, MarketingGoal, CampaignOpportunity, ApprovalRequest
from app.models.analytics import CampaignPerformance, ChannelPerformance, AudiencePerformance, RevenueAttribution
from app.models.system import AgentRun, AgentDecision, TrendInsight, SchedulerJob, TelegramEvent, AuditLog

__all__ = [
    "Customer", "Order", "Product", "Segment", "SegmentSnapshot",
    "Campaign", "CampaignVariant", "ABTest", "ABTestResult", "MarketingGoal", "CampaignOpportunity", "ApprovalRequest",
    "CampaignPerformance", "ChannelPerformance", "AudiencePerformance", "RevenueAttribution",
    "AgentRun", "AgentDecision", "TrendInsight", "SchedulerJob", "TelegramEvent", "AuditLog",
]
