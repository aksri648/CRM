import uuid
import httpx
from app.config import settings
from app.utils.logging import logger


async def call_agent_generate_campaign(goal: str, run_id: str) -> dict:
    url = f"{settings.AGENT_SERVICE_URL}/api/v1/agents/generate-campaign"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json={"goal": goal, "run_id": run_id})
            resp.raise_for_status()
            return resp.json()
    except httpx.RequestError as e:
        logger.error("agent_generate_campaign_failed", error=str(e))
        raise


async def call_agent_discover_opportunities(run_id: str) -> dict:
    url = f"{settings.AGENT_SERVICE_URL}/api/v1/agents/discover-opportunities"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json={"run_id": run_id})
            resp.raise_for_status()
            return resp.json()
    except httpx.RequestError as e:
        logger.error("agent_discover_opportunities_failed", error=str(e))
        raise


async def get_agent_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.AGENT_SERVICE_URL}/api/v1/health")
            return resp.status_code == 200
    except Exception:
        return False
