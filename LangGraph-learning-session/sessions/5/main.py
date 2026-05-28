from graph import app
from checkpointer import cleanup_old_checkpoints
from user_profiles import (
    get_user_profile,
    save_user_profile
)

current_thread_id = "user_123"
RETENTION_DAYS = 7

cleanup_old_checkpoints(RETENTION_DAYS)


def get_config():
    return {
        "configurable": {
            "thread_id": current_thread_id
        }
    }


def build_initial_state(
    user_input,
    user_profile
):
    return {
        "user_input": user_input,
        "messages": [
            {
                "role": "user",
                "content": user_input
            }
        ],
        "current_tool": "",
        "tool_input": "",
        "tool_output": "",
        "user_profile": user_profile,
        "final_answer": "",
        "iteration_count": 0
    }


def resume_latest_checkpoint():
    config = get_config()
    snapshot = app.get_state(config)

    if not snapshot.values:
        print("\nNo checkpoint found.")
        return

    state = dict(snapshot.values)

    if state.get("final_answer"):
        print("\nCheckpoint already completed.")
        print(state["final_answer"])
        return

    result = app.invoke(
        state,
        config=config
    )

    print("\nResumed Assistant:")
    print(result["final_answer"])


def inspect_checkpoint():
    config = get_config()
    snapshot = app.get_state(config)

    if not snapshot.values:
        print("\nNo checkpoint found.")
        return

    state = dict(snapshot.values)
    messages = state.get("messages", [])

    print("\n=== CHECKPOINT STATE ===")
    print(f"thread_id: {current_thread_id}")
    print(f"user_input: {state.get('user_input', '')}")
    print(f"current_tool: {state.get('current_tool', '')}")
    print(f"tool_output: {state.get('tool_output', '')}")
    print(f"final_answer: {state.get('final_answer', '')}")
    print(f"iteration_count: {state.get('iteration_count', 0)}")

    print("\n=== STORED MESSAGES ===")
    for index, message in enumerate(messages, start=1):
        role = message.get("role", "")
        content = message.get("content", "")
        print(f"{index}. {role}: {content}")

    print("\n=== CHECKPOINT HISTORY ===")
    for index, item in enumerate(
        app.get_state_history(config),
        start=1
    ):
        print(
            f"{index}. next={item.next} "
            f"tasks={len(item.tasks)}"
        )

        if index >= 5:
            break


def cleanup_checkpoints_command(user_input):
    parts = user_input.split()
    retention_days = RETENTION_DAYS

    if len(parts) == 2:
        retention_days = int(parts[1])

    deleted_count = cleanup_old_checkpoints(
        retention_days
    )
    print(
        f"\nDeleted {deleted_count} expired checkpoints "
        f"older than {retention_days} days."
    )

while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    if user_input == "/whoami":
        print(f"\nCurrent user: {current_thread_id}")
        continue

    if user_input.startswith("/user "):
        current_thread_id = user_input[len("/user "):].strip()

        if not current_thread_id:
            print("\nUse: /user thread_id")
            current_thread_id = "user_123"
            continue

        print(f"\nSwitched to user: {current_thread_id}")
        continue

    if user_input == "/resume":
        resume_latest_checkpoint()
        continue

    if user_input == "/checkpoint":
        inspect_checkpoint()
        continue

    if user_input.startswith("/cleanup-checkpoints"):
        cleanup_checkpoints_command(user_input)
        continue

    if user_input.startswith("/profile "):
        parts = user_input[len("/profile "):].split("|")

        if len(parts) != 3:
            print(
                "\nUse: /profile language|city|timezone"
            )
            continue

        save_user_profile(
            current_thread_id,
            parts[0].strip(),
            parts[1].strip(),
            parts[2].strip()
        )
        print("\nProfile saved.")
        continue

    user_profile = get_user_profile(
        current_thread_id
    )

    if user_input.startswith("/crash "):
        crash_input = user_input[len("/crash "):].strip()
        state = build_initial_state(
            crash_input,
            user_profile
        )
        app.update_state(
            get_config(),
            state
        )
        print(
            "\nSimulated crash. Restart the app, "
            "then run /resume."
        )
        continue

    result = app.invoke(
        build_initial_state(
            user_input,
            user_profile
        ),
        config=get_config()
    )

    print("\nAssistant:")
    print(result["final_answer"])

