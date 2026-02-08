from langgraph.graph import StateGraph
from app.state import ResearchState
from app.agents.planner import planner_agent
from app.agents.searcher import search_agent
from app.agents.evaluator import evaluator_agent
from app.agents.synthesizer import synthesizer_agent

def should_continue(state: ResearchState):
    if state.current_step < len(state.plan):
        return "search"
    return "synthesize"

graph = StateGraph(ResearchState)

graph.add_node("planner", planner_agent)
graph.add_node("search", search_agent)
graph.add_node("evaluate", evaluator_agent)
graph.add_node("synthesize", synthesizer_agent)

graph.set_entry_point("planner")

graph.add_edge("planner", "search")
graph.add_edge("search", "evaluate")

# 🔁 LOOP HERE
graph.add_conditional_edges(
    "evaluate",
    should_continue,
    {
        "search": "search",
        "synthesize": "synthesize"
    }
)

research_graph = graph.compile()
