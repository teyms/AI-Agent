# Session 1 — What Actually Happens Inside an AI Agent

## Goal of This Session

By the end of this session, you should deeply understand:

```text
User Input
→ Prompt Construction
→ LLM Call
→ Structured Output
→ Tool Decision
→ Tool Execution
→ Observation
→ Next Decision
→ Final Response
```

This is the core of almost ALL AI agents.

---

# Part 1 — The Most Important Mental Model

## An LLM Is NOT An Agent

An LLM alone is just:

```text
Next-token prediction engine
```

Input:

```text
"What's the weather in Singapore?"
```

Output:

```text
A statistically likely continuation of text.
```

It does NOT:

* truly reason like humans
* remember permanently
* access APIs automatically
* know current data automatically
* execute code automatically

---

## Then What Is An Agent?

An agent is:

```text
LLM
+ Tools
+ Memory
+ Decision Loop
+ Orchestration
```

The orchestration layer is the REAL engineering.

---

# Core Agent Loop

This is the heart of almost every agent system:

```text
1. Observe input
2. Think/decide
3. Use tool if needed
4. Observe result
5. Decide again
6. Repeat until done
```

Visually:

```text
User
 ↓
LLM decides
 ↓
Tool call?
 ├── No → Final answer
 └── Yes
        ↓
     Execute tool
        ↓
     Feed result back
        ↓
     LLM decides again
```

This loop is EVERYTHING.

---

# Part 2 — Your First Non-Agent LLM Program

Before agents, understand plain LLM calls.

Create a folder:

```text
ai-agent-learning/
```

Inside:

```text
main.py
.env
requirements.txt
```

---

# Install Dependencies

```bash
pip install openai python-dotenv
```

---

# requirements.txt

```text
openai
python-dotenv
```

---

# .env

```text
OPENAI_API_KEY=your_key_here
```

---

# Your First LLM Call

## main.py

```python
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Explain what an AI agent is in 2 sentences."
        }
    ]
)

print(response.choices[0].message.content)
```

---

# Understand What Just Happened

You sent:

```text
messages[]
```

This is the ENTIRE conversation context.

The model itself is stateless.

VERY important.

---

# The Roles

## System Role

Controls behavior.

Example:

```text
"You are a strict JSON generator."
```

or

```text
"You are a cybersecurity expert."
```

---

## User Role

The actual user request.

---

## Assistant Role

Previous assistant responses.

Used to maintain conversation continuity.

---

# CRITICAL CONCEPT

# The LLM Has No Memory

Every request is independent.

You resend the conversation EVERY time.

Example:

```text
Request #1
→ send messages

Request #2
→ resend ALL previous messages
```

That is how “memory” works initially.

---

# Part 3 — Structured Outputs (VERY Important)

Most production agents should NOT return free text.

Instead:

## BAD

```text
"Yeah I think maybe this is a calendar request"
```

## GOOD

```json
{
  "intent": "calendar",
  "needs_tool": true,
  "priority": "high"
}
```

Why?

Because machines can reliably process structure.

---

# Your First Structured Output Program

Replace your code with:

```python
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": """
You are an intent classifier.

Return ONLY valid JSON.

Schema:
{
    "intent": string,
    "needs_tool": boolean,
    "reason": string
}
"""
        },
        {
            "role": "user",
            "content": "Schedule a meeting with John tomorrow at 3pm"
        }
    ]
)

content = response.choices[0].message.content

print(content)

parsed = json.loads(content)

print(parsed["intent"])
```

---

# Why This Matters

This is the foundation of:

* workflows
* routing
* tool selection
* orchestration
* agents

---

# Part 4 — The First Tool-Calling Mental Model

Now imagine:

User says:

```text
"What's the weather in Singapore?"
```

The LLM itself does NOT know live weather.

So what should happen?

---

# The Correct Architecture

```text
User asks weather
 ↓
LLM decides:
"I need weather tool"
 ↓
Your code calls weather API
 ↓
Tool result returned
 ↓
LLM generates final response
```

This is tool orchestration.

---

# IMPORTANT DISTINCTION

The LLM NEVER directly executes tools.

YOUR CODE executes tools.

This is one of the most important concepts in AI engineering.

---

# Real Tool Flow

```text
LLM output:
{
  "tool": "weather",
  "arguments": {
      "location": "Singapore"
  }
}
```

Then:

```python
result = get_weather("Singapore")
```

Then:

```text
Feed result back into LLM
```

---

# THIS Is The Secret

AI agents are mostly:

```text
LLM-generated control flow
```

NOT magic intelligence.

---

# Your First Exercise (VERY Important)

Build a simple intent classifier.

## Requirements

Input:

```text
"Send an email to John"
```

Expected JSON:

```json
{
  "intent": "email",
  "needs_tool": true,
  "tool_name": "send_email"
}
```

Support intents:

* email
* calendar
* research
* coding
* unknown

---

# Rules

1. Use structured JSON output
2. Parse JSON in Python
3. Print parsed result cleanly
4. Handle invalid JSON safely using try/except

---

# Your Goal

You are NOT building “AI magic.”

You are building:

```text
Reliable orchestration systems
powered by LLM reasoning
```

That mindset is extremely important.

---

# Next Session Preview

## Session 2 — Building Your First REAL Tool-Calling Agent

You’ll learn:

* manual tool orchestration
* tool registry
* retries
* validation
* agent loop
* observation/action cycle

which is the TRUE core of agent engineering.
