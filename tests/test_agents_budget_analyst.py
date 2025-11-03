# Copyright (c) Microsoft. All rights reserved.

"""Tests for budget analyst agent factory."""

from unittest.mock import Mock

from agent_framework import HostedCodeInterpreterTool

from spec_to_agents.agents.budget_analyst import create_agent


def test_create_agent_without_request_user_input() -> None:
    """Test that budget analyst agent is created without request_user_input tool."""
    # Arrange
    mock_client = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent
    mock_global_tools: dict[str, Mock] = {}

    # Act
    agent = create_agent(client=mock_client, global_tools=mock_global_tools)  # type: ignore[arg-type]

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    # Verify that the first element in tools list is of type HostedCodeInterpreterTool
    assert len(call_kwargs["tools"]) == 1
    assert isinstance(call_kwargs["tools"][0], HostedCodeInterpreterTool)


def test_create_agent_signature_has_no_request_user_input_parameter() -> None:
    """Test that create_agent function signature uses DI parameters."""
    import inspect

    sig = inspect.signature(create_agent)
    params = list(sig.parameters.keys())

    assert "client" in params
    assert "global_tools" in params
    assert "request_user_input" not in params
    assert len(params) == 2
