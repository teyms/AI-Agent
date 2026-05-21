import json
from pathlib import Path


MEMORY_FILE = Path(__file__).with_name("conversation_memory.json")
MAX_MESSAGES = 10

conversation_history = []


def load_memory():
    global conversation_history

    if not MEMORY_FILE.exists():
        return

    with MEMORY_FILE.open("r", encoding="utf-8") as file:
        loaded_memory = json.load(file)

    if isinstance(loaded_memory, list):
        conversation_history = loaded_memory


def save_memory():
    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(conversation_history, file, indent=2)


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


load_memory()
