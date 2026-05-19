# Session 4 — Planning and Multi-Step Workflows

## Goal of This Session

By the end of this session, you will understand:

```text id="m4f2s9"
- Why simple agents fail on complex tasks
- How planning works
- Task decomposition
- Multi-step orchestration
- Workflow execution
- Intermediate validation
- Dynamic routing
- Sequential vs parallel execution
- Why production AI systems are mostly workflows
```

You will build your FIRST workflow-driven AI system.

This is where AI engineering starts becoming REAL backend/system engineering.

---

# Part 1 — Why Simple Agents Fail

Your Session 2 agent works for:

```text id="rk7g0v"
"What is the weather?"
"Calculate 25 * 8"
```

But now try:

```text id="u1r8f5"
"Research the weather in Tokyo,
compare it with Singapore,
then summarize the differences."
```

Suddenly the task requires:

```text id="4l7r8t"
1. Multiple steps
2. Planning
3. Intermediate state
4. Multiple tool calls
5. Structured execution
```

Simple “one-shot” agents break down.

---

# THIS Is The Big Industry Secret

Most production “agents” are actually:

```text id="gr88jm"
Workflow orchestration systems
with LLM-powered reasoning steps
```

NOT autonomous AGI.

This is extremely important.

---

# Part 2 — What Is Planning?

Planning means:

```text id="jlwmx1"
Break large goal
→ into smaller executable steps
```

Example:

```text id="jlwmx2"
Goal:
"Compare weather between Tokyo and Singapore"
```

Possible plan:

```text id="jlwmx3"
1. Get Tokyo weather
2. Get Singapore weather
3. Compare results
4. Generate summary
```

This is task decomposition.

---

# Part 3 — Core Workflow Architecture

```text id="jlwmx4"
User Request
 ↓
Planner
 ↓
Generate Steps
 ↓
Execute Step 1
 ↓
Store Result
 ↓
Execute Step 2
 ↓
Store Result
 ↓
Generate Final Output
```

This architecture dominates enterprise AI systems.

---

# Part 4 — Project Structure

```text id="jlwmx5"
session4/
├── main.py
├── planner.py
├── executor.py
├── workflow.py
├── tools.py
├── memory.py
├── requirements.txt
└── .env
```

---

# Part 5 — Building A Planner

## planner.py

```python id="jlwmx6"
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI()
```

---

# Planning Function

```python id="jlwmx7"
def create_plan(user_input):

    system_prompt = """
You are a workflow planner.

Break the user request into executable steps.

Available tools:
- get_weather(location)
- calculator(expression)

Return ONLY valid JSON.

Schema:
{
  "steps": [
    {
      "step_number": int,
      "action": string,
      "tool": string,
      "arguments": {}
    }
  ]
}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
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

# Example Plan Output

Input:

```text id="jlwmx8"
Compare weather between Singapore and Tokyo
```

Output:

```json id="jlwmx9"
{
  "steps": [
    {
      "step_number": 1,
      "action": "Get Singapore weather",
      "tool": "get_weather",
      "arguments": {
        "location": "Singapore"
      }
    },
    {
      "step_number": 2,
      "action": "Get Tokyo weather",
      "tool": "get_weather",
      "arguments": {
        "location": "Tokyo"
      }
    }
  ]
}
```

---

# IMPORTANT CONCEPT

The LLM is NOT executing.

It is generating:

```text id="jlwmy0"
Execution instructions
```

YOUR orchestration layer executes them.

---

# Part 6 — Workflow State

Complex workflows require state.

Example:

```text id="jlwmy1"
Current step
Completed steps
Tool outputs
Failures
Retries
```

This becomes VERY important.

---

# workflow.py

```python id="jlwmy2"
workflow_state = {
    "current_step": 0,
    "completed_steps": [],
    "tool_outputs": {}
}
```

---

# Why State Matters

Without state:

* workflows cannot resume
* retries become difficult
* debugging becomes painful

This is why frameworks like LangGraph became important later.

---

# Part 7 — Workflow Executor

## executor.py

```python id="jlwmy3"
from tools import get_weather, calculator

TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator
}
```

---

# Execute Single Step

```python id="jlwmy4"
def execute_step(step):

    tool_name = step["tool"]
    arguments = step["arguments"]

    if tool_name not in TOOLS:
        return {
            "success": False,
            "error": "Tool not found"
        }

    try:

        result = TOOLS[tool_name](**arguments)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
```

---

# IMPORTANT ENGINEERING LESSON

Notice:

```text id="jlwmy5"
Tool execution
≠
LLM reasoning
```

These are separate layers.

Good agent systems separate:

* reasoning
* orchestration
* execution

cleanly.

---

# Part 8 — Running Entire Workflow

## workflow.py

```python id="jlwmy6"
from planner import create_plan
from executor import execute_step
```

---

# Main Workflow Function

```python id="jlwmy7"
def run_workflow(user_input):

    plan = create_plan(user_input)

    print("\n=== GENERATED PLAN ===")
    print(plan)

    results = []

    for step in plan["steps"]:

        print(f"\nExecuting Step {step['step_number']}")
        print(step["action"])

        result = execute_step(step)

        results.append({
            "step": step,
            "execution_result": result
        })

    return results
```

---

# Example Execution

```text id="jlwmy8"
Executing Step 1
Get Singapore weather

