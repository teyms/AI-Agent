from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import uuid
import time
from prompts import SYSTEM_PROMPT
from memory import get_user_profile
from tools import (
    calculator,
    get_current_time,
    search_knowledge_base
)
from logging_config import logger
from persistence import save_state, load_state


load_dotenv()
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


TOOLS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "search_knowledge_base": search_knowledge_base
}

MAX_TOTAL_TOKENS = int(os.getenv("MAX_TOTAL_TOKENS", "8000"))
MAX_ESTIMATED_COST = 0.01
ESTIMATED_COST_PER_1K_TOKENS = 0.001


def log_json(event, **data):
    logger.info(
        json.dumps(
            {
                "event": event,
                **data,
            }
        )
    )


def get_token_usage(response):
    if not response.usage:
        return 0

    return response.usage.total_tokens or 0


def estimate_cost(total_tokens):
    return (total_tokens / 1000) * ESTIMATED_COST_PER_1K_TOKENS


def token_budget_exceeded(total_tokens):
    return total_tokens > MAX_TOTAL_TOKENS


def require_approval(tool_name, tool_arguments):
    if tool_name != "calculator":
        return True

    expression = tool_arguments.get("expression", "")
    print("\n=== APPROVAL REQUIRED ===")
    print(f"Tool: {tool_name}")
    print(f"Expression: {expression}")

    approval = input("Allow calculator execution? (yes/no): ")
    return approval.lower() == "yes"


def normalize_tool_arguments(tool_name, tool_arguments):
    if isinstance(tool_arguments, dict):
        return tool_arguments

    if tool_name == "calculator" and isinstance(tool_arguments, str):
        return {
            "expression": tool_arguments
        }

    return {}


def reasoning_step(
    user_input,
    conversation_history
):
    start_time = time.perf_counter()
    user_profile = get_user_profile()
    system_prompt = f"""
{SYSTEM_PROMPT}

User memory:
- Preferred language: {user_profile["preferred_language"]}
- Location: {user_profile["location"]}
- Favorite tools: {", ".join(user_profile["favorite_tools"])}
"""

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "system",
                "content": system_prompt
            }
        ] + conversation_history + [
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    content = response.choices[0].message.content
    latency_seconds = time.perf_counter() - start_time

    return safe_parse_json(content), get_token_usage(response), latency_seconds

def execute_tool(
    tool_name,
    tool_arguments,
    trace_id
):
    start_time = time.perf_counter()
    tool_arguments = normalize_tool_arguments(
        tool_name,
        tool_arguments
    )

    logger.info(
        f"[{trace_id}] Running tool: {tool_name}"
    )
    log_json(
        "tool_call_started",
        trace_id=trace_id,
        tool_name=tool_name,
        tool_arguments=tool_arguments,
    )

    if not require_approval(tool_name, tool_arguments):
        log_json(
            "tool_call_denied",
            trace_id=trace_id,
            tool_name=tool_name,
            latency_seconds=time.perf_counter() - start_time,
        )
        return "Tool execution denied by user approval."

    if tool_name not in TOOLS:

        log_json(
            "tool_call_error",
            trace_id=trace_id,
            tool_name=tool_name,
            error="Tool not found",
            latency_seconds=time.perf_counter() - start_time,
        )
        return "Tool not found"

    tool_function = TOOLS[tool_name]

    try:

        result = tool_function(**tool_arguments)
        log_json(
            "tool_call_finished",
            trace_id=trace_id,
            tool_name=tool_name,
            latency_seconds=time.perf_counter() - start_time,
        )
        return result

    except Exception as e:

        log_json(
            "tool_call_error",
            trace_id=trace_id,
            tool_name=tool_name,
            error=str(e),
            latency_seconds=time.perf_counter() - start_time,
        )
        return f"Tool execution failed: {str(e)}"


def tool_failed(tool_result):
    return isinstance(tool_result, str) and (
        tool_result.startswith("Tool not found")
        or tool_result.startswith("Tool execution failed")
        or tool_result.startswith("Calculation error")
    )


def reflect_tool_retry(user_input, decision, tool_result):
    start_time = time.perf_counter()
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """
You fix failed tool calls.

Return ONLY valid JSON.

Schema:
{
    "retry": boolean,
    "tool_name": string,
    "tool_arguments": {}
}

Rules:
- Retry only if the same goal can be attempted with corrected arguments.
- If retry is false, keep tool_name empty and tool_arguments empty.
"""
            },
            {
                "role": "user",
                "content": f"""
Original user request:
{user_input}

Failed decision:
{json.dumps(decision)}

Tool result:
{tool_result}
"""
            }
        ]
    )

    latency_seconds = time.perf_counter() - start_time
    return safe_parse_json(response.choices[0].message.content), get_token_usage(response), latency_seconds

