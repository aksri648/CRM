import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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


RESEND_EVENT_MAP = {
    "email.sent": "sent",
    "email.delivered": "delivered",
    "email.opened": "opened",
    "email.clicked": "clicked",
    "email.bounced": "failed",
    "email.complained": "failed",
    "email.delivery_delayed": "delayed",
}

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
             "metadata": e.event_metadata, "created_at": e.created_at.isoformat() if e.created_at else None} for e in events]


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
    if cb_sent: callback.delivered_to_agent = True; callback.delivered_at = datetime.utcnow()
    await db.commit()
    return {"event_id": str(event.id), "callback_id": str(callback.id), "delivered_to_app": cb_sent}


def _require_internal_token(x_internal_token: str | None) -> None:
    expected = settings.INTERNAL_SHARED_TOKEN
    if not expected or x_internal_token != expected:
        raise HTTPException(status_code=401, detail="Invalid internal token")


@router.post("/internal/process-batch")
async def internal_process_batch(
    payload: dict,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
    db: AsyncSession = Depends(get_db),
):
    _require_internal_token(x_internal_token)
    ids = payload.get("communication_ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail="communication_ids required")

    processed = 0
    errors: list[dict] = []
    for raw_id in ids:
        try:
            comm_id = uuid.UUID(raw_id)
        except (ValueError, TypeError):
            errors.append({"id": raw_id, "error": "invalid uuid"})
            continue
        try:
            result = await simulate_lifecycle(db, comm_id)
            if result:
                processed += 1
            else:
                errors.append({"id": raw_id, "error": "communication not found"})
        except Exception as exc:
            logger.error("process_batch_item_failed", id=raw_id, error=str(exc))
            errors.append({"id": raw_id, "error": str(exc)})

    return {"processed": processed, "total": len(ids), "errors": errors}


@router.post("/webhooks/resend")
async def resend_webhook(request: Request, token: str = Query(default=""), db: AsyncSession = Depends(get_db)):
    expected = settings.RESEND_WEBHOOK_SECRET
    if not expected or token != expected:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type_raw = body.get("type") or body.get("event")
    mapped = RESEND_EVENT_MAP.get(event_type_raw)
    if not mapped:
        logger.info("resend_webhook_unhandled_type", type=event_type_raw)
        return {"status": "ignored", "type": event_type_raw}

    data = body.get("data") or {}
    communication_id = None
    for tag in data.get("tags") or []:
        if tag.get("name") == "communication_id":
            communication_id = tag.get("value")
            break
    if not communication_id:
        external_id = data.get("email_id") or data.get("id")
        if external_id:
            result = await db.execute(select(Communication).where(Communication.external_id == external_id))
            comm = result.scalar_one_or_none()
            if comm:
                communication_id = str(comm.id)

    if not communication_id:
        logger.warning("resend_webhook_no_communication", payload_keys=list(data.keys()))
        return {"status": "ignored", "reason": "no communication_id"}

    metadata = {"provider_event": event_type_raw}
    if mapped == "failed":
        metadata["reason"] = data.get("reason") or event_type_raw

    event = await record_event(db, uuid.UUID(communication_id), mapped, metadata=metadata)
    if not event:
        return {"status": "ignored", "reason": "communication not found"}

    result = await db.execute(select(Communication).where(Communication.id == uuid.UUID(communication_id)))
    comm = result.scalar_one_or_none()
    if comm:
        await send_callback_to_app({
            "communication_id": communication_id, "campaign_id": str(comm.campaign_id),
            "customer_id": str(comm.customer_id), "event_type": mapped,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata,
        })

    return {"status": "recorded", "event_type": mapped}


@router.get("/pipeline/status")
async def pipeline_status(db: AsyncSession = Depends(get_db)):
    qd = (await db.execute(select(func.count(QueueJob.id)).where(QueueJob.status == "queued"))).scalar() or 0
    rq = (await db.execute(select(func.count(QueueJob.id)).where(QueueJob.status == "retrying"))).scalar() or 0
    dq = (await db.execute(select(func.count(QueueJob.id)).where(QueueJob.status == "failed"))).scalar() or 0
    return {"queue_depth": qd, "retry_queue_size": rq, "dlq_size": dq, "worker_status": "healthy"}


@router.get("/")
async def root():
    return {"service": "Xeno Communication Service", "version": "1.0.0", "status": "running"}
