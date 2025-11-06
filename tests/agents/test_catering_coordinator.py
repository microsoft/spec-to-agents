# Copyright (c) Microsoft. All rights reserved.

"""Tests for catering coordinator agent."""

from unittest.mock import Mock

from spec_to_agents.agents import catering_coordinator


def test_catering_coordinator_agent_created_without_response_format() -> None:
    """Catering coordinator should be created without response_format parameter."""
    # Arrange
    mock_client = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = catering_coordinator.create_agent(mock_client, mcp_tool=None)

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs

    # Verify response_format is NOT set (agent returns natural text)
    assert "response_format" not in call_kwargs, (
        "Catering coordinator should not have response_format parameter. "
        "Agent should return natural text, not SpecialistOutput."
    )

    # Verify store=True for service-managed threads
    assert call_kwargs.get("store") is True, "Agent should use service-managed threads"


def test_catering_coordinator_does_not_import_specialist_output() -> None:
    """Catering coordinator module should not use SpecialistOutput."""
    import inspect

    # Get the source code of the catering_coordinator module
    source = inspect.getsource(catering_coordinator)

    # Check that SpecialistOutput is not used as response_format
    assert "response_format=SpecialistOutput" not in source, (
        "Catering coordinator should not use SpecialistOutput as response_format"
    )
