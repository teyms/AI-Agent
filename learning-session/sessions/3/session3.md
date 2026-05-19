# Session 3 — Memory and Conversation State

## Goal of This Session

By the end of this session, you will understand:

```text id="wfsxv6"
- How conversational memory actually works
- Why LLMs are stateless
- How agents maintain context
- Short-term vs long-term memory
- Context windows and token limits
- Conversation history management
- Summarization memory
- Basic persistent memory systems
```

You will build your FIRST memory-enabled agent.

This is where your agents start becoming MUCH more realistic.

---

# Part 1 — The Most Important Truth About Memory

## LLMs Have NO Native Memory

This is critical.

The model itself does NOT remember:

* previous requests
* previous conversations
* your name
* tool outputs
* earlier decisions

EVERY request is independent.

---

# Then Why Does ChatGPT “Remember”?

Because the system:

```text id="jod5c6"
Stores conversation history
↓
Resends relevant context
↓
To the LLM every request
```

The “memory” is engineered OUTSIDE the model.

---

# Core Memory Architecture

```text id="qk9wzo"
User Message
 ↓
Load Conversation History
 ↓
Construct messages[]
 ↓
Send to LLM
 ↓
Get Response
 ↓
Store New Messages
```

This is how most conversational AI works.

---

# Part 2 — Types of Memory

# 1. Short-Term Memory

Conversation history.

Example:

```text id="b14r62"
User:
"My name is Tey"

Later:
"What is my name?"
```

The model only knows because:

* previous messages are resent

---

# 2. Long-Term Memory

Persistent facts stored separately.

Example:

```text id="5j0t1p"
User profile:
- prefers Python
- works in backend engineering
- interested in AI agents
```

Usually stored in:

* database
* vector DB
* profile store

---

# 3. Working Memory

Temporary task state.

Example:

```text id="s8m5h7"
Research progress
Current workflow step
Partial tool outputs
Retry state
```

Very important for agents.

---

# Part 3 — Why Context Windows Matter

LLMs have token limits.

Example:

| Model               | Approx Context      |
| ------------------- | ------------------- |
| Small models        | smaller context     |
| Modern large models | much larger context |

If conversation becomes too large:

```text id="xx2qvn"
Older messages get truncated
```

Then the model “forgets.”

---

# IMPORTANT CONCEPT

Memory is NOT infinite.

Context is expensive.

You must engineer memory carefully.

---

# Part 4 — Your First Conversation Memory System

## Project Structure

```text id="39rwnm"
session3/
├── main.py
├── memory.py
├── agent.py
├── tools.py
├── requirements.txt
└── .env
```

---

# Part 5 — Building Message History

## memory.py

```python id="q52vc7"
conversation_history = []
```

Simple but important.

This is your first memory store.

---

# Add Helper Functions

```python id="8v5kxe"
def add_message(role, content):

    conversation_history.append({
        "role": role,
        "content": content
    })


def get_messages():
    return conversation_history


def clear_memory():
    conversation_history.clear()
```

---

# CRITICAL UNDERSTANDING

This memory exists in YOUR application.

NOT inside the LLM.

---

# Part 6 — Updating Agent To Use Memory

## agent.py

```python id="yy6q90"
from openai import OpenAI
from dotenv import load_dotenv
from memory import add_message, get_messages

load_dotenv()

client = OpenAI()
```

---

# Build Conversational Agent

```python id="mctthh"
def chat(user_input):

    add_message("user", user_input)

    messages = [
        {
            "role": "system",
            "content": """
You are a helpful assistant.
Use conversation history naturally.
"""
        }
    ]

    messages.extend(get_messages())

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
    )

    assistant_reply = response.choices[0].message.content

    add_message("assistant", assistant_reply)

    return assistant_reply
```

---

# main.py

```python id="5n6ymz"
from agent import chat

while True:

    user_input = input("\nUser: ")

    if user_input.lower() == "exit":
        break

    response = chat(user_input)

    print("\nAssistant:")
    print(response)
```

---

# Test Memory

Example:

```text id="ckoltr"
User:
My favorite language is Python

User:
What is my favorite language?
```

Now the assistant can answer correctly.

Why?

Because:

* conversation history was resent

NOT because the model remembered.

---

# Part 7 — Visualizing What Actually Happens

Second request internally becomes:

```text id="rduv1w"
[
  system message,
  user: "My favorite language is Python",
  assistant: "...",
  user: "What is my favorite language?"
]
```

The entire history is resent.

---

# THIS Is Conversation Memory

Most beginners misunderstand this.

Now you understand the real mechanism.

---

# Part 8 — Problem: Infinite History Growth

Your current memory system has a major issue.

Conversation grows forever:

```text id="2xw3tm"
More messages
→ More tokens
→ Higher cost
→ Slower requests
→ Eventually exceeds context limit
```

This becomes a MAJOR engineering challenge.

---

# Part 9 — Sliding Window Memory

Simplest solution:

Only keep recent messages.

---

# memory.py

