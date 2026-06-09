import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analytics import CampaignPerformance, ChannelPerformance
from app.models.campaign import Campaign
from app.models.crm import Customer
from app.services.cache_service import cache_get, cache_set, cache_delete


async def compute_campaign_performance(db: AsyncSession, campaign_id: uuid.UUID) -> CampaignPerformance | None:
    result = await db.execute(select(CampaignPerformance).where(CampaignPerformance.campaign_id == campaign_id))
    return result.scalar_one_or_none()


async def get_channel_performance(db: AsyncSession, channel: str | None = None,
                                    period_start: datetime | None = None,
                                    period_end: datetime | None = None) -> list[ChannelPerformance]:
    query = select(ChannelPerformance)
    if channel:
        query = query.where(ChannelPerformance.channel == channel)
    if period_start:
        query = query.where(ChannelPerformance.period_start >= period_start)
    if period_end:
        query = query.where(ChannelPerformance.period_end <= period_end)
    query = query.order_by(ChannelPerformance.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_dashboard_stats(db: AsyncSession) -> dict:
    cache_key = "dashboard:global"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    total_customers = (await db.execute(select(func.count(Customer.id)))).scalar() or 0
    active_campaigns = (await db.execute(
        select(func.count(Campaign.id)).where(Campaign.status.in_(["launched", "active"]))
    )).scalar() or 0

    perf_result = await db.execute(select(CampaignPerformance))
    performances = perf_result.scalars().all()

    total_sent = sum(p.sent_count for p in performances)
    total_revenue = sum(float(p.revenue) for p in performances)
    total_opens = sum(p.open_count for p in performances)
    total_clicks = sum(p.click_count for p in performances)
    total_conversions = sum(p.conversion_count for p in performances)

    avg_open_rate = (total_opens / total_sent * 100) if total_sent > 0 else 0
    avg_ctr = (total_clicks / total_sent * 100) if total_sent > 0 else 0
    avg_conversion_rate = (total_conversions / total_sent * 100) if total_sent > 0 else 0

    channel_perf = await get_channel_performance(db)
    channel_breakdown = [
        {
            "channel": cp.channel, "sent_count": cp.sent_count, "delivered_count": cp.delivered_count,
            "open_count": cp.open_count, "click_count": cp.click_count, "conversion_count": cp.conversion_count,
            "revenue": float(cp.revenue), "open_rate": cp.open_rate, "click_through_rate": cp.click_through_rate,
        }
        for cp in channel_perf
    ]
    recent_result = await db.execute(
        select(Campaign).options(selectinload(Campaign.variants)).order_by(Campaign.created_at.desc()).limit(10)
    )
    recent_campaigns = recent_result.scalars().all()

    stats = {
        "total_customers": total_customers, "active_campaigns": active_campaigns,
        "total_sent": total_sent, "total_revenue": float(total_revenue),
        "avg_open_rate": round(avg_open_rate, 2), "avg_ctr": round(avg_ctr, 2),
        "avg_conversion_rate": round(avg_conversion_rate, 2),
        "channel_breakdown": channel_breakdown,
        "recent_campaigns": [
            {"id": str(c.id), "name": c.name, "channel": c.channel, "status": c.status,
             "approval_status": c.approval_status, "created_at": c.created_at.isoformat() if c.created_at else None}
            for c in recent_campaigns
        ],
    }
    await cache_set(cache_key, stats, ttl=120)
    return stats


async def invalidate_analytics_cache():
    await cache_delete("dashboard:global")


async def update_campaign_performance_from_callback(db: AsyncSession, campaign_id: uuid.UUID, event_type: str, metadata: dict | None = None):
    result = await db.execute(select(CampaignPerformance).where(CampaignPerformance.campaign_id == campaign_id))
    perf = result.scalar_one_or_none()
    if not perf:
        perf = CampaignPerformance(campaign_id=campaign_id)
        db.add(perf)

    if event_type == "sent":
        perf.sent_count += 1
    elif event_type == "delivered":
        perf.delivered_count += 1
    elif event_type == "opened":
        perf.open_count += 1
    elif event_type == "read":
        perf.read_count += 1
    elif event_type == "clicked":
        perf.click_count += 1
    elif event_type == "converted":
        perf.conversion_count += 1
        if metadata and "revenue" in metadata:
            perf.revenue += Decimal(str(metadata["revenue"]))

    total_sent = perf.sent_count or 1
    delivered = perf.delivered_count or 1
    opened = perf.open_count or 1
    clicked = perf.click_count or 1
    perf.delivery_rate = round((perf.delivered_count / total_sent) * 100, 2)
    perf.open_rate = round((perf.open_count / delivered) * 100, 2)
    perf.click_through_rate = round((perf.click_count / opened) * 100, 2)
    perf.conversion_rate = round((perf.conversion_count / clicked) * 100, 2)
    perf.computed_at = datetime.utcnow()
    await db.commit()
