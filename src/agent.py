import sys
from pathlib import Path
import json
import os
SESSION_2_PATH = Path(__file__).resolve().parents[1] / "learning-session" / "sessions" / "2"
sys.path.append(str(SESSION_2_PATH))

from session2 import get_weather, calculator,get_current_time, tell_joke
TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_current_time": get_current_time,
    "tell_joke": tell_joke,
}
from openai import OpenAI
from dotenv import load_dotenv
import json


load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


def decide_tool(user_input: str):

    system_prompt = """
You are an AI agent.

Decide whether a tool is needed.

Available tools:
1. get_weather(location)
2. calculator(expression)
3. get_current_time(city)
4. tell_joke(category)

Return ONLY valid JSON.

Schema:
{
    "needs_tool": boolean,
    "tool_name": string,
    "tool_arguments": {
        "key": "value"
    },
    "final_answer": string
}

Rules:
- If no tool needed, set final_answer.
- If tool needed, final_answer should be empty.
"""

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    content = response.choices[0].message.content

    return parse_tool_decision(content)


def execute_tool(tool_name, tool_arguments):

    if tool_name not in TOOLS:
        return "Tool not found."
    # if not isinstance(tool_arguments, dict):
    #     return "Invalid tool arguments."    

    tool_function = TOOLS[tool_name]

    max_retries = 3

    for attempt in range(max_retries):

        try:
            return tool_function(**tool_arguments)

        except Exception as e:

            print(f"Retry {attempt+1}")

            if attempt == max_retries - 1:
                return f"Tool execution failed: {str(e)}"


def run_agent(user_input: str):

    decision = decide_tool(user_input)

    print("\n=== AGENT DECISION ===")
    print(decision)

    if not decision["needs_tool"]:
        return decision["final_answer"]

    tool_result = execute_tool(
        decision["tool_name"],
        decision["tool_arguments"]
    )

    print("\n=== TOOL RESULT ===")
    print(tool_result)

    final_response = generate_final_response(
        user_input,
        tool_result
    )

    return final_response


def generate_final_response(user_input, tool_result):

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """
You are a helpful assistant.

Use the tool result to answer the user.
"""
            },
            {
                "role": "user",
                "content": f"""
User request:
{user_input}

Tool result:
{tool_result}
"""
            }
        ]
    )

    return response.choices[0].message.content

import json


def parse_tool_decision(content: str):
    try:
        decision = json.loads(content)
    except json.JSONDecodeError:
        return {
            "needs_tool": False,
            "tool_name": "",
            "tool_arguments": {},
            "final_answer": "I could not parse the model response."
        }

    required_keys = ["needs_tool", "tool_name", "tool_arguments", "final_answer"]

    for key in required_keys:
        if key not in decision:
            return {
                "needs_tool": False,
                "tool_name": "",
                "tool_arguments": {},
                "final_answer": f"Model response is missing key: {key}"
            }

    if not isinstance(decision["needs_tool"], bool):
        return {
            "needs_tool": False,
            "tool_name": "",
            "tool_arguments": {},
            "final_answer": "Model response has invalid needs_tool value."
        }

    if not isinstance(decision["tool_arguments"], dict):
        return {
            "needs_tool": False,
            "tool_name": "",
            "tool_arguments": {},
            "final_answer": "Model response has invalid tool_arguments value."
        }

    return decision