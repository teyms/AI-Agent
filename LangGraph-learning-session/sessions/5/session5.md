# LangGraph Session 5 — Memory and Persistence in LangGraph

## Goal of This Session

By the end of this session, you will understand:

```text id="mem001"
- Why persistence matters
- Checkpointing
- Durable execution
- Conversation memory
- Stateful workflows
- Resumable graphs
- Short-term vs long-term memory
- Memory architecture in LangGraph
- Why production agents require persistence
```

This is where LangGraph starts becoming:

```text id="mem002"
production-grade orchestration infrastructure
```

instead of:

* temporary runtime workflows.

---

# Part 1 — The Big Problem

Right now your graph execution is:

```text id="mem003"
in-memory only
```

If your app crashes:

```text id="mem004"
everything disappears
```

Including:

* messages
* workflow state
* retries
* tool outputs
* reasoning traces

This is unacceptable in production systems.

---

# IMPORTANT INDUSTRY REALITY

Real AI systems MUST survive:

* crashes
* restarts
* redeployments
* long-running workflows

This is why:

```text id="mem005"
durability
```

becomes critical.

---

# Part 2 — What Is Checkpointing?

Checkpointing means:

```text id="mem006"
saving workflow state after each step
```

Example:

```text id="mem007"
Node A executes
↓
Save state
↓
Node B executes
↓
Save state
```

If crash happens:

```text id="mem008"
resume from latest checkpoint
```

VERY important concept.

---

# Part 3 — LangGraph Persistence Mental Model

LangGraph persistence is basically:

```text id="mem009"
Graph execution
+
Persistent state storage
```

The graph becomes:

* resumable
* durable
* recoverable

This is HUGE for enterprise AI systems.

---

# Part 4 — What We Will Build

We will upgrade Session 4 into:

```text id="mem010"
User
 ↓
LangGraph Agent
 ↓
Checkpoint Saved
 ↓
Crash/Restart
 ↓
Resume Workflow
```

We will also add:

* persistent conversation memory
* thread IDs
* SQLite persistence

---

# Part 5 — Install Dependencies

```bash id="mem011"
pip install langgraph langchain-core langgraph-checkpoint-sqlite openai python-dotenv
```

---

# IMPORTANT NOTE

We will use:

SQLite

because:

* lightweight
* local
* production-capable for many cases
* excellent for learning

---

# Part 6 — Project Structure

```text id="mem012"
langgraph_session5/
├── main.py
├── graph.py
├── nodes.py
├── state.py
├── tools.py
├── prompts.py
├── checkpointer.py
├── requirements.txt
└── .env
```

---

# Part 7 — Update State

## state.py

```python id="mem013"
from typing import TypedDict, List


class AgentState(TypedDict):

    user_input: str

    messages: List[dict]

    current_tool: str

    tool_input: str

    tool_output: str

    final_answer: str

    iteration_count: int
```

---

# IMPORTANT CONCEPT

State is now becoming:

```text id="mem014"
persistent workflow state
```

This is VERY important.

---

# Part 8 — Why Iteration State Matters

Persistence is not only about:

* chat history

It is also about:

* orchestration metadata
* retries
* execution progress
* workflow lifecycle

VERY important production distinction.

---

# Part 9 — OpenAI Setup

## nodes.py

```python id="mem015"
import os
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")
```

---

# Part 10 — SQLite Checkpointer

THIS is the core of this session.

## checkpointer.py

```python id="mem016"
from langgraph.checkpoint.sqlite import (
    SqliteSaver
)
```

---

# Create SQLite Checkpointer

```python id="mem017"
checkpointer = SqliteSaver.from_conn_string(
    "checkpoints.db"
)
```

---

# IMPORTANT CONCEPT

LangGraph now automatically persists:

* graph state
* messages
* execution progress

into SQLite.

This is VERY powerful.

---

# Part 11 — Why This Matters

Without persistence:

```text id="mem018"
Agent execution
=
temporary runtime memory
```

With checkpointing:

```text id="mem019"
Agent execution
=
durable workflow state
```

