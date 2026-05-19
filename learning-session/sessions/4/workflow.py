from planner import create_plan
from executor import execute_step
from memory import load_workflow_state, save_workflow_state

from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

workflow_state = load_workflow_state()

MAX_RETRIES = 3

def require_approval(step):
    if step["tool"] != "calculator":
        return True

    print("\nCalculator step requires approval.")
    print(f"Action: {step['action']}")
    print(f"Arguments: {step['arguments']}")

    approval = input("Allow calculator execution? (yes/no): ")
    return approval.lower() == "yes"

def log_workflow(event, data):
    log_entry = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        "data": data
    }

    workflow_state["logs"].append(log_entry)
    save_workflow_state(workflow_state)
    print(f"[{log_entry['time']}] {event}: {data}")

def apply_conditional_routing(step, result):
    if step["tool"] != "get_weather":
        return None

    if not result["success"]:
        return None

    weather_result = result["result"].lower()
    if "rainy" not in weather_result:
        return None

    branch_result = {
        "success": True,
        "result": "Weather is rainy. Suggest bringing an umbrella."
    }

    log_workflow("conditional_route", {
        "condition": "weather contains rainy",
        "result": branch_result
    })

    return {
        "step": {
            "step_number": f"{step['step_number']}.1",
            "action": "Suggest umbrella because weather is rainy",
            "tool": "conditional_route",
            "arguments": {}
        },
        "attempts": 1,
        "execution_result": branch_result
    }

def run_workflow(user_input):
    workflow_start = datetime.now()
    log_workflow("workflow_started", {"user_input": user_input})

    plan = create_plan(user_input)

    print("\n=== GENERATED PLAN ===")
    print(plan)

    results = []

    for step in plan["steps"]:

        workflow_state["current_step"] = step["step_number"]
        save_workflow_state(workflow_state)
        print(f"\nExecuting Step {step['step_number']}")
        print(step["action"])
        step_start = datetime.now()
        log_workflow("step_started", step)

        if not require_approval(step):
            result = {
                "success": False,
                "error": "User denied approval"
            }
            log_workflow("step_error", result)
            results.append({
                "step": step,
                "attempts": 0,
                "execution_result": result
            })
            continue

        result = None

        for attempt in range(1, MAX_RETRIES + 1):
            result = execute_step(step)

            if result["success"]:
                break

            print(f"Step failed. Retry {attempt}/{MAX_RETRIES}")

        step_duration = (datetime.now() - step_start).total_seconds()
        if result and not result["success"]:
            log_workflow("step_error", result)
        elif result:
            workflow_state["completed_steps"].append(step["step_number"])
            workflow_state["tool_outputs"][step["step_number"]] = result["result"]
            save_workflow_state(workflow_state)

        log_workflow("step_finished", {
            "step_number": step["step_number"],
            "attempts": attempt,
            "duration_seconds": step_duration,
            "result": result
        })

        results.append({
            "step": step,
            "attempts": attempt,
            "execution_result": result
        })

        branch_result = apply_conditional_routing(step, result)
        if branch_result:
            results.append(branch_result)

    workflow_duration = (datetime.now() - workflow_start).total_seconds()
    log_workflow("workflow_finished", {
        "duration_seconds": workflow_duration
    })

    final_answer = generate_final_response(
        user_input,
        results
    )

    return final_answer

def generate_final_response(user_input, workflow_results):

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
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
