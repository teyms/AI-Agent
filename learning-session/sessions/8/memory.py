import json
from pathlib import Path


MEMORY_FILE = Path(__file__).with_name("conversation_memory.json")
MAX_MESSAGES = 10

conversation_history = []
user_profile = {
    "preferred_language": "Python",
    "location": "Johor",
    "favorite_tools": ["calculator", "search_knowledge_base"],
}


def load_memory():
    global conversation_history, user_profile

    if not MEMORY_FILE.exists():
        return

    with MEMORY_FILE.open("r", encoding="utf-8") as file:
        loaded_memory = json.load(file)

    if isinstance(loaded_memory, list):
        conversation_history = loaded_memory
    elif isinstance(loaded_memory, dict):
        conversation_history = loaded_memory.get("conversation_history", [])
        user_profile.update(loaded_memory.get("user_profile", {}))


def save_memory():
    memory_data = {
        "conversation_history": conversation_history,
        "user_profile": user_profile,
    }

    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(memory_data, file, indent=2)


def add_message(role, content):
    conversation_history.append({
        "role": role,
        "content": content,
    })

    if len(conversation_history) > MAX_MESSAGES:
        conversation_history.pop(0)

    save_memory()


def get_messages():
    return conversation_history


def clear_memory():
    conversation_history.clear()
    save_memory()


def get_user_profile():
    return user_profile


load_memory()
