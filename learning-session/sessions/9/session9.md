# Session 9 — State Machines and Graph-Based Agent Architecture

## Goal of This Session

By the end of this session, you will understand:

```text id="graph001"
- What state machines are
- Why workflows become graphs
- Nodes and edges
- Transitions
- Stateful orchestration
- Conditional routing
- Durable workflows
- Resumable execution
- Graph execution engines
- Why LangGraph exists
```

This is the FINAL foundational session before learning:

LangGraph

This session is EXTREMELY important.

You are about to transition from:

```text id="graph002"
AI application builder
→
AI orchestration engineer
```

---

# Part 1 — Why Simple Workflows Eventually Break

Your previous workflow system looked like:

```text id="graph003"
Step A
→ Step B
→ Step C
```

This works for simple flows.

But real systems quickly become:

```text id="graph004"
If condition A:
    do X

Else:
    do Y

Retry if failed

Pause for approval

Resume later

Loop until success
```

Now workflows become:

```text id="graph005"
non-linear
```

This is where graphs become necessary.

---

# Part 2 — What Is A State Machine?

A state machine is:

```text id="graph006"
A system that:
- exists in a state
- transitions between states
- based on events or conditions
```

---

# Example — ATM Machine

```text id="graph007"
Idle
↓
Card Inserted
↓
PIN Verification
├── Correct → Transaction
└── Wrong → Error
```

This is a state machine.

---

# IMPORTANT CONCEPT

AI agents are fundamentally:

```text id="graph008"
stateful orchestration systems
```

NOT just chatbots.

This is VERY important.

---

# Part 3 — AI Agent State Machine

Example:

```text id="graph009"
START
↓
Classify Intent
├── Research Request
│    ↓
│   Retrieve Docs
│    ↓
│   Generate Answer
│
├── Tool Request
│    ↓
│   Execute Tool
│    ↓
│   Validate Output
│
└── Unknown
     ↓
   Ask Clarification
```

This is MUCH closer to real production AI.

---

# Part 4 — Nodes and Edges

Graphs consist of:

---

# Nodes

Nodes represent:

```text id="graph010"
units of execution
```

Examples:

* retrieve docs
* execute tool
* validate result
* summarize answer

---

# Edges

Edges represent:

```text id="graph011"
transitions between nodes
```

Example:

```text id="graph012"
If retrieval successful
→ continue

Else
→ retry
```

---

# IMPORTANT MENTAL MODEL

```text id="graph013"
Node = work
Edge = decision
```

This is foundational for LangGraph.

---

# Part 5 — Basic Graph Visualization

Simple graph:

```text id="graph014"
START
 ↓
Intent Classifier
 ├── Research → Retrieval Node
 ├── Tool Use → Tool Node
 └── Unknown → Clarification Node
```

---

# More Advanced Graph

```text id="graph015"
START
 ↓
Planner
 ↓
Execute Step
 ↓
Validation
 ├── Success → Next Step
 ├── Retry → Execute Step
 └── Fail → Human Approval
```

This is REAL orchestration thinking.

---

# Part 6 — Why Graphs Matter

Linear workflows break when systems require:

```text id="graph016"
- retries
- loops
- branching
- parallel execution
- approvals
- resumability
- dynamic routing
```

Graphs solve this naturally.

---

# Part 7 — Project Structure

```text id="graph017"
session9/
├── main.py
├── graph_engine.py
├── nodes.py
├── edges.py
├── state.py
├── tools.py
├── agent.py
├── requirements.txt
└── .env
```

---

# Part 8 — Workflow State Object

## state.py

```python id="graph018"
class AgentState:

    def __init__(self):

        self.user_input = ""

        self.current_node = "START"

        self.messages = []

        self.tool_results = []

        self.retries = 0

        self.final_answer = None

        self.completed = False
```

---

# IMPORTANT CONCEPT

The ENTIRE workflow operates on:

```text id="graph019"
shared mutable state
```

This becomes VERY important.

Modern orchestration systems are mostly:

```text id="graph020"
state transition systems
```

---

