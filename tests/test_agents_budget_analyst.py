# Copyright (c) Microsoft. All rights reserved.

"""Tests for budget analyst agent factory."""

from unittest.mock import Mock

from spec_to_agents.agents.budget_analyst import create_agent


def test_create_agent_without_request_user_input():
    """Test that budget analyst agent is created without request_user_input tool."""
    # Arrange
    mock_client = Mock()
    mock_code_interpreter = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = create_agent(mock_client, mock_code_interpreter, mcp_tool=None)

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    # Verify tools list only contains code_interpreter, not request_user_input
    assert call_kwargs["tools"] == [mock_code_interpreter]
    assert len(call_kwargs["tools"]) == 1


def test_create_agent_signature_has_no_request_user_input_parameter():
    """Test that create_agent function signature doesn't include request_user_input."""
    import inspect

    sig = inspect.signature(create_agent)
    params = list(sig.parameters.keys())

    assert "client" in params
    assert "code_interpreter" in params
    assert "mcp_tool" in params
    assert "request_user_input" not in params
    assert len(params) == 3
