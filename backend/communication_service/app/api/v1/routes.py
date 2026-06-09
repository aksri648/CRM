import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.communication import Communication, CommunicationEvent, DeliveryAttempt, CallbackEvent, QueueJob
from app.schemas import (
    CommunicationCreate, CommunicationResponse, CampaignDispatchRequest, CampaignDispatchResponse,
    EventCreate, EventResponse, CallbackRequest,
)
from app.services.dispatch_service import dispatch_campaign
from app.services.lifecycle_service import record_event, simulate_lifecycle
from app.services.callback_service import send_callback_to_app
from app.utils.logging import logger

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "communication-service", "timestamp": datetime.utcnow().isoformat()}


@router.post("/campaigns/dispatch", response_model=CampaignDispatchResponse)
async def dispatch_campaign_endpoint(data: CampaignDispatchRequest, db: AsyncSession = Depends(get_db)):
    result = await dispatch_campaign(db, data)
    return result


@router.post("/communications", response_model=CommunicationResponse)
async def create_communication(data: CommunicationCreate, db: AsyncSession = Depends(get_db)):
    comm = Communication(campaign_id=data.campaign_id, customer_id=data.customer_id,
                          variant_id=data.variant_id, channel=data.channel,
                          subject_line=data.subject_line, message_body=data.message_body,
                          status="queued", queued_at=datetime.utcnow())
    db.add(comm); await db.commit(); await db.refresh(comm)
    return CommunicationResponse.model_validate(comm)


@router.get("/communications")
async def list_communications(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                               campaign_id: uuid.UUID | None = None, customer_id: uuid.UUID | None = None,
                               status: str | None = None, channel: str | None = None,
                               db: AsyncSession = Depends(get_db)):
    query = select(Communication).order_by(Communication.created_at.desc())
    if campaign_id: query = query.where(Communication.campaign_id == campaign_id)
    if customer_id: query = query.where(Communication.customer_id == customer_id)
    if status: query = query.where(Communication.status == status)
    if channel: query = query.where(Communication.channel == channel)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    comms = result.scalars().all()
    return {"communications": [CommunicationResponse.model_validate(c) for c in comms], "total": total, "page": page, "page_size": page_size}


@router.get("/communications/{communication_id}", response_model=CommunicationResponse)
async def get_communication(communication_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Communication).where(Communication.id == communication_id))
    comm = result.scalar_one_or_none()
    if not comm: raise HTTPException(status_code=404)
    return CommunicationResponse.model_validate(comm)


@router.post("/events", response_model=EventResponse)
async def create_event(data: EventCreate, db: AsyncSession = Depends(get_db)):
    event = await record_event(db, data.communication_id, data.event_type, data.timestamp, data.metadata)
    if not event: raise HTTPException(status_code=404)
    return EventResponse.model_validate(event)


@router.get("/communications/{communication_id}/events")
async def list_events(communication_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CommunicationEvent).where(CommunicationEvent.communication_id == communication_id).order_by(CommunicationEvent.created_at))
    events = result.scalars().all()
    return [{"id": e.id, "communication_id": e.communication_id, "event_type": e.event_type,
             "timestamp": e.timestamp.isoformat() if e.timestamp else None,
             "metadata": e.metadata, "created_at": e.created_at.isoformat() if e.created_at else None} for e in events]


@router.post("/simulate/lifecycle")
async def simulate_communication_lifecycle(communication_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await simulate_lifecycle(db, communication_id)
    if not result: raise HTTPException(status_code=404)
    return result


@router.post("/simulate/campaign/{campaign_id}")
async def simulate_campaign_lifecycle(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Communication).where(Communication.campaign_id == campaign_id))
    comms = result.scalars().all()
    results = []
    for c in comms:
        res = await simulate_lifecycle(db, c.id)
        if res: results.append(res)
    return {"campaign_id": str(campaign_id), "simulated": len(results), "results": results}


@router.post("/callbacks/receive")
async def receive_callback(data: CallbackRequest, db: AsyncSession = Depends(get_db)):
    event = await record_event(db, data.communication_id, data.event_type, data.timestamp, data.metadata)
    if not event: raise HTTPException(status_code=404)
    callback = CallbackEvent(communication_id=data.communication_id, event_type=data.event_type, payload=data.model_dump())
    db.add(callback)
    cb_sent = await send_callback_to_app(data.model_dump())
    if cb_sent: callback.delivered_to_app = True; callback.delivered_at = datetime.utcnow()
    await db.commit()
    return {"event_id": str(event.id), "callback_id": str(callback.id), "delivered_to_app": cb_sent}


@router.get("/pipeline/status")
async def pipeline_status(db: AsyncSession = Depends(get_db)):
    qd = (await db.execute(select(func.count(QueueJob.id)).where(QueueJob.status == "queued"))).scalar() or 0
    rq = (await db.execute(select(func.count(QueueJob.id)).where(QueueJob.status == "retrying"))).scalar() or 0
    dq = (await db.execute(select(func.count(QueueJob.id)).where(QueueJob.status == "failed"))).scalar() or 0
    return {"queue_depth": qd, "retry_queue_size": rq, "dlq_size": dq, "worker_status": "healthy"}


@router.get("/")
async def root():
    return {"service": "Xeno Communication Service", "version": "1.0.0", "status": "running"}
