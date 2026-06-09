import httpx
from app.config import settings
from app.utils.logging import logger


async def send_telegram_message(text: str, reply_markup: dict | None = None) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": settings.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            return resp.status_code == 200
    except Exception as e:
        logger.error("telegram_send_error", error=str(e))
        return False


def build_approval_keyboard(approval_id: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "Approve", "callback_data": f"approve:{approval_id}"},
             {"text": "Reject", "callback_data": f"reject:{approval_id}"}],
        ]
    }


async def send_approval_notification(campaign, approval) -> bool:
    if not campaign:
        return False
    text = (
        f"AI Campaign Proposal\n\n"
        f"Goal: {campaign.description or campaign.name}\n"
        f"Channel: {campaign.channel}\n"
        f"Expected Reach: {campaign.expected_reach or 'N/A'} customers\n"
        f"Expected CTR: {campaign.expected_ctr or 'N/A'}%\n"
        f"Expected Revenue: {campaign.expected_revenue or 'N/A'}\n\n"
        f"Campaign ID: {campaign.id}"
    )
    keyboard = build_approval_keyboard(str(approval.id))
    return await send_telegram_message(text, keyboard)


async def process_telegram_callback(callback_data: str) -> dict:
    try:
        action, approval_id = callback_data.split(":")
        return {"action": action, "approval_id": approval_id}
    except (ValueError, AttributeError):
        return {"action": "unknown", "approval_id": ""}
