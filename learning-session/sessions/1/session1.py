import json
import os

from dotenv import load_dotenv
from openai import OpenAI


def call_llm_api() -> None:
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
    )

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain what an AI agent is in 2 sentences."},
        ],
    )

    print(response.choices[0].message.content)

def structured_output() -> None:
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
    )

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """
    You are an intent classifier.

    Return ONLY valid JSON.

    Schema:
    {
        "intent": string,
        "needs_tool": boolean,
        "reason": string
    }
    """
            },
            {
                "role": "user",
                # "content": "Schedule a meeting with John tomorrow at 3pm"
                "content": "Send email to John"
            }
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    print(content)

    parsed = json.loads(content)

    print(parsed["intent"])
