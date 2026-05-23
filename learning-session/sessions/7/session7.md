# Session 7 — Tool-Using Reasoning Agents

## Goal of This Session

By the end of this session, you will understand:

```text id="reason001"
- What reasoning agents actually are
- ReAct-style reasoning loops
- Observation → Thought → Action cycles
- Dynamic tool selection
- Reflection and retries
- Combining:
  - memory
  - RAG
  - workflows
  - tools
- Why autonomous agents are difficult
- Why most production agents are constrained systems
```

You will build your FIRST reasoning agent manually.

This is one of the most important milestones in AI agent engineering.

---

# Part 1 — What Is A Reasoning Agent?

Your previous systems were mostly:

```text id="reason002"
Workflow-driven
```

Example:

```text id="reason003"
Step A
→ Step B
→ Step C
```

Deterministic.

---

# A Reasoning Agent Is Different

A reasoning agent dynamically decides:

```text id="reason004"
What to do next
```

based on:

* observations
* tool outputs
* failures
* current context

---

# Core Reasoning Loop

```text id="reason005"
Observe
↓
Think
↓
Choose Action
↓
Execute Tool
↓
Observe Result
↓
Think Again
↓
Repeat
```

This is the foundation of:

* ReAct agents
* tool-using agents
* coding agents
* research agents

---

# Part 2 — ReAct Pattern

One of the most important reasoning patterns.

ReAct means:

```text id="reason006"
Reason + Act
```

---

# ReAct Example

```text id="reason007"
Question:
"What is the weather in Tokyo and should I bring an umbrella?"
```

Agent loop:

```text id="reason008"
Thought:
I need weather information.

Action:
get_weather(Tokyo)

Observation:
18°C and rainy

Thought:
Rain likely requires umbrella.

Final Answer:
Yes, you should bring an umbrella.
```

VERY important architecture.

---

# IMPORTANT INDUSTRY REALITY

Modern “AI agents” are mostly:

```text id="reason009"
LLM-generated control flow
```

NOT autonomous intelligence.

This understanding is critical.

---

# Part 3 — Project Structure

```text id="reason010"
session7/
├── main.py
├── agent.py
├── tools.py
├── memory.py
├── rag.py
├── sqlite_vec_store.py
├── prompts.py
├── requirements.txt
└── .env
```

---

# Part 4 — Environment Variables

## .env

```text id="reason011"
LLM_API_KEY=your_key
LLM_BASE_URL=your_base_url
LLM_MODEL=your_model

LLM_EMBEDDING_API_KEY=your_embedding_key
LLM_EMBEDDING_BASE_URL=your_embedding_base_url
LLM_EMBEDDING_MODEL=your_embedding_model
```

---

# Part 5 — OpenAI Client Setup

## agent.py

```python id="reason012"
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")
```

---

# Embedding Client

## sqlite_vec_store.py

```python id="reason013"
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

embedding_client = OpenAI(
    api_key=os.getenv("LLM_EMBEDDING_API_KEY"),
    base_url=os.getenv("LLM_EMBEDDING_BASE_URL"),
)

EMBEDDING_MODEL = os.getenv(
    "LLM_EMBEDDING_MODEL"
)
```

---

# IMPORTANT CONCEPT

You can separate:

* reasoning model
* embedding model

This is VERY common in production systems.

---

# Part 6 — sqlite-vec Introduction

You chose:

sqlite-vec

Excellent choice for learning.

Why?

```text id="reason014"
- lightweight
- local
- simple
- no external vector DB
- easy debugging
- production-capable for many cases
```

This is MUCH better for learning than immediately using managed vector DBs.

---

# Install Dependencies

```bash id="reason015"
pip install sqlite-vec sqlite-utils numpy openai python-dotenv
```

---

# Part 7 — Creating sqlite-vec Database

## sqlite_vec_store.py

```python id="reason016"
import sqlite3
import sqlite_vec
```

---

# Initialize Database

