from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_router_node,
    rewrite_query_node,
    retrieval_node,
    retrieval_validation_node,
    clarification_node,
    rag_answer_node,
    citation_validation_node,
    direct_answer_node
)


graph = StateGraph(
    AgentState
)


graph.add_node(
    "router",
    agent_router_node
)

graph.add_node(
    "rewrite_query",
    rewrite_query_node
)

graph.add_node(
    "retrieve",
    retrieval_node
)

graph.add_node(
    "validate_retrieval",
    retrieval_validation_node
)

graph.add_node(
    "clarify",
    clarification_node
)

graph.add_node(
    "rag_answer",
    rag_answer_node
)

graph.add_node(
    "validate_citations",
    citation_validation_node
)

graph.add_node(
    "direct_answer",
    direct_answer_node
)


def route_retrieval(
    state: AgentState
):

    if state["needs_retrieval"]:

        return "retrieve"

    return "direct_answer"


graph.add_conditional_edges(
    "router",
    route_retrieval,
    {
        "retrieve": "rewrite_query",
        "direct_answer": "direct_answer"
    }
)

graph.add_edge(
    "rewrite_query",
    "retrieve"
)


graph.add_edge(
    "retrieve",
    "validate_retrieval"
)


def route_retrieval_validation(
    state: AgentState
):
    if state["retrieval_status"] == "good":
        return "rag_answer"

    if state["retrieval_status"] == "clarify":
        return "clarify"

    return END


graph.add_conditional_edges(
    "validate_retrieval",
    route_retrieval_validation,
    {
        "rag_answer": "rag_answer",
        "clarify": "clarify",
        END: END
    }
)

graph.add_edge(
    "clarify",
    "retrieve"
)

graph.add_edge(
    "rag_answer",
    "validate_citations"
)

graph.add_edge(
    "validate_citations",
    END
)

graph.add_edge(
    "direct_answer",
    END
)


graph.set_entry_point(
    "router"
)


app = graph.compile()

