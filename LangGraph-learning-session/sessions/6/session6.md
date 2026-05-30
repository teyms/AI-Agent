# LangGraph Session 6 — RAG Agents with LangGraph + sqlite-vec

## Goal of This Session

By the end of this session, you will understand:

```text id="rag001"
- How RAG fits into LangGraph
- Retrieval nodes
- Retrieval routing
- sqlite-vec integration
- Grounded generation
- Retrieval-aware orchestration
- Citation handling
- Why RAG is orchestration, not just embeddings
```

This session upgrades your LangGraph agent into:

```text id="rag002"
a knowledge-aware AI system
```

instead of:

* a generic tool agent.

---

# Part 1 — Important Mindset Shift

Most beginners think:

```text id="rag003"
RAG = vector search
```

Wrong.

Production RAG is actually:

```text id="rag004"
retrieval orchestration
```

Meaning:

* query understanding
* retrieval routing
* chunk selection
* grounding
* validation
* citation handling
* fallback logic

LangGraph is excellent for this.

---

# Part 2 — What We Will Build

We will build this graph:

```text id="rag005"
START
 ↓
agent_node
 ├── needs RAG → retrieval_node
 │                     ↓
 │               answer_node
 │
 └── no RAG → direct_answer_node
 ↓
END
```

This introduces:

* retrieval-aware routing
* document grounding
* knowledge injection

VERY important production concepts.

---

# Part 3 — Project Structure

```text id="rag006"
langgraph_session6/
├── main.py
├── graph.py
├── nodes.py
├── state.py
├── prompts.py
├── sqlite_vec_store.py
├── ingest.py
├── documents/
├── requirements.txt
└── .env
```

---

# Install Dependencies

```bash id="rag007"
pip install \
langgraph \
langchain-core \
sqlite-vec \
openai \
python-dotenv
```

---

# Part 4 — Environment Variables

## .env

```text id="rag008"
LLM_API_KEY=your_key
LLM_BASE_URL=your_base_url
LLM_MODEL=your_model

LLM_EMBEDDING_API_KEY=your_embedding_key
LLM_EMBEDDING_BASE_URL=your_embedding_base_url
LLM_EMBEDDING_MODEL=your_embedding_model
```

---

# Part 5 — OpenAI Setup

## sqlite_vec_store.py

```python id="rag009"
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
```

---

# Embedding Client

```python id="rag010"
embedding_client = OpenAI(
    api_key=os.getenv(
        "LLM_EMBEDDING_API_KEY"
    ),
    base_url=os.getenv(
        "LLM_EMBEDDING_BASE_URL"
    ),
)

EMBEDDING_MODEL = os.getenv(
    "LLM_EMBEDDING_MODEL"
)
```

---

# Main LLM Client

## nodes.py

```python id="rag011"
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")
```

---

# IMPORTANT CONCEPT

Production systems often separate:

* embedding model
* reasoning model

This is VERY common.

---

# Part 6 — Initialize sqlite-vec

## sqlite_vec_store.py

```python id="rag012"
import sqlite3
import sqlite_vec
```

---

# Initialize DB

```python id="rag013"
def init_db():

    conn = sqlite3.connect(
        "rag.db"
    )

    conn.enable_load_extension(True)

    sqlite_vec.load(conn)

    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS document_embeddings
        USING vec0(
            id INTEGER PRIMARY KEY,
            text_chunk TEXT,
            source TEXT,
            embedding FLOAT[1536]
        )
    """)

    conn.commit()

    return conn
```

---

# IMPORTANT CONCEPT

You now have:

* local vector infrastructure
* embedded directly inside SQLite

This is VERY powerful for:

* local AI apps
* internal company tools
* lightweight production systems

---

# Part 7 — Embedding Function

## sqlite_vec_store.py

```python id="rag014"
def create_embedding(text):

    response = embedding_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response.data[0].embedding
```

---

# Part 8 — Insert Documents

## sqlite_vec_store.py

```python id="rag015"
def insert_document(
    conn,
    text_chunk,
    source
):

    embedding = create_embedding(
        text_chunk
    )

    conn.execute(
        """
        INSERT INTO document_embeddings(
            text_chunk,
            source,
            embedding
        )
        VALUES (?, ?, ?)
        """,
        (
            text_chunk,
            source,
            embedding
        )
    )

    conn.commit()
```

---

# Part 9 — Retrieval Function