This is the foundation of:

* resumable agents
* enterprise orchestration
* long-running workflows

---

# Part 12 — Create Tool

## tools.py

```python id="mem020"
from datetime import datetime


def get_current_time():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
```

---

# Part 13 — Prompt

## prompts.py

```python id="mem021"
SYSTEM_PROMPT = """
You are a helpful AI assistant.

You may:
- answer directly
- use tools

Available tools:
1. get_current_time()

Return ONLY valid JSON.

Schema:
{
    "needs_tool": boolean,
    "tool_name": string,
    "tool_input": string,
    "final_answer": string
}
"""
```

---

# Part 14 — Agent Node

## nodes.py

```python id="mem022"
from state import AgentState

from prompts import SYSTEM_PROMPT
```

---

# agent_node

```python id="mem023"
def agent_node(
    state: AgentState
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + state["messages"]
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    parsed = json.loads(content)

    updates = {
        "iteration_count": (
            state["iteration_count"] + 1
        )
    }

    if parsed["needs_tool"]:

        updates["current_tool"] = (
            parsed["tool_name"]
        )

        updates["tool_input"] = (
            parsed["tool_input"]
        )

    else:

        updates["final_answer"] = (
            parsed["final_answer"]
        )

    updates["messages"] = (
        state["messages"] + [
            {
                "role": "assistant",
                "content": content
            }
        ]
    )

    return updates
```

---

# IMPORTANT CONCEPT

Every node execution now contributes to:

* persistent state history

This is HUGE.

---

# Part 15 — Tool Node

## nodes.py

```python id="mem024"
from tools import get_current_time
```

---

# tool_node

```python id="mem025"
def tool_node(
    state: AgentState
):

    result = get_current_time()

    observation = (
        f"Tool Result: {result}"
    )

    return {
        "tool_output": result,
        "messages": (
            state["messages"] + [
                {
                    "role": "user",
                    "content": observation
                }
            ]
        )
    }
```

---

# Part 16 — Build Graph

## graph.py

```python id="mem026"
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_node,
    tool_node
)

from checkpointer import (
    checkpointer
)
```

---

# Create Graph

```python id="mem027"
graph = StateGraph(
    AgentState
)
```

---

# Add Nodes

```python id="mem028"
graph.add_node(
    "agent",
    agent_node
)

graph.add_node(
    "tool",
    tool_node
)
```

---

# Routing Function

```python id="mem029"
def route_agent(
    state: AgentState
):

    if state["final_answer"]:

        return END

    return "tool"
```

---

# Conditional Routing

```python id="mem030"
graph.add_conditional_edges(
    "agent",
    route_agent,
    {
        "tool": "tool",
        END: END
    }
)
```

---

# Tool Loop

```python id="mem031"
graph.add_edge(
    "tool",
    "agent"
)
```

---

# Entry Point

```python id="mem032"
graph.set_entry_point(
    "agent"
)
```

---

# Compile With Checkpointer

THIS is the critical step.

```python id="mem033"
app = graph.compile(
    checkpointer=checkpointer
)
```

---

# IMPORTANT CONCEPT

This upgrades your graph into:

```text id="mem034"
durable graph execution
```

VERY important milestone.

---

# Part 17 — Thread IDs

THIS is extremely important.

LangGraph persistence works using:

```text id="mem035"
thread_id
```

Think of it as:

```text id="mem036"
workflow/session identifier
```

---

# Why Thread IDs Matter

Without thread IDs:

```text id="mem037"
all users share same workflow
```

Bad.

Thread IDs separate:

* conversations
* workflows
* state histories

---

# Part 18 — Main Entry Point

## main.py

```python id="mem038"
from graph import app
```

---

# Create Thread ID

```python id="mem039"
thread_id = "user_123"
```

---

# Config Object

```python id="mem040"
config = {
    "configurable": {
        "thread_id": thread_id
    }
}
```

---

# Invoke Graph

