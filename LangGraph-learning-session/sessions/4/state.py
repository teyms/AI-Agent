from typing import TypedDict, List


class AgentState(TypedDict):
    user_input: str
    messages: List[dict]
    current_tool: str
    tool_input: str
    tool_output: str
    tool_failed: bool
    json_schema_valid: bool
    tool_output_valid: bool
    validation_error: str
    retry_count: int
    max_tool_retries: int
    iteration_count: int
    max_iterations: int
    fallback_reason: str
    node_execution_log: List[str]
    tool_calls: List[dict]
    reasoning_traces: List[str]
    final_answer: str




    