## sqlite_vec_store.py

```python id="rag016"
def search_similar(
    conn,
    query,
    top_k=3
):

    query_embedding = create_embedding(
        query
    )

    results = conn.execute(
        """
        SELECT
            text_chunk,
            source,
            distance
        FROM document_embeddings
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
        """,
        (
            query_embedding,
            top_k
        )
    ).fetchall()

    return results
```

---

# THIS Is REAL Retrieval Infrastructure

No fake in-memory search anymore.

You now have:

* actual vector retrieval
* local vector DB behavior
* production-style retrieval pipeline

---

# Part 10 — Ingest Documents

## ingest.py

```python id="rag017"
from sqlite_vec_store import (
    init_db,
    insert_document
)
```

---

# Initialize DB

```python id="rag018"
conn = init_db()
```

---

# Example Documents

```python id="rag019"
documents = [
    {
        "source": "leave_policy.txt",
        "text": """
Employees receive 14 days
of annual leave.
"""
    },
    {
        "source": "remote_work.txt",
        "text": """
Employees may work remotely
up to 3 days per week.
"""
    }
]
```

---

# Insert Documents

```python id="rag020"
for doc in documents:

    insert_document(
        conn,
        doc["text"],
        doc["source"]
    )

print("Documents ingested.")
```

---

# IMPORTANT LESSON

In production:

* ingestion pipelines
* chunking
* metadata extraction

are HUGE engineering topics.

---

# Part 11 — State Design

## state.py

```python id="rag021"
from typing import (
    TypedDict,
    List
)


class AgentState(TypedDict):

    user_input: str

    messages: List[dict]

    retrieved_docs: List[dict]

    final_answer: str

    needs_retrieval: bool
```

---

# IMPORTANT CONCEPT

RAG systems require:

* retrieval state
* grounding state

NOT just conversation memory.

---

# Part 12 — Agent Router Node

## prompts.py

```python id="rag022"
ROUTER_PROMPT = """
Determine whether retrieval is needed.

Return ONLY valid JSON.

Schema:
{
    "needs_retrieval": boolean
}
"""
```

---

# Router Node

## nodes.py

```python id="rag023"
import json

from prompts import ROUTER_PROMPT
```

---

# agent_router_node

```python id="rag024"
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
```

---

# IMPORTANT CONCEPT

The LLM is now:

* orchestrating retrieval behavior

This is VERY important.

---

# Part 13 — Retrieval Node

## nodes.py

```python id="rag025"
from sqlite_vec_store import (
    init_db,
    search_similar
)

conn = init_db()
```

---

# retrieval_node

```python id="rag026"
def retrieval_node(
    state: AgentState
):

    results = search_similar(
        conn,
        state["user_input"]
    )

    formatted = []

    for result in results:

        formatted.append({
            "text": result[0],
            "source": result[1]
        })

    return {
        "retrieved_docs": formatted
    }
```

---

# IMPORTANT CONCEPT

Retrieval becomes:

```text id="rag027"
a graph node
```

NOT:

* hidden infrastructure

This is VERY important architectural thinking.

---

# Part 14 — RAG Answer Node

## prompts.py

```python id="rag028"
RAG_PROMPT = """
Answer ONLY using retrieved documents.

If information missing:
say you do not know.

Include citations.
"""
```

---

# rag_answer_node

## nodes.py

```python id="rag029"
def rag_answer_node(
    state: AgentState
):

    context = "\n\n".join([
        f"Source: {doc['source']}\n"
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
{state["user_input"]}

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
```

---

# THIS Is Grounded Generation

The LLM is now constrained by:

* retrieved context

VERY important.

---

# Part 15 — Direct Answer Node

## nodes.py

```python id="rag030"
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
```

---

# Part 16 — Build Graph

## graph.py

```python id="rag031"
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_router_node,
    retrieval_node,
    rag_answer_node,
    direct_answer_node
)
```

---

# Create Graph

```python id="rag032"
graph = StateGraph(
    AgentState
)
```

---

# Add Nodes

```python id="rag033"
graph.add_node(
    "router",
    agent_router_node
)

graph.add_node(
    "retrieve",
    retrieval_node
)

graph.add_node(
    "rag_answer",
    rag_answer_node
)

graph.add_node(
    "direct_answer",
    direct_answer_node
)
```

---

# Part 17 — Routing Function

## graph.py

