# LangGraph Session 9 — Multi-Agent and Supervisor Architectures

## Goal of This Session

By the end of this session, you will understand:

```text id="multi001"
- What multi-agent systems actually are
- Supervisor architectures
- Worker agents
- Delegation
- Agent handoffs
- Task routing
- Agent specialization
- When multi-agent systems make sense
- When they are a bad idea
```

This is one of the most misunderstood topics in AI.

Many people hear:

```text id="multi002"
multi-agent
```

and imagine:

```text id="multi003"
multiple AIs collaborating intelligently
```

Reality is usually:

```text id="multi004"
structured orchestration
```

Very important distinction.

---

# Part 1 — The Biggest Misconception

Many tutorials show:

```text id="multi005"
Agent A
↔ Agent B
↔ Agent C
```

and claim:

```text id="multi006"
"they work together"
```

In reality:

```text id="multi007"
someone still orchestrates them
```

Usually:

```text id="multi008"
Supervisor
↓
Delegates Tasks
↓
Collects Results
↓
Produces Final Answer
```

This is MUCH more common.

---

# IMPORTANT INDUSTRY REALITY

Most production systems are:

```text id="multi009"
Supervisor + Specialists
```

NOT:

```text id="multi010"
fully autonomous agent societies
```

---

# Part 2 — Why Multi-Agent Exists

Single-agent systems work well until:

```text id="multi011"
one agent must become:
- planner
- researcher
- calculator
- coder
- reviewer
- summarizer
```

This creates:

```text id="multi012"
prompt bloat
```

and:

```text id="multi013"
responsibility overload
```

---

# Solution

Split responsibilities.

Example:

```text id="multi014"
Research Agent
Code Agent
Review Agent
```

Each becomes:

* simpler
* more focused
* easier to evaluate

---

# Part 3 — Common Multi-Agent Patterns

## Pattern 1 — Supervisor

Most common.

```text id="multi015"
Supervisor
├── Research Agent
├── Coding Agent
└── Review Agent
```

Supervisor decides:

* who works
* when
* what result to use

---

## Pattern 2 — Pipeline

```text id="multi016"
Research
↓
Summarize
↓
Review
↓
Final Output
```

Mostly deterministic.

---

## Pattern 3 — Handoff

```text id="multi017"
Agent A
↓
Agent B
↓
Agent C
```

Each specializes in one stage.

---

## Pattern 4 — Parallel Specialists

```text id="multi018"
Research Agent
Analysis Agent
Risk Agent
```

run simultaneously.

Results merged later.

---

# Part 4 — What We Will Build

We will implement:

```text id="multi019"
START
 ↓
Supervisor
 ├── Research Agent
 ├── Math Agent
 └── General Agent
 ↓
Merge Results
 ↓
END
```

This is the most useful architecture to understand first.

---

# Part 5 — Project Structure

```text id="multi020"
langgraph_session9/
├── main.py
├── graph.py
├── state.py
├── agents.py
├── prompts.py
├── requirements.txt
└── .env
```

---

# Part 6 — State Design

## state.py

```python id="multi021"
from typing import TypedDict


class AgentState(TypedDict):

    user_input: str

    selected_agent: str

    worker_result: str

    final_answer: str
```

---

# IMPORTANT CONCEPT

Supervisor systems need state that tracks:

```text id="multi022"
delegation decisions
```

This is new.

---

# Part 7 — OpenAI Setup

## agents.py

```python id="multi023"
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
```

---

# Part 8 — Worker Prompts

## prompts.py

```python id="multi024"
RESEARCH_PROMPT = """
You are a research specialist.

Provide factual and detailed answers.
"""
```

---

```python id="multi025"
MATH_PROMPT = """
You are a math specialist.

Solve mathematical questions.
"""
```

---

```python id="multi026"
GENERAL_PROMPT = """
You are a helpful assistant.
"""
```

---

# IMPORTANT CONCEPT

Each worker has:

```text id="multi027"
specialized instructions
```

This is one reason multi-agent systems can be useful.

---

# Part 9 — Research Agent

## agents.py

```python id="multi028"
from prompts import (
    RESEARCH_PROMPT
)
```

---

```python id="multi029"
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
```

---

# Part 10 — Math Agent

## agents.py

```python id="multi030"
from prompts import (
    MATH_PROMPT
)
```

---

```python id="multi031"
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
```

---

# Part 11 — General Agent

## agents.py

```python id="multi032"
from prompts import (
    GENERAL_PROMPT
)
```

---

```python id="multi033"
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
```

---

# Part 12 — Supervisor Node

THIS is the heart of the architecture.

## graph.py

```python id="multi034"
def supervisor_node(
    state: AgentState
):
```

---

```python id="multi035"
    question = (
        state["user_input"]
        .lower()
    )

    if any(
        word in question
        for word in [
            "calculate",
            "math",
            "+"
        ]
    ):

        return {
            "selected_agent":
                "math"
        }

    if any(
        word in question
        for word in [
            "research",
            "history",
            "explain"
        ]
    ):

        return {
            "selected_agent":
                "research"
        }

    return {
        "selected_agent":
            "general"
    }
```

---

# IMPORTANT CONCEPT

The supervisor:

```text id="multi036"
does not solve the task
```

It decides:

```text id="multi037"
who should solve it
```

Very important distinction.

---

# Part 13 — Worker Node

## graph.py

```python id="multi038"
from agents import (
    research_agent,
    math_agent,
    general_agent
)
```

---

```python id="multi039"
def worker_node(
    state: AgentState
):
```

---

