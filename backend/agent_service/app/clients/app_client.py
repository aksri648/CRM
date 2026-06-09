import httpx
from app.config import settings
from app.utils.logging import logger


async def post_decision(agent_run_id: str, agent_name: str, output: dict) -> bool:
    url = f"{settings.APP_SERVICE_URL}/api/v1/agent/decisions"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={
                "agent_run_id": agent_run_id, "agent_name": agent_name, "output": output,
            })
            return resp.status_code == 200
    except Exception as e:
        logger.warning("post_decision_failed", error=str(e))
        return False
