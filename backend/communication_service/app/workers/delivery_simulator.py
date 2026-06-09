from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.communication import Communication
from app.services.lifecycle_service import simulate_lifecycle


async def run_delivery_simulation(db: AsyncSession, batch_size: int = 50) -> dict:
    result = await db.execute(select(Communication).where(Communication.status == "queued").limit(batch_size))
    comms = result.scalars().all()
    results = []
    for c in comms:
        res = await simulate_lifecycle(db, c.id)
        if res: results.append(res)
    return {"processed": len(results), "statuses": [r["final_status"] for r in results]}
