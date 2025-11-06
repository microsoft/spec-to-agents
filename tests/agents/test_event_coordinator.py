# Copyright (c) Microsoft. All rights reserved.

"""Tests for event coordinator agent."""

from unittest.mock import Mock

from spec_to_agents.agents import event_coordinator
from spec_to_agents.models.messages import SpecialistOutput


def test_agent_returns_specialist_output() -> None:
    """Event coordinator should be created with SpecialistOutput response_format."""
    # Arrange
    mock_client = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = event_coordinator.create_agent(mock_client)

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs

    # Verify response_format IS set to SpecialistOutput (coordinator makes routing decisions)
    assert call_kwargs.get("response_format") == SpecialistOutput, (
        "Event coordinator should have response_format=SpecialistOutput. "
        "Coordinator analyzes specialist output and returns routing decisions."
    )

    # Verify store=False for stateless conversation management
    assert call_kwargs.get("store") is False, "Coordinator should use stateless calls (store=False)"


def test_agent_uses_specialist_output_format() -> None:
    """Event coordinator module should use SpecialistOutput as response_format."""
    import inspect

    # Get the source code of the event_coordinator module
    source = inspect.getsource(event_coordinator)

    # Check that SpecialistOutput is used as response_format
    assert "response_format=SpecialistOutput" in source, (
        "Event coordinator should use SpecialistOutput as response_format"
    )
