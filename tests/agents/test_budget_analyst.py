# Copyright (c) Microsoft. All rights reserved.

"""Tests for budget analyst agent."""

from unittest.mock import Mock

from spec_to_agents.agents import budget_analyst


def test_agent_returns_specialist_output() -> None:
    """Budget analyst should be created without response_format parameter."""
    # Arrange
    mock_client = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = budget_analyst.create_agent(mock_client, mcp_tool=None)

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs

    # Verify response_format is NOT set (agent returns natural text)
    assert call_kwargs.get("response_format") is None, (
        "Budget analyst should not have response_format parameter. "
        "Agent should return natural text, not SpecialistOutput."
    )

    # Verify store=True for service-managed threads
    assert call_kwargs.get("store") is True, "Agent should use service-managed threads"


def test_agent_uses_specialist_output_format() -> None:
    """Budget analyst module should not use SpecialistOutput."""
    import inspect

    # Get the source code of the budget_analyst module
    source = inspect.getsource(budget_analyst)

    # Check that SpecialistOutput is not used as response_format
    assert "response_format=SpecialistOutput" not in source, (
        "Budget analyst should not use SpecialistOutput as response_format"
    )