```python id="multi040"
    question = (
        state["user_input"]
    )

    selected = (
        state["selected_agent"]
    )

    if selected == "research":

        result = research_agent(
            question
        )

    elif selected == "math":

        result = math_agent(
            question
        )

    else:

        result = general_agent(
            question
        )

    return {
        "worker_result":
            result
    }
```

---

# IMPORTANT INSIGHT

This node is:

```text id="multi041"
delegation execution
```

The supervisor:

* chooses

The worker:

* performs

---

# Part 14 — Final Node

## graph.py

```python id="multi042"
def final_node(
    state: AgentState
):

    return {
        "final_answer":
            state["worker_result"]
    }
```

---

# Part 15 — Build Graph

## graph.py

```python id="multi043"
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState
```

---

# Create Graph

```python id="multi044"
graph = StateGraph(
    AgentState
)
```

---

# Add Nodes

```python id="multi045"
graph.add_node(
    "supervisor",
    supervisor_node
)

graph.add_node(
    "worker",
    worker_node
)

graph.add_node(
    "final",
    final_node
)
```

---

# Entry Point

```python id="multi046"
graph.set_entry_point(
    "supervisor"
)
```

---

# Connect Flow

```python id="multi047"
graph.add_edge(
    "supervisor",
    "worker"
)

graph.add_edge(
    "worker",
    "final"
)

graph.add_edge(
    "final",
    END
)
```

---

# Compile

```python id="multi048"
app = graph.compile()
```

---

# Part 16 — Example Execution

Input:

```text id="multi049"
calculate 25 * 8
```

Execution:

```text id="multi050"
Supervisor
↓
Math Agent
↓
Final
```

---

Input:

```text id="multi051"
Explain World War II
```

Execution:

```text id="multi052"
Supervisor
↓
Research Agent
↓
Final
```

---

# Part 17 — Why This Works

Instead of:

```text id="multi053"
one giant prompt
```

you now have:

```text id="multi054"
specialized workers
```

which are:

* easier to tune
* easier to test
* easier to evaluate

---

# Part 18 — Parallel Agents

A more advanced architecture:

```text id="multi055"
Supervisor
├── Research Agent
├── Risk Agent
└── Summary Agent
```

All run simultaneously.

Results merged later.

---

# Example

For an investment assistant:

```text id="multi056"
Research Agent
→ gathers data

Risk Agent
→ evaluates risks

Summary Agent
→ generates recommendation
```

This is VERY common.

---

# Part 19 — Agent Handoffs

Another architecture:

```text id="multi057"
Research Agent
↓
Writer Agent
↓
Reviewer Agent
```

Each agent hands off:

```text id="multi058"
state
```

to the next.

Very similar to workflow pipelines.

---

# Part 20 — When Multi-Agent Is Useful

Useful when:

```text id="multi059"
- different expertise needed
- independent tasks exist
- evaluation boundaries exist
- parallelism helps
```

Examples:

```text id="multi060"
- coding assistants
- research systems
- financial analysis
- customer support escalation
```

---

# Part 21 — When Multi-Agent Is A Bad Idea

Most people overuse it.

Bad use cases:

```text id="multi061"
Simple FAQ bot
Simple RAG app
Simple workflow
```

You often need:

```text id="multi062"
one graph
```

NOT:

```text id="multi063"
five agents
```

---

# IMPORTANT INDUSTRY REALITY

Many multi-agent demos are actually:

```text id="multi064"
unnecessary complexity
```

Very important lesson.

---

# Part 22 — Enterprise Architecture Reality

Most enterprise systems are:

```text id="multi065"
Supervisor
+
Specialized Workers
```

rather than:

```text id="multi066"
autonomous agent societies
```

This architecture is:

* predictable
* testable
* auditable

---

# Part 23 — Common Beginner Mistakes

## Mistake 1

Creating agents for everything.

Not needed.

---

## Mistake 2

No clear specialization.

Workers should have:

* distinct responsibilities

---

## Mistake 3

Workers making routing decisions.

Supervisor should own routing.

---

## Mistake 4

Overlapping prompts.

Creates confusion.

---

## Mistake 5

No evaluation per worker.

Each worker should be measurable.

---

# Part 24 — What You Learned

You now understand:

## Conceptually

```text id="multi067"
- supervisor architecture
- delegation
- worker agents
- handoffs
- multi-agent orchestration
```

## Technically

```text id="multi068"
- supervisor nodes
- worker nodes
- task delegation
- specialization
```

You have now built:

```text id="multi069"
your first multi-agent LangGraph architecture
```

which is very close to how many real enterprise systems are designed.

---

# Your Exercises

## Exercise 1 — Add Reviewer Agent

Flow:

```text id="multi070"
Supervisor
↓
Worker
↓
Reviewer
↓
Final
```

---

## Exercise 2 — Add Risk Agent

For risky requests:

* risk analysis first

---

## Exercise 3 — Add Parallel Specialists

Run:

* research
* risk
* summary

and merge results.

---

## Exercise 4 — Add RAG Worker

Use:

* sqlite-vec retrieval

as a specialized agent.

---

## Exercise 5 — Add Evaluation Scores

Track:

* worker quality
* routing accuracy

inside state.

---

# LangGraph Session 10 Preview

Next you'll learn:

```text id="multi071"
Production LangGraph Architecture
```

You will combine:

```text id="multi072"
- memory
- checkpointing
- RAG
- tools
- validation
- HITL
- multi-agent orchestration
- observability
- deployment patterns
```

into a complete production-ready architecture.

This will conclude the core LangGraph series and bridge into real enterprise AI engineering.
