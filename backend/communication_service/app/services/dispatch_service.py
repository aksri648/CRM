import httpx
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.communication import Communication, QueueJob
from app.schemas import CampaignDispatchRequest, CampaignDispatchResponse
from app.utils.logging import logger


async def _trigger_workflow(campaign_id: uuid.UUID, communication_ids: list[uuid.UUID]) -> str | None:
    """Kick off the Cloudflare Workflow for the campaign. Returns instance_id, or None on failure."""
    if not settings.WORKFLOWS_ENABLED:
        return None
    if not settings.WORKER_INTERNAL_URL or not settings.INTERNAL_SHARED_TOKEN:
        logger.warning("workflow_dispatch_skipped_missing_config")
        return None

    url = f"{settings.WORKER_INTERNAL_URL}/internal/workflows/dispatch"
    payload = {
        "campaign_id": str(campaign_id),
        "communication_ids": [str(cid) for cid in communication_ids],
        "batch_size": settings.WORKFLOW_BATCH_SIZE,
        "rate_limit_seconds": settings.WORKFLOW_RATE_LIMIT_SECONDS,
    }
    headers = {"X-Internal-Token": settings.INTERNAL_SHARED_TOKEN}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        logger.error("workflow_dispatch_network_error", error=str(exc))
        return None
    if resp.status_code >= 400:
        logger.error("workflow_dispatch_failed", status=resp.status_code, body=resp.text[:300])
        return None
    body = resp.json()
    return body.get("instance_id")


async def dispatch_campaign(db: AsyncSession, data: CampaignDispatchRequest) -> CampaignDispatchResponse:
    comms: list[Communication] = []
    for cid in data.customer_ids:
        comm = Communication(
            campaign_id=data.campaign_id, customer_id=cid, variant_id=data.variant_id,
            channel=data.channel, subject_line=data.subject_line, message_body=data.message_body,
            status="queued", queued_at=datetime.utcnow(),
        )
        db.add(comm)
        comms.append(comm)
    await db.flush()

    workflow_instance_id: str | None = None
    if settings.WORKFLOWS_ENABLED:
        workflow_instance_id = await _trigger_workflow(
            data.campaign_id, [c.id for c in comms]
        )

    if not workflow_instance_id:
        for comm in comms:
            db.add(QueueJob(
                job_type="campaign_delivery",
                payload={
                    "communication_id": str(comm.id),
                    "campaign_id": str(data.campaign_id),
                    "customer_id": str(comm.customer_id),
                    "channel": data.channel,
                },
                status="queued", scheduled_at=datetime.utcnow(),
            ))

    await db.commit()
    logger.info(
        "campaign_dispatched",
        campaign_id=str(data.campaign_id),
        total=len(comms),
        path="workflow" if workflow_instance_id else "in_process_queue",
        workflow_instance=workflow_instance_id,
    )
    return CampaignDispatchResponse(
        campaign_id=data.campaign_id,
        total_communications=len(data.customer_ids),
        queued_count=len(comms),
        status="dispatched",
    )
