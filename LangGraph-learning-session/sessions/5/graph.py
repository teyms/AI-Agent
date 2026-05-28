from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_node,
    tool_node
)

from checkpointer import (
    checkpointer
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


def route_agent(
    state: AgentState
):

    if state["final_answer"]:

        return END

    return "tool"


graph.add_conditional_edges(
    "agent",
    route_agent,
    {
        "tool": "tool",
        END: END
    }
)

graph.add_edge(
    "tool",
    "agent"
)

graph.set_entry_point(
    "agent"
)


app = graph.compile(
    checkpointer=checkpointer
)


