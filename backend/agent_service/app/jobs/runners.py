"""Sync RQ runners that wrap async LangGraph invocations.

RQ jobs run in worker processes that don't have an event loop. Each runner
spins up a fresh asyncio loop with asyncio.run().
"""
import asyncio
import uuid

from app.agents.graph import campaign_graph, opportunity_graph, command_centre_graph
from app.agents.state import MarketingState


def run_campaign_job(goal: str, run_id: str) -> dict:
    initial_state = MarketingState(
        goal=goal, approval_status="pending", metadata={}, errors=[],
        agent_trace=[], current_agent="Athena",
    )
    config = {"configurable": {"thread_id": run_id}}
    result = asyncio.run(campaign_graph.ainvoke(initial_state, config))

    channel = result.get("channel") if isinstance(result.get("channel"), dict) else {}
    channel_info = channel.get("predicted_outcome", {}) if isinstance(channel, dict) else {}

    return {
        "run_id": run_id,
        "proposal": result.get("proposal", {}),
        "segment": result.get("segment", {}),
        "channel_info": channel_info,
        "message_variants": result.get("message_variants", []),
        "reasoning": result.get("reasoning"),
        "agent_trace": result.get("agent_trace", []),
    }


def run_opportunity_job(run_id: str) -> dict:
    initial_state = MarketingState(
        goal="Discover marketing opportunities based on latest trends and customer behavior.",
        approval_status="pending", metadata={}, errors=[], agent_trace=[], current_agent="Orion",
    )
    config = {"configurable": {"thread_id": run_id}}
    result = asyncio.run(opportunity_graph.ainvoke(initial_state, config))

    audience_data = result.get("audience", {})
    supporting_data = audience_data.get("supporting_data", {}) if isinstance(audience_data, dict) else {}
    all_opportunities = supporting_data.get("all_opportunities", []) if isinstance(supporting_data, dict) else []

    return {
        "run_id": run_id,
        "opportunities": all_opportunities,
        "agent_trace": result.get("agent_trace", []),
    }


def run_command_centre_job(query: str) -> dict:
    initial_state = MarketingState(
        goal=query, approval_status="pending", metadata={}, errors=[],
        agent_trace=[], current_agent="CommandCentre",
    )
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = asyncio.run(command_centre_graph.ainvoke(initial_state, config))

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
