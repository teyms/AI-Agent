from graph import app


while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke({
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
        "tool_failed": False,
        "json_schema_valid": True,
        "tool_output_valid": True,
        "validation_error": "",
        "retry_count": 0,
        "max_tool_retries": 1,
        "iteration_count": 0,
        "max_iterations": 5,
        "fallback_reason": "",
        "node_execution_log": [],
        "tool_calls": [],
        "reasoning_traces": [],
        "final_answer": ""
    })

    print("\n=== FINAL STATE ===")
    print(result)

    print("\nAssistant:")
    print(result["final_answer"])



    
