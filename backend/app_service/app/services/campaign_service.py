import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaign import Campaign, CampaignVariant, MarketingGoal, CampaignOpportunity
from app.schemas import CampaignCreate, CampaignResponse, MarketingGoalCreate


async def create_campaign(db: AsyncSession, data: CampaignCreate, user: str | None = None) -> Campaign:
    campaign = Campaign(
        name=data.name,
        description=data.description,
        goal_id=data.goal_id,
        segment_id=data.segment_id,
        channel=data.channel,
        scheduled_at=data.scheduled_at,
        created_by=user,
    )
    db.add(campaign)
    await db.flush()
    for v_data in data.variants:
        variant = CampaignVariant(
            campaign_id=campaign.id,
            name=v_data.name,
            variant_type=v_data.variant_type,
            subject_line=v_data.subject_line,
            message_body=v_data.message_body,
            cta_text=v_data.cta_text,
            style=v_data.style,
            traffic_allocation=v_data.traffic_allocation,
        )
        db.add(variant)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def get_campaign(db: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.variants), selectinload(Campaign.marketing_goal))
        .where(Campaign.id == campaign_id)
    )
    return result.scalar_one_or_none()


async def list_campaigns(db: AsyncSession, page: int = 1, page_size: int = 20,
                          status: str | None = None, channel: str | None = None) -> dict:
    query = select(Campaign).options(selectinload(Campaign.variants)).order_by(Campaign.created_at.desc())
    if status:
        query = query.where(Campaign.status == status)
    if channel:
        query = query.where(Campaign.channel == channel)
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    campaigns = result.scalars().all()
    return {"campaigns": [CampaignResponse.model_validate(c) for c in campaigns], "total": total, "page": page, "page_size": page_size}


async def launch_campaign(db: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        return None
    campaign.status = "launched"
    campaign.launched_at = datetime.utcnow()
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def create_marketing_goal(db: AsyncSession, data: MarketingGoalCreate) -> MarketingGoal:
    goal = MarketingGoal(**data.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def list_marketing_goals(db: AsyncSession) -> list[MarketingGoal]:
    result = await db.execute(select(MarketingGoal).order_by(MarketingGoal.created_at.desc()))
    return result.scalars().all()


async def list_opportunities(db: AsyncSession, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    query = select(CampaignOpportunity).order_by(CampaignOpportunity.created_at.desc())
    if status:
        query = query.where(CampaignOpportunity.status == status)
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    opportunities = result.scalars().all()
    return {"opportunities": list(opportunities), "total": total, "page": page, "page_size": page_size}
