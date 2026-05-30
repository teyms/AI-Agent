from graph import app


while True:

    user_input = input(
        "\nUser: "
    )

    if user_input == "exit":
        break

    result = app.invoke({
        "user_input": user_input,
        "rewritten_query": "",
        "query_was_rewritten": False,
        "messages": [],
        "retrieved_docs": [],
        "metadata_filters": {},
        "retrieval_confidence": 0,
        "retrieval_status": "",
        "citation_status": "",
        "clarification_count": 0,
        "final_answer": "",
        "needs_retrieval": False
    })

    print("\nAssistant:")
    print(result["final_answer"])
