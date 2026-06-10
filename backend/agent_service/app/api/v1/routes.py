import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.agents.graph import campaign_graph, opportunity_graph, command_centre_graph
from app.agents.state import MarketingState
from app.utils.logging import logger

router = APIRouter()


def _enqueue(func, *args):
    """Lazy import of RQ so the import error doesn't surface when RQ is disabled."""
    from app.jobs.queue import get_queue
    queue = get_queue()
    job = queue.enqueue(func, *args, job_timeout=settings.RQ_JOB_TIMEOUT)
    return job


def _job_response(job) -> dict:
    status = job.get_status(refresh=True)
    payload: dict = {"job_id": job.id, "status": status}
    if status == "finished":
        payload["result"] = job.result
    elif status == "failed":
        payload["error"] = str(job.exc_info or "job failed")
    return payload


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-service", "timestamp": datetime.utcnow().isoformat()}


@router.post("/agents/generate-campaign")
async def generate_campaign(data: dict):
    goal = data.get("goal", "")
    run_id = data.get("run_id", str(uuid.uuid4()))
    if not goal:
        raise HTTPException(status_code=400, detail="Goal is required")

    if settings.RQ_ENABLED:
        try:
            from app.jobs.runners import run_campaign_job
            job = _enqueue(run_campaign_job, goal, run_id)
            return {"job_id": job.id, "status": "queued", "run_id": run_id}
        except Exception as e:
            logger.error("rq_enqueue_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to enqueue: {e}")

    try:
        initial_state = MarketingState(
            goal=goal, approval_status="pending", metadata={}, errors=[],
            agent_trace=[], current_agent="Athena",
        )
        config = {"configurable": {"thread_id": run_id}}
        result = await campaign_graph.ainvoke(initial_state, config)

        return {
            "run_id": run_id,
            "proposal": result.get("proposal", {}),
            "segment": result.get("segment", {}),
            "channel_info": result.get("channel", {}).get("predicted_outcome", {}) if isinstance(result.get("channel"), dict) else {},
            "message_variants": result.get("message_variants", []),
            "reasoning": result.get("reasoning"),
            "agent_trace": result.get("agent_trace", []),
        }

    except Exception as e:
        logger.error("campaign_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Campaign generation failed: {str(e)}")


@router.post("/agents/discover-opportunities")
async def discover_opportunities(data: dict):
    run_id = data.get("run_id", str(uuid.uuid4()))

    if settings.RQ_ENABLED:
        try:
            from app.jobs.runners import run_opportunity_job
            job = _enqueue(run_opportunity_job, run_id)
            return {"job_id": job.id, "status": "queued", "run_id": run_id}
        except Exception as e:
            logger.error("rq_enqueue_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to enqueue: {e}")

    try:
        initial_state = MarketingState(
            goal="Discover marketing opportunities based on latest trends and customer behavior.",
            approval_status="pending", metadata={}, errors=[], agent_trace=[], current_agent="Orion",
        )
        config = {"configurable": {"thread_id": run_id}}
        result = await opportunity_graph.ainvoke(initial_state, config)

        audience_data = result.get("audience", {})
        supporting_data = audience_data.get("supporting_data", {}) if isinstance(audience_data, dict) else {}
        all_opportunities = supporting_data.get("all_opportunities", []) if isinstance(supporting_data, dict) else []

        return {
            "run_id": run_id,
            "opportunities": all_opportunities,
            "agent_trace": result.get("agent_trace", []),
        }

    except Exception as e:
        logger.error("opportunity_discovery_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Opportunity discovery failed: {str(e)}")


@router.post("/agents/command-centre")
async def command_centre(data: dict):
    query = data.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    try:
        initial_state = MarketingState(
            goal=query, approval_status="pending", metadata={}, errors=[],
            agent_trace=[], current_agent="CommandCentre",
        )
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await command_centre_graph.ainvoke(initial_state, config)

        meta = result.get("metadata", {})
        cc_response = meta.get("command_centre_response", {}) if isinstance(meta, dict) else {}

        return {
            "response": cc_response.get("response", "I could not process that query."),
            "reasoning": result.get("reasoning"),
            "confidence_score": cc_response.get("confidence_score"),
            "supporting_data": cc_response.get("supporting_data", {}),
            "predicted_outcome": cc_response.get("predicted_outcome", {}),
            "agent_trace": result.get("agent_trace", []),
        }

    except Exception as e:
        logger.error("command_centre_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Command centre query failed: {str(e)}")


@router.get("/agents/jobs/{job_id}")
async def get_job(job_id: str):
    if not settings.RQ_ENABLED:
        raise HTTPException(status_code=404, detail="RQ is not enabled on this service")
    try:
        from app.jobs.queue import get_redis
        from rq.job import Job
        job = Job.fetch(job_id, connection=get_redis())
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_response(job)


@router.post("/nlp/classify")
async def nlp_classify_route(data: dict):
    """Run the deterministic segment classifier on a free-text marketing goal.

    Useful for: debugging Atlas's segment choices, demoing the model directly,
    and any caller that wants segmentation without invoking the full LangGraph.
    """
    text = (data or {}).get("text") or (data or {}).get("goal")
    if not text:
        raise HTTPException(status_code=400, detail="Provide 'text' or 'goal' in the body.")
    from app.nlp import classify as nlp_classify
    return nlp_classify(text).to_dict()


@router.get("/")
async def root():
    return {"service": "Xeno Agent Service", "version": "1.0.0", "status": "running"}
