from tools import (
    calculator,
    get_weather,
    search_knowledge_base
)

def classify_intent_node(state):
    user_input = state.user_input.lower()
    if "weather" in user_input:
        state.current_node = "WEATHER_TOOL"
    elif "calculate" in user_input:
        state.current_node = "CALCULATOR_TOOL"
    elif (
        "search" in user_input
        or "policy" in user_input
        or "retrieve" in user_input
        or "knowledge" in user_input
    ):
        state.current_node = "PARALLEL_RETRIEVAL"
    else:
        state.current_node = "FINAL_RESPONSE"

    return state

def weather_tool_node(state):
    result = get_weather("Singapore")
    state.tool_results.append(result)
    state.last_tool_node = "WEATHER_TOOL"
    state.current_node = "VALIDATION"

    return state


def calculator_tool_node(state):
    expression = (
        state.user_input
        .replace("calculate", "")
        .strip()
    )
    result = calculator(expression)
    state.tool_results.append(result)
    state.last_tool_node = "CALCULATOR_TOOL"
    state.current_node = "VALIDATION"

    return state


def retrieval_node(state):
    chunks = search_knowledge_base(state.user_input)
    state.retrieved_chunks = chunks
    state.tool_results.append(chunks)
    state.last_tool_node = "RETRIEVAL"
    state.current_node = "VALIDATION"

    return state


def policy_retrieval_node(state):
    return search_knowledge_base(
        f"{state.user_input} company policy"
    )


def notes_retrieval_node(state):
    return search_knowledge_base(
        f"{state.user_input} agent notes"
    )


def parallel_retrieval_node(state):
    state.parallel_retrieval_results = {
        "policy": policy_retrieval_node(state),
        "notes": notes_retrieval_node(state)
    }
    state.last_tool_node = "PARALLEL_RETRIEVAL"
    state.current_node = "MERGE_RETRIEVAL"

    return state


def merge_retrieval_node(state):
    merged_chunks = []
    seen = set()

    for chunks in state.parallel_retrieval_results.values():
        for chunk in chunks:
            key = (
                chunk["source"],
                chunk["text"]
            )

            if key in seen:
                continue

            seen.add(key)
            merged_chunks.append(chunk)

    state.retrieved_chunks = merged_chunks
    state.tool_results.append(merged_chunks)
    state.current_node = "VALIDATION"

    return state


def summarization_node(state):
    if state.retrieved_chunks:
        texts = [
            chunk["text"]
            for chunk in state.retrieved_chunks
        ]
        state.summary = " ".join(texts)
    elif state.tool_results:
        state.summary = str(state.tool_results[-1])
    else:
        state.summary = "No useful result found."

    state.current_node = "FINAL_RESPONSE"

    return state


def final_response_node(state):

    if state.summary:
        state.final_answer = state.summary

    elif state.tool_results:
        state.final_answer = (
            f"Tool result: "
            f"{state.tool_results[-1]}"
        )

    else:
        state.final_answer = (
            "No tool used."
        )

    state.completed = True

    return state



def validation_node(state):
    if not state.tool_results:
        state.current_node = "FINAL_RESPONSE"
        return state

    last_result = str(state.tool_results[-1])

    if (
        "failed" in last_result.lower()
        or "error" in last_result.lower()
        or "not found" in last_result.lower()
    ):
        if state.retries < state.max_retries:
            state.current_node = "RETRY"
        else:
            state.current_node = "HUMAN_APPROVAL"
    else:
        state.current_node = "SUMMARIZATION"

    return state


def retry_node(state):
    state.retries += 1

    if state.last_tool_node:
        state.current_node = state.last_tool_node
    else:
        state.current_node = "HUMAN_APPROVAL"

    return state


def human_approval_node(state):
    approval = input(
        "Approve action? (yes/no): "
    )
    if approval == "yes":
        state.current_node = "FINAL_RESPONSE"
    else:
        state.final_answer = (
            "Action rejected."
        )
        state.completed = True

    return state

