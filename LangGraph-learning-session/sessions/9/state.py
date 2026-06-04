from typing import TypedDict


class AgentState(TypedDict):
    user_input: str
    selected_agent: str
    worker_result: str
    rag_result: str
    risk_result: str
    research_result: str
    summary_result: str
    worker_quality_score: float
    routing_accuracy_score: float
    review_result: str
    final_answer: str



    