```python id="reason017"
def init_db():

    conn = sqlite3.connect("rag.db")

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

Unlike earlier JSON storage:

```text id="reason018"
You now have REAL vector search infrastructure
```

This is MUCH closer to production systems.

---

# Part 8 — Embedding Generation

## sqlite_vec_store.py

```python id="reason019"
def create_embedding(text):

    response = embedding_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response.data[0].embedding
```

---

# Part 9 — Insert Documents Into sqlite-vec

## sqlite_vec_store.py

```python id="reason020"
def insert_document(
    conn,
    text_chunk,
    source
):

    embedding = create_embedding(text_chunk)

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

# IMPORTANT UNDERSTANDING

You are now storing:

```text id="reason021"
text
+
embedding vector
```

inside SQLite itself.

Very powerful architecture for:

* local assistants
* desktop AI apps
* lightweight enterprise systems

---

# Part 10 — Vector Retrieval

## sqlite_vec_store.py

```python id="reason022"
def search_similar(
    conn,
    query,
    top_k=5
):

    query_embedding = create_embedding(query)

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

# THIS Is REAL Vector Search

No manual cosine similarity anymore.

The vector extension handles:

* indexing
* similarity search
* optimized retrieval

---

# Part 11 — Tools

## tools.py

```python id="reason023"
from datetime import datetime


def get_current_time():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def calculator(expression):

    try:
        return str(eval(expression))

    except Exception as e:
        return f"Calculation error: {str(e)}"
```

---

# RAG Tool

```python id="reason024"
from sqlite_vec_store import (
    init_db,
    search_similar
)

conn = init_db()


def search_knowledge_base(query):

    results = search_similar(
        conn,
        query
    )

    formatted = []

    for result in results:

        formatted.append({
            "text": result[0],
            "source": result[1]
        })

    return formatted
```

---

# IMPORTANT CONCEPT

RAG retrieval is just another tool.

This is VERY important.

Modern agents combine:

* reasoning
* tools
* retrieval
* memory

into ONE orchestration loop.

---

# Part 12 — Tool Registry

## agent.py

```python id="reason025"
from tools import (
    calculator,
    get_current_time,
    search_knowledge_base
)

