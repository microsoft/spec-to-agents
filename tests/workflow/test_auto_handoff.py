# Copyright (c) Microsoft. All rights reserved.

"""Tests for AutoHandoffBuilder with automatic coordinator creation."""

from unittest.mock import MagicMock, Mock

import pytest
from agent_framework import AgentProtocol

from spec_to_agents.workflow.auto_handoff import AutoHandoffBuilder


def create_mock_agent(name: str, description: str = "") -> AgentProtocol:
    """Create a mock agent that implements AgentProtocol."""
    mock_agent = Mock(spec=AgentProtocol)
    mock_agent.name = name
    mock_agent.description = description
    return mock_agent


class TestAutoHandoffBuilder:
    """Test AutoHandoffBuilder auto-coordinator feature."""

    def test_auto_creates_coordinator_when_not_set(self) -> None:
        """Test that AutoHandoffBuilder auto-creates coordinator if not explicitly set."""
        # Mock client
        mock_client = MagicMock()
        mock_coordinator = create_mock_agent("event_planning_coordinator")
        mock_client.create_agent.return_value = mock_coordinator

        # Mock participant agents
        venue_agent = create_mock_agent("venue", "Finds event venues")
        budget_agent = create_mock_agent("budget", "Analyzes budgets")

        # Build workflow without calling .set_coordinator()
        builder = AutoHandoffBuilder(
            name="Event Planning",
            participants=[venue_agent, budget_agent],
            client=mock_client,
        )

        # Should not raise - coordinator created automatically
        builder.build()

        # Verify coordinator agent was created
        mock_client.create_agent.assert_called_once()
        call_kwargs = mock_client.create_agent.call_args[1]

        # Check instructions contain participant descriptions
        assert "venue" in call_kwargs["instructions"]
        assert "budget" in call_kwargs["instructions"]
        assert "Finds event venues" in call_kwargs["instructions"]
        assert "Analyzes budgets" in call_kwargs["instructions"]

    def test_requires_client_for_auto_coordinator(self) -> None:
        """Test that AutoHandoffBuilder requires client if coordinator not set."""
        venue_agent = create_mock_agent("venue")

        builder = AutoHandoffBuilder(
            name="Test",
            participants=[venue_agent],
            # No client provided
        )

        with pytest.raises(ValueError, match="requires 'client' parameter"):
            builder.build()

    def test_manual_coordinator_still_works(self) -> None:
        """Test that explicit .set_coordinator() still works (HandoffBuilder behavior)."""
        coordinator = create_mock_agent("coordinator")
        venue_agent = create_mock_agent("venue")

        # Explicitly set coordinator (should NOT auto-create)
        # No client needed when using explicit coordinator
        builder = AutoHandoffBuilder(
            participants=[coordinator, venue_agent],
        ).set_coordinator("coordinator")

        builder.build()

        # Should build successfully without client

    def test_custom_coordinator_name(self) -> None:
        """Test custom coordinator_name parameter."""
        mock_client = MagicMock()
        mock_coordinator = create_mock_agent("custom_coordinator")
        mock_client.create_agent.return_value = mock_coordinator

        venue_agent = create_mock_agent("venue")

        builder = AutoHandoffBuilder(
            participants=[venue_agent],
            client=mock_client,
            coordinator_name="Custom Coordinator",
        )

        builder.build()

        # Verify custom name used
        call_kwargs = mock_client.create_agent.call_args[1]
        assert "Custom Coordinator" in call_kwargs["instructions"]
