# LangGraph Session 2 — Your First Real StateGraph

## Goal of This Session

By the end of this session, you will:

```text
- Build your first real LangGraph app
- Define graph state
- Create nodes
- Connect edges
- Compile a graph
- Invoke a graph
- Understand state updates
- Understand execution flow
```

This is your FIRST actual LangGraph implementation.

Now the abstractions should finally make sense because you already understand:

* orchestration
* workflows
* state machines
* graph execution

from the earlier sessions.

---

# Part 1 — What We Will Build

We will build a simple graph-based assistant.

Flow:

```text
START
 ↓
classify_intent
 ├── weather → weather_node
 ├── calculator → calculator_node
 └── general → general_response_node
 ↓
final_response_node
 ↓
END
```

This may look simple.

But this is the foundational architecture of MUCH larger systems.

---

# Part 2 — Install Dependencies

```bash
pip install langgraph langchain-core openai python-dotenv
```

---

# Project Structure

```text
langgraph_session2/
├── main.py
├── graph.py
├── nodes.py
├── state.py
├── tools.py
├── requirements.txt
└── .env
```

---

# Part 3 — Environment Variables

## .env

```text
LLM_API_KEY=your_key
LLM_BASE_URL=your_base_url
LLM_MODEL=your_model
```

---

# Part 4 — LLM Setup

## nodes.py

```python
import os

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

# Part 5 — Define State

This is one of the MOST important parts.

## state.py

```python
from typing import TypedDict, List


class AgentState(TypedDict):

    user_input: str

    intent: str

    tool_result: str

    final_answer: str

    messages: List[str]
```

---

# IMPORTANT CONCEPT

State is:

```text
shared workflow memory
```

between ALL nodes.

Every node:

* reads state
* updates state

This is the heart of LangGraph.

---

# Part 6 — Why TypedDict?

LangGraph strongly encourages structured state.

Benefits:

```text
- predictable workflows
- type safety
- easier debugging
- clearer architecture
```

This is MUCH better than random dictionaries everywhere.

---

# Part 7 — Create Tools

## tools.py

```python
def get_weather():

    return "30°C and rainy"


def calculator(expression):

    try:

        return str(eval(expression))

    except Exception as e:

        return f"Calculation failed: {str(e)}"
```

---

# Part 8 — Create Nodes

Nodes are just functions.

VERY important.

---

# Intent Classification Node

## nodes.py

```python
from state import AgentState
```

---

# classify_intent_node

```python
def classify_intent_node(
    state: AgentState
):

    user_input = state["user_input"].lower()

    if "weather" in user_input:

        intent = "weather"

    elif "calculate" in user_input:

        intent = "calculator"

    else:

        intent = "general"

    return {
        "intent": intent
    }
```

---

# IMPORTANT LANGGRAPH CONCEPT

Notice:

```python
return {
    "intent": intent
}
```

We are NOT mutating state directly.

LangGraph merges state updates automatically.

VERY important concept.

---

# Weather Node

## nodes.py

```python
from tools import (
    get_weather,
    calculator
)
```

---

# weather_node

```python
def weather_node(
    state: AgentState
):

    result = get_weather()

    return {
        "tool_result": result
    }
```

---

# Calculator Node

```python
def calculator_node(
    state: AgentState
):

    user_input = state["user_input"]

    expression = (
        user_input
        .replace("calculate", "")
        .strip()
    )

    result = calculator(expression)

    return {
        "tool_result": result
    }
```

---

# General Response Node

```python
def general_response_node(
    state: AgentState
):

    return {
        "tool_result": (
            "General response."
        )
    }
```

---

# Final Response Node

```python
def final_response_node(
    state: AgentState
):

    final_answer = (
        f"Result: "
        f"{state['tool_result']}"
    )

    return {
        "final_answer": final_answer
    }
```

---

# Part 9 — Build Graph

THIS is where LangGraph starts becoming powerful.

## graph.py

```python
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    classify_intent_node,
    weather_node,
    calculator_node,
    general_response_node,
    final_response_node
)
```

---

# Create Graph

```python
graph = StateGraph(AgentState)
```

---

# IMPORTANT CONCEPT

You are defining:

```text
a graph operating on AgentState
```

VERY important mental model.

---

# Part 10 — Add Nodes

## graph.py

```python
graph.add_node(
    "classify",
    classify_intent_node
)

graph.add_node(
    "weather",
    weather_node
)

graph.add_node(
    "calculator",
    calculator_node
)

graph.add_node(
    "general",
    general_response_node
)

graph.add_node(
    "final",
    final_response_node
)
```

---

# IMPORTANT CONCEPT

Node names become:

```text
graph execution identifiers
```

These names are VERY important later.

---

# Part 11 — Define Routing

Now we define graph flow.

---

# Entry Point

```python
graph.set_entry_point("classify")
```

---

# Conditional Routing Function

```python
def route_intent(
    state: AgentState
):

    intent = state["intent"]

    if intent == "weather":

        return "weather"

    elif intent == "calculator":

        return "calculator"

    else:

        return "general"
