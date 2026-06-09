from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START

from app.agents.state import MarketingState
from app.agents.agents import (
    athena_agent, atlas_agent, sophia_agent, mercury_agent,
    nova_agent, darwin_agent, orion_agent, apollo_agent, sentinel_agent,
)


campaign_graph_builder = StateGraph(MarketingState)
for name, fn in [("Athena", athena_agent), ("Atlas", atlas_agent), ("Sophia", sophia_agent),
                  ("Mercury", mercury_agent), ("Nova", nova_agent), ("Darwin", darwin_agent),
                  ("Apollo", apollo_agent), ("Sentinel", sentinel_agent)]:
    campaign_graph_builder.add_node(name, fn)
campaign_graph_builder.add_edge(START, "Athena")
campaign_graph_builder.add_edge("Athena", "Atlas")
campaign_graph_builder.add_edge("Atlas", "Sophia")
campaign_graph_builder.add_edge("Sophia", "Mercury")
campaign_graph_builder.add_edge("Mercury", "Nova")
campaign_graph_builder.add_edge("Nova", "Darwin")
campaign_graph_builder.add_edge("Darwin", "Apollo")
campaign_graph_builder.add_edge("Apollo", "Sentinel")
campaign_graph_builder.add_edge("Sentinel", END)
campaign_graph = campaign_graph_builder.compile(checkpointer=MemorySaver(), interrupt_before=["Sentinel"])


opportunity_graph_builder = StateGraph(MarketingState)
for name, fn in [("Orion", orion_agent), ("Atlas", atlas_agent), ("Sophia", sophia_agent),
                  ("Mercury", mercury_agent), ("Nova", nova_agent), ("Darwin", darwin_agent),
                  ("Sentinel", sentinel_agent)]:
    opportunity_graph_builder.add_node(name, fn)
opportunity_graph_builder.add_edge(START, "Orion")
opportunity_graph_builder.add_edge("Orion", "Atlas")
opportunity_graph_builder.add_edge("Atlas", "Sophia")
opportunity_graph_builder.add_edge("Sophia", "Mercury")
opportunity_graph_builder.add_edge("Mercury", "Nova")
opportunity_graph_builder.add_edge("Nova", "Darwin")
opportunity_graph_builder.add_edge("Darwin", "Sentinel")
opportunity_graph_builder.add_edge("Sentinel", END)
opportunity_graph = opportunity_graph_builder.compile(checkpointer=MemorySaver(), interrupt_before=["Sentinel"])
