import json
from pathlib import Path


MEMORY_FILE = Path(__file__).with_name("workflow_memory.json")

DEFAULT_WORKFLOW_STATE = {
    "current_step": 0,
    "completed_steps": [],
    "tool_outputs": {},
    "logs": []
}


def load_workflow_state():
    if not MEMORY_FILE.exists():
        return DEFAULT_WORKFLOW_STATE.copy()

    with MEMORY_FILE.open("r", encoding="utf-8") as file:
        workflow_state = json.load(file)

    if not isinstance(workflow_state, dict):
        return DEFAULT_WORKFLOW_STATE.copy()

    return {
        "current_step": workflow_state.get("current_step", 0),
        "completed_steps": workflow_state.get("completed_steps", []),
        "tool_outputs": workflow_state.get("tool_outputs", {}),
        "logs": workflow_state.get("logs", [])
    }


def save_workflow_state(workflow_state):
    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(workflow_state, file, indent=2)
