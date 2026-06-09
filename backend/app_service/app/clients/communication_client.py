import uuid
import httpx
from app.config import settings
from app.utils.logging import logger


async def dispatch_campaign_to_communication_service(
    campaign_id: uuid.UUID,
    customer_ids: list[uuid.UUID],
    channel: str,
    variant_id: uuid.UUID | None = None,
    subject_line: str | None = None,
    message_body: str | None = None,
) -> dict:
    url = f"{settings.COMMUNICATION_SERVICE_URL}/api/v1/campaigns/dispatch"
    payload = {
        "campaign_id": str(campaign_id),
        "customer_ids": [str(cid) for cid in customer_ids],
        "channel": channel,
        "variant_id": str(variant_id) if variant_id else None,
        "subject_line": subject_line,
        "message_body": message_body,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.RequestError as e:
        logger.error("communication_dispatch_failed", error=str(e))
        raise


async def simulate_campaign_lifecycle(campaign_id: uuid.UUID) -> dict:
    url = f"{settings.COMMUNICATION_SERVICE_URL}/api/v1/simulate/campaign/{campaign_id}"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url)
            resp.raise_for_status()
            return resp.json()
    except httpx.RequestError as e:
        logger.error("communication_simulate_failed", error=str(e))
        raise


async def get_communication_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.COMMUNICATION_SERVICE_URL}/api/v1/health")
            return resp.status_code == 200
    except Exception:
        return False
