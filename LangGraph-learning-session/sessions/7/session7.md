# LangGraph Session 7 — Human-In-The-Loop (HITL) Workflows

## Goal of This Session

By the end of this session, you will understand:

```text id="hitl001"
- What Human-In-The-Loop (HITL) means
- Why enterprises require approval workflows
- Interrupt and resume execution
- Pauseable graphs
- Human review systems
- Approval/rejection flows
- Risk-based orchestration
- Durable execution with checkpoints
```

This session is one of the MOST important enterprise AI topics.

Many production AI systems are actually:

```text id="hitl002"
AI-assisted workflows
```

NOT:

```text id="hitl003"
fully autonomous agents
```

---

# Part 1 — Why Human-In-The-Loop Exists

Suppose your AI agent can:

```text id="hitl004"
- send emails
- approve payments
- modify databases
- deploy code
- delete files
```

Would you allow:

```text id="hitl005"
LLM → Production Database
```

directly?

Usually:

```text id="hitl006"
NO
```

---

# Enterprise Reality

Most companies prefer:

```text id="hitl007"
LLM
 ↓
Recommendation
 ↓
Human Approval
 ↓
Execution
```

This dramatically reduces:

* risk
* compliance concerns
* accidental damage

---

# Part 2 — Examples Of HITL Systems

Common enterprise workflows:

```text id="hitl008"
AI generates deployment plan
↓
Engineer approves
↓
Deployment executes
```

---

```text id="hitl009"
AI drafts customer reply
↓
Support agent reviews
↓
Email sent
```

---

```text id="hitl010"
AI recommends access removal
↓
System owner approves
↓
Access revoked
```

---

# IMPORTANT INSIGHT

Many successful AI systems are:

```text id="hitl011"
co-pilot systems
```

NOT:

* autonomous systems.

---

# Part 3 — LangGraph Is Excellent For HITL

Why?

Because LangGraph supports:

```text id="hitl012"
- persistence
- checkpointing
- pausing
- resuming
- state management
```

exactly what HITL workflows require.

---

# Part 4 — What We Will Build

We will build:

```text id="hitl013"
START
 ↓
generate_action
 ↓
approval_required
 ↓
HUMAN REVIEW
 ├── approve → execute_action
 └── reject → reject_action
 ↓
END
```

This pattern appears everywhere in enterprise AI.

---

# Part 5 — Project Structure

```text id="hitl014"
langgraph_session7/
├── main.py
├── graph.py
├── nodes.py
├── state.py
├── prompts.py
├── checkpointer.py
├── requirements.txt
└── .env
```

---

# Install Dependencies

```bash id="hitl015"
pip install \
langgraph \
langgraph-checkpoint-sqlite \
openai \
python-dotenv
```

---

# Part 6 — State Design

## state.py

```python id="hitl016"
from typing import TypedDict


class AgentState(TypedDict):

    user_request: str

    proposed_action: str

    approval_status: str

    final_result: str
```

---

# IMPORTANT CONCEPT

State now contains:

```text id="hitl017"
business workflow status
```

not just:

* conversation data.

---

# Part 7 — OpenAI Setup

## nodes.py

```python id="hitl018"
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

# Part 8 — Action Generation Prompt

## prompts.py

```python id="hitl019"
ACTION_PROMPT = """
You are an enterprise assistant.

Generate a proposed action
for the user's request.

Keep it concise.
"""
```

---

# Part 9 — Generate Action Node

## nodes.py

```python id="hitl020"
from prompts import ACTION_PROMPT
```

---

# generate_action_node

```python id="hitl021"
def generate_action_node(
    state: AgentState
):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": ACTION_PROMPT
            },
            {
                "role": "user",
                "content": state["user_request"]
            }
        ]
    )

    proposed_action = (
        response
        .choices[0]
        .message
        .content
    )

    return {
        "proposed_action":
            proposed_action
    }
```

---

# Example

Input:

```text id="hitl022"
Remove access for John
```

Output:

```text id="hitl023"
Proposed Action:
Remove John's system access.
```

---

# Part 10 — Why We Do NOT Execute Immediately

Bad:

```text id="hitl024"
AI
↓
Delete User
```

Good:

```text id="hitl025"
AI
↓
Recommend Delete User
↓
Human Approval
↓
Delete User
```

Huge difference.

---

# Part 11 — Approval Node

This is where HITL begins.

## nodes.py

```python id="hitl026"
def approval_node(
    state: AgentState
):

    print(
        "\n=== APPROVAL REQUIRED ==="
    )

    print(
        state["proposed_action"]
    )

    decision = input(
        "\nApprove? "
        "(approve/reject): "
    )

    return {
        "approval_status":
            decision
    }
```

---

# IMPORTANT NOTE

This is a simplified version.

Later we'll use:

* interrupts
* checkpointing
* external approval systems

instead of terminal input.

---

# Part 12 — Execute Action Node

## nodes.py

```python id="hitl027"
def execute_action_node(
    state: AgentState
):

    return {
        "final_result":
            f"Executed: "
            f"{state['proposed_action']}"
    }
```

---

# Part 13 — Reject Node

## nodes.py

```python id="hitl028"
def reject_action_node(
    state: AgentState
):

    return {
        "final_result":
            "Action rejected."
    }
```

---

# Part 14 — Build Graph

## graph.py

```python id="hitl029"
from langgraph.graph import (
    StateGraph,
    END
)

from state import AgentState

from nodes import (
    generate_action_node,
    approval_node,
    execute_action_node,
    reject_action_node
)
```

---

# Create Graph

```python id="hitl030"
graph = StateGraph(
    AgentState
)
```

---

# Add Nodes

```python id="hitl031"
graph.add_node(
    "generate_action",
    generate_action_node
)

