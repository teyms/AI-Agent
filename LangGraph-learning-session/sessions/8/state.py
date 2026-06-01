from typing import TypedDict


class AgentState(TypedDict):
    user_input: str
    proposed_tool: str
    tool_input: str
    validation_status: str
    retry_count: int
    token_count: int
    max_tokens: int
    cost_guardrail_status: str
    permission_status: str
    tool_output: str
    output_validation_status: str
    confidence_score: float
    confidence_status: str
    secondary_validation_status: str
    secondary_validation_reason: str
    final_answer: str
    error_message: str
