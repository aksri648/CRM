import asyncio
import httpx
from app.config import settings
from app.utils.logging import logger


JOB_POLL_INTERVAL = 1.5
JOB_POLL_TIMEOUT = 180.0


async def _poll_job(client: httpx.AsyncClient, job_id: str) -> dict:
    """Poll /agents/jobs/{job_id} until finished/failed or timeout."""
    url = f"{settings.AGENT_SERVICE_URL}/api/v1/agents/jobs/{job_id}"
    elapsed = 0.0
    while elapsed < JOB_POLL_TIMEOUT:
        resp = await client.get(url)
        resp.raise_for_status()
        payload = resp.json()
        status = payload.get("status")
        if status == "finished":
            return payload.get("result") or {}
        if status == "failed":
            raise RuntimeError(payload.get("error") or "Agent job failed")
        await asyncio.sleep(JOB_POLL_INTERVAL)
        elapsed += JOB_POLL_INTERVAL
    raise RuntimeError(f"Agent job {job_id} did not complete within {JOB_POLL_TIMEOUT}s")


async def _post_and_resolve(path: str, json_body: dict, timeout: float = 120.0) -> dict:
    url = f"{settings.AGENT_SERVICE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=json_body)
        resp.raise_for_status()
        body = resp.json()
        if body.get("status") == "queued" and body.get("job_id"):
            return await _poll_job(client, body["job_id"])
        return body


async def call_agent_generate_campaign(goal: str, run_id: str) -> dict:
    try:
        return await _post_and_resolve(
            "/api/v1/agents/generate-campaign",
            {"goal": goal, "run_id": run_id},
        )
    except httpx.RequestError as e:
        logger.error("agent_generate_campaign_failed", error=str(e))
        raise


async def call_agent_discover_opportunities(run_id: str) -> dict:
    try:
        return await _post_and_resolve(
            "/api/v1/agents/discover-opportunities",
            {"run_id": run_id},
        )
    except httpx.RequestError as e:
        logger.error("agent_discover_opportunities_failed", error=str(e))
        raise


async def call_agent_command_centre(query: str) -> dict:
    url = f"{settings.AGENT_SERVICE_URL}/api/v1/agents/command-centre"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json={"query": query})
            resp.raise_for_status()
            return resp.json()
    except httpx.RequestError as e:
        logger.error("agent_command_centre_failed", error=str(e))
        raise


async def get_agent_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.AGENT_SERVICE_URL}/api/v1/health")
            return resp.status_code == 200
    except Exception:
        return False
