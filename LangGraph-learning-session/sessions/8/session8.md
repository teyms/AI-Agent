# LangGraph Session 8 — Error Handling, Validation, Guardrails and Retries

## Goal of This Session

By the end of this session, you will understand:

```text id="guard001"
- Why production agents fail
- Validation nodes
- Retry strategies
- Fallback paths
- Guardrails
- Tool safety
- Schema validation
- Error recovery
- Circuit breakers
- Production reliability patterns
```

This session is one of the most important in the entire LangGraph series.

Many AI demos work because:

```text id="guard002"
everything succeeds
```

Production systems fail because:

```text id="guard003"
everything eventually fails
```

---

# Part 1 — Production Reality

Suppose your graph contains:

```text id="guard004"
Agent
↓
Tool
↓
RAG
↓
Answer
```

Potential failures:

```text id="guard005"
- invalid JSON
- tool timeout
- API outage
- hallucinated tool name
- retrieval failure
- empty response
- malformed arguments
- permission denied
```

Production systems must expect failure.

---

# IMPORTANT INDUSTRY MINDSET

Beginner:

```text id="guard006"
How do I make the AI smarter?
```

Production engineer:

```text id="guard007"
How do I make the system survive failure?
```

Very important distinction.

---

# Part 2 — What We Will Build

We will create:

```text id="guard008"
START
 ↓
Agent
 ↓
Validate
 ├── valid → Execute Tool
 ├── retry → Agent
 └── fallback → Human Review
 ↓
END
```

This introduces:

```text id="guard009"
- validation
- retries
- fallback routing
- safety layers
```

which are critical in enterprise systems.

---

# Part 3 — Project Structure

```text id="guard010"
langgraph_session8/
├── main.py
├── graph.py
├── state.py
├── nodes.py
├── prompts.py
├── validators.py
├── tools.py
├── requirements.txt
└── .env
```

---

# Part 4 — State Design

## state.py

```python id="guard011"
from typing import TypedDict


class AgentState(TypedDict):

    user_input: str

    proposed_tool: str

    tool_input: str

    validation_status: str

    retry_count: int

    tool_output: str

    final_answer: str

    error_message: str
```

---

# IMPORTANT CONCEPT

State now tracks:

```text id="guard012"
workflow health
```

not just:

* user requests

This is a production engineering mindset.

---

# Part 5 — Create Tools

## tools.py

```python id="guard013"
def calculator(expression):

    try:

        return str(eval(expression))

    except Exception as e:

        raise Exception(
            f"Calculator failed: {str(e)}"
        )
```

---

# Time Tool

```python id="guard014"
from datetime import datetime


def get_current_time():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
```

---

# Registry

```python id="guard015"
TOOLS = {
    "calculator": calculator,
    "get_current_time": get_current_time
}
```

---

# Part 6 — Why Tool Validation Matters

Without validation:

LLM may generate:

```text id="guard016"
delete_database
```

even though:

```text id="guard017"
tool does not exist
```

Bad.

Validation prevents this.

---

# Part 7 — Allowed Tool Validator

## validators.py

```python id="guard018"
ALLOWED_TOOLS = {
    "calculator",
    "get_current_time"
}
```

---

# Validate Tool

```python id="guard019"
def validate_tool_name(
    tool_name
):

    return (
        tool_name
        in ALLOWED_TOOLS
    )
```

---

# IMPORTANT CONCEPT

LLMs never directly control:

```text id="guard020"
real system permissions
```

Your orchestration layer does.

Very important security principle.

---

# Part 8 — Agent Prompt

## prompts.py

```python id="guard021"
SYSTEM_PROMPT = """
You are an AI agent.

Return ONLY valid JSON.

Schema:

{
    "tool_name": string,
    "tool_input": string
}
"""
```

---

# Part 9 — Agent Node

## nodes.py

```python id="guard022"
import os
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

MODEL_NAME = os.getenv("LLM_MODEL")
```

---

# agent_node

```python id="guard023"
from prompts import SYSTEM_PROMPT
```

---

```python id="guard024"
def agent_node(
    state: AgentState
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": state["user_input"]
            }
        ]
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    try:

        parsed = json.loads(content)

        return {
            "proposed_tool":
                parsed["tool_name"],

            "tool_input":
                parsed["tool_input"],

            "error_message": ""
        }

    except Exception:

        return {
            "error_message":
                "Invalid JSON"
        }
```

---

# IMPORTANT LESSON

Never trust:

```text id="guard025"
LLM output
```

without validation.

---

# Part 10 — Validation Node

## nodes.py

```python id="guard026"
from validators import (
    validate_tool_name
)
```

---

# validate_node

```python id="guard027"
def validate_node(
    state: AgentState
):

    if state["error_message"]:

        if state["retry_count"] < 2:

            return {
                "validation_status":
                    "retry",

                "retry_count":
                    state["retry_count"] + 1
            }

        return {
            "validation_status":
                "fallback"
        }

    if not validate_tool_name(
        state["proposed_tool"]
    ):

        return {
            "validation_status":
                "fallback"
        }

    return {
        "validation_status":
            "valid"
    }
```

---

# IMPORTANT CONCEPT

Validation nodes separate:

```text id="guard028"
generation
```

from:

```text id="guard029"
execution
```

This is very important architecture.

---

# Part 11 — Execute Tool Node

## nodes.py

```python id="guard030"
from tools import TOOLS
```

---

# execute_tool_node

```python id="guard031"
def execute_tool_node(
    state: AgentState
):

    try:

        tool_function = TOOLS[
            state["proposed_tool"]
        ]

        result = tool_function(
            state["tool_input"]
        )

        return {
            "tool_output": result
        }

    except Exception as e:

        return {
            "error_message":
                str(e)
        }
```

