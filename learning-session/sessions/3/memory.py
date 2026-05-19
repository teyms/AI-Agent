import json
from pathlib import Path

user_profile = {
    "favorite_language": "Python",
    "city": "Johor",
    "learning_goal": "Learn AI agents"
}

MAX_MESSAGES = 10
MEMORY_FILE = Path(__file__).with_name("memory.json")

conversation_history = []
conversation_summary = ""

def load_memory():
    global conversation_history, conversation_summary

    if not MEMORY_FILE.exists():
        return

    with MEMORY_FILE.open("r", encoding="utf-8") as file:
        loaded_memory = json.load(file)

    if isinstance(loaded_memory, list):
        conversation_history = loaded_memory
    elif isinstance(loaded_memory, dict):
        conversation_summary = loaded_memory.get("summary", "")
        conversation_history = loaded_memory.get("messages", [])

def save_memory():
    memory_data = {
        "summary": conversation_summary,
        "messages": conversation_history
    }

    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(memory_data, file, indent=2)

load_memory()  

def add_message(role, content):
    conversation_history.append({
        "role": role,
        "content": content
    })
    #comment to achieve auto summarize of messages
    # if len(conversation_history) > MAX_MESSAGES:
    #     conversation_history.pop(0)
    save_memory()

def get_messages():
    return conversation_history


def clear_memory():
    global conversation_summary

    conversation_history.clear()
    conversation_summary = ""
    save_memory()    
    # conversation_history.clear()
    # save_memory()


def update_summary(summary_text):
    global conversation_summary

    conversation_summary = summary_text
    save_memory()

def get_summary():
    return conversation_summary

def get_user_profile():
    return user_profile

def need_summary():
    return len(conversation_history)>MAX_MESSAGES
