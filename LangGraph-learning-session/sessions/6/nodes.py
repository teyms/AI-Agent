import os

from dotenv import load_dotenv
from openai import OpenAI

import json

from prompts import ROUTER_PROMPT,RAG_PROMPT
from state import AgentState

from sqlite_vec_store import (
    init_db,
    hybrid_search
)

conn = init_db()

load_dotenv()
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")


def extract_metadata_filters(query):
    query = query.lower()
    filters = {
        "department": None,
        "document_type": None
    }

    if "engineering" in query or "engineer" in query:
        filters["department"] = "Engineering"
    elif (
        "hr" in query
        or "leave" in query
        or "medical" in query
        or "remote work" in query
    ):
        filters["department"] = "HR"

    if "policy" in query:
        filters["document_type"] = "policy"
    elif "handbook" in query:
        filters["document_type"] = "handbook"
    elif "faq" in query:
        filters["document_type"] = "faq"
    elif "onboarding" in query:
        filters["document_type"] = "onboarding"

    return filters


def rewrite_query_node(
    state: AgentState
):
    query = state["user_input"].strip()
    normalized_query = query.lower()
    rewritten_query = query

    vague_terms = [
        "policy",
        "docs",
        "documents",
        "benefits",
        "rules"
    ]

    if normalized_query in vague_terms:
        rewritten_query = (
            f"{query} employee company policy"
        )
    elif "leave" in normalized_query:
        rewritten_query = (
            f"{query} annual leave HR policy"
        )
    elif "remote" in normalized_query:
        rewritten_query = (
            f"{query} remote work HR policy"
        )
    elif "deploy" in normalized_query:
        rewritten_query = (
            f"{query} engineering handbook deployment"
        )

    return {
        "rewritten_query": rewritten_query,
        "query_was_rewritten": rewritten_query != query
    }


def agent_router_node(
    state: AgentState
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": ROUTER_PROMPT
            },
            {
                "role": "user",
                "content": state["user_input"]
            }
        ]
    )

    parsed = json.loads(
        response
        .choices[0]
        .message
        .content
    )

    return {
        "needs_retrieval": (
            parsed["needs_retrieval"]
        )
    }

def retrieval_node(
    state: AgentState
):
    query = (
        state["rewritten_query"]
        or state["user_input"]
    )
    filters = extract_metadata_filters(
        query
    )

    results = hybrid_search(
        conn,
        query,
        department=filters["department"],
        document_type=filters["document_type"]
    )

    formatted = []

    for result in results:

        formatted.append({
            "text": result["text"],
            "source": result["source"],
            "department": result["department"],
            "document_type": result["document_type"],
            "score": result["score"],
            "match_type": result["match_type"]
        })

    retrieval_confidence = 0

    if formatted:
        retrieval_confidence = formatted[0]["score"]

    return {
        "retrieved_docs": formatted,
        "metadata_filters": filters,
        "retrieval_confidence": retrieval_confidence
    }


def retrieval_validation_node(
    state: AgentState
):
    if (
        state["retrieved_docs"]
        and state["retrieval_confidence"] >= 0.2
    ):
        return {
            "retrieval_status": "good"
        }

    if state["clarification_count"] < 1:
        return {
            "retrieval_status": "clarify"
        }

    return {
        "retrieval_status": "failed",
        "final_answer": (
            "I could not find enough relevant "
            "documents to answer confidently."
        )
    }


def clarification_node(
    state: AgentState
):
    clarified_query = input(
        "Please clarify what documents you want: "
    )

    return {
        "user_input": clarified_query,
        "rewritten_query": "",
        "query_was_rewritten": False,
        "retrieved_docs": [],
        "retrieval_confidence": 0,
        "retrieval_status": "",
        "clarification_count": (
            state["clarification_count"] + 1
        )
    }


def rag_answer_node(
    state: AgentState
):

    context = "\n\n".join([
        f"Source: {doc['source']}\n"
        f"Department: {doc['department']}\n"
        f"Document Type: {doc['document_type']}\n"
        f"Match Type: {doc['match_type']}\n"
        f"{doc['text']}"
        for doc in state["retrieved_docs"]
    ])

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": RAG_PROMPT
            },
            {
                "role": "user",
                "content": f"""
Question:
{state["rewritten_query"] or state["user_input"]}

Documents:
{context}
"""
            }
        ]
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    return {
        "final_answer": answer
    }


def citation_validation_node(
    state: AgentState
):
    answer = state["final_answer"]
    sources = [
        doc["source"]
        for doc in state["retrieved_docs"]
    ]
    missing_sources = [
        source
        for source in sources
        if source not in answer
    ]

    if not sources:
        return {
            "citation_status": "no_sources"
        }

    if not missing_sources:
        return {
            "citation_status": "valid"
        }

    source_list = ", ".join(sources)

    return {
        "citation_status": "fixed",
        "final_answer": (
            f"{answer}\n\nSources: {source_list}"
        )
    }


def direct_answer_node(
    state: AgentState
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": state["user_input"]
            }
        ]
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    return {
        "final_answer": answer
    }
