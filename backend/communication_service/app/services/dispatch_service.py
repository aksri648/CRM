import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.communication import Communication, QueueJob
from app.schemas import CampaignDispatchRequest, CampaignDispatchResponse
from app.utils.logging import logger


async def dispatch_campaign(db: AsyncSession, data: CampaignDispatchRequest) -> CampaignDispatchResponse:
    comms = []
    for cid in data.customer_ids:
        comm = Communication(campaign_id=data.campaign_id, customer_id=cid, variant_id=data.variant_id,
                              channel=data.channel, subject_line=data.subject_line, message_body=data.message_body,
                              status="queued", queued_at=datetime.utcnow())
        db.add(comm); comms.append(comm)
    await db.flush()
    for comm in comms:
        db.add(QueueJob(job_type="campaign_delivery",
                        payload={"communication_id": str(comm.id), "campaign_id": str(data.campaign_id),
                                 "customer_id": str(comm.customer_id), "channel": data.channel},
                        status="queued", scheduled_at=datetime.utcnow()))
    await db.commit()
    logger.info("campaign_dispatched", campaign_id=str(data.campaign_id), total=len(comms))
    return CampaignDispatchResponse(campaign_id=data.campaign_id, total_communications=len(data.customer_ids),
                                     queued_count=len(comms), status="dispatched")
