from tools import (
    calculator,
    currency_conversion,
    current_time,
    get_weather,
    search_notes,
)

TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "current_time": current_time,
    "currency_conversion": currency_conversion,
    "search_notes": search_notes,
}

def execute_step(step):

    tool_name = step["tool"]
    arguments = step["arguments"]

    if tool_name not in TOOLS:
        return {
            "success": False,
            "error": "Tool not found"
        }

    try:

        result = TOOLS[tool_name](**arguments)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
