# LangGraph Session 4 — Tool Calling with LangGraph

## Goal of This Session

By the end of this session, you will understand:

```text id="4q0e92"
- Tool orchestration in LangGraph
- Tool nodes
- LLM-driven tool selection
- ReAct-style loops
- Dynamic tool execution
- Observation → Action cycles
- Tool routing
- Why agents are mostly orchestration systems
```

This is the session where your LangGraph workflows start becoming:

```text id="5ewlm9"
real AI agents
```

instead of:

* deterministic workflows.

---

# Part 1 — What Changes In This Session?

Previously:

```text id="13jlwm"
Routing logic
=
hardcoded Python logic
```

Example:

```python id="49aj7z"
if "weather" in user_input:
    return "weather"
```

But real agents work differently.

Instead:

```text id="3rlf5g"
LLM decides:
- whether tools are needed
- which tool to use
- what arguments to pass
```

This is a MAJOR architectural shift.

---

# Part 2 — Agent Mental Model

The core loop becomes:

```text id="fp7wl0"
Observe
↓
Reason
↓
Choose Tool
↓
Execute Tool
↓
Observe Result
↓
Reason Again
```

This is:

* ReAct-style orchestration
* the heart of modern AI agents

---

# IMPORTANT INDUSTRY REALITY

Most AI agents are basically:

```text id="20aq3n"
LLM-generated control flow
```

NOT autonomous intelligence.

Very important mindset.

---

# Part 3 — What We Will Build

We will build:

```text id="o2m7r7"
START
 ↓
agent_node
 ├── tool needed → tool_node
 │                      ↓
 │                agent_node
 │
 └── final answer → END
```

This creates:

```text id="hvt9r3"
a reasoning loop
```

VERY important architecture.

---

# Part 4 — Project Structure

```text id="0d5c6q"
langgraph_session4/
├── main.py
├── graph.py
├── nodes.py
├── tools.py
├── state.py
├── prompts.py
├── requirements.txt
└── .env
```

---

# Install Dependencies

```bash id="c3rku7"
pip install langgraph langchain-core openai python-dotenv
```

---

# Part 5 — Environment Variables

## .env

```text id="eu6fq7"
LLM_API_KEY=your_key
LLM_BASE_URL=your_base_url
LLM_MODEL=your_model
```

---

# Part 6 — State Design

## state.py

```python id="k1wjlwm"
from typing import TypedDict, List


class AgentState(TypedDict):

    user_input: str

    messages: List[dict]

    current_tool: str

    tool_input: str

    tool_output: str

    final_answer: str
```

---

# IMPORTANT CONCEPT

Your graph state is becoming:

```text id="mjlwm2"
conversation + orchestration state
```

This is VERY important.

---

# Part 7 — Why Messages Matter

Unlike earlier sessions:

```text id="7jlwm3"
messages
```

now become central.

Why?

Because:

* reasoning loops require conversation history
* tool observations must be fed back to the LLM

This is foundational for agents.

---

# Part 8 — Create Tools

## tools.py

```python id="xjlwm4"
from datetime import datetime
```

---

# Weather Tool

```python id="hjlwm5"
def get_weather(location):

    fake_weather = {
        "singapore": "30°C rainy",
        "tokyo": "18°C cloudy",
        "london": "12°C windy"
    }

    return fake_weather.get(
        location.lower(),
        "Weather not found."
    )
```

---

# Calculator Tool

```python id="kjlwm6"
def calculator(expression):

    try:

        return str(eval(expression))

    except Exception as e:

        return f"Calculation error: {str(e)}"
```

---

# Time Tool

```python id="njlwm7"
def get_current_time():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
```

---

# Tool Registry

```python id="pjlwm8"
TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_current_time": get_current_time
}
```

---

# IMPORTANT CONCEPT

This is:

```text id="ujlwm9"
dynamic tool dispatch
```

Very important production architecture.

---

# Part 9 — OpenAI Setup

## nodes.py

```python id="wjlwm0"
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

# Part 10 — Agent Prompt

## prompts.py

```python id="yjlwm1"
SYSTEM_PROMPT = """
You are an AI agent.

You may:
- answer directly
- use tools

Available tools:
1. get_weather(location)
2. calculator(expression)
3. get_current_time()

Return ONLY valid JSON.

Schema:
{
    "thought": string,
    "needs_tool": boolean,
    "tool_name": string,
    "tool_input": string,
    "final_answer": string
}

Rules:
- Think step-by-step
- Use tools when needed
- If no tool needed:
  set final_answer
"""
```

---

# IMPORTANT CONCEPT

This is:

* structured reasoning output

NOT:

* magical internal thinking.

Very important distinction.

---

# Part 11 — Agent Node

THIS is the heart of the session.

## nodes.py

```python id="zjlwm2"
from state import AgentState
from prompts import SYSTEM_PROMPT
```

---

# agent_node

```python id="1jlwm3"
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

    updates = {}

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

# THIS Is VERY Important

The LLM is now:

* generating runtime execution decisions

This is the core of modern agents.

---

# Part 12 — Tool Node

## nodes.py

```python id="2jlwm4"
from tools import TOOLS
```

---

# tool_node

