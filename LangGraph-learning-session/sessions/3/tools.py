def calculator(expression):

    try:
        if expression == "bad":
            raise Exception(
                "Simulated failure"
            )
        return str(eval(expression))
    
    except Exception as e:
        return f"ERROR: {str(e)}"

# def calculator(expression):
#     try:
#         return str(eval(expression))

#     except Exception as e:
#         return f"Calculation failed: {str(e)}"
    