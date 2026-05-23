from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from prompts import SYSTEM_PROMPT
from memory import get_user_profile
from tools import (
    calculator,
    get_current_time,
    search_knowledge_base
)


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

MAX_TOTAL_TOKENS = 8000
MAX_ESTIMATED_COST = 0.01
ESTIMATED_COST_PER_1K_TOKENS = 0.001


def get_token_usage(response):
    if not response.usage:
        return 0

    return response.usage.total_tokens or 0


def estimate_cost(total_tokens):
    return (total_tokens / 1000) * ESTIMATED_COST_PER_1K_TOKENS


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

    return json.loads(content), get_token_usage(response)

def execute_tool(
    tool_name,
    tool_arguments
):
    tool_arguments = normalize_tool_arguments(
        tool_name,
        tool_arguments
    )

    if not require_approval(tool_name, tool_arguments):
        return "Tool execution denied by user approval."

    if tool_name not in TOOLS:

        return "Tool not found"

    tool_function = TOOLS[tool_name]

    try:

        return tool_function(**tool_arguments)

    except Exception as e:

        return f"Tool execution failed: {str(e)}"


def tool_failed(tool_result):
    return isinstance(tool_result, str) and (
        tool_result.startswith("Tool not found")
        or tool_result.startswith("Tool execution failed")
        or tool_result.startswith("Calculation error")
    )


def reflect_tool_retry(user_input, decision, tool_result):
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

    return json.loads(response.choices[0].message.content), get_token_usage(response)

def run_agent(user_input):

    conversation_history = []

    max_iterations = 5
    total_tokens = 0

    for iteration in range(max_iterations):

        decision, token_usage = reasoning_step(
            user_input,
            conversation_history
        )
        total_tokens += token_usage
        estimated_cost = estimate_cost(total_tokens)

        print("\n=== REASONING STEP ===")
        print(decision)
        print("\n=== BUDGET ===")
        print({
            "iteration": iteration + 1,
            "tokens": total_tokens,
            "estimated_cost": estimated_cost
        })

        if total_tokens > MAX_TOTAL_TOKENS or estimated_cost > MAX_ESTIMATED_COST:
            return "Agent stopped because budget limit was reached."

        if not decision["needs_tool"]:

            return decision["final_answer"]

        tool_result = execute_tool(
            decision["tool_name"],
            decision["tool_arguments"]
        )

        if tool_failed(tool_result):
            retry_decision, retry_tokens = reflect_tool_retry(
                user_input,
                decision,
                tool_result
            )
            total_tokens += retry_tokens

            print("\n=== RETRY REFLECTION ===")
            print(retry_decision)
            print("\n=== BUDGET ===")
            print({
                "iteration": iteration + 1,
                "tokens": total_tokens,
                "estimated_cost": estimate_cost(total_tokens)
            })

            if total_tokens > MAX_TOTAL_TOKENS or estimate_cost(total_tokens) > MAX_ESTIMATED_COST:
                return "Agent stopped because budget limit was reached."

            if retry_decision["retry"]:
                tool_result = execute_tool(
                    retry_decision["tool_name"],
                    retry_decision["tool_arguments"]
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

    return "Agent exceeded max iterations."

# from openai import OpenAI
# from dotenv import load_dotenv
# from memory import (
#     add_message,
#     get_messages,
#     get_user_profile,
#     get_summary,
#     update_summary,
#     clear_memory,
#     need_summary,
# )

# import os

# load_dotenv()
# profile = get_user_profile()
# client = OpenAI(
#     api_key=os.getenv("LLM_API_KEY"),
#     base_url=os.getenv("LLM_BASE_URL"),
# )

# def chat(user_input):

#     add_message("user", user_input)
#     summary = get_summary()

#     messages = [
#         {
#             "role": "system",
#             "content": f"""
# You are a helpful assistant.
# Use conversation history naturally.

# User profile:
# - Favorite language: {profile["favorite_language"]}
# - City: {profile["city"]}
# - Learning goal: {profile["learning_goal"]}

# Conversation summary:{summary}
# """
#         }
#     ]
#     pass_conversations = get_messages()
#     messages.extend(pass_conversations)
#     # print('get_messages', pass_conversations)

#     response = client.chat.completions.create(
#         model=os.getenv("LLM_MODEL"),
#         messages=messages
#     )

#     assistant_reply = response.choices[0].message.content

#     add_message("assistant", assistant_reply)
#     summarize_conversation()    

#     return assistant_reply

# def summarize_conversation():
#     messages = get_messages()

#     if not need_summary():
#         return
    
#     print("============Summarizing Messages==============")
#     response = client.chat.completions.create(
#         model=os.getenv("LLM_MODEL"),
#         messages=[
#             {
#                 "role": "system",
#                 "content": "Summarize this conversation briefly. Keep important user facts, goals, and decisions."
#             },
#             {
#                 "role": "user",
#                 "content": str(messages)
#             }
#         ]
#     )

#     summary = response.choices[0].message.content

#     update_summary(summary)
#     clear_memory()
