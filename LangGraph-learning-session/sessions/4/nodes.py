import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from state import AgentState
from prompts import SYSTEM_PROMPT

from tools import TOOLS

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")


def append_node_log(
    state: AgentState,
    node_name: str
):
    return state["node_execution_log"] + [
        node_name
    ]



def agent_node(
    state: AgentState
):
    iteration_count = (
        state["iteration_count"] + 1
    )

    if iteration_count > state["max_iterations"]:
        return {
            "iteration_count": iteration_count,
            "node_execution_log": append_node_log(
                state,
                "agent"
            ),
            "final_answer": (
                "Stopped because maximum "
                "iterations were reached."
            ),
            "fallback_reason": "iteration limit"
        }

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + state["messages"]
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        return {
            "json_schema_valid": False,
            "validation_error": (
                f"Invalid JSON: {str(e)}"
            ),
            "iteration_count": iteration_count,
            "node_execution_log": append_node_log(
                state,
                "agent"
            ),
            "messages": (
                state["messages"] + [
                    {
                        "role": "assistant",
                        "content": content
                    }
                ]
            )
        }

    required_fields = {
        "thought",
        "needs_tool",
        "tool_name",
        "tool_input",
        "final_answer"
    }
    if not required_fields.issubset(parsed):
        return {
            "json_schema_valid": False,
            "validation_error": "Agent JSON schema is missing fields.",
            "iteration_count": iteration_count,
            "node_execution_log": append_node_log(
                state,
                "agent"
            )
        }

    updates = {}

    if parsed["needs_tool"]:
        updates["current_tool"] = (
            parsed["tool_name"]
        )
        updates["tool_input"] = (
            parsed["tool_input"]
        )
        updates["tool_output"] = ""
        updates["tool_failed"] = False
        updates["tool_output_valid"] = True
    else:
        updates["final_answer"] = (
            parsed["final_answer"]
        )
    updates["json_schema_valid"] = True
    updates["validation_error"] = ""
    updates["iteration_count"] = iteration_count
    updates["node_execution_log"] = append_node_log(
        state,
        "agent"
    )
    updates["reasoning_traces"] = (
        state["reasoning_traces"] + [
            parsed["thought"]
        ]
    )
    updates["messages"] = (
        state["messages"] + [
            {
                "role": "assistant",
                "content": content
            }
        ]
    )

    return updates

def tool_node(
    state: AgentState
):
    tool_name = state["current_tool"]
    tool_input = state["tool_input"]
    tool_function = TOOLS.get(tool_name)

    if tool_function is None:
        result = f"Tool error: unknown tool {tool_name}"
    elif tool_name == "get_current_time":
        result = tool_function()
    else:
        result = tool_function(tool_input)

    tool_failed = (
        result.startswith("Calculation error")
        or result.startswith("Tool error")
        or result.startswith("Knowledge base search failed")
        or result == "Weather not found."
        or result == "Knowledge base database not found."
    )
    retry_count = state["retry_count"]

    if tool_failed:
        retry_count += 1

    tool_message = (
        f"Tool Result: {result}"
    )

    return {
        "tool_output": result,
        "tool_failed": tool_failed,
        "tool_output_valid": not tool_failed,
        "retry_count": retry_count,
        "node_execution_log": append_node_log(
            state,
            "tool"
        ),
        "tool_calls": (
            state["tool_calls"] + [
                {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_output": result,
                    "failed": tool_failed
                }
            ]
        ),
        "messages": (
            state["messages"] + [
                {
                    "role": "user",
                    "content": tool_message
                }
            ]
        )
    }


def validation_node(
    state: AgentState
):
    if not state["json_schema_valid"]:
        return {
            "fallback_reason": state["validation_error"],
            "node_execution_log": append_node_log(
                state,
                "validation"
            )
        }

    if state["tool_output"]:
        tool_output = state["tool_output"]
        tool_output_valid = not (
            tool_output.startswith("Calculation error")
            or tool_output.startswith("Tool error")
            or tool_output.startswith("Knowledge base search failed")
            or tool_output == "Weather not found."
            or tool_output == "Knowledge base database not found."
        )

        if not tool_output_valid:
            return {
                "tool_failed": True,
                "tool_output_valid": False,
                "validation_error": "Tool output failed validation.",
                "node_execution_log": append_node_log(
                    state,
                    "validation"
                )
            }

    return {
        "tool_output_valid": True,
        "validation_error": "",
        "node_execution_log": append_node_log(
            state,
            "validation"
        )
    }


def fallback_node(
    state: AgentState
):
    if state["validation_error"]:
        reason = state["validation_error"]
    elif state["tool_failed"]:
        reason = (
            "tool failed after retry"
        )
    else:
        reason = state["fallback_reason"]

    return {
        "fallback_reason": reason,
        "node_execution_log": append_node_log(
            state,
            "fallback"
        ),
        "final_answer": (
            f"Fallback: {reason}."
        )
    }










