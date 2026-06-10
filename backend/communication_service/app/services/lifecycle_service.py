import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.communication import Communication, CommunicationEvent
from app.services.callback_service import send_callback_to_app
from app.services.email_service import send_email, EmailNotConfigured, EmailSendFailed
from app.clients.app_client import get_customer_email
from app.utils.logging import logger


async def record_event(db: AsyncSession, communication_id: uuid.UUID, event_type: str,
                        timestamp: datetime | None = None, metadata: dict | None = None) -> CommunicationEvent | None:
    result = await db.execute(select(Communication).where(Communication.id == communication_id))
    comm = result.scalar_one_or_none()
    if not comm: return None
    ts = timestamp or datetime.utcnow()
    event = CommunicationEvent(communication_id=communication_id, event_type=event_type, timestamp=ts, event_metadata=metadata or {})
    db.add(event)
    status_map = {"queued": "queued", "sent": "sent", "delivered": "delivered", "opened": "opened",
                  "read": "read", "clicked": "clicked", "converted": "converted", "failed": "failed"}
    if event_type in status_map:
        new_status = status_map[event_type]
        ts_attr = f"{new_status}_at"
        if hasattr(comm, ts_attr): setattr(comm, ts_attr, ts)
        if new_status == "failed" and metadata and "reason" in metadata:
            comm.failure_reason = metadata["reason"]
        comm.status = new_status
    await db.commit()
    return event


async def _send_real_email(db: AsyncSession, comm: Communication) -> dict | None:
    customer = await get_customer_email(str(comm.customer_id))
    if not customer or not customer.get("email"):
        await record_event(db, comm.id, "failed", metadata={"reason": "Customer email not resolvable"})
        return {"communication_id": str(comm.id), "final_status": "failed", "events": [{"event_type": "failed"}]}

    subject = comm.subject_line or "A message from Xeno"
    body = comm.message_body or ""
    html = f"<html><body>{body}</body></html>"

    try:
        result = await send_email(
            to=customer["email"],
            subject=subject,
            html=html,
            communication_id=str(comm.id),
            campaign_id=str(comm.campaign_id),
        )
    except (EmailNotConfigured, EmailSendFailed) as e:
        logger.error("real_email_send_failed", error=str(e), communication_id=str(comm.id))
        await record_event(db, comm.id, "failed", metadata={"reason": str(e)})
        return {"communication_id": str(comm.id), "final_status": "failed", "events": [{"event_type": "failed"}]}

    provider_id = result.get("id")
    sent_ts = datetime.utcnow()
    await record_event(db, comm.id, "sent", timestamp=sent_ts, metadata={"provider_message_id": provider_id})
    comm.external_id = provider_id
    await db.commit()

    await send_callback_to_app({
        "communication_id": str(comm.id), "campaign_id": str(comm.campaign_id),
        "customer_id": str(comm.customer_id), "event_type": "sent",
        "timestamp": sent_ts.isoformat(),
        "metadata": {"channel": comm.channel, "provider_message_id": provider_id},
    })

    return {
        "communication_id": str(comm.id),
        "final_status": "sent",
        "events": [{"event_type": "sent", "timestamp": sent_ts.isoformat(), "provider_message_id": provider_id}],
        "note": "Subsequent delivered/opened/clicked events arrive via Resend webhook",
    }


async def _simulate_lifecycle(db: AsyncSession, comm: Communication) -> dict:
    stages = [("sent", 0.98, timedelta(seconds=random.randint(1, 10))),
              ("delivered", 0.95, timedelta(seconds=random.randint(5, 60))),
              ("opened", 0.65, timedelta(minutes=random.randint(5, 120))),
              ("read", 0.50, timedelta(seconds=random.randint(10, 300))),
              ("clicked", 0.25, timedelta(seconds=random.randint(30, 600))),
              ("converted", 0.10, timedelta(hours=random.randint(1, 48)))]
    current_time = datetime.utcnow()
    prev_ts = current_time
    events_seq = []
    for stage, prob, delay in stages:
        if random.random() > prob:
            if random.random() < 0.3:
                await record_event(db, comm.id, "failed", timestamp=prev_ts + delay,
                                    metadata={"reason": f"Failed at {stage}", "stage": stage})
                events_seq.append({"event_type": "failed", "stage": stage})
            break
        prev_ts += delay
        event = await record_event(db, comm.id, stage, timestamp=prev_ts)
        if event:
            events_seq.append({"event_type": stage, "timestamp": prev_ts.isoformat()})
            await send_callback_to_app({"communication_id": str(comm.id), "campaign_id": str(comm.campaign_id),
                                         "customer_id": str(comm.customer_id), "event_type": stage,
                                         "timestamp": prev_ts.isoformat(), "metadata": {"channel": comm.channel}})
    await db.refresh(comm)
    return {"communication_id": str(comm.id), "final_status": comm.status, "events": events_seq}


async def simulate_lifecycle(db: AsyncSession, communication_id: uuid.UUID) -> dict | None:
    result = await db.execute(select(Communication).where(Communication.id == communication_id))
    comm = result.scalar_one_or_none()
    if not comm: return None

    if comm.channel == "email" and settings.EMAIL_SEND_ENABLED and settings.RESEND_API_KEY:
        sent = await _send_real_email(db, comm)
        if sent is not None:
            return sent

    return await _simulate_lifecycle(db, comm)
