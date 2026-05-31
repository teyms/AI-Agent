from typing import List, TypedDict


class AgentState(TypedDict):
    user_request: str
    proposed_action: str
    risk_level: str
    approval_status: str
    manager_approval_status: str
    security_approval_status: str
    approval_history: List[dict]
    final_result: str
