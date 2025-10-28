# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import Mock

from agent_framework import FunctionCallContent

from spec2agent.workflow.executors import HumanInLoopAgentExecutor


def test_extract_user_request_detects_tool_call():
    """Test that _extract_user_request finds request_user_input tool calls."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Create mock AgentExecutorResponse with tool call
    mock_response = Mock()
    mock_message = Mock()

    # Create FunctionCallContent for request_user_input
    tool_call = Mock(spec=FunctionCallContent)
    tool_call.name = "request_user_input"
    tool_call.arguments = json.dumps({
        "prompt": "Which venue?",
        "context": {"venues": ["A", "B"]},
        "request_type": "selection",
    })

    mock_message.contents = [tool_call]
    mock_response.agent_run_response.messages = [mock_message]

    # Extract should find the tool call
    result = executor._extract_user_request(mock_response)

    assert result is not None
    assert result["prompt"] == "Which venue?"
    assert result["context"] == {"venues": ["A", "B"]}
    assert result["request_type"] == "selection"


def test_extract_user_request_returns_none_when_no_tool_call():
    """Test that _extract_user_request returns None when no tool call present."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Create mock response with no tool calls
    mock_response = Mock()
    mock_message = Mock()
    mock_message.contents = []  # No tool calls
    mock_response.agent_run_response.messages = [mock_message]

    result = executor._extract_user_request(mock_response)

    assert result is None


def test_extract_user_request_ignores_other_tools():
    """Test that _extract_user_request ignores non-request_user_input tools."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    mock_response = Mock()
    mock_message = Mock()

    # Create tool call for different tool
    other_tool = Mock(spec=FunctionCallContent)
    other_tool.name = "some_other_tool"
    other_tool.arguments = json.dumps({"arg": "value"})

    mock_message.contents = [other_tool]
    mock_response.agent_run_response.messages = [mock_message]

    result = executor._extract_user_request(mock_response)

    assert result is None