def run_agent(user_input, trace_id=None, recovered_state=None):
    trace_id = trace_id or str(uuid.uuid4())
    logger.info(
        f"[{trace_id}] Starting agent run"
    )

    conversation_history = []
    if recovered_state:
        conversation_history = recovered_state.get("conversation_history", [])

    max_iterations = 5
    total_tokens = 0
    if recovered_state:
        total_tokens = recovered_state.get("total_tokens", 0)

    save_state(
        trace_id,
        {
            "user_input": user_input,
            "conversation_history": conversation_history,
            "total_tokens": total_tokens,
            "iteration": 0,
        },
        "running"
    )

    for iteration in range(max_iterations):

        decision, token_usage, latency_seconds = reasoning_step(
            user_input,
            conversation_history
        )
        total_tokens += token_usage
        estimated_cost = estimate_cost(total_tokens)
        log_json(
            "reasoning_step",
            trace_id=trace_id,
            iteration=iteration + 1,
            latency_seconds=latency_seconds,
            token_usage=token_usage,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
        )

        if decision is None:
            log_json(
                "error",
                trace_id=trace_id,
                error="Agent failed to parse model response.",
            )
            save_state(
                trace_id,
                {
                    "user_input": user_input,
                    "conversation_history": conversation_history,
                    "total_tokens": total_tokens,
                    "iteration": iteration + 1,
                    "error": "Agent failed to parse model response.",
                },
                "failed"
            )
            return "Agent failed to parse model response."

        print("\n=== REASONING STEP ===")
        print(decision)
        print("\n=== BUDGET ===")
        print({
            "iteration": iteration + 1,
            "tokens": total_tokens,
            "estimated_cost": estimated_cost
        })

        if token_budget_exceeded(total_tokens):
            log_json(
                "token_budget_exceeded",
                trace_id=trace_id,
                total_tokens=total_tokens,
                max_total_tokens=MAX_TOTAL_TOKENS,
            )
            logger.info(
                f"[{trace_id}] Agent stopped because token budget was reached"
            )
            save_state(
                trace_id,
                {
                    "user_input": user_input,
                    "conversation_history": conversation_history,
                    "total_tokens": total_tokens,
                    "iteration": iteration + 1,
                },
                "stopped"
            )
            return "Agent stopped because token budget was reached."

        if estimated_cost > MAX_ESTIMATED_COST:
            logger.info(
                f"[{trace_id}] Agent stopped because budget limit was reached"
            )
            save_state(
                trace_id,
                {
                    "user_input": user_input,
                    "conversation_history": conversation_history,
                    "total_tokens": total_tokens,
                    "iteration": iteration + 1,
                },
                "stopped"
            )
            return "Agent stopped because budget limit was reached."

        if not decision["needs_tool"]:

            logger.info(
                f"[{trace_id}] Agent finished with final answer"
            )
            save_state(
                trace_id,
                {
                    "user_input": user_input,
                    "conversation_history": conversation_history,
                    "total_tokens": total_tokens,
                    "iteration": iteration + 1,
                    "final_answer": decision["final_answer"],
                },
                "completed"
            )
            return decision["final_answer"]

        tool_result = execute_tool(
            decision["tool_name"],
            decision["tool_arguments"],
            trace_id
        )

        if tool_failed(tool_result):
            retry_decision, retry_tokens, retry_latency_seconds = reflect_tool_retry(
                user_input,
                decision,
                tool_result
            )
            total_tokens += retry_tokens
            log_json(
                "retry_reflection",
                trace_id=trace_id,
                iteration=iteration + 1,
                latency_seconds=retry_latency_seconds,
                token_usage=retry_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimate_cost(total_tokens),
            )

            if retry_decision is None:
                retry_decision = {
                    "retry": False,
                    "tool_name": "",
                    "tool_arguments": {}
                }

            print("\n=== RETRY REFLECTION ===")
            print(retry_decision)
            print("\n=== BUDGET ===")
            print({
                "iteration": iteration + 1,
                "tokens": total_tokens,
                "estimated_cost": estimate_cost(total_tokens)
            })

            if token_budget_exceeded(total_tokens):
                log_json(
                    "token_budget_exceeded",
                    trace_id=trace_id,
                    total_tokens=total_tokens,
                    max_total_tokens=MAX_TOTAL_TOKENS,
                )
                logger.info(
                    f"[{trace_id}] Agent stopped because token budget was reached"
                )
                save_state(
                    trace_id,
                    {
                        "user_input": user_input,
                        "conversation_history": conversation_history,
                        "total_tokens": total_tokens,
                        "iteration": iteration + 1,
                        "last_decision": decision,
                        "last_tool_result": tool_result,
                    },
                    "stopped"
                )
                return "Agent stopped because token budget was reached."

            if estimate_cost(total_tokens) > MAX_ESTIMATED_COST:
                logger.info(
                    f"[{trace_id}] Agent stopped because budget limit was reached"
                )
                save_state(
                    trace_id,
                    {
                        "user_input": user_input,
                        "conversation_history": conversation_history,
                        "total_tokens": total_tokens,
                        "iteration": iteration + 1,
                        "last_decision": decision,
                        "last_tool_result": tool_result,
                    },
                    "stopped"
                )
                return "Agent stopped because budget limit was reached."

            if retry_decision["retry"]:
                tool_result = execute_tool(
                    retry_decision["tool_name"],
                    retry_decision["tool_arguments"],
                    trace_id
                )

        print("\n=== TOOL RESULT ===")
        print(tool_result)

        conversation_history.append({
            "role": "assistant",
            "content": json.dumps(decision)
        })

        conversation_history.append({
            "role": "user",
            "content": f"""
Tool result:
{tool_result}
"""
        })

        save_state(
            trace_id,
            {
                "user_input": user_input,
                "conversation_history": conversation_history,
                "total_tokens": total_tokens,
                "iteration": iteration + 1,
                "last_decision": decision,
                "last_tool_result": tool_result,
            },
            "running"
        )

    logger.info(
        f"[{trace_id}] Agent exceeded max iterations"
    )
    save_state(
        trace_id,
        {
            "user_input": user_input,
            "conversation_history": conversation_history,
            "total_tokens": total_tokens,
            "iteration": max_iterations,
        },
        "stopped"
    )
    return "Agent exceeded max iterations."


def recover_run(run_id):
    saved_run = load_state(run_id)
    if not saved_run:
        return "No saved run found."

    state = saved_run["state"]
    return run_agent(
        state["user_input"],
        trace_id=run_id,
        recovered_state=state,
    )

def safe_parse_json(content):

    try:

        return json.loads(content)

    except Exception as e:

        logger.error(
            f"Invalid JSON: {str(e)}"
        )

        return None