# Part 9 — Node Functions

Nodes are just functions.

## nodes.py

```python id="graph021"
def classify_intent_node(state):

    user_input = state.user_input

    if "weather" in user_input:

        state.current_node = "WEATHER_TOOL"

    elif "calculate" in user_input:

        state.current_node = "CALCULATOR_TOOL"

    else:

        state.current_node = "FINAL_RESPONSE"

    return state
```

---

# IMPORTANT LESSON

Nodes:

* read state
* modify state
* decide next transition

VERY important.

---

# Weather Node

## nodes.py

```python id="graph022"
from tools import get_weather
```

---

# Weather Tool Node

```python id="graph023"
def weather_tool_node(state):

    result = get_weather("Singapore")

    state.tool_results.append(result)

    state.current_node = "FINAL_RESPONSE"

    return state
```

---

# Final Response Node

```python id="graph024"
def final_response_node(state):

    if state.tool_results:

        state.final_answer = (
            f"Tool result: "
            f"{state.tool_results[-1]}"
        )

    else:

        state.final_answer = (
            "No tool used."
        )

    state.completed = True

    return state
```

---

# Part 10 — Graph Engine

THIS is the most important part.

## graph_engine.py

```python id="graph025"
from nodes import (
    classify_intent_node,
    weather_tool_node,
    final_response_node
)
```

---

# Node Registry

```python id="graph026"
NODES = {
    "START": classify_intent_node,
    "WEATHER_TOOL": weather_tool_node,
    "FINAL_RESPONSE": final_response_node
}
```

---

# Graph Runner

```python id="graph027"
def run_graph(state):

    max_iterations = 20

    iterations = 0

    while not state.completed:

        iterations += 1

        if iterations > max_iterations:

            raise Exception(
                "Graph exceeded max iterations"
            )

        current_node = state.current_node

        print(
            f"\nExecuting Node:"
            f" {current_node}"
        )

        node_function = NODES[current_node]

        state = node_function(state)

    return state
```

---

# THIS Is The Core Insight

You just built:

```text id="graph028"
stateful graph execution
```

This is the HEART of LangGraph-style systems.

---

# Part 11 — Conditional Routing

Routing is graph orchestration.

Example:

```text id="graph029"
If tool failed:
→ Retry Node

Else:
→ Continue
```

---

# Retry Example

## nodes.py

```python id="graph030"
def validation_node(state):

    last_result = state.tool_results[-1]

    if "failed" in last_result.lower():

        if state.retries < 3:

            state.retries += 1

            state.current_node = "WEATHER_TOOL"

        else:

            state.current_node = "HUMAN_APPROVAL"

    else:

        state.current_node = "FINAL_RESPONSE"

    return state
```

---

# IMPORTANT CONCEPT

Graph edges are usually:

```text id="graph031"
condition-based transitions
```

This is EXACTLY what LangGraph automates later.

---

# Part 12 — Human Approval Nodes

Enterprise systems often pause workflows.

Example:

```text id="graph032"
Approval required
```

---

# Approval Flow

```text id="graph033"
Execute Action
↓
Need Approval?
├── YES → Human Approval Node
└── NO → Continue
```

Very common production pattern.

---

# Example Approval Node

## nodes.py

```python id="graph034"
def human_approval_node(state):

    approval = input(
        "Approve action? (yes/no): "
    )

    if approval == "yes":

        state.current_node = "FINAL_RESPONSE"

    else:

        state.final_answer = (
            "Action rejected."
        )

        state.completed = True

    return state
```

---

# Part 13 — Durable Workflows

What if server crashes mid-workflow?

Without persistence:

```text id="graph035"
workflow lost
```

Bad.

---

# Durable Architecture

```text id="graph036"
Save state after every node
```

Very important.

---

# Persist State

## graph_engine.py

```python id="graph037"
import json
```

---

# Save Function

```python id="graph038"
def save_state(state):

    with open(
        "workflow_state.json",
        "w"
    ) as f:

        json.dump(
            state.__dict__,
            f,
            indent=2
        )
```

---

