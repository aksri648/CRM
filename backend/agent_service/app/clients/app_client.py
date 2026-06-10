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


async def fetch_pipeline_status() -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.APP_SERVICE_URL}/api/v1/pipeline/status")
            return resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        logger.warning("fetch_pipeline_failed", error=str(e))
        return {}


async def fetch_dashboard_stats() -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.APP_SERVICE_URL}/api/v1/dashboard/stats")
            return resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        logger.warning("fetch_dashboard_failed", error=str(e))
        return {}


async def fetch_campaigns(page: int = 1, page_size: int = 10) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.APP_SERVICE_URL}/api/v1/campaigns?page={page}&page_size={page_size}")
            return resp.json() if resp.status_code == 200 else {"campaigns": [], "total": 0}
    except Exception as e:
        logger.warning("fetch_campaigns_failed", error=str(e))
        return {"campaigns": [], "total": 0}


async def fetch_proposals() -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.APP_SERVICE_URL}/api/v1/proposals")
            return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.warning("fetch_proposals_failed", error=str(e))
        return []


async def fetch_customers(page: int = 1, page_size: int = 10, search: str | None = None) -> dict:
    try:
        params = f"page={page}&page_size={page_size}"
        if search:
            params += f"&search={search}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.APP_SERVICE_URL}/api/v1/customers?{params}")
            return resp.json() if resp.status_code == 200 else {"customers": [], "total": 0}
    except Exception as e:
        logger.warning("fetch_customers_failed", error=str(e))
        return {"customers": [], "total": 0}


async def fetch_lifecycle_distribution() -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.APP_SERVICE_URL}/api/v1/customers/lifecycle/distribution")
            return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.warning("fetch_lifecycle_failed", error=str(e))
        return []


async def fetch_channel_analytics(channel: str | None = None) -> list:
    try:
        url = f"{settings.APP_SERVICE_URL}/api/v1/analytics/channels"
        if channel:
            url += f"?channel={channel}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.warning("fetch_channel_analytics_failed", error=str(e))
        return []


async def fetch_opportunities(page: int = 1, page_size: int = 10) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.APP_SERVICE_URL}/api/v1/opportunities?page={page}&page_size={page_size}")
            return resp.json() if resp.status_code == 200 else {"opportunities": [], "total": 0}
    except Exception as e:
        logger.warning("fetch_opportunities_failed", error=str(e))
        return {"opportunities": [], "total": 0}