```python id="rag034"
def route_retrieval(
    state: AgentState
):

    if state["needs_retrieval"]:

        return "retrieve"

    return "direct_answer"
```

---

# Conditional Routing

```python id="rag035"
graph.add_conditional_edges(
    "router",
    route_retrieval,
    {
        "retrieve": "retrieve",
        "direct_answer": "direct_answer"
    }
)
```

---

# Retrieval Flow

```python id="rag036"
graph.add_edge(
    "retrieve",
    "rag_answer"
)
```

---

# End Edges

```python id="rag037"
graph.add_edge(
    "rag_answer",
    END
)

graph.add_edge(
    "direct_answer",
    END
)
```

---

# Entry Point

```python id="rag038"
graph.set_entry_point(
    "router"
)
```

---

# Compile Graph

```python id="rag039"
app = graph.compile()
```

---

# Part 18 — Main Entry Point

## main.py

```python id="rag040"
from graph import app


while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke({
        "user_input": user_input,
        "messages": [],
        "retrieved_docs": [],
        "final_answer": "",
        "needs_retrieval": False
    })

    print("\nAssistant:")
    print(result["final_answer"])
```

---

# Part 19 — Example RAG Flow

Input:

```text id="rag041"
How many leave days do employees get?
```

Execution:

```text id="rag042"
router
→ retrieve
→ rag_answer
→ END
```

Output:

```text id="rag043"
Employees receive 14 days
of annual leave.

Source: leave_policy.txt
```

---

# Part 20 — Example Non-RAG Flow

Input:

```text id="rag044"
What is 2 + 2?
```

Execution:

```text id="rag045"
router
→ direct_answer
→ END
```

This is:

* retrieval-aware orchestration

VERY important concept.

---

# Part 21 — Why LangGraph Fits RAG So Well

RAG systems naturally require:

* routing
* validation
* retrieval
* reranking
* fallback logic
* retries

Graphs model this naturally.

This is why LangGraph is VERY strong for:

* enterprise RAG systems.

---

# Part 22 — Production RAG Reality

Real production RAG often adds:

* reranking
* hybrid search
* metadata filtering
* query rewriting
* citation validation
* confidence scoring
* chunk compression

around this core graph.

---

# Part 23 — IMPORTANT Security Concept

Retrieved documents are:

```text id="rag046"
UNTRUSTED INPUT
```

Never blindly trust:

* PDFs
* Confluence docs
* tickets
* uploaded files

Prompt injection is a real risk.

---

# Part 24 — Common Beginner Mistakes

## Mistake 1 — Treating RAG As Only Retrieval

RAG is:

* orchestration
* grounding
* validation
* context engineering

NOT just embeddings.

---

## Mistake 2 — Huge Context Injection

Too much context:

* hurts accuracy
* increases cost

---

## Mistake 3 — No Retrieval Validation

Always validate:

* retrieved chunks
* confidence
* relevance

---

## Mistake 4 — No Citation Support

Enterprise systems often require:

* traceability
* source attribution

---

## Mistake 5 — Blindly Trusting Retrieved Content

Retrieved docs may contain:

* outdated info
* malicious instructions
* hallucinated data

---

# Part 25 — What You Learned

You now understand:

## Conceptually

```text id="rag047"
- retrieval-aware orchestration
- grounded generation
- retrieval routing
- graph-based RAG
```

## Technically

```text id="rag048"
- sqlite-vec integration
- retrieval nodes
- retrieval routing
- RAG answer generation
- citation-aware workflows
```

You have now built:

* your first LangGraph RAG agent.

---

# Your Exercises

## Exercise 1 — Add Metadata Filtering

Filter by:

* department
* document type

---

## Exercise 2 — Add Hybrid Search

Combine:

* vector search
* keyword matching

---

## Exercise 3 — Add Retrieval Validation

If retrieval confidence low:

* ask clarification

---

## Exercise 4 — Add Citation Validation

Ensure:

* all answers include source attribution

---

## Exercise 5 — Add Query Rewriting

Rewrite vague queries before retrieval.

---

# LangGraph Session 7 Preview

Next you’ll learn:

```text id="rag049"
Human-In-The-Loop Workflows
```

You will build:

* approval workflows
* interrupt/resume execution
* pauseable graphs
* human review systems
* enterprise-safe agents

This is where LangGraph becomes:

* true enterprise orchestration infrastructure.
