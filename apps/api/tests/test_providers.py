from types import SimpleNamespace

from app.ai.llm.providers.anthropic import (
    parse_anthropic_content,
    to_anthropic_payload,
    to_anthropic_tools,
)
from app.ai.llm.providers.openai import OpenAIProvider
from app.ai.llm.providers.openai_compat import parse_openai_chat_message
from app.ai.type import AIMessage


def test_openai_provider_class_name_matches_gateway_import():
    assert OpenAIProvider.__name__ == "OpenAIProvider"


def test_parse_openai_chat_message_includes_tool_calls():
    message = SimpleNamespace(
        role="assistant",
        content=None,
        tool_calls=[
            SimpleNamespace(
                id="call_1",
                function=SimpleNamespace(
                    name="calculator",
                    arguments='{"expression": "1+1"}',
                ),
            )
        ],
    )

    result = parse_openai_chat_message(message)

    assert result.tool_calls == [
        {
            "id": "call_1",
            "function": {
                "name": "calculator",
                "arguments": '{"expression": "1+1"}',
            },
        }
    ]


def test_to_anthropic_tools_maps_openai_schema():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "math",
                "parameters": {
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
            },
        }
    ]

    converted = to_anthropic_tools(tools)

    assert converted == [
        {
            "name": "calculator",
            "description": "math",
            "input_schema": tools[0]["function"]["parameters"],
        }
    ]


def test_to_anthropic_payload_splits_system_and_merges_tool_results():
    system, messages = to_anthropic_payload(
        [
            AIMessage(role="system", content="you are helpful"),
            AIMessage(role="user", content="1+1"),
            AIMessage(
                role="assistant",
                content=None,
                tool_calls=[
                    {
                        "id": "call_1",
                        "function": {
                            "name": "calculator",
                            "arguments": '{"expression": "1+1"}',
                        },
                    }
                ],
            ),
            AIMessage(role="tool", tool_call_id="call_1", content="2"),
        ]
    )

    assert system == "you are helpful"
    assert messages[0] == {"role": "user", "content": "1+1"}
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"][0]["type"] == "tool_use"
    assert messages[1]["content"][0]["input"] == {"expression": "1+1"}
    assert messages[2] == {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "call_1",
                "content": "2",
            }
        ],
    }


def test_parse_anthropic_content_reads_tool_use_blocks():
    result = parse_anthropic_content(
        [
            {"type": "text", "text": "let me calc"},
            {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "calculator",
                "input": {"expression": "12*7+5"},
            },
        ]
    )

    assert result.content == "let me calc"
    assert result.tool_calls[0]["id"] == "toolu_1"
    assert result.tool_calls[0]["function"]["name"] == "calculator"
    assert '"expression": "12*7+5"' in result.tool_calls[0]["function"]["arguments"]
