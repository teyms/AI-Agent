from typing import List, TypedDict


class AgentState(TypedDict):
    user_input: str
    intent: str
    confidence: float
    confidence_status: str
    response: str
    retry_count: int
    max_retries: int
    timed_out: bool
    clarification_count: int
    validation_status: str
    output_format_status: str
    permission_status: str
    final_validation_status: str
    execution_path: List[str]
    failures: List[str]
    validation_errors: List[str]
    final_answer: str
