# Copyright (c) Microsoft. All rights reserved.

"""Tests for budget analyst agent factory."""

from unittest.mock import Mock

from agent_framework import HostedCodeInterpreterTool

from spec_to_agents.agents.budget_analyst import create_agent


def test_create_agent_without_request_user_input(setup_di_container):
    """Test that budget analyst agent is created without request_user_input tool."""
    # Arrange
    container = setup_di_container
    mock_client = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Override client provider with mock
    container.client.override(mock_client)

    # Act
    agent = create_agent()

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    # Verify that the first element in tools list is of type HostedCodeInterpreterTool
    assert len(call_kwargs["tools"]) == 1
    assert isinstance(call_kwargs["tools"][0], HostedCodeInterpreterTool)


def test_create_agent_signature_has_no_request_user_input_parameter():
    """
    Test that create_agent function signature uses DI pattern.

    The function should use @inject decorator and have all parameters
    with default Provide[] values for dependency injection.
    """
    import inspect

    sig = inspect.signature(create_agent)
    params = list(sig.parameters.keys())

    # Should have DI-injected parameters
    assert "client" in params
    assert "global_tools" in params
    assert "model_config" in params
    # Should NOT have request_user_input parameter
    assert "request_user_input" not in params
