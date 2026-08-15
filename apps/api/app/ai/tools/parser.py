import json

from app.core.exceptions import ToolException


def parse_tool_call_arguments(
    arguments: str,
):
    try:
        return json.loads(arguments)
    except json.JSONDecodeError as e:
        raise ToolException(f"Failed to parse tool call arguments: {e}") from e
