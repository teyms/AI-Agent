from typing import TypedDict, List


class AgentState(TypedDict):
    user_input: str
    messages: List[dict]
    current_tool: str
    tool_input: str
    tool_output: str
    user_profile: dict
    final_answer: str
    iteration_count: int