```

---

# Add Conditional Edges

```python
graph.add_conditional_edges(
    "classify",
    route_intent,
    {
        "weather": "weather",
        "calculator": "calculator",
        "general": "general"
    }
)
```

---

# THIS Is The BIG Moment

You are now creating:

```text
runtime graph routing
```

based on:

* workflow state

This is the heart of LangGraph orchestration.

---

# Part 12 — Connect Remaining Edges

```python
graph.add_edge(
    "weather",
    "final"
)

graph.add_edge(
    "calculator",
    "final"
)

graph.add_edge(
    "general",
    "final"
)

graph.add_edge(
    "final",
    END
)
```

---

# Visual Flow

```text
classify
 ├── weather → final
 ├── calculator → final
 └── general → final
```

---

# Part 13 — Compile Graph

## graph.py

```python
app = graph.compile()
```

---

# IMPORTANT CONCEPT

Compilation converts:

```text
graph definition
```

into:

```text
runnable execution engine
```

VERY important.

---

# Part 14 — Main Entry Point

## main.py

```python
from graph import app
```

---

# Invoke Graph

```python
while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke({
        "user_input": user_input,
        "intent": "",
        "tool_result": "",
        "final_answer": "",
        "messages": []
    })

    print("\n=== FINAL STATE ===")
    print(result)

    print("\nAssistant:")
    print(result["final_answer"])
```

---

# Example Run

Input:

```text
What is the weather?
```

Execution:

```text
classify
→ weather
→ final
→ END
```

Output:

```text
Result: 30°C and rainy
```

---

# Example Run 2

Input:

```text
calculate 25 * 8
```

Execution:

```text
classify
→ calculator
→ final
→ END
```

Output:

```text
Result: 200
```

---

# Part 15 — Understanding Graph Execution

This is VERY important.

LangGraph internally does:

```text
1. Load current state
2. Execute node
3. Merge state updates
4. Determine next edge
5. Execute next node
6. Repeat until END
```

This is EXACTLY what you manually built earlier.

Now formalized.

---

# Part 16 — State Merging

Remember:

Node:

```python
return {
    "intent": "weather"
}
```

LangGraph internally merges:

```python
{
    previous_state
    +
    node_updates
}
```

This is VERY important.

Nodes usually return:

```text
partial state updates
```

NOT entire state.

---

# Part 17 — Why This Architecture Is Powerful

This graph architecture naturally supports:

```text
- branching
- retries
- loops
- approvals
- persistence
- resumability
- multi-agent systems
```

WITHOUT giant messy if/else code.

---

# Part 18 — LangGraph vs Giant Agent Loop

Without graphs:

```python
while True:

    if intent == ...
    elif ...
    elif ...
```

becomes huge and unmaintainable.

Graphs make orchestration:

* explicit
* visual
* structured
* modular

This is VERY important in production systems.

---

# Part 19 — Common Beginner Mistakes

## Mistake 1 — Mutating State Directly

Bad:

```python
state["intent"] = "weather"
return state
```

Preferred:

```python
return {
    "intent": "weather"
}
```

Let LangGraph manage merging.

---

## Mistake 2 — Overloading Nodes

Each node should represent:

* one meaningful workflow step

NOT:

* entire system logic

---

## Mistake 3 — Poor State Design

Messy state
→ messy graphs

Good state design is CRITICAL.

---

## Mistake 4 — Too Many Tiny Nodes

Not every small helper needs a graph node.

Use nodes for:

* orchestration boundaries

---

## Mistake 5 — Forgetting END

Graphs should terminate clearly.

---

# Part 20 — What You Learned

You now understand:

## Conceptually

```text
- StateGraph
- graph execution
- state merging
- conditional routing
- node orchestration
```

## Technically

```text
- add_node()
- add_edge()
- add_conditional_edges()
- set_entry_point()
- compile()
- invoke()
```

You just built your FIRST real LangGraph application.

---

# Your Exercises

## Exercise 1 — Add Time Tool

Add:

```text
current_time node
```

and route to it.

---

## Exercise 2 — Add Validation Node

After calculator:

* validate result
* then continue

---

## Exercise 3 — Add Retry Flow

If calculator fails:

* route to retry node

---

## Exercise 4 — Add Logging Node

Track execution path.

---

## Exercise 5 — Add RAG Node

Add:

```text
search_knowledge_base
```

using your sqlite-vec setup.

---

# LangGraph Session 3 Preview

Next you’ll learn:

```text
Conditional Routing and Dynamic Graph Execution
```

You will build:

* runtime branching
* retries
* loops
* fallback paths
* validation flows
* dynamic routing systems

This is where LangGraph starts feeling like:

* a real orchestration engine
* instead of just a workflow library.