# Save After Every Node

```python id="graph039"
state = node_function(state)

save_state(state)
```

---

# IMPORTANT CONCEPT

Durability is CRITICAL for:

* enterprise workflows
* long-running agents
* async orchestration

---

# Part 14 — Resumable Execution

Now you can:

```text id="graph040"
resume interrupted workflows
```

This is HUGE.

---

# Resume Example

```python id="graph041"
def load_state():

    with open(
        "workflow_state.json",
        "r"
    ) as f:

        data = json.load(f)

    state = AgentState()

    state.__dict__.update(data)

    return state
```

---

# THIS Is Enterprise Workflow Thinking

Most enterprise AI systems care heavily about:

```text id="graph042"
durability
resumability
auditability
```

NOT just “smart AI.”

---

# Part 15 — Parallel Execution

Graphs naturally support parallel branches.

Example:

```text id="graph043"
Retrieve Docs
├── Search Policies
├── Search FAQ
└── Search Tickets
```

Then merge results later.

---

# Parallelism Is Important For

```text id="graph044"
- latency reduction
- scalability
- throughput
```

Very important production topic.

---

# Part 16 — Why LangGraph Exists

You are manually building:

```text id="graph045"
- graph execution
- state management
- transitions
- retries
- persistence
- resumability
- conditional routing
```

This is EXACTLY the problem:

LangGraph

solves.

---

# IMPORTANT REALIZATION

LangGraph is NOT “AI magic.”

It is primarily:

```text id="graph046"
graph orchestration infrastructure
```

for LLM systems.

VERY important mindset.

---

# Part 17 — State Machines vs Autonomous Agents

Many beginners imagine:

```text id="graph047"
free-thinking AGI
```

Reality:

Most successful production systems are:

```text id="graph048"
constrained state machines
```

with:

* tool use
* reasoning steps
* validations
* workflows

This is MUCH more reliable.

---

# Part 18 — Enterprise AI Architecture Reality

Enterprise AI systems prioritize:

```text id="graph049"
- reliability
- auditability
- permissions
- retries
- observability
- governance
```

NOT:

* unlimited autonomy

This is extremely important.

---

# Part 19 — Common Beginner Mistakes

## Mistake 1

Thinking graphs are only for visualization.

Graphs are execution architecture.

---

## Mistake 2

No durable state.

Makes workflows fragile.

---

## Mistake 3

No iteration limits.

Infinite loops happen often.

---

## Mistake 4

No transition validation.

Bad routing causes chaos.

---

## Mistake 5

Building giant autonomous loops.

Constrained systems are usually superior.

---

# Part 20 — What You Learned

You now understand:

## Conceptually

* state machines
* graph orchestration
* nodes
* edges
* transitions
* durability
* resumability
* workflow execution

## Technically

* graph runners
* state persistence
* node registries
* conditional routing
* resumable execution
* graph-based orchestration

You now have the mental foundation required for:

LangGraph

---

# Your Exercises

## Exercise 1 — Add More Nodes

Add:

* retrieval node
* summarization node
* validation node

---

## Exercise 2 — Add Retry Branching

If tool fails:

* retry
* then escalate

---

## Exercise 3 — Add Parallel Retrieval

Run:

* multiple retrieval nodes

and merge outputs.

---

## Exercise 4 — Add Persistent SQLite State

Store workflow state in SQLite instead of JSON.

---

## Exercise 5 — Add Workflow Visualization

Print graph execution path:

```text id="graph050"
START
→ RETRIEVAL
→ VALIDATION
→ FINAL_RESPONSE
```

---

# Next Phase Preview

You are now ready for:

# LangGraph

Next you will finally learn:

```text id="graph051"
- StateGraph
- graph nodes
- graph edges
- conditional routing
- durable execution
- memory integration
- tool nodes
- persistence
- human-in-the-loop workflows
- multi-agent orchestration
```

And now:

```text id="graph052"
the abstractions will actually make sense
```

because you understand:

* the problems
* the architecture
* the tradeoffs
* the engineering realities

underneath the framework.
