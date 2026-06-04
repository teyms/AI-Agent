from graph import app


user_input = input("User: ")

result = app.invoke({
    "user_input": user_input,
    "selected_agent": "",
    "worker_result": "",
    "rag_result": "",
    "risk_result": "",
    "research_result": "",
    "summary_result": "",
    "worker_quality_score": 0.0,
    "routing_accuracy_score": 0.0,
    "review_result": "",
    "final_answer": ""
})

print("\nFinal Answer:")
print(result["final_answer"])

print("\nEvaluation:")
print("Worker quality:", result["worker_quality_score"])
print("Routing accuracy:", result["routing_accuracy_score"])
