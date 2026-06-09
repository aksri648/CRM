import uuid
from app.agents.graph import campaign_graph, opportunity_graph
from app.agents.state import MarketingState
from app.utils.logging import logger


async def run_campaign_generation(goal: str, run_id: str | None = None) -> dict:
    rid = run_id or str(uuid.uuid4())
    initial_state = MarketingState(
        goal=goal, approval_status="pending", metadata={}, errors=[],
        agent_trace=[], current_agent="Athena",
    )
    config = {"configurable": {"thread_id": rid}}
    result = await campaign_graph.ainvoke(initial_state, config)
    return {"run_id": rid, **result}


async def run_opportunity_discovery(run_id: str | None = None) -> dict:
    rid = run_id or str(uuid.uuid4())
    initial_state = MarketingState(
        goal="Discover marketing opportunities based on latest trends.",
        approval_status="pending", metadata={}, errors=[], agent_trace=[], current_agent="Orion",
    )
    config = {"configurable": {"thread_id": rid}}
    result = await opportunity_graph.ainvoke(initial_state, config)
    return {"run_id": rid, **result}
