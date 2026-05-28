import os
import json

from state import AgentState
from prompts import SYSTEM_PROMPT

from dotenv import load_dotenv
from openai import OpenAI

from tools import get_current_time

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")


def agent_node(
    state: AgentState
):
    profile = state["user_profile"]
    system_prompt = f"""
{SYSTEM_PROMPT}

User profile:
- Preferred language: {profile["preferred_language"]}
- City: {profile["city"]}
- Timezone: {profile["timezone"]}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            }
        ] + state["messages"]
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    parsed = json.loads(content)

    updates = {
        "iteration_count": (
            state["iteration_count"] + 1
        )
    }

    if parsed["needs_tool"]:
        updates["current_tool"] = (
            parsed["tool_name"]
        )
        updates["tool_input"] = (
            parsed["tool_input"]
        )

    else:
        updates["final_answer"] = (
            parsed["final_answer"]
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

    result = get_current_time()

    observation = (
        f"Tool Result: {result}"
    )

    return {
        "tool_output": result,
        "messages": (
            state["messages"] + [
                {
                    "role": "user",
                    "content": observation
                }
            ]
        )
    }



    
