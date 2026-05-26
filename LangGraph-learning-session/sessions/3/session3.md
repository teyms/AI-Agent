# LangGraph Session 3 — Conditional Routing and Dynamic Graph Execution

## Goal of This Session

By the end of this session, you will understand:

```text
- Conditional routing
- Dynamic graph execution
- Retry loops
- Validation flows
- Fallback paths
- Runtime decisions
- Cyclic graphs
- Why LangGraph is more than a simple workflow engine
```

This is the session where LangGraph starts becoming:

```text
a real orchestration engine
```

instead of just:

* connected functions.

---

# Part 1 — The Limitation Of Session 2

Your Session 2 graph looked like:

```text
START
 ↓
classify
 ├── weather
 ├── calculator
 └── general
 ↓
final
 ↓
END
```

This is still mostly:

```text
deterministic routing
```

But real production systems need:

```text
- retries
- validation
- fallback logic
- dynamic branching
- loops
- escalation paths
```

This is where LangGraph becomes powerful.

---

# Part 2 — What Is Conditional Routing?

Conditional routing means:

```text
The next node depends on runtime state.
```

Example:

```text
If tool succeeded
→ continue

If tool failed
→ retry

If retries exceeded
→ fallback

If confidence low
→ ask clarification
```

This is VERY common in real AI systems.

---

# Part 3 — Runtime Decision Graphs

Unlike simple chains:

```text
A → B → C
```

LangGraph supports:

```text
A
├── if success → B
├── if retry → A
└── if failed → C
```

This is:

* dynamic execution
* runtime orchestration

VERY important concept.

---

# Part 4 — What We Will Build

We will upgrade Session 2 into:

```text
START
 ↓
classify
 ↓
calculator
 ↓
validate_result
 ├── success → final
 ├── retry → calculator
 └── fallback → fallback_node
 ↓
END
```

This introduces:

* loops
* retries
* validation routing

which are CRITICAL for production AI systems.

---

# Part 5 — Updated Project Structure

```text
langgraph_session3/
├── main.py
├── graph.py
├── nodes.py
├── state.py
├── tools.py
├── requirements.txt
└── .env
```

---

# Part 6 — Update State

## state.py

```python
from typing import TypedDict


class AgentState(TypedDict):

    user_input: str

    intent: str

    response: str

    retry_count: int

    validation_status: str

    final_answer: str
```

---

# IMPORTANT CONCEPT

State now tracks:

```text
workflow metadata
```

NOT just LLM context.

Very important distinction.

---

# Part 7 — Why Retry State Matters

Production systems MUST track:

```text
- retries
- failures
- execution status
- validation state
```

Without state:

* orchestration becomes unreliable.

---

# Part 8 — Update Calculator Tool

## tools.py

We intentionally introduce failure scenarios.

```python
def calculator(expression):

    try:

        if expression == "bad":

            raise Exception(
                "Simulated failure"
            )

        return str(eval(expression))

    except Exception as e:

        return f"ERROR: {str(e)}"
```

---

# IMPORTANT LESSON

In production:

```text
failures are normal
```

Good systems are built around:

* recovery
* retries
* fallbacks

NOT assuming everything succeeds.

---

# Part 9 — Calculator Node

## nodes.py

```python
from state import AgentState

from tools import calculator
```

---

# calculator_node

```python
def calculator_node(
    state: AgentState
):

    user_input = (
        state["user_input"]
        .replace("calculate", "")
        .strip()
    )

    result = calculator(user_input)

    return {
        "response": result
    }
```

---

# Part 10 — Validation Node

VERY important production concept.

## nodes.py

```python
def validate_result_node(
    state: AgentState
):

    response = state["response"]

    if response.startswith("ERROR"):

        if state["retry_count"] < 2:

            return {
                "validation_status": "retry",
                "retry_count": (
                    state["retry_count"] + 1
                )
            }

        return {
            "validation_status": "fallback"
        }

    return {
        "validation_status": "success"
    }
```

---

# IMPORTANT CONCEPT

Validation nodes are EXTREMELY important.

Production systems often validate:

* tool outputs
* JSON schemas
* retrieval quality
* confidence scores
* permissions

before continuing.

---

# Part 11 — Fallback Node

## nodes.py

```python
def fallback_node(
    state: AgentState
):

    return {
        "final_answer": (
            "Unable to complete request "
            "after retries."
        )
    }
```

---

# IMPORTANT PRODUCTION CONCEPT

Fallbacks are critical.

Never assume:

* retries always work
* APIs always succeed
* LLM outputs always valid

---

# Part 12 — Final Node

## nodes.py

```python
def final_response_node(
    state: AgentState
):

    return {
        "final_answer": (
            f"Final Result: "
            f"{state['response']}"
        )
    }
```

---

# Part 13 — Build Graph

## graph.py

```python
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    calculator_node,
    validate_result_node,
    fallback_node,
    final_response_node
)
```

---

# Create Graph

```python
graph = StateGraph(AgentState)
```

---

# Add Nodes

```python
graph.add_node(
    "calculator",
    calculator_node
)

graph.add_node(
    "validate",
    validate_result_node
)

graph.add_node(
    "fallback",
    fallback_node
)

graph.add_node(
    "final",
    final_response_node
)
```

