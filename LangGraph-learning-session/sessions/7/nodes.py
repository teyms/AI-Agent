import os
from datetime import datetime
from prompts import ACTION_PROMPT
from state import AgentState

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODEL_NAME = os.getenv("LLM_MODEL")


def append_approval_history(
    state: AgentState,
    approver,
    decision
):
    return state["approval_history"] + [
        {
            "approver": approver,
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            "decision": decision,
            "risk_level": state["risk_level"]
        }
    ]

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


def risk_scoring_node(
    state: AgentState
):
    text = (
        state["user_request"]
        + " "
        + state["proposed_action"]
    ).lower()

    high_risk_terms = [
        "delete",
        "remove",
        "payment",
        "production",
        "security",
        "permission",
        "database"
    ]
    medium_risk_terms = [
        "email",
        "update",
        "change",
        "notify",
        "schedule"
    ]

    if any(term in text for term in high_risk_terms):
        risk_level = "high"
    elif any(term in text for term in medium_risk_terms):
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level
    }


def approval_node(
    state: AgentState
):
    print(
        "\n=== APPROVAL REQUIRED ==="
    )
    print(
        state["proposed_action"]
    )
    print(
        f"Risk level: {state['risk_level']}"
    )

    decision = input(
        "\nApprove? "
        "(approve/reject): "
    )

    return {
        "approval_status":
            decision,
        "approval_history": append_approval_history(
            state,
            "general",
            decision
        )
    }


def manager_approval_node(
    state: AgentState
):
    print(
        "\n=== MANAGER APPROVAL REQUIRED ==="
    )
    print(
        state["proposed_action"]
    )
    print(
        f"Risk level: {state['risk_level']}"
    )

    decision = input(
        "\nManager approve? "
        "(approve/reject): "
    )

    return {
        "manager_approval_status": decision,
        "approval_history": append_approval_history(
            state,
            "manager",
            decision
        )
    }


def security_approval_node(
    state: AgentState
):
    print(
        "\n=== SECURITY APPROVAL REQUIRED ==="
    )
    print(
        state["proposed_action"]
    )
    print(
        f"Risk level: {state['risk_level']}"
    )

    decision = input(
        "\nSecurity approve? "
        "(approve/reject): "
    )

    return {
        "security_approval_status": decision,
        "approval_history": append_approval_history(
            state,
            "security",
            decision
        )
    }

def execute_action_node(
    state: AgentState
):

    return {
        "final_result":
            f"Executed: "
            f"{state['proposed_action']}"
    }


def reject_action_node(
    state: AgentState
):

    return {
        "final_result":
            "Action rejected."
    }


