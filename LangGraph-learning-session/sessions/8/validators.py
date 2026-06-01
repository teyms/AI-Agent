ALLOWED_TOOLS = {
    "calculator",
    "get_current_time"
}


def validate_tool_name(
    tool_name
):
    return (
        tool_name
        in ALLOWED_TOOLS
    )


def validate_tool_output(
    tool_output
):
    if not tool_output:
        return False

    if str(tool_output).startswith(
        "Calculator failed"
    ):
        return False

    return True


def score_answer_quality(
    tool_output
):
    if not validate_tool_output(
        tool_output
    ):
        return 0.0

    output = str(tool_output)

    if len(output.strip()) < 2:
        return 0.4

    return 0.9


def estimate_tokens(
    text
):
    return max(
        1,
        len(str(text).split())
    )


def validate_permission(
    user_input,
    tool_name
):
    text = str(user_input).lower()

    restricted_terms = [
        "delete",
        "admin",
        "password",
        "secret",
        "permission"
    ]

    if any(term in text for term in restricted_terms):
        return False

    return validate_tool_name(tool_name)