```python id="3jlwm5"
def tool_node(
    state: AgentState
):

    tool_name = state["current_tool"]

    tool_input = state["tool_input"]

    tool_function = TOOLS[tool_name]

    result = tool_function(tool_input)

    tool_message = (
        f"Tool Result: {result}"
    )

    return {
        "tool_output": result,
        "messages": (
            state["messages"] + [
                {
                    "role": "user",
                    "content": tool_message
                }
            ]
        )
    }
```

---

# IMPORTANT CONCEPT

The tool result becomes:

```text id="4jlwm6"
new observation
```

fed back into the reasoning loop.

This is:

* observation/action architecture

---

# Part 13 — Router Function

## graph.py

```python id="5jlwm7"
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    agent_node,
    tool_node
)
```

---

# Create Graph

```python id="6jlwm8"
graph = StateGraph(
    AgentState
)
```

---

# Add Nodes

```python id="7jlwm9"
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

# Router Function

```python id="8jlwm0"
def route_agent(
    state: AgentState
):

    if state["final_answer"]:

        return END

    return "tool"
```

---

# Add Conditional Routing

```python id="9jlwm1"
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

# Connect Tool Back To Agent

```python id="0jlwm2"
graph.add_edge(
    "tool",
    "agent"
)
```

---

# THIS Is The BIG Moment

You just created:

```text id="1jlwm3"
a ReAct-style reasoning loop
```

VERY important milestone.

---

# Part 14 — Entry Point

```python id="2jlwm4"
graph.set_entry_point(
    "agent"
)
```

---

# Compile Graph

```python id="3jlwm5"
app = graph.compile()
```

---

# Part 15 — Main Entry Point

## main.py

```python id="4jlwm6"
from graph import app


while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke({
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
        "final_answer": ""
    })

    print("\n=== FINAL STATE ===")
    print(result)

    print("\nAssistant:")
    print(result["final_answer"])
```

---

# Part 16 — Example Weather Flow

Input:

```text id="5jlwm7"
What is the weather in Singapore?
```

Execution:

```text id="6jlwm8"
agent
→ tool
→ agent
→ END
```

Reasoning:

```text id="7jlwm9"
Thought:
Need weather information

Tool:
get_weather("Singapore")

Observation:
30°C rainy

Final Answer:
The weather in Singapore is 30°C and rainy.
```

---

# Part 17 — Example Calculator Flow

Input:

```text id="8jlwm0"
calculate 25 * 8
```

Execution:

```text id="9jlwm1"
agent
→ tool
→ agent
→ END
```

This is REAL agent orchestration.

---

# Part 18 — Why This Architecture Matters

This architecture enables:

* dynamic reasoning
* multiple tool calls
* iterative planning
* observation/action loops
* flexible orchestration

This is MUCH closer to:

* coding agents
* research agents
* autonomous assistants

---

# Part 19 — Why Messages Become Critical

The reasoning loop depends on:

```text id="0jlwm2"
conversation continuity
```

because the LLM must see:

* previous reasoning
* tool results
* observations

to continue correctly.

This is VERY important.

---

# Part 20 — Production Reality

Real agents usually add:

* retries
* validation
* memory
* RAG
* tool permissions
* observability
* checkpointing

around this core loop.

But fundamentally:

```text id="1jlwm3"
this is the heart of modern AI agents
```

---

# Part 21 — Why LangGraph Fits Agents So Well

Agents naturally require:

* loops
* state
* routing
* dynamic execution
* retries

Graphs model this naturally.

This is why LangGraph became popular for:

* agent orchestration.

---

# Part 22 — Common Beginner Mistakes

## Mistake 1 — Infinite Loops

Agents can loop forever.

Always:

* limit iterations
* add stop conditions

---

## Mistake 2 — No Tool Validation

Never trust:

* tool names
* arguments

blindly.

---

## Mistake 3 — Overloading State

Keep state:

* clean
* structured
* intentional

---

## Mistake 4 — No Observation Injection

Tool results MUST be fed back into:

* messages
* reasoning context

---

## Mistake 5 — Letting Agents Use Dangerous Tools

Always restrict:

* filesystem
* deployment
* payments
* destructive actions

---

# Part 23 — What You Learned

You now understand:

## Conceptually

```text id="2jlwm4"
- ReAct loops
- reasoning agents
- observation/action cycles
- dynamic tool selection
- iterative orchestration
```

## Technically

```text id="3jlwm5"
- tool nodes
- routing loops
- LLM-generated control flow
- stateful reasoning
- LangGraph agent architecture
```

You have now built:

* your first real LangGraph agent.

---

# Your Exercises

## Exercise 1 — Add Retry Logic

If tool fails:

* retry once
* then fallback

---

## Exercise 2 — Add Iteration Limits

Prevent:

* infinite loops

---

## Exercise 3 — Add RAG Tool

Add:

```text id="4jlwm6"
search_knowledge_base
```

using your sqlite-vec setup.

---

## Exercise 4 — Add Validation Node

Validate:

* tool output
* JSON schema

before continuing.

---

## Exercise 5 — Add Logging

Track:

* node execution
* tool calls
* reasoning traces

inside state.

---

# LangGraph Session 5 Preview

Next you’ll learn:

```text id="5jlwm7"
Memory and Persistence in LangGraph
```

You will build:

* persistent memory
* checkpointing
* conversation history
* resumable execution
* durable workflows

This is where LangGraph becomes:

* truly production-oriented.