---

# Part 12 — Retry Routing

## graph.py

```python id="guard032"
def validation_router(
    state: AgentState
):

    status = state[
        "validation_status"
    ]

    if status == "valid":

        return "execute"

    if status == "retry":

        return "agent"

    return "fallback"
```

---

# THIS Is The Important Pattern

```text id="guard033"
Validate
↓
Retry
↓
Validate
↓
Fallback
```

Very common production architecture.

---

# Part 13 — Fallback Node

## nodes.py

```python id="guard034"
def fallback_node(
    state: AgentState
):

    return {
        "final_answer":
            (
                "Unable to complete "
                "request safely."
            )
    }
```

---

# IMPORTANT CONCEPT

Production systems must:

```text id="guard035"
fail safely
```

NOT:

```text id="guard036"
fail unpredictably
```

---

# Part 14 — Final Response Node

## nodes.py

```python id="guard037"
def final_node(
    state: AgentState
):

    return {
        "final_answer":
            (
                f"Result: "
                f"{state['tool_output']}"
            )
    }
```

---

# Part 15 — Build Graph

## graph.py

```python id="guard038"
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_node,
    validate_node,
    execute_tool_node,
    fallback_node,
    final_node
)
```

---

# Create Graph

```python id="guard039"
graph = StateGraph(
    AgentState
)
```

---

# Add Nodes

```python id="guard040"
graph.add_node(
    "agent",
    agent_node
)

graph.add_node(
    "validate",
    validate_node
)

graph.add_node(
    "execute",
    execute_tool_node
)

graph.add_node(
    "fallback",
    fallback_node
)

graph.add_node(
    "final",
    final_node
)
```

---

# Entry Point

```python id="guard041"
graph.set_entry_point(
    "agent"
)
```

---

# Connect Agent → Validate

```python id="guard042"
graph.add_edge(
    "agent",
    "validate"
)
```

---

# Conditional Routing

```python id="guard043"
graph.add_conditional_edges(
    "validate",
    validation_router,
    {
        "execute": "execute",
        "agent": "agent",
        "fallback": "fallback"
    }
)
```

---

# End Flow

```python id="guard044"
graph.add_edge(
    "execute",
    "final"
)

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

```python id="guard045"
app = graph.compile()
```

---

# Part 16 — Circuit Breakers

Production systems often use:

```text id="guard046"
circuit breakers
```

Meaning:

```text id="guard047"
too many failures
↓
stop execution
```

Example:

```python id="guard048"
if retry_count > 5:
    return "fallback"
```

This prevents:

* infinite retries
* runaway costs

---

# Part 17 — Schema Validation

Production systems often validate:

```text id="guard049"
JSON schema
```

before execution.

Example:

```python id="guard050"
required_keys = [
    "tool_name",
    "tool_input"
]
```

Missing fields:

```text id="guard051"
→ retry
```

Very common pattern.

---

# Part 18 — Guardrails

Guardrails are:

```text id="guard052"
constraints around agent behavior
```

Examples:

```text id="guard053"
- tool allowlists
- permission checks
- moderation
- cost limits
- iteration limits
```

Guardrails are NOT:

```text id="guard054"
just prompts
```

Very important lesson.

---

# Part 19 — Tool Safety

Never trust:

```text id="guard055"
tool inputs
```

Example:

```text id="guard056"
delete_user("*")
```

might delete:

```text id="guard057"
everyone
```

Validation is critical.

---

# Part 20 — Production Reliability Pattern

Very common enterprise graph:

```text id="guard058"
Agent
↓
Validate
↓
Execute
↓
Validate Output
├── success → Final
├── retry → Execute
└── fallback → Human Review
```

This pattern appears everywhere.

---

# Part 21 — Why LangGraph Fits Reliability Engineering

Graphs naturally support:

```text id="guard059"
- retries
- loops
- validation
- fallbacks
- escalation
```

This makes LangGraph excellent for:

* enterprise workflows.

---

# Part 22 — Common Beginner Mistakes

## Mistake 1

Trusting model output directly.

Never do this.

---

## Mistake 2

No retry limits.

Leads to:

* runaway systems

---

## Mistake 3

No fallback path.

Every workflow needs one.

---

## Mistake 4

Mixing validation and execution.

Keep them separate.

---

## Mistake 5

Thinking prompts are guardrails.

Prompts are only one layer.

---

# Part 23 — What You Learned

You now understand:

## Conceptually

```text id="guard060"
- validation architecture
- retry systems
- fallback strategies
- guardrails
- reliability engineering
```

## Technically

```text id="guard061"
- validation nodes
- retry loops
- fallback routing
- tool allowlists
- schema validation
```

You have now built:

```text id="guard062"
a reliability-aware LangGraph workflow
```

which is much closer to:

* production systems.

---

# Your Exercises

## Exercise 1 — Add Output Validation

Validate:

* tool outputs
* answer quality

before final response.

---

## Exercise 2 — Add Confidence Threshold

Low confidence:

```text id="guard063"
→ human review
```

---

## Exercise 3 — Add Cost Guardrail

Stop execution if:

```text id="guard064"
token budget exceeded
```

---

## Exercise 4 — Add Permission Checks

Example:

```text id="guard065"
admin-only tools
```

---

## Exercise 5 — Add Secondary Validation LLM

Use another model to:

```text id="guard066"
review output before execution
```

---

# LangGraph Session 9 Preview

Next you'll learn:

```text id="guard067"
Multi-Agent and Supervisor Architectures
```

You will build:

* supervisor agents
* worker agents
* delegation
* task routing
* agent handoffs
* orchestration at scale

This is where LangGraph starts looking like:

* real enterprise AI agent systems.