```python id="tuvx91"
MAX_MESSAGES = 10


def add_message(role, content):

    conversation_history.append({
        "role": role,
        "content": content
    })

    if len(conversation_history) > MAX_MESSAGES:
        conversation_history.pop(0)
```

---

# This Creates

```text id="wejlwm"
Short-term memory
```

Very common in production systems.

---

# Tradeoff

## Pros

* cheap
* simple
* fast

## Cons

* forgets older context

---

# Part 10 — Summarization Memory

More advanced systems summarize old conversations.

Instead of:

```text id="dz1jxq"
100 old messages
```

Store:

```text id="njlwm1"
Conversation summary
```

Example:

```text id="mbyvx9"
"User prefers Python and is learning AI agents."
```

This is MUCH cheaper.

---

# Basic Summarization Example

## memory.py

```python id="5r7u6t"
conversation_summary = ""
```

---

# Add Summary Function

```python id="m4mq0k"
def update_summary(summary_text):

    global conversation_summary

    conversation_summary = summary_text


def get_summary():
    return conversation_summary
```

---

# Then Your Prompt Becomes

```text id="m9p1o3"
System Prompt
+
Conversation Summary
+
Recent Messages
```

This is a VERY common production pattern.

---

# Part 11 — Long-Term Memory

Now imagine:

```text id="v0tlfd"
Remember user preferences forever
```

Example:

* preferred language
* timezone
* favorite frameworks
* writing style

These are usually stored in:

* SQL DB
* Redis
* vector DB
* profile service

---

# Example Long-Term Memory Structure

```python id="8o1jgx"
user_profile = {
    "name": "Tey",
    "preferred_language": "Python",
    "learning_goal": "AI agents"
}
```

---

# Long-Term Memory Architecture

```text id="8yrk1s"
User Input
 ↓
Load User Profile
 ↓
Load Recent Conversation
 ↓
Build Prompt
 ↓
LLM Response
```

---

# Part 12 — Important Production Reality

More memory is NOT always better.

Too much irrelevant memory causes:

* distraction
* hallucinations
* slower responses
* higher cost

Good memory systems retrieve:

```text id="a2sv9v"
Relevant memory
NOT all memory
```

This becomes important later in RAG systems.

---

# Part 13 — Memory vs RAG

Many beginners confuse these.

---

# Memory

About:

* user
* conversation
* ongoing tasks

Example:

```text id="jqnhmr"
User likes Python
```

---

# RAG

About:

* external knowledge
* documents
* files
* company data

Example:

```text id="i0lv4d"
Retrieve company handbook
```

Different purposes.

---

# Part 14 — Real Agent Memory Architecture

Production systems often use:

```text id="mjlwmf"
Short-Term Memory
+
Summaries
+
Long-Term User Profile
+
RAG Knowledge Retrieval
```

combined together.

---

# Part 15 — Add Memory To Your Tool Agent

Update your Session 2 agent.

Now the agent should remember:

```text id="8qk40f"
- previous tool outputs
- user preferences
- earlier conversation
```

This makes the agent MUCH more realistic.

---

# Example

```text id="4dxjlwm"
User:
"My city is Singapore"

Later:
"What is the weather today?"
```

The agent should infer:

```text id="f3gx2d"
location = Singapore
```

WITHOUT user repeating it.

This is where memory becomes powerful.

---

# Part 16 — Common Beginner Mistakes

## Mistake 1

Thinking memory is “inside” the model.

Wrong.

Memory is external orchestration.

---

## Mistake 2

Sending entire conversation forever.

Leads to:

* massive costs
* poor performance
* context overflow

---

## Mistake 3

Treating all memory equally.

Most memory is irrelevant noise.

---

## Mistake 4

No memory expiration.

Some memory should expire:

* temporary workflows
* old preferences
* outdated tasks

---

# Part 17 — What You Learned

You now understand:

## Conceptually

* LLMs are stateless
* memory is engineered externally
* context windows are limited
* memory systems require design tradeoffs

## Technically

* message history
* short-term memory
* sliding windows
* summaries
* long-term profiles
* context assembly

This is foundational AI engineering knowledge.

---

# Your Exercises

## Exercise 1 — Persistent File Memory

Save conversation history to:

```text id="jlwmq0"
memory.json
```

and reload it when app restarts.

---

## Exercise 2 — User Profile Memory

Store:

```python id="jlwmt1"
favorite_language
city
learning_goal
```

and inject into prompts.

---

## Exercise 3 — Auto-Summarization

When conversation exceeds:

* 10 messages

generate summary automatically.

---

## Exercise 4 — Memory Reset Command

Add:

```text id="jlwmu2"
/reset
```

to clear conversation memory.

---

# Session 4 Preview

Next you’ll learn:

# Planning and Multi-Step Workflows

This is where agents become MUCH more powerful.

You will build systems that can:

```text id="jlwmv3"
- break tasks into steps
- plan execution
- chain multiple tools
- validate intermediate results
- retry failed steps
- execute workflows dynamically
```

You’ll finally understand:

* why simple agents fail on complex tasks
* why planning matters
* why workflows dominate production AI systems
* how orchestration engines actually work