---

# Part 14 — Entry Point

```python
graph.set_entry_point(
    "calculator"
)
```

---

# Part 15 — Connect Calculator To Validation

```python
graph.add_edge(
    "calculator",
    "validate"
)
```

---

# Part 16 — Conditional Routing

THIS is the most important part of this session.

## graph.py

```python
def validation_router(
    state: AgentState
):

    status = state[
        "validation_status"
    ]

    if status == "success":

        return "final"

    elif status == "retry":

        return "calculator"

    else:

        return "fallback"
```

---

# Add Conditional Edges

```python
graph.add_conditional_edges(
    "validate",
    validation_router,
    {
        "final": "final",
        "calculator": "calculator",
        "fallback": "fallback"
    }
)
```

---

# THIS Is The Big Moment

You just created:

```text
a cyclic graph
```

because:

```text
validate
→ calculator
```

creates a loop.

This is VERY important.

---

# Part 17 — Complete Graph

```python
graph.add_edge(
    "final",
    END
)

graph.add_edge(
    "fallback",
    END
)
```

---

# Compile Graph

```python
app = graph.compile()
```

---

# Part 18 — Main Entry Point

## main.py

```python
from graph import app


while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke({
        "user_input": user_input,
        "intent": "",
        "response": "",
        "retry_count": 0,
        "validation_status": "",
        "final_answer": ""
    })

    print("\n=== FINAL STATE ===")
    print(result)

    print("\nAssistant:")
    print(result["final_answer"])
```

---

# Part 19 — Example Success Flow

Input:

```text
calculate 25 * 8
```

Execution:

```text
calculator
→ validate
→ final
→ END
```

Output:

```text
Final Result: 200
```

---

# Part 20 — Example Retry Flow

Input:

```text
calculate bad
```

Execution:

```text
calculator
→ validate
→ calculator
→ validate
→ calculator
→ validate
→ fallback
→ END
```

VERY important.

You now have:

* retry loops
* validation routing
* fallback handling

This is REAL orchestration behavior.

---

# Part 21 — Why Cyclic Graphs Matter

Simple workflows are:

```text
acyclic
```

No loops.

But real AI systems require:

```text
- retries
- self-correction
- reflection
- iterative reasoning
```

which naturally create:

* cycles
* loops

LangGraph handles this elegantly.

---

# Part 22 — Runtime Graph Execution

VERY important mental model.

The graph is NOT fully predetermined.

Execution path depends on:

```text
runtime state
```

This is what makes LangGraph powerful.

---

# Part 23 — Production Validation Examples

Real systems validate:

* tool outputs
* JSON schema
* retrieval confidence
* hallucination risk
* permission checks
* cost thresholds
* moderation safety

Validation nodes are everywhere in enterprise AI systems.

---

# Part 24 — Why This Is Better Than Giant If/Else

Without graph routing:

```python
if failed:
    retry()

if retries > 3:
    fallback()
```

becomes:

* huge
* messy
* hard to debug

Graphs make orchestration:

* explicit
* modular
* visual
* debuggable

---

# Part 25 — Important LangGraph Insight

LangGraph is NOT just:

* node execution

It is fundamentally:

```text
state-driven routing
```

VERY important concept.

---

# Part 26 — Common Beginner Mistakes

## Mistake 1 — Infinite Loops

Bad routing can create:

```text
never-ending cycles
```

Always:

* limit retries
* limit iterations

---

## Mistake 2 — No Validation Nodes

Without validation:

* bad outputs propagate
* workflows become fragile

---

## Mistake 3 — Too Much Logic In Routers

Routers should:

* decide routing

NOT:

* perform business logic

---

## Mistake 4 — Mixing Validation And Execution

Keep:

* execution nodes
* validation nodes

separate when possible.

Cleaner architecture.

---

## Mistake 5 — No Fallback Paths

Production systems MUST degrade gracefully.

---

# Part 27 — What You Learned

You now understand:

## Conceptually

```text
- conditional routing
- runtime graph execution
- retry loops
- validation flows
- cyclic graphs
- fallback architectures
```

## Technically

```text
- add_conditional_edges()
- cyclic routing
- validation nodes
- retry counters
- dynamic execution paths
```

This is REAL orchestration engineering.

---

# Your Exercises

## Exercise 1 — Add Clarification Loop

If input unclear:

* ask clarification
* retry classification

---

## Exercise 2 — Add Confidence Validation

If confidence low:

* fallback to human review

---

## Exercise 3 — Add Logging Node

Track:

* execution path
* retries
* failures

inside state.

---

## Exercise 4 — Add Timeouts

If retries exceed:

* terminate workflow

---

## Exercise 5 — Add Multi-Validation

Validate:

* output format
* confidence
* permissions

before final answer.

---

# LangGraph Session 4 Preview

Next you’ll learn:

```text
Tool Calling with LangGraph
```

You will build:

* real tool orchestration
* tool nodes
* dynamic tool execution
* tool routing
* ReAct-style loops
* LLM-driven tool decisions

This is where LangGraph starts feeling like:

* a true AI agent framework.
