# Session 2 — Building Your First REAL Tool-Calling Agent

## Goal of This Session

By the end of this session, you will understand:

```text id="fsl3kl"
How an agent:
- decides to use tools
- executes tools
- observes tool results
- loops until task completion
- handles failures safely
```

You will build your FIRST real manual agent without frameworks.

This is one of the most important milestones in AI agent engineering.

---

# What You Will Build

A simple workflow assistant agent that can:

* answer simple questions
* use tools when needed
* decide which tool to call
* process tool results
* retry when tool fails
* return final answers

Example:

```text id="ztv7wa"
User:
"What is the weather in Singapore?"
```

Flow:

```text id="f36m5m"
LLM decides:
"I need weather tool"

↓

Python executes weather tool

↓

Tool result:
"30°C, rainy"

↓

LLM generates final response
```

This is REAL agent behavior.

---

# Part 1 — Architecture Overview

Your architecture:

```text id="t5j4q0"
User
 ↓
LLM Decision
 ↓
Tool Needed?
 ├── No → Final Answer
 └── Yes
        ↓
     Execute Tool
        ↓
     Return Tool Result
        ↓
     LLM Observes Result
        ↓
     Final Answer
```

This loop is the foundation of most production AI systems.

---

# Part 2 — Project Structure

Create:

```text id="vwf8so"
ai-agent-learning/
└── session2/
    ├── main.py
    ├── tools.py
    ├── agent.py
    ├── requirements.txt
    └── .env
```

---

# Install Dependencies

```bash id="e7sgx3"
pip install openai python-dotenv
```

---

# requirements.txt

```text id="i4d2uc"
openai
python-dotenv
```

---

# .env

```text id="72zjlwm"
OPENAI_API_KEY=your_key_here
```

---

# Part 3 — Creating Your First Tools

## tools.py

```python id="rr6m3o"
def get_weather(location: str):
    fake_weather_data = {
        "singapore": "30°C, rainy",
        "tokyo": "18°C, cloudy",
        "london": "10°C, windy"
    }

    return fake_weather_data.get(
        location.lower(),
        "Weather data not found."
    )


def calculator(expression: str):
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"
```

---

# IMPORTANT LESSON

These are NOT AI tools.

They are NORMAL Python functions.

The AI only decides:

* WHEN to use them
* WHICH tool to use
* WHAT arguments to pass

YOUR CODE executes them.

This distinction is critical.

---

# Part 4 — Building Tool Registry

## Why Tool Registry Matters

As agents grow:

```text id="w5z16x"
You cannot hardcode:
if tool == weather
if tool == calculator
if tool == ...
```

Instead:

```text id="ywbvbq"
tool_name
→ lookup tool
→ execute dynamically
```

This becomes scalable.

---

# agent.py

```python id="3j0st1"
from tools import get_weather, calculator

TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator
}
```

---

# Part 5 — First Agent Decision Prompt

We will NOT use automatic tool calling yet.

We want to understand the mechanics manually.

---

# agent.py

```python id="c4x4fu"
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI()
```

---

# Create Decision Function

```python id="4kzsz5"
def decide_tool(user_input: str):

    system_prompt = """
You are an AI agent.

Decide whether a tool is needed.

Available tools:
1. get_weather(location)
2. calculator(expression)

Return ONLY valid JSON.

Schema:
{
    "needs_tool": boolean,
    "tool_name": string,
    "tool_arguments": {
        "key": "value"
    },
    "final_answer": string
}

Rules:
- If no tool needed, set final_answer.
- If tool needed, final_answer should be empty.
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

# IMPORTANT CONCEPT

The LLM is acting like:

```text id="4qfnhq"
Reasoning engine
+
Workflow router
```

NOT tool executor.

---

# Part 6 — Executing Tools

Add this to:

## agent.py

```python id="u95c1u"
def execute_tool(tool_name, tool_arguments):

    if tool_name not in TOOLS:
        return "Tool not found."

    tool_function = TOOLS[tool_name]

    try:
        return tool_function(**tool_arguments)

    except Exception as e:
        return f"Tool execution error: {str(e)}"
```

---

# CRITICAL LESSON

This is where:

* permissions
* security
* validation
* retries
* rate limiting

eventually happen.

This layer becomes VERY important in production systems.

---

# Part 7 — Observation Loop

Now we build the real orchestration flow.

---

# agent.py

```python id="x4pf2u"
def run_agent(user_input: str):

    decision = decide_tool(user_input)

    print("\n=== AGENT DECISION ===")
    print(decision)

    if not decision["needs_tool"]:
        return decision["final_answer"]

    tool_result = execute_tool(
        decision["tool_name"],
        decision["tool_arguments"]
    )

    print("\n=== TOOL RESULT ===")
    print(tool_result)

    final_response = generate_final_response(
        user_input,
        tool_result
    )

    return final_response
