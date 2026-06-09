import httpx
from app.config import settings
from app.utils.logging import logger


async def send_callback_to_app(data: dict) -> bool:
    url = f"{settings.APP_SERVICE_URL}/api/v1/callbacks/events"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=data)
            if resp.status_code == 200:
                return True
            logger.warning("callback_failed", status_code=resp.status_code)
            return False
    except Exception as e:
        logger.error("callback_error", error=str(e))
        return False
