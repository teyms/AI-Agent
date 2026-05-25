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
        "tool_result": "",
        "final_answer": "",
        "messages": []
    })

    print("\n=== FINAL STATE ===")
    print(result)

    print("\nAssistant:")
    print(result["final_answer"])