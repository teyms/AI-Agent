from state import AgentState
from langgraph.graph import (
    StateGraph,
    END
)
from agents import (
    research_agent,
    math_agent,
    general_agent,
    risk_agent,
    summary_agent,
    rag_agent,
    reviewer_agent
)

RISK_WORDS = [
    "delete",
    "drop",
    "production",
    "password",
    "secret",
    "payment",
    "security",
    "admin"
]

PARALLEL_WORDS = [
    "analyze",
    "compare",
    "evaluate",
    "parallel",
    "specialists"
]

RAG_WORDS = [
    "policy",
    "document",
    "docs",
    "knowledge",
    "leave",
    "handbook",
    "benefits"
]

def supervisor_node(
    state: AgentState
):
    question = (
        state["user_input"]
        .lower()
    )

    if any(
        word in question
        for word in RAG_WORDS
    ):
        return {
            "selected_agent":
                "rag"
        }

    if any(
        word in question
        for word in PARALLEL_WORDS
    ):
        return {
            "selected_agent":
                "parallel"
        }

    if any(
        word in question
        for word in [
            "calculate",
            "math",
            "+"
        ]
    ):
        return {
            "selected_agent":
                "math"
        }

    if any(
        word in question
        for word in [
            "research",
            "history",
            "explain"
        ]
    ):
        return {
            "selected_agent":
                "research"
        }

    return {
        "selected_agent":
            "general"
    }

def is_risky_request(
    state: AgentState
):
    question = (
        state["user_input"]
        .lower()
    )

    return any(
        word in question
        for word in RISK_WORDS
    )

def route_after_supervisor(
    state: AgentState
):
    if is_risky_request(
        state
    ):
        return "risk"

    if state["selected_agent"] == "parallel":
        return "parallel"

    return "worker"

def route_after_risk(
    state: AgentState
):
    if state["selected_agent"] == "parallel":
        return "parallel"

    return "worker"

def worker_node(
    state: AgentState
):
    question = (
        state["user_input"]
    )

    selected = (
        state["selected_agent"]
    )

    if selected == "research":

        result = research_agent(
            question
        )

    elif selected == "math":

        result = math_agent(
            question
        )

    elif selected == "rag":

        result = rag_agent(
            question
        )

        return {
            "worker_result":
                result,
            "rag_result":
                result
        }

    else:

        result = general_agent(
            question
        )

    return {
        "worker_result":
            result
    }

def risk_node(
    state: AgentState
):
    result = risk_agent(
        state["user_input"]
    )

    return {
        "risk_result":
            result
    }

def parallel_node(
    state: AgentState
):
    question = (
        state["user_input"]
    )

    research_result = research_agent(
        question
    )

    risk_result = (
        state["risk_result"]
        or risk_agent(
            question
        )
    )

    summary_result = summary_agent(
        question
    )

    return {
        "research_result":
            research_result,
        "risk_result":
            risk_result,
        "summary_result":
            summary_result,
        "worker_result":
            f"""
Research:
{research_result}

Risk:
{risk_result}

Summary:
{summary_result}
"""
    }

def reviewer_node(
    state: AgentState
):
    worker_result = (
        state["worker_result"]
    )

    if state["risk_result"]:
        worker_result = f"""
Risk analysis:
{state["risk_result"]}

Worker answer:
{worker_result}
"""

    result = reviewer_agent(
        state["user_input"],
        worker_result
    )

    return {
        "review_result":
            result
    }

def expected_agent_for_question(
    question
):
    question = question.lower()

    if any(
        word in question
        for word in RAG_WORDS
    ):
        return "rag"

    if any(
        word in question
        for word in PARALLEL_WORDS
    ):
        return "parallel"

    if any(
        word in question
        for word in [
            "calculate",
            "math",
            "+"
        ]
    ):
        return "math"

    if any(
        word in question
        for word in [
            "research",
            "history",
            "explain"
        ]
    ):
        return "research"

    return "general"

def evaluator_node(
    state: AgentState
):
    expected_agent = expected_agent_for_question(
        state["user_input"]
    )

    routing_accuracy_score = 0.0

    if state["selected_agent"] == expected_agent:
        routing_accuracy_score = 1.0

    worker_quality_score = 0.0

    if state["worker_result"].strip():
        worker_quality_score = 0.6

    if len(
        state["worker_result"]
        .strip()
    ) >= 80:
        worker_quality_score = 1.0

    return {
        "worker_quality_score":
            worker_quality_score,
        "routing_accuracy_score":
            routing_accuracy_score
    }

def final_node(
    state: AgentState
):
    return {
        "final_answer":
            state["review_result"]
    }


graph = StateGraph(
    AgentState
)

graph.add_node(
    "supervisor",
    supervisor_node
)

graph.add_node(
    "worker",
    worker_node
)

graph.add_node(
    "risk",
    risk_node
)

graph.add_node(
    "parallel",
    parallel_node
)

graph.add_node(
    "reviewer",
    reviewer_node
)

graph.add_node(
    "evaluator",
    evaluator_node
)

graph.add_node(
    "final",
    final_node
)

graph.set_entry_point(
    "supervisor"
)

graph.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {
        "risk": "risk",
        "parallel": "parallel",
        "worker": "worker"
    }
)

graph.add_conditional_edges(
    "risk",
    route_after_risk,
    {
        "parallel": "parallel",
        "worker": "worker"
    }
)

graph.add_edge(
    "worker",
    "reviewer"
)

graph.add_edge(
    "parallel",
    "reviewer"
)

graph.add_edge(
    "reviewer",
    "evaluator"
)

graph.add_edge(
    "evaluator",
    "final"
)

graph.add_edge(
    "final",
    END
)

app = graph.compile()

