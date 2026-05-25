from typing import TypedDict, List


class AgentState(TypedDict):
    user_input: str
    intent: str
    tool_result: str
    validation_result: str
    retries: int
    execution_path: List[str]
    retrieved_context: str
    final_answer: str
    messages: List[str]
