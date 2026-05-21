from retriever import retrieve
from memory import add_message, get_messages
from openai import OpenAI
from dotenv import load_dotenv
import os 

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=(os.getenv("LLM_BASE_URL") or "").strip().strip("\"'"),
)


def ask_rag(question):
    add_message("user", question)

    retrieved_chunks = retrieve(question)
    conversation_history = get_messages()
    if not retrieved_chunks:
        answer = "I don't have enough information."
        add_message("assistant", answer)
        return {
            "answer": answer,
            "citations": []
        }

    context = "\n\n".join([
        f"Source: {chunk['source']}\n{chunk['text']}"
        for chunk in retrieved_chunks
    ])

    citations = [
        {
            "source": chunk["source"],
            "chunk": chunk["text"],
        }
        for chunk in retrieved_chunks
    ]

    response = client.chat.completions.create(
        model=(os.getenv("LLM_MODEL") or "").strip().strip("\"'"),
        messages=[
            {
                "role": "system",
                "content": f"""
Answer ONLY using provided context.
Use conversation history only to understand follow-up questions.

Context:
{context}

Conversation history:
{conversation_history}
"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    answer = response.choices[0].message.content
    add_message("assistant", answer)

    return {
        "answer": answer,
        "citations": citations
    }