Executing Step 2
Get Tokyo weather
```

---

# Part 9 — Final Synthesis

After execution:

```text id="jlwmy9"
Workflow outputs
↓
LLM synthesizes final answer
```

---

# Add Final Response Generator

## workflow.py

```python id="jlwmz0"
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
```

---

# Final Synthesis Function

```python id="jlwmz1"
def generate_final_response(user_input, workflow_results):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are a helpful assistant.

Use workflow execution results
to answer the user clearly.
"""
            },
            {
                "role": "user",
                "content": f"""
Original request:
{user_input}

Workflow results:
{workflow_results}
"""
            }
        ]
    )

    return response.choices[0].message.content
```

---

# Update Workflow Runner

```python id="jlwmz2"
def run_workflow(user_input):

    plan = create_plan(user_input)

    results = []

    for step in plan["steps"]:

        result = execute_step(step)

        results.append({
            "step": step,
            "execution_result": result
        })

    final_answer = generate_final_response(
        user_input,
        results
    )

    return final_answer
```

---

# Part 10 — THIS Is A Real Workflow System

You now built:

```text id="jlwmz3"
Planning
→ Step decomposition
→ Sequential execution
→ Intermediate state
→ Final synthesis
```

This is VERY close to real production AI architectures.

---

# Part 11 — Sequential vs Parallel Execution

Currently:

```text id="jlwmz4"
Step 1
↓
Step 2
↓
Step 3
```

Sequential.

---

# But Some Steps Can Run In Parallel

Example:

```text id="jlwmz5"
Get Singapore weather
AND
Get Tokyo weather
```

These are independent.

Parallel execution improves:

* speed
* latency
* scalability

Very important later.

---

# Parallel Concept

```text id="jlwmz6"
Planner
 ↓
Parallel Tasks
 ├── Task A
 ├── Task B
 └── Task C
 ↓
Merge Results
```

Modern AI systems heavily use this.

---

# Part 12 — Intermediate Validation

Production systems validate EACH step.

Example:

```text id="jlwmz7"
Did tool fail?
Did output match schema?
Did retrieval return empty?
```

Without validation:

* workflows become fragile

---

# Example Validation

```python id="jlwmz8"
if not result["success"]:
    print("Step failed")

    # Retry
    # Fallback
    # Human approval
    # Escalation
```

---

# Part 13 — Human-In-The-Loop

Critical production concept.

Some actions require approval.

Example:

```text id="jlwmz9"
Send email?
Delete records?
Transfer money?
Deploy code?
```

Never fully autonomous.

---

# Real Architecture

```text id="jlwn00"
Workflow
 ↓
Approval Required?
 ├── YES → Human Review
 └── NO
 ↓
Continue
```

This dominates enterprise AI systems.

---

# Part 14 — Workflow vs Agent

VERY important distinction.

---

# Workflow

Deterministic.

```text id="jlwn01"
Step A
→ Step B
→ Step C
```

Reliable.

Predictable.

Preferred in enterprise systems.

---

# Agent

Dynamic decisions.

```text id="jlwn02"
Observe
→ Decide
→ Tool
→ Observe
→ Decide again
```

Flexible.

Less predictable.

Harder to debug.

---

# MOST Production Systems Are Hybrid

Example:

```text id="jlwn03"
Workflow
└── contains small agentic steps
```

NOT:

```text id="jlwn04"
Infinite autonomous loops
```

This understanding is VERY important.

---

# Part 15 — Why LangGraph Exists

You are now manually building:

* state machines
* orchestration
* execution graphs
* workflow state
* transitions

This is EXACTLY why:

LangGraph exists.

Later it will automate:

* graph execution
* state persistence
* retries
* node routing

But now you understand the mechanics underneath.

---

# Part 16 — Common Beginner Mistakes

## Mistake 1

Trying to build fully autonomous agents too early.

Workflows are MUCH more reliable.

---

## Mistake 2

No intermediate validation.

One bad step can corrupt entire workflows.

---

## Mistake 3

No workflow state tracking.

Makes debugging extremely painful.

---

## Mistake 4

Letting LLM directly control dangerous actions.

Always gate:

* deployment
* deletion
* payments
* external writes

---

# Part 17 — What You Learned

You now understand:

## Conceptually

* planning
* decomposition
* workflows
* orchestration
* stateful execution
* sequential execution
* validation
* approvals

## Technically

* planners
* execution engines
* workflow state
* synthesis
* retries
* orchestration loops

This is foundational production AI engineering.

---

# Your Exercises

## Exercise 1 — Add More Tools

Add:

* current_time
* currency_conversion
* search_notes

---

## Exercise 2 — Add Retry Per Step

Retry failed workflow steps automatically.

---

## Exercise 3 — Add Workflow Logging

Log:

* start time
* step execution
* errors
* duration

---

## Exercise 4 — Add Approval Step

Before calculator executes:

```text id="jlwn05"
Require user confirmation
```

---

## Exercise 5 — Conditional Routing

Example:

```text id="jlwn06"
If weather is rainy
→ suggest umbrella
```

Introduce branching workflows.

---

# Session 5 Preview

Next you’ll learn:

# RAG (Retrieval-Augmented Generation)

This is one of the MOST important topics in production AI.

You will build:

```text id="jlwn07"
- document ingestion
- chunking
- embeddings
- vector search
- retrieval pipelines
- citation systems
- grounded AI responses
```

You’ll finally understand:

* how company knowledge assistants work
* why embeddings matter
* why chunking quality matters
* why most enterprise AI systems are actually RAG systems
