def calculator(expression):
    try:
        return str(eval(expression))

    except Exception as e:
        raise Exception(
            f"Calculator failed: {str(e)}"
        )
    
from datetime import datetime
def get_current_time():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


TOOLS = {
    "calculator": calculator,
    "get_current_time": get_current_time
}


