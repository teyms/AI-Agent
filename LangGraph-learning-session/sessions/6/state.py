from typing import (
    TypedDict,
    List
)


class AgentState(TypedDict):
    user_input: str
    rewritten_query: str
    query_was_rewritten: bool
    messages: List[dict]
    retrieved_docs: List[dict]
    metadata_filters: dict
    retrieval_confidence: float
    retrieval_status: str
    citation_status: str
    clarification_count: int
    final_answer: str
    needs_retrieval: bool
