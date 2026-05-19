from openai import OpenAI
from dotenv import load_dotenv
import json

import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


def create_plan(user_input):

    system_prompt = """
You are a workflow planner.

Break the user request into executable steps.

Available tools:
- get_weather(location)
- calculator(expression)
- current_time(city)
- currency_conversion(amount, from_currency, to_currency)
- search_notes(query)

Return ONLY valid JSON.

Schema:
{
  "steps": [
    {
      "step_number": int,
      "action": string,
      "tool": string,
      "arguments": {}
    }
  ]
}
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

    return json.loads(content)
