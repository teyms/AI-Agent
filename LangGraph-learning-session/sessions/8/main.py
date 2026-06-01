from graph import app


user_input = input("User: ")

result = app.invoke({
    "user_input": user_input,
    "proposed_tool": "",
    "tool_input": "",
    "validation_status": "",
    "retry_count": 0,
    "token_count": 0,
    "max_tokens": 500,
    "cost_guardrail_status": "",
    "permission_status": "",
    "tool_output": "",
    "output_validation_status": "",
    "confidence_score": 0.0,
    "confidence_status": "",
    "secondary_validation_status": "",
    "secondary_validation_reason": "",
    "final_answer": "",
    "error_message": ""
})

print("\nFinal Answer:")
print(result["final_answer"])
