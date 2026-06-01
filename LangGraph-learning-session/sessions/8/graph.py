from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_node,
    validate_node,
    execute_tool_node,
    output_validation_node,
    secondary_validation_node,
    human_review_node,
    fallback_node,
    final_node
)
from state import AgentState

def validation_router(
    state: AgentState
):
    status = state[
        "validation_status"
    ]

    if status == "valid":
        return "execute"

    if status == "retry":
        return "agent"

    return "fallback"


graph = StateGraph(
    AgentState
)

graph.add_node(
    "agent",
    agent_node
)

graph.add_node(
    "validate",
    validate_node
)

graph.add_node(
    "execute",
    execute_tool_node
)

graph.add_node(
    "output_validate",
    output_validation_node
)

graph.add_node(
    "secondary_validate",
    secondary_validation_node
)

graph.add_node(
    "human_review",
    human_review_node
)

graph.add_node(
    "fallback",
    fallback_node
)

graph.add_node(
    "final",
    final_node
)

graph.set_entry_point(
    "agent"
)

graph.add_edge(
    "agent",
    "validate"
)

graph.add_conditional_edges(
    "validate",
    validation_router,
    {
        "execute": "execute",
        "agent": "agent",
        "fallback": "fallback"
    }
)

graph.add_edge(
    "execute",
    "output_validate"
)


def output_validation_router(
    state: AgentState
):
    if (
        state["output_validation_status"]
        == "fallback"
    ):
        return "fallback"

    if state["confidence_status"] == "low":
        return "human_review"

    return "secondary_validate"


graph.add_conditional_edges(
    "output_validate",
    output_validation_router,
    {
        "secondary_validate": "secondary_validate",
        "human_review": "human_review",
        "fallback": "fallback"
    }
)


def secondary_validation_router(
    state: AgentState
):
    if (
        state["secondary_validation_status"]
        == "valid"
    ):
        return "final"

    return "human_review"


graph.add_conditional_edges(
    "secondary_validate",
    secondary_validation_router,
    {
        "final": "final",
        "human_review": "human_review"
    }
)

graph.add_edge(
    "final",
    END
)

graph.add_edge(
    "human_review",
    END
)

graph.add_edge(
    "fallback",
    END
)

app = graph.compile()
