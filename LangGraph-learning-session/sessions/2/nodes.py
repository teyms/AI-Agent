import os
from dotenv import load_dotenv
from openai import OpenAI

from state import AgentState
from tools import (
    get_weather,
    calculator,
    get_current_time,
    search_knowledge_base,
)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")



def classify_intent_node(
    state: AgentState
):
    user_input = state["user_input"].lower()

    if "weather" in user_input:
        intent = "weather"
    elif "calculate" in user_input:
        intent = "calculator"
    elif (
        "rag" in user_input
        or "knowledge" in user_input
        or "policy" in user_input
        or "search" in user_input
    ):
        intent = "rag"
    elif "current time" in user_input or "time" in user_input:
        intent = "current_time"
    else:
        intent = "general"

    return {
        "intent": intent
    }

def weather_node(
    state: AgentState
):
    result = get_weather()

    return {
        "tool_result": result
    }


def calculator_node(
    state: AgentState
):
    user_input = state["user_input"]
    expression = (
        user_input
        .replace("calculate", "")
        .strip()
    )
    result = calculator(expression)

    return {
        "tool_result": result
    }

def current_time_node(
    state: AgentState
):
    result = get_current_time()

    return {
        "tool_result": result
    }

def rag_node(
    state: AgentState
):
    context = search_knowledge_base(
        state["user_input"]
    )

    return {
        "retrieved_context": context,
        "tool_result": context
    }

def validation_node(
    state: AgentState
):
    tool_result = state["tool_result"]

    if tool_result.startswith("Calculation failed"):
        validation_result = "invalid"
    else:
        validation_result = "valid"

    return {
        "validation_result": validation_result
    }

def retry_node(
    state: AgentState
):
    user_input = state["user_input"]
    retries = state.get("retries", 0) + 1
    expression = (
        user_input
        .replace("calculate", "")
        .strip()
    )
    result = calculator(expression)

    return {
        "tool_result": result,
        "retries": retries
    }

def logging_node(
    state: AgentState
):
    intent = state["intent"]
    execution_path = [
        "classify",
        intent
    ]

    if intent == "calculator":
        execution_path.append("validation")

        if state.get("validation_result") == "invalid":
            execution_path.append("retry")

    execution_path.extend([
        "logging",
        "final"
    ])

    return {
        "execution_path": execution_path
    }

def general_response_node(
    state: AgentState
):

    return {
        "tool_result": (
            "General response."
        )
    }

def final_response_node(
    state: AgentState
):

    final_answer = (
        f"Result: "
        f"{state['tool_result']}"
    )

    return {
        "final_answer": final_answer
    }