```python id="mem041"
while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke(
        {
            "user_input": user_input,
            "messages": [
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            "current_tool": "",
            "tool_input": "",
            "tool_output": "",
            "final_answer": "",
            "iteration_count": 0
        },
        config=config
    )

    print("\nAssistant:")
    print(result["final_answer"])
```

---

# Part 19 — Persistent Conversation Memory

Now:

* close app
* restart app
* invoke same thread_id

LangGraph reloads:

* previous state
* previous messages
* workflow progress

This is VERY important.

---

# Part 20 — Durable Workflow Architecture

Your graph is now:

```text id="mem042"
stateful
durable
recoverable
persistent
```

This is MUCH closer to:

* enterprise workflow systems

than simple chatbots.

---

# Part 21 — Why Persistence Is Critical

Enterprise workflows may:

* run for hours
* require approvals
* pause waiting for humans
* survive deployments

Without persistence:

* impossible.

---

# Part 22 — Human-In-The-Loop Systems

Persistence enables:

```text id="mem043"
pause
resume
approval workflows
```

Example:

```text id="mem044"
Agent:
"Approve deployment?"

(wait 3 hours)

User:
"Approved"

Workflow resumes.
```

This is HUGE.

---

# Part 23 — Why LangGraph Became Popular

Many frameworks only support:

```text id="mem045"
stateless execution
```

LangGraph became popular because it supports:

```text id="mem046"
durable orchestration
```

which is essential for:

* production agents.

---

# Part 24 — Memory Types In LangGraph

VERY important distinction.

---

# Short-Term Memory

Usually:

* messages
* recent workflow state

Stored in:

* graph checkpoints

---

# Long-Term Memory

Usually:

* user profile
* preferences
* historical facts

Stored separately:

* SQL
* vector DB
* profile service

---

# IMPORTANT CONCEPT

Checkpointing ≠ long-term memory.

Very important distinction.

---

# Part 25 — Production Architecture Reality

Real systems often combine:

```text id="mem047"
LangGraph checkpoints
+
Redis
+
SQL
+
Vector DB
+
Object storage
```

together.

---

# Part 26 — Common Beginner Mistakes

## Mistake 1 — Forgetting Thread IDs

Without unique thread IDs:

* state collisions happen.

---

## Mistake 2 — Storing Huge State

State should stay:

* relevant
* compact

Large state hurts:

* performance
* cost
* debugging

---

## Mistake 3 — Confusing Checkpoints With User Memory

Checkpoint:

* workflow execution state

User memory:

* long-term personalization

Different concepts.

---

## Mistake 4 — Infinite Persistence

Not all workflow state should live forever.

Need:

* cleanup
* expiration
* archival strategies

---

## Mistake 5 — Storing Secrets In State

Never persist:

* API keys
* passwords
* sensitive tokens

inside workflow state.

---

# Part 27 — What You Learned

You now understand:

## Conceptually

```text id="mem048"
- durable execution
- checkpointing
- resumable workflows
- persistent state
- thread-based orchestration
```

## Technically

```text id="mem049"
- SqliteSaver
- graph checkpointing
- thread_id
- durable LangGraph execution
- persistent conversation workflows
```

This is REAL production orchestration engineering.

---

# Your Exercises

## Exercise 1 — Add User Profiles

Store:

* preferred language
* city
* timezone

outside checkpoints.

---

## Exercise 2 — Add Resume After Crash

Simulate:

* crash
* restart
* continue workflow

---

## Exercise 3 — Add Multi-User Support

Use:

* different thread IDs

for separate users.

---

## Exercise 4 — Add Checkpoint Inspection

Inspect:

* saved workflow state
* stored messages

inside SQLite.

---

## Exercise 5 — Add Expiration Logic

Automatically delete:

* old checkpoints

after X days.

---

# LangGraph Session 6 Preview

Next you’ll learn:

```text id="mem050"
RAG Agents with LangGraph + sqlite-vec
```

You will build:

* retrieval nodes
* retrieval routing
* sqlite-vec integration
* grounded answers
* citation systems
* retrieval-aware orchestration

This is where LangGraph starts becoming:

* enterprise knowledge-agent infrastructure.