TOOLS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "search_knowledge_base": search_knowledge_base
}
```

---

# Part 13 — ReAct Prompt

## prompts.py

```python id="reason026"
SYSTEM_PROMPT = """
You are a reasoning AI agent.

You may:
- think about problems
- choose tools
- observe tool results
- continue reasoning

Available tools:
1. calculator(expression)
2. get_current_time()
3. search_knowledge_base(query)

Return ONLY valid JSON.

Schema:
{
    "thought": string,
    "needs_tool": boolean,
    "tool_name": string,
    "tool_arguments": {},
    "final_answer": string
}

Rules:
- Think step-by-step
- Use tools when necessary
- If final answer ready:
  needs_tool = false
"""
```

---

# IMPORTANT CONCEPT

The LLM is generating:

```text id="reason027"
reasoning traces
```

This is NOT “real thinking.”

It is structured reasoning output.

Very important distinction.

---

# Part 14 — Reasoning Step

## agent.py

```python id="reason028"
import json
from prompts import SYSTEM_PROMPT
```

---

# Agent Reasoning Function

```python id="reason029"
def reasoning_step(
    user_input,
    conversation_history
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + conversation_history + [
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    content = response.choices[0].message.content

    return json.loads(content)
```

---

# Part 15 — Tool Execution

## agent.py

```python id="reason030"
def execute_tool(
    tool_name,
    tool_arguments
):

    if tool_name not in TOOLS:

        return "Tool not found"

    tool_function = TOOLS[tool_name]

    try:

        return tool_function(**tool_arguments)

    except Exception as e:

        return f"Tool execution failed: {str(e)}"
```

---

# Part 16 — The Full ReAct Loop

THIS is the heart of reasoning agents.

## agent.py

```python id="reason031"
def run_agent(user_input):

    conversation_history = []

    max_iterations = 5

    for iteration in range(max_iterations):

        decision = reasoning_step(
            user_input,
            conversation_history
        )

        print("\n=== REASONING STEP ===")
        print(decision)

        if not decision["needs_tool"]:

            return decision["final_answer"]

        tool_result = execute_tool(
            decision["tool_name"],
            decision["tool_arguments"]
        )

        print("\n=== TOOL RESULT ===")
        print(tool_result)

        conversation_history.append({
            "role": "assistant",
            "content": json.dumps(decision)
        })

        conversation_history.append({
            "role": "user",
            "content": f"""
Tool result:
{tool_result}
"""
        })

    return "Agent exceeded max iterations."
```

---

# THIS Is The Real Agent Loop

You now built:

```text id="reason032"
Observe
↓
Reason
↓
Act
↓
Observe Result
↓
Reason Again
```

This is the core of:

* coding agents
* research agents
* autonomous assistants

---

# Part 17 — Why Iteration Limits Matter

Without limits:

```text id="reason033"
Infinite loops
```

become common.

Production systems MUST have:

* iteration limits
* timeout limits
* budget limits

Very important.

---

# Part 18 — Reflection

Advanced agents reflect on failures.

Example:

```text id="reason034"
Tool failed
↓
Reason about failure
↓
Retry differently
```

This dramatically improves robustness.

---

# Reflection Example

```python id="reason035"
if "failed" in tool_result.lower():

    conversation_history.append({
        "role": "user",
        "content": """
The previous tool call failed.
Try another approach.
"""
    })
```

---

# IMPORTANT INDUSTRY REALITY

Modern reasoning agents are mostly:

```text id="reason036"
LLM-guided retry systems
```

NOT magic intelligence.

---

# Part 19 — Combining Memory + RAG + Tools

Your agent now combines:

```text id="reason037"
Memory
+
Tool Use
+
RAG
+
Reasoning
```

This is VERY close to modern production AI systems.

---

# Part 20 — Why Autonomous Agents Are Hard

Autonomous agents struggle with:

```text id="reason038"
- infinite loops
- hallucinated plans
- bad tool choices
- context drift
- cascading failures
- excessive cost
- unsafe actions
```

This is why enterprise systems usually prefer:

```text id="reason039"
Constrained workflows
+
Limited autonomy
```

instead of fully autonomous systems.

---

# Part 21 — Common Beginner Mistakes

## Mistake 1

Thinking reasoning traces are true reasoning.

They are generated text patterns.

---

## Mistake 2

Unlimited tool access.

Dangerous.

Always restrict:

* permissions
* tools
* scope

---

## Mistake 3

No iteration limits.

Leads to:

* runaway costs
* infinite loops

---

## Mistake 4

No validation.

Never trust:

* tool names
* arguments
* reasoning outputs

blindly.

---

## Mistake 5

Overusing autonomous loops.

Workflows are usually more reliable.

---

# Part 22 — What You Learned

You now understand:

## Conceptually

* reasoning loops
* ReAct architecture
* observation/action cycles
* reflection
* dynamic tool use
* autonomous agent limitations

## Technically

* iterative orchestration
* reasoning prompts
* tool loops
* reflection handling
* sqlite-vec retrieval
* combined RAG + memory + tools

This is foundational reasoning-agent engineering.

---

# Your Exercises

## Exercise 1 — Add Retry Reflection

If tool fails:

* retry with modified arguments

---

## Exercise 2 — Add Retrieval Citations

Include:

* chunk source
* retrieved passages

in final answers.

---

## Exercise 3 — Add User Memory

Remember:

* preferred language
* location
* favorite tools

---

## Exercise 4 — Add Budget Limits

Track:

* iteration count
* token usage
* estimated cost

---

## Exercise 5 — Add Approval Workflow

Before calculator executes:

```text id="reason040"
Require confirmation
```

before running potentially dangerous expressions.

---

# Session 8 Preview

Next you’ll learn:

# Production Agent Architecture

You will build systems with:

```text id="reason041"
- structured logging
- observability
- tracing
- evaluations
- guardrails
- retries
- rate limiting
- async workflows
- queues
- background jobs
- agent state persistence
```

You’ll finally understand:

* why demos fail in production
* how production AI systems are engineered
* how enterprise AI reliability works
* why observability is critical