graph.add_node(
    "approval",
    approval_node
)

graph.add_node(
    "execute",
    execute_action_node
)

graph.add_node(
    "reject",
    reject_action_node
)
```

---

# Part 15 — Entry Point

```python id="hitl032"
graph.set_entry_point(
    "generate_action"
)
```

---

# Connect Action → Approval

```python id="hitl033"
graph.add_edge(
    "generate_action",
    "approval"
)
```

---

# Part 16 — Approval Routing

## graph.py

```python id="hitl034"
def approval_router(
    state: AgentState
):

    if (
        state["approval_status"]
        == "approve"
    ):

        return "execute"

    return "reject"
```

---

# Conditional Edges

```python id="hitl035"
graph.add_conditional_edges(
    "approval",
    approval_router,
    {
        "execute": "execute",
        "reject": "reject"
    }
)
```

---

# End Nodes

```python id="hitl036"
graph.add_edge(
    "execute",
    END
)

graph.add_edge(
    "reject",
    END
)
```

---

# Compile Graph

```python id="hitl037"
app = graph.compile()
```

---

# Part 17 — Main Entry Point

## main.py

```python id="hitl038"
from graph import app


user_request = input(
    "Request: "
)

result = app.invoke({
    "user_request":
        user_request,
    "proposed_action": "",
    "approval_status": "",
    "final_result": ""
})

print(
    "\nFinal Result:"
)

print(
    result["final_result"]
)
```

---

# Example Execution

```text id="hitl039"
Request:
Remove John's access

AI:
Proposed Action:
Remove John's access

Approve?
approve

Result:
Executed:
Remove John's access
```

---

# Part 18 — Why This Is Not Yet Production

This implementation blocks:

```python id="hitl040"
input()
```

inside the workflow.

Production systems do NOT do this.

Instead:

```text id="hitl041"
pause
save checkpoint
wait for approval
resume later
```

This is where LangGraph interrupts become important.

---

# Part 19 — Real Production Architecture

Production version:

```text id="hitl042"
START
 ↓
Generate Action
 ↓
Pause Workflow
 ↓
Save Checkpoint
 ↓
Send Approval Request
 ↓
Manager Clicks Approve
 ↓
Resume Workflow
 ↓
Execute
 ↓
END
```

VERY important pattern.

---

# Part 20 — Why Checkpointing Matters

Suppose approval comes:

```text id="hitl043"
8 hours later
```

Without persistence:

```text id="hitl044"
workflow lost
```

With LangGraph checkpoints:

```text id="hitl045"
workflow resumes
```

exactly where it stopped.

---

# Part 21 — Risk-Based Routing

Not all actions need approval.

Example:

```text id="hitl046"
Low Risk:
- summarize document
- answer FAQ

High Risk:
- delete user
- deploy code
- send email
```

You can build:

```text id="hitl047"
risk scoring nodes
```

before approval.

---

# Example

```text id="hitl048"
risk_assessment
 ├── low → execute
 └── high → approval
```

This is very common.

---

# Part 22 — Multi-Level Approval

Large companies often require:

```text id="hitl049"
Level 1 Approval
↓
Level 2 Approval
↓
Execution
```

LangGraph handles this naturally.

---

# Example Graph

```text id="hitl050"
Generate
↓
Manager Approval
↓
Security Approval
↓
Execute
```

Very common enterprise pattern.

---

# Part 23 — AI Confidence Routing

Another useful pattern:

```text id="hitl051"
confidence > 90%
→ auto approve

confidence < 90%
→ human review
```

This creates:

* scalable automation
* controlled risk

---

# Part 24 — Enterprise Reality

Most successful AI systems today are:

```text id="hitl052"
AI recommendations
+
Human approvals
```

NOT:

```text id="hitl053"
fully autonomous agents
```

Very important lesson.

---

# Part 25 — Common Beginner Mistakes

## Mistake 1

Trying to fully automate everything.

Usually unnecessary.

---

## Mistake 2

No approval path.

Dangerous for:

* finance
* HR
* security
* deployments

---

## Mistake 3

No persistence.

Approval workflows often take:

* hours
* days

---

## Mistake 4

Mixing approval and execution.

Keep them separate.

---

## Mistake 5

Approving based only on AI confidence.

Business risk matters too.

---

# Part 26 — What You Learned

You now understand:

## Conceptually

```text id="hitl054"
- Human-In-The-Loop systems
- approval workflows
- pause/resume architecture
- risk-based routing
- enterprise AI patterns
```

## Technically

```text id="hitl055"
- approval nodes
- conditional approval routing
- review workflows
- execution gating
```

You have now built:

* your first HITL LangGraph workflow.

---

# Your Exercises

## Exercise 1 — Add Risk Scoring

Classify:

```text id="hitl056"
low
medium
high
```

risk before approval.

---

## Exercise 2 — Auto Approve Low Risk

Only:

* medium/high risk

require approval.

---

## Exercise 3 — Multi-Level Approval

Add:

```text id="hitl057"
manager approval
security approval
```

before execution.

---

## Exercise 4 — Store Approval History

Track:

* approver
* timestamp
* decision

inside state.

---

## Exercise 5 — Integrate SQLite Checkpoints

Pause:

* save workflow

Resume:

* continue after approval.

---

# LangGraph Session 8 Preview

Next you'll learn:

```text id="hitl058"
Error Handling, Validation, Guardrails and Retries
```

You will build:

* validation nodes
* retry loops
* fallback strategies
* schema validation
* tool safety
* production guardrails

This is where LangGraph starts becoming:

* production-ready enterprise infrastructure.
