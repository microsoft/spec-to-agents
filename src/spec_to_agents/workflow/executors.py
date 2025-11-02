# Copyright (c) Microsoft. All rights reserved.

"""Utility functions for event planning workflow."""

import json
from typing import Any

from agent_framework import (
    ChatMessage,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
)


def convert_tool_content_to_text(messages: list[ChatMessage]) -> list[ChatMessage]:
    """
    Convert tool calls and results to text summaries for cross-agent communication.

    When passing conversation history between agents with different service thread IDs,
    tool calls and results must be converted to text to avoid thread ID validation errors
    in Azure AI Agent Client. This preserves the context of what tools were used and their
    outcomes while making the messages compatible with a different agent's thread.

    Parameters
    ----------
    messages : list[ChatMessage]
        Original messages that may contain FunctionCallContent and FunctionResultContent

    Returns
    -------
    list[ChatMessage]
        New messages with tool content converted to TextContent summaries

    Notes
    -----
    This addresses the error: "No thread ID was provided, but chat messages includes tool results."
    Tool calls and results are inherently tied to the service thread where they were executed.
    When routing between agents in a workflow, each agent has its own thread ID, so we must
    convert tool-related content to plain text to avoid thread ID conflicts.
    """
    converted_messages: list[ChatMessage] = []
    for message in messages:
        new_contents: list[Any] = []
        for content in message.contents:
            if isinstance(content, FunctionCallContent):
                # Convert function call to descriptive text
                if isinstance(content.arguments, dict):
                    args_str = json.dumps(content.arguments)
                else:
                    args_str = str(content.arguments)
                text_repr = f"[Tool Call: {content.name}({args_str})]"
                new_contents.append(TextContent(text=text_repr))
            elif isinstance(content, FunctionResultContent):
                # Convert function result to descriptive text
                if content.result is not None:
                    result_str = content.result if isinstance(content.result, str) else json.dumps(content.result)
                    text_repr = f"[Tool Result for call {content.call_id}: {result_str}]"
                elif content.exception is not None:
                    text_repr = f"[Tool Error for call {content.call_id}: {content.exception}]"
                else:
                    text_repr = f"[Tool Result for call {content.call_id}: No result]"
                new_contents.append(TextContent(text=text_repr))
            else:
                # Keep other content types as-is (TextContent, ImageContent, etc.)
                new_contents.append(content)

        # Create new message with converted contents, preserving role and metadata
        converted_messages.append(
            ChatMessage(
                role=message.role,
                contents=new_contents,
                author_name=message.author_name,
                message_id=message.message_id,
            )
        )
    return converted_messages