```

---

# Part 8 — Generating Final Response

The agent now:

* observed user input
* used tool
* observed tool output

Now it synthesizes the final answer.

---

# agent.py

```python id="z4lrdu"
def generate_final_response(user_input, tool_result):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are a helpful assistant.

Use the tool result to answer the user.
"""
            },
            {
                "role": "user",
                "content": f"""
User request:
{user_input}

Tool result:
{tool_result}
"""
            }
        ]
    )

    return response.choices[0].message.content
```

---

# Part 9 — Main Entry Point

## main.py

```python id="vcd0yl"
from agent import run_agent

while True:

    user_input = input("\nUser: ")

    if user_input.lower() == "exit":
        break

    result = run_agent(user_input)

    print("\nAgent:")
    print(result)
```

---

# Example Runs

## Example 1

Input:

```text id="kcc0yc"
What is the weather in Singapore?
```

Output flow:

```text id="dcnoy9"
=== AGENT DECISION ===
{
  "needs_tool": true,
  "tool_name": "get_weather",
  "tool_arguments": {
      "location": "Singapore"
  }
}

=== TOOL RESULT ===
30°C, rainy

Agent:
The current weather in Singapore is 30°C and rainy.
```

---

## Example 2

Input:

```text id="2v6wt5"
What is 25 * 88?
```

Output:

```text id="q1gqyz"
=== AGENT DECISION ===
{
  "needs_tool": true,
  "tool_name": "calculator",
  "tool_arguments": {
      "expression": "25 * 88"
  }
}
```

---

# Part 10 — THIS Is The Agent Loop

You just manually built:

```text id="shs1qg"
Observe
→ Decide
→ Act
→ Observe
→ Respond
```

This is the CORE of AI agents.

Frameworks later automate this.

But now you understand the underlying mechanics.

---

# Part 11 — Add Retry Logic (VERY Important)

Production systems MUST handle failures.

Example:

```python id="wq4gjr"
def execute_tool(tool_name, tool_arguments):

    if tool_name not in TOOLS:
        return "Tool not found."

    tool_function = TOOLS[tool_name]

    max_retries = 3

    for attempt in range(max_retries):

        try:
            return tool_function(**tool_arguments)

        except Exception as e:

            print(f"Retry {attempt+1}")

            if attempt == max_retries - 1:
                return f"Tool execution failed: {str(e)}"
```

---

# Why Retry Logic Matters

Real systems fail because of:

* network errors
* API timeouts
* rate limits
* temporary outages

Agents MUST be resilient.

---

# Part 12 — Security Warning (VERY Important)

This code:

```python id="8np5k4"
eval(expression)
```

is dangerous in production.

Never expose unrestricted eval to users.

Later you’ll learn:

* sandboxing
* restricted execution
* permission systems
* tool validation

Security becomes EXTREMELY important in agent engineering.

---

# Part 13 — What You Learned

You now understand:

## Conceptually

* LLM != agent
* tools are external functions
* orchestration is the real engineering
* agent loops drive behavior

## Technically

* structured outputs
* tool routing
* tool execution
* observation loop
* retries
* orchestration flow

This is HUGE progress.

---

# Common Beginner Mistakes

## Mistake 1

Thinking the LLM executes tools itself.

Wrong.

YOUR code executes tools.

---

## Mistake 2

Trusting LLM outputs blindly.

Always validate:

* tool names
* arguments
* JSON schema

---

## Mistake 3

Building autonomous systems too early.

Reliable workflows are MUCH more valuable.

---

# Your Exercises

## Exercise 1 — Add New Tool

Add:

```python id="3nck18"
get_current_time(city)
```

---

## Exercise 2 — Add Joke Tool

```python id="zl9x08"
tell_joke(category)
```

---

## Exercise 3 — Tool Validation

Prevent unknown tools from executing.

---

## Exercise 4 — Better JSON Safety

Handle:

* invalid JSON
* missing keys
* malformed responses

---

# Session 3 Preview

Next you’ll learn:

# Memory and Conversation State

You will build:

```text id="k1uh8u"
Persistent conversation memory
Short-term memory
Message history
Context management
Token-awareness
```

This is where agents start becoming MUCH more realistic.

You’ll finally understand:

* how ChatGPT “remembers”
* why context windows matter
* why long conversations fail
* how memory systems are engineered
