import httpx
from app.config import settings
from app.utils.logging import logger

RESEND_ENDPOINT = "https://api.resend.com/emails"


class EmailNotConfigured(Exception):
    pass


class EmailSendFailed(Exception):
    pass


async def send_email(
    to: str,
    subject: str,
    html: str,
    communication_id: str | None = None,
    campaign_id: str | None = None,
) -> dict:
    if not settings.RESEND_API_KEY:
        raise EmailNotConfigured("RESEND_API_KEY is not set")

    payload: dict = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    tags = []
    if communication_id:
        tags.append({"name": "communication_id", "value": communication_id})
    if campaign_id:
        tags.append({"name": "campaign_id", "value": campaign_id})
    if tags:
        payload["tags"] = tags

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(RESEND_ENDPOINT, json=payload, headers=headers)
        except httpx.RequestError as e:
            logger.error("resend_request_error", error=str(e))
            raise EmailSendFailed(f"network error: {e}") from e

    if resp.status_code >= 400:
        logger.error("resend_send_failed", status=resp.status_code, body=resp.text[:500])
        raise EmailSendFailed(f"resend {resp.status_code}: {resp.text[:200]}")

    return resp.json()
