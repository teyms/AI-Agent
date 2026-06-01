import os
import json
from prompts import SYSTEM_PROMPT
from state import AgentState
from validators import (
    validate_tool_name,
    validate_tool_output,
    score_answer_quality,
    estimate_tokens,
    validate_permission
)
from tools import TOOLS

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

MODEL_NAME = os.getenv("LLM_MODEL")


def agent_node(
    state: AgentState
):
    estimated_tokens = (
        state["token_count"]
        + estimate_tokens(state["user_input"])
        + 50
    )

    if estimated_tokens > state["max_tokens"]:
        return {
            "token_count": estimated_tokens,
            "cost_guardrail_status": "exceeded",
            "validation_status": "fallback",
            "error_message": "Token budget exceeded"
        }

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": state["user_input"]
            }
        ]
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    try:
        parsed = json.loads(content)
        token_count = estimated_tokens + estimate_tokens(
            content
        )

        return {
            "proposed_tool":
                parsed["tool_name"],

            "tool_input":
                parsed["tool_input"],

            "token_count": token_count,
            "cost_guardrail_status": "ok",
            "error_message": ""
        }

    except Exception:

        return {
            "error_message":
                "Invalid JSON"
        }

def validate_node(
    state: AgentState
):
    if state["cost_guardrail_status"] == "exceeded":
        return {
            "validation_status":
                "fallback"
        }

    if state["error_message"]:
        if state["retry_count"] < 2:
            return {
                "validation_status":
                    "retry",

                "retry_count":
                    state["retry_count"] + 1
            }

        return {
            "validation_status":
                "fallback"
        }

    if not validate_tool_name(
        state["proposed_tool"]
    ):
        return {
            "validation_status":
                "fallback"
        }

    if not validate_permission(
        state["user_input"],
        state["proposed_tool"]
    ):
        return {
            "validation_status": "fallback",
            "permission_status": "denied",
            "error_message": "Permission denied"
        }

    return {
        "validation_status":
            "valid",
        "permission_status": "allowed"
    }


def execute_tool_node(
    state: AgentState
):
    try:
        tool_function = TOOLS[
            state["proposed_tool"]
        ]

        if state["proposed_tool"] == "get_current_time":
            result = tool_function()
        else:
            result = tool_function(
                state["tool_input"]
            )

        return {
            "tool_output": result
        }

    except Exception as e:

        return {
            "error_message":
                str(e)
        }


def output_validation_node(
    state: AgentState
):
    if not validate_tool_output(
        state["tool_output"]
    ):
        return {
            "output_validation_status":
                "fallback",
            "confidence_score": 0.0,
            "confidence_status": "low"
        }

    confidence_score = score_answer_quality(
        state["tool_output"]
    )

    if confidence_score < 0.7:
        confidence_status = "low"
    else:
        confidence_status = "ok"

    return {
        "output_validation_status": "valid",
        "confidence_score": confidence_score,
        "confidence_status": confidence_status
    }


def human_review_node(
    state: AgentState
):
    reason = state["secondary_validation_reason"]

    if reason:
        return {
            "final_answer":
                (
                    "Human review required: "
                    f"{reason}"
                )
        }

    return {
        "final_answer":
            (
                "Human review required "
                "because confidence is low."
            )
    }


def secondary_validation_node(
    state: AgentState
):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": """
You are a validation judge.

Return ONLY valid JSON.

Schema:
{
    "valid": boolean,
    "reason": string
}

Rules:
- valid is true only if the tool output directly answers the user.
- valid is false if the output is irrelevant, unsafe, empty, or unclear.
"""
            },
            {
                "role": "user",
                "content": f"""
User request:
{state["user_input"]}

Tool used:
{state["proposed_tool"]}

Tool input:
{state["tool_input"]}

Tool output:
{state["tool_output"]}
"""
            }
        ]
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    try:
        parsed = json.loads(content)
    except Exception:
        return {
            "secondary_validation_status": "review",
            "secondary_validation_reason": (
                "secondary validator returned invalid JSON"
            )
        }

    if parsed.get("valid"):
        return {
            "secondary_validation_status": "valid",
            "secondary_validation_reason": (
                parsed.get("reason", "")
            )
        }

    return {
        "secondary_validation_status": "review",
        "secondary_validation_reason": (
            parsed.get(
                "reason",
                "secondary validator rejected the output"
            )
        )
    }


def fallback_node(
    state: AgentState
):
    if state["cost_guardrail_status"] == "exceeded":
        reason = "token budget exceeded"
    elif state["permission_status"] == "denied":
        reason = "permission denied"
    else:
        reason = "request safely"

    return {
        "final_answer":
            (
                "Unable to complete "
                f"{reason}."
            )
    }

def final_node(
    state: AgentState
):
    return {
        "final_answer":
            (
                f"Result: "
                f"{state['tool_output']}"
            )
    }

