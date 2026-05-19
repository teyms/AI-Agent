from openai import OpenAI
from dotenv import load_dotenv
from memory import (
    add_message,
    get_messages,
    get_user_profile,
    get_summary,
    update_summary,
    clear_memory,
    need_summary,
)

import os

load_dotenv()
profile = get_user_profile()
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

def chat(user_input):

    add_message("user", user_input)
    summary = get_summary()

    messages = [
        {
            "role": "system",
            "content": f"""
You are a helpful assistant.
Use conversation history naturally.

User profile:
- Favorite language: {profile["favorite_language"]}
- City: {profile["city"]}
- Learning goal: {profile["learning_goal"]}

Conversation summary:{summary}
"""
        }
    ]
    pass_conversations = get_messages()
    messages.extend(pass_conversations)
    # print('get_messages', pass_conversations)

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=messages
    )

    assistant_reply = response.choices[0].message.content

    add_message("assistant", assistant_reply)
    summarize_conversation()    

    return assistant_reply

def summarize_conversation():
    messages = get_messages()

    if not need_summary():
        return
    
    print("============Summarizing Messages==============")
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "system",
                "content": "Summarize this conversation briefly. Keep important user facts, goals, and decisions."
            },
            {
                "role": "user",
                "content": str(messages)
            }
        ]
    )

    summary = response.choices[0].message.content

    update_summary(summary)
    clear_memory()