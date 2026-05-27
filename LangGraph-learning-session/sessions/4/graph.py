from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_node,
    tool_node,
    validation_node,
    fallback_node
)


graph = StateGraph(
    AgentState
)

graph.add_node(
    "agent",
    agent_node
)

graph.add_node(
    "tool",
    tool_node
)

graph.add_node(
    "validation",
    validation_node
)

graph.add_node(
    "fallback",
    fallback_node
)


graph.add_edge(
    "agent",
    "validation"
)


def route_validation(
    state: AgentState
):
    if state["fallback_reason"]:
        return "fallback"

    if state["final_answer"]:
        return END

    if not state["tool_output"]:
        return "tool"

    if state["tool_failed"]:
        if state["retry_count"] <= state["max_tool_retries"]:
            return "tool"

        return "fallback"

    return "agent"


graph.add_conditional_edges(
    "validation",
    route_validation,
    {
        "tool": "tool",
        "agent": "agent",
        "fallback": "fallback",
        END: END
    }
)


graph.add_edge(
    "tool",
    "validation"
)

graph.add_edge(
    "fallback",
    END
)

graph.set_entry_point(
    "agent"
)





app = graph.compile()
