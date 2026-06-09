import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Customer, Order
from app.schemas import CustomerResponse, OrderResponse


async def list_customers(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    lifecycle_stage: str | None = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
) -> dict:
    query = select(Customer)
    if search:
        query = query.where(
            Customer.first_name.ilike(f"%{search}%") |
            Customer.last_name.ilike(f"%{search}%") |
            Customer.email.ilike(f"%{search}%")
        )
    if lifecycle_stage:
        query = query.where(Customer.lifecycle_stage == lifecycle_stage)
    sort_col = getattr(Customer, sort_by, Customer.created_at)
    query = query.order_by(sort_col.desc() if sort_desc else sort_col.asc())
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    customers = result.scalars().all()
    return {"customers": [CustomerResponse.model_validate(c) for c in customers], "total": total, "page": page, "page_size": page_size}


async def get_customer(db: AsyncSession, customer_id: uuid.UUID) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()


async def get_customer_orders(db: AsyncSession, customer_id: uuid.UUID, page: int = 1, page_size: int = 20) -> dict:
    query = select(Order).where(Order.customer_id == customer_id).order_by(Order.order_date.desc())
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()
    return {"orders": [OrderResponse.model_validate(o) for o in orders], "total": total, "page": page, "page_size": page_size}


async def get_lifecycle_distribution(db: AsyncSession) -> list[dict]:
    query = select(Customer.lifecycle_stage, func.count(Customer.id)).where(Customer.lifecycle_stage.isnot(None)).group_by(Customer.lifecycle_stage)
    result = await db.execute(query)
    return [{"stage": row[0], "count": row[1]} for row in result.all()]
