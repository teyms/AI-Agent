import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

MODEL_NAME = os.getenv(
    "LLM_MODEL"
)



from prompts import (
    RESEARCH_PROMPT
)
def research_agent(
    question
):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": RESEARCH_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )

from prompts import (
    MATH_PROMPT
)
def math_agent(
    question
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": MATH_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


from prompts import (
    GENERAL_PROMPT
)
def general_agent(
    question
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": GENERAL_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


from prompts import (
    RISK_PROMPT
)
def risk_agent(
    question
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": RISK_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


from prompts import (
    SUMMARY_PROMPT
)
def summary_agent(
    question
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SUMMARY_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


from prompts import (
    RAG_PROMPT
)
from sqlite_vec_store import (
    retrieve_documents
)
def rag_agent(
    question
):
    documents = retrieve_documents(
        question
    )

    if not documents:
        return (
            "I could not find relevant documents "
            "in the sqlite-vec knowledge base."
        )

    context = "\n\n".join([
        f"Source: {document['source']}\n"
        f"{document['text']}"
        for document in documents
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
{question}

Retrieved documents:
{context}
"""
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


from prompts import (
    REVIEWER_PROMPT
)
def reviewer_agent(
    question,
    worker_result
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": REVIEWER_PROMPT
            },
            {
                "role": "user",
                "content": f"""
User question:
{question}

Worker answer:
{worker_result}
"""
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )



