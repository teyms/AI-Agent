from graph import app


while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke({
        "user_input": user_input,
        "intent": "",
        "confidence": 0,
        "confidence_status": "",
        "response": "",
        "retry_count": 0,
        "max_retries": 2,
        "timed_out": False,
        "clarification_count": 0,
        "validation_status": "",
        "output_format_status": "",
        "permission_status": "",
        "final_validation_status": "",
        "execution_path": [],
        "failures": [],
        "validation_errors": [],
        "final_answer": ""
    })

    print("\n=== FINAL STATE ===")
    print(result)

    print("\nAssistant:")
    print(result["final_answer"])
