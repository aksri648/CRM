import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.communication import Communication, QueueJob, DeliveryAttempt
from app.services.lifecycle_service import simulate_lifecycle
from app.config import settings
from app.utils.logging import logger


class QueueProcessor:
    def __init__(self, db: AsyncSession): self.db = db

    async def process_batch(self, batch_size: int | None = None) -> int:
        size = batch_size or settings.BATCH_SIZE
        result = await self.db.execute(
            select(QueueJob).where(QueueJob.status == "queued")
            .where(QueueJob.retry_count < QueueJob.max_retries)
            .order_by(QueueJob.priority.desc(), QueueJob.created_at).limit(size))
        jobs = result.scalars().all()
        processed = 0
        for job in jobs:
            try:
                await self._process_job(job); processed += 1
            except Exception as e:
                job.retry_count += 1; job.last_error = str(e)
                job.status = "retrying" if job.retry_count < job.max_retries else "failed"
        await self.db.commit()
        return processed

    async def _process_job(self, job: QueueJob) -> None:
        job.started_at = datetime.utcnow(); job.status = "processing"
        payload = job.payload; comm_id = payload.get("communication_id")
        if comm_id:
            comm = (await self.db.execute(select(Communication).where(Communication.id == uuid.UUID(comm_id)))).scalar_one_or_none()
            if comm:
                self.db.add(DeliveryAttempt(communication_id=comm.id, attempt_number=comm.retry_count + 1, status="processing"))
        if job.job_type in ("delivery", "campaign_delivery") and comm_id:
            await simulate_lifecycle(self.db, uuid.UUID(comm_id))
        job.status = "completed"; job.completed_at = datetime.utcnow()
