from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS crm"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS system"))
        from app.models.crm import Customer, Order, Product, Segment, SegmentSnapshot
        from app.models.campaign import Campaign, CampaignVariant, ABTest, ABTestResult, MarketingGoal, CampaignOpportunity, ApprovalRequest
        from app.models.analytics import CampaignPerformance, ChannelPerformance, AudiencePerformance, RevenueAttribution
        from app.models.system import AgentRun, AgentDecision, TrendInsight, SchedulerJob, TelegramEvent, AuditLog
        await conn.run_sync(Base.metadata.create_all)
