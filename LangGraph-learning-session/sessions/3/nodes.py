import os
from dotenv import load_dotenv
from openai import OpenAI

from state import AgentState
from tools import (
    calculator,
)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")


def classify_input_node(
    state: AgentState
):
    user_input = state["user_input"].lower()
    expression = (
        user_input
        .replace("calculate", "")
        .strip()
    )

    if "calculate" in user_input and expression:
        intent = "calculator"
        confidence = 0.9
    else:
        intent = "unclear"
        if state["clarification_count"] == 0:
            confidence = 0.6
        else:
            confidence = 0.3

    return {
        "intent": intent,
        "confidence": confidence
    }


def clarification_node(
    state: AgentState
):
    clarified_input = input(
        "Please clarify the calculation: "
    )

    return {
        "user_input": clarified_input,
        "clarification_count": (
            state["clarification_count"] + 1
        )
    }


def confidence_validation_node(
    state: AgentState
):
    if state["confidence"] < 0.5:
        return {
            "confidence_status": "low"
        }

    return {
        "confidence_status": "ok"
    }


def human_review_node(
    state: AgentState
):
    validation_errors = state.get(
        "validation_errors",
        []
    )

    if validation_errors:
        return {
            "final_answer": (
                "Human review required: "
                f"{', '.join(validation_errors)}."
            )
        }

    return {
        "final_answer": (
            "Low confidence. "
            "Please send this request to human review."
        )
    }


def calculator_node(
    state: AgentState
):

    user_input = (
        state["user_input"]
        .replace("calculate", "")
        .strip()
    )

    result = calculator(user_input)

    return {
        "response": result
    }


def validate_result_node(
    state: AgentState
):
    response = state["response"]
    if response.startswith("ERROR"):
        if state["retry_count"] < state["max_retries"]:
            return {
                "validation_status": "retry",
                "retry_count": (
                    state["retry_count"] + 1
                )
            }
        
        return {
            "validation_status": "timeout",
            "timed_out": True
        }

    return {
        "validation_status": "success"
    }


def multi_validation_node(
    state: AgentState
):
    validation_errors = []
    response = state["response"]
    user_input = state["user_input"].lower()

    try:
        float(response)
        output_format_status = "valid"
    except ValueError:
        output_format_status = "invalid"
        validation_errors.append("invalid output format")

    if state["confidence"] < 0.5:
        validation_errors.append("low confidence")

    if (
        "admin" in user_input
        or "delete" in user_input
        or "restricted" in user_input
    ):
        permission_status = "denied"
        validation_errors.append("permission denied")
    else:
        permission_status = "allowed"

    if validation_errors:
        final_validation_status = "failed"
    else:
        final_validation_status = "passed"

    return {
        "output_format_status": output_format_status,
        "permission_status": permission_status,
        "final_validation_status": final_validation_status,
        "validation_errors": validation_errors
    }


def fallback_node(
    state: AgentState
):
    return {
        "final_answer": (
            "Unable to complete request "
            "after retries."
        )
    }


def timeout_node(
    state: AgentState
):
    return {
        "final_answer": (
            "Workflow terminated because "
            "retry limit was exceeded."
        )
    }


def logging_node(
    state: AgentState
):
    execution_path = [
        "classify",
        "confidence_validate"
    ]
    failures = []

    if state["clarification_count"] > 0:
        execution_path.extend([
            "clarify",
            "classify",
            "confidence_validate"
        ])

    if state["confidence_status"] == "low":
        execution_path.extend([
            "human_review",
            "logging"
        ])
        failures.append("low confidence")
    elif state["intent"] == "unclear":
        execution_path.extend([
            "clarify",
            "classify"
        ])
    else:
        for _ in range(state["retry_count"] + 1):
            execution_path.extend([
                "calculator",
                "validate"
            ])

        if state["retry_count"] > 0:
            failures.append("calculator retry")

        if state["validation_status"] == "success":
            execution_path.extend([
                "multi_validate",
                "final",
                "logging"
            ])
            if state["final_validation_status"] == "failed":
                execution_path = execution_path[:-2]
                execution_path.extend([
                    "human_review",
                    "logging"
                ])
                failures.extend(state["validation_errors"])
        elif state["validation_status"] == "timeout":
            execution_path.extend([
                "timeout",
                "logging"
            ])
            failures.append("retry limit exceeded")
        else:
            execution_path.extend([
                "fallback",
                "logging"
            ])
            failures.append("calculator failed")

    return {
        "execution_path": execution_path,
        "failures": failures
    }


def final_response_node(
    state: AgentState
):

    return {
        "final_answer": (
            f"Final Result: "
            f"{state['response']}"
        )
    }
