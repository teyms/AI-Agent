import json
import sqlite3
from state import (
    DB_PATH,
    STATE_ID,
    init_state_db
)
from nodes import (
    classify_intent_node,
    calculator_tool_node,
    weather_tool_node,
    retrieval_node,
    parallel_retrieval_node,
    merge_retrieval_node,
    summarization_node,
    validation_node,
    retry_node,
    human_approval_node,
    final_response_node
)

NODES = {
    "START": classify_intent_node,
    "CALCULATOR_TOOL": calculator_tool_node,
    "WEATHER_TOOL": weather_tool_node,
    "RETRIEVAL": retrieval_node,
    "PARALLEL_RETRIEVAL": parallel_retrieval_node,
    "MERGE_RETRIEVAL": merge_retrieval_node,
    "SUMMARIZATION": summarization_node,
    "VALIDATION": validation_node,
    "RETRY": retry_node,
    "HUMAN_APPROVAL": human_approval_node,
    "FINAL_RESPONSE": final_response_node
}


def run_graph(state):
    max_iterations = 20
    iterations = 0

    if not hasattr(state, "execution_path"):
        state.execution_path = []

    while not state.completed:
        iterations += 1
        if iterations > max_iterations:
            raise Exception(
                "Graph exceeded max iterations"
            )

        current_node = state.current_node
        state.execution_path.append(current_node)
        print(
            f"\nExecuting Node:"
            f" {current_node}"
        )
        node_function = NODES[current_node]
        state = node_function(state)
        save_state(state)

    print_workflow_path(state)
    return state


def print_workflow_path(state):
    print("\nWorkflow Path:")

    for index, node_name in enumerate(state.execution_path):
        if index == 0:
            print(node_name)
        else:
            print(f"-> {node_name}")

def save_state(state):
    state_json = json.dumps(
        state.__dict__,
        indent=2
    )

    with sqlite3.connect(DB_PATH) as db:
        init_state_db(db)
        db.execute(
            """
            INSERT INTO workflow_state (
                id,
                state_json,
                updated_at
            )
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                STATE_ID,
                state_json
            )
        )


