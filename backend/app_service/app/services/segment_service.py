import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crm import Segment, SegmentSnapshot, Customer
from app.schemas import SegmentCreate, SegmentResponse


async def create_segment(db: AsyncSession, data: SegmentCreate) -> Segment:
    segment = Segment(name=data.name, description=data.description, criteria=data.criteria, is_dynamic=data.is_dynamic)
    db.add(segment)
    await db.commit()
    await db.refresh(segment)
    return segment


async def get_segment(db: AsyncSession, segment_id: uuid.UUID) -> Segment | None:
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    return result.scalar_one_or_none()


async def list_segments(db: AsyncSession, page: int = 1, page_size: int = 20) -> dict:
    query = select(Segment).order_by(Segment.created_at.desc())
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    segments = result.scalars().all()
    return {"segments": [SegmentResponse.model_validate(s) for s in segments], "total": total, "page": page, "page_size": page_size}


async def evaluate_segment_criteria(db: AsyncSession, criteria: dict) -> list[Customer]:
    query = select(Customer).where(Customer.is_active == True)
    if criteria.get("lifecycle_stage"):
        query = query.where(Customer.lifecycle_stage == criteria["lifecycle_stage"])
    if criteria.get("min_orders"):
        query = query.where(Customer.total_orders >= criteria["min_orders"])
    if criteria.get("max_orders"):
        query = query.where(Customer.total_orders <= criteria["max_orders"])
    if criteria.get("min_spent"):
        query = query.where(Customer.total_spent >= criteria["min_spent"])
    if criteria.get("max_spent"):
        query = query.where(Customer.total_spent <= criteria["max_spent"])
    if criteria.get("min_days_since_order"):
        query = query.where(Customer.days_since_last_order.isnot(None), Customer.days_since_last_order >= criteria["min_days_since_order"])
    if criteria.get("max_days_since_order"):
        query = query.where(Customer.days_since_last_order.isnot(None), Customer.days_since_last_order <= criteria["max_days_since_order"])
    result = await db.execute(query)
    return list(result.scalars().all())


async def snapshot_segment(db: AsyncSession, segment_id: uuid.UUID) -> SegmentSnapshot | None:
    segment = await get_segment(db, segment_id)
    if not segment:
        return None
    customers = await evaluate_segment_criteria(db, segment.criteria)
    snapshot = SegmentSnapshot(segment_id=segment_id, customer_ids=[c.id for c in customers], customer_count=len(customers))
    segment.customer_count = len(customers)
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot
