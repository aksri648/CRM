import httpx
from app.config import settings
from app.utils.logging import logger


async def get_customer_email(customer_id: str) -> dict | None:
    if not settings.INTERNAL_SHARED_TOKEN:
        logger.warning("internal_shared_token_missing")
        return None
    url = f"{settings.APP_SERVICE_URL}/api/v1/internal/customers/{customer_id}/email"
    headers = {"X-Internal-Token": settings.INTERNAL_SHARED_TOKEN}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.RequestError as e:
            logger.error("app_service_customer_lookup_error", error=str(e), customer_id=customer_id)
            return None
    if resp.status_code != 200:
        logger.warning("app_service_customer_lookup_failed", status=resp.status_code, customer_id=customer_id)
        return None
    return resp.json()
