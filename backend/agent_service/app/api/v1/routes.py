import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.agents.graph import campaign_graph, opportunity_graph, command_centre_graph
from app.agents.state import MarketingState
from app.utils.logging import logger

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-service", "timestamp": datetime.utcnow().isoformat()}


@router.post("/agents/generate-campaign")
async def generate_campaign(data: dict):
    goal = data.get("goal", "")
    run_id = data.get("run_id", str(uuid.uuid4()))
    if not goal:
        raise HTTPException(status_code=400, detail="Goal is required")

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


@router.get("/")
async def root():
    return {"service": "Xeno Agent Service", "version": "1.0.0", "status": "running"}
