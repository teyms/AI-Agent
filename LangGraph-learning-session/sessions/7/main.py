from graph import app

thread_id = "approval_user_123"

config = {
    "configurable": {
        "thread_id": thread_id
    }
}


user_request = input(
    "Request: "
)

result = app.invoke(
    {
        "user_request":
            user_request,
        "proposed_action": "",
        "risk_level": "",
        "approval_status": "",
        "manager_approval_status": "",
        "security_approval_status": "",
        "approval_history": [],
        "final_result": ""
    },
    config=config
)

print(
    "\nFinal Result:"
)

print(
    result["final_result"]
)

print(
    f"\nCheckpoint saved for thread_id: {thread_id}"
)







