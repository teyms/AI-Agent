from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState
from nodes import (
    classify_intent_node,
    weather_node,
    calculator_node,
    current_time_node,
    rag_node,
    validation_node,
    retry_node,
    logging_node,
    general_response_node,
    final_response_node
)

graph = StateGraph(AgentState)

graph.add_node(
    "classify",
    classify_intent_node
)

graph.add_node(
    "weather",
    weather_node
)

graph.add_node(
    "calculator",
    calculator_node
)

graph.add_node(
    "current_time",
    current_time_node
)

graph.add_node(
    "rag",
    rag_node
)

graph.add_node(
    "validation",
    validation_node
)

graph.add_node(
    "retry",
    retry_node
)

graph.add_node(
    "logging",
    logging_node
)

graph.add_node(
    "general",
    general_response_node
)

graph.add_node(
    "final",
    final_response_node
)

graph.set_entry_point("classify")


def route_intent(
    state: AgentState
):
    intent = state["intent"]

    if intent == "weather":
        return "weather"
    elif intent == "calculator":
        return "calculator"
    elif intent == "rag":
        return "rag"
    elif intent == "current_time":
        return "current_time"
    else:
        return "general"
    # return state["intent"]

graph.add_conditional_edges(
    "classify",
    route_intent,
    {
        "weather": "weather",
        "calculator": "calculator",
        "rag": "rag",
        "current_time": "current_time",
        "general": "general"
    }
)



graph.add_edge(
    "weather",
    "logging"
)

graph.add_edge(
    "calculator",
    "validation"
)

def route_validation(
    state: AgentState
):
    if state["validation_result"] == "invalid":
        return "retry"

    return "final"

graph.add_conditional_edges(
    "validation",
    route_validation,
    {
        "retry": "retry",
        "final": "logging"
    }
)

graph.add_edge(
    "retry",
    "logging"
)

graph.add_edge(
    "current_time",
    "logging"
)

graph.add_edge(
    "rag",
    "logging"
)

graph.add_edge(
    "general",
    "logging"
)

graph.add_edge(
    "logging",
    "final"
)

graph.add_edge(
    "final",
    END
)

app = graph.compile()
