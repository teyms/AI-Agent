from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    classify_input_node,
    clarification_node,
    confidence_validation_node,
    human_review_node,
    calculator_node,
    validate_result_node,
    multi_validation_node,
    fallback_node,
    timeout_node,
    logging_node,
    final_response_node
)

graph = StateGraph(AgentState)

graph.add_node(
    "classify",
    classify_input_node
)

graph.add_node(
    "clarify",
    clarification_node
)

graph.add_node(
    "confidence_validate",
    confidence_validation_node
)

graph.add_node(
    "human_review",
    human_review_node
)

graph.add_node(
    "calculator",
    calculator_node
)

graph.add_node(
    "validate",
    validate_result_node
)

graph.add_node(
    "multi_validate",
    multi_validation_node
)

graph.add_node(
    "fallback",
    fallback_node
)

graph.add_node(
    "timeout",
    timeout_node
)

graph.add_node(
    "logging",
    logging_node
)

graph.add_node(
    "final",
    final_response_node
)


graph.set_entry_point(
    "classify"
)


graph.add_edge(
    "classify",
    "confidence_validate"
)


def confidence_router(
    state: AgentState
):
    if state["confidence_status"] == "low":
        return "human_review"

    return classification_router(state)


def classification_router(
    state: AgentState
):
    if state["intent"] == "calculator":
        return "calculator"

    if state["clarification_count"] >= 2:
        return "fallback"

    return "clarify"


graph.add_conditional_edges(
    "confidence_validate",
    confidence_router,
    {
        "calculator": "calculator",
        "clarify": "clarify",
        "fallback": "fallback",
        "human_review": "human_review"
    }
)


graph.add_edge(
    "clarify",
    "classify"
)

graph.add_edge(
    "calculator",
    "validate"
)


def validation_router(
    state: AgentState
):
    status = state[
        "validation_status"
    ]

    if status == "success":
        return "multi_validate"
    elif status == "retry":
        return "calculator"
    elif status == "timeout":
        return "timeout"
    else:
        return "fallback"
    

graph.add_conditional_edges(
    "validate",
    validation_router,
    {
        "multi_validate": "multi_validate",
        "calculator": "calculator",
        "timeout": "timeout",
        "fallback": "fallback"
    }
)


def multi_validation_router(
    state: AgentState
):
    if state["final_validation_status"] == "passed":
        return "final"

    return "human_review"


graph.add_conditional_edges(
    "multi_validate",
    multi_validation_router,
    {
        "final": "final",
        "human_review": "human_review"
    }
)

graph.add_edge(
    "final",
    "logging"
)

graph.add_edge(
    "fallback",
    "logging"
)

graph.add_edge(
    "timeout",
    "logging"
)

graph.add_edge(
    "human_review",
    "logging"
)

graph.add_edge(
    "logging",
    END
)

app = graph.compile()
