from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState
from checkpointer import checkpointer

from nodes import (
    generate_action_node,
    risk_scoring_node,
    approval_node,
    manager_approval_node,
    security_approval_node,
    execute_action_node,
    reject_action_node
)

graph = StateGraph(
    AgentState
)

graph.add_node(
    "generate_action",
    generate_action_node
)

graph.add_node(
    "score_risk",
    risk_scoring_node
)

graph.add_node(
    "approval",
    approval_node
)

graph.add_node(
    "manager_approval",
    manager_approval_node
)

graph.add_node(
    "security_approval",
    security_approval_node
)

graph.add_node(
    "execute",
    execute_action_node
)

graph.add_node(
    "reject",
    reject_action_node
)

graph.set_entry_point(
    "generate_action"
)

graph.add_edge(
    "generate_action",
    "score_risk"
)

def risk_router(
    state: AgentState
):
    if state["risk_level"] == "low":
        return "execute"

    return "manager_approval"


graph.add_conditional_edges(
    "score_risk",
    risk_router,
    {
        "execute": "execute",
        "manager_approval": "manager_approval"
    }
)


def manager_approval_router(
    state: AgentState
):
    if state["manager_approval_status"] != "approve":
        return "reject"

    if state["risk_level"] == "high":
        return "security_approval"

    return "execute"


graph.add_conditional_edges(
    "manager_approval",
    manager_approval_router,
    {
        "security_approval": "security_approval",
        "execute": "execute",
        "reject": "reject"
    }
)


def security_approval_router(
    state: AgentState
):
    if state["security_approval_status"] == "approve":
        return "execute"

    return "reject"


graph.add_conditional_edges(
    "security_approval",
    security_approval_router,
    {
        "execute": "execute",
        "reject": "reject"
    }
)

def approval_router(
    state: AgentState
):
    if (
        state["approval_status"]
        == "approve"
    ):
        return "execute"

    return "reject"

graph.add_conditional_edges(
    "approval",
    approval_router,
    {
        "execute": "execute",
        "reject": "reject"
    }
)

graph.add_edge(
    "execute",
    END
)

graph.add_edge(
    "reject",
    END
)

app = graph.compile(
    checkpointer=checkpointer
)
