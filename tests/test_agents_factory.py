# Copyright (c) Microsoft. All rights reserved.

"""Tests for centralized agent factory."""

from unittest.mock import Mock

from spec_to_agents.agents.factory import (
    create_budget_analyst_agent,
    create_catering_coordinator_agent,
    create_event_coordinator_agent,
    create_logistics_manager_agent,
    create_venue_specialist_agent,
)


def test_create_event_coordinator_agent():
    """Test that event coordinator agent is created correctly."""
    mock_client = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    agent = create_event_coordinator_agent(mock_client)

    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["name"] == "EventCoordinator"
    assert call_kwargs["store"] is True
    assert "instructions" in call_kwargs


def test_create_venue_specialist_agent():
    """Test that venue specialist agent is created with web search."""
    mock_client = Mock()
    mock_web_search = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    agent = create_venue_specialist_agent(mock_client, mock_web_search, mcp_tool=None)

    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["name"] == "VenueSpecialist"
    assert call_kwargs["tools"] == [mock_web_search]
    assert call_kwargs["store"] is True
    assert "response_format" in call_kwargs


def test_create_budget_analyst_agent():
    """Test that budget analyst agent is created with code interpreter."""
    mock_client = Mock()
    mock_code_interpreter = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    agent = create_budget_analyst_agent(mock_client, mock_code_interpreter, mcp_tool=None)

    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["name"] == "BudgetAnalyst"
    assert call_kwargs["tools"] == [mock_code_interpreter]
    assert call_kwargs["store"] is True
    assert "response_format" in call_kwargs


def test_create_catering_coordinator_agent():
    """Test that catering coordinator agent is created with web search."""
    mock_client = Mock()
    mock_web_search = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    agent = create_catering_coordinator_agent(mock_client, mock_web_search, mcp_tool=None)

    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["name"] == "CateringCoordinator"
    assert call_kwargs["tools"] == [mock_web_search]
    assert call_kwargs["store"] is True
    assert "response_format" in call_kwargs


def test_create_logistics_manager_agent():
    """Test that logistics manager agent is created with calendar and weather tools."""
    mock_client = Mock()
    mock_weather = Mock()
    mock_create_cal = Mock()
    mock_list_cal = Mock()
    mock_delete_cal = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    agent = create_logistics_manager_agent(
        mock_client, mock_weather, mock_create_cal, mock_list_cal, mock_delete_cal, mcp_tool=None
    )

    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["name"] == "LogisticsManager"
    assert call_kwargs["tools"] == [mock_weather, mock_create_cal, mock_list_cal, mock_delete_cal]
    assert call_kwargs["store"] is True
    assert "response_format" in call_kwargs


def test_agents_with_mcp_tool():
    """Test that agents include MCP tool when provided."""
    mock_client = Mock()
    mock_web_search = Mock()
    mock_mcp = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    agent = create_venue_specialist_agent(mock_client, mock_web_search, mcp_tool=mock_mcp)

    assert agent == mock_agent
    call_kwargs = mock_client.create_agent.call_args.kwargs
    # MCP tool should be appended to tools list
    assert len(call_kwargs["tools"]) == 2
    assert call_kwargs["tools"][0] == mock_web_search
    assert call_kwargs["tools"][1] == mock_mcp


def test_backward_compatibility_with_individual_modules():
    """Test that individual agent modules still work for backward compatibility."""
    from spec_to_agents.agents import budget_analyst, event_coordinator, venue_specialist

    mock_client = Mock()
    mock_code_interpreter = Mock()
    mock_web_search = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Test event coordinator
    agent = event_coordinator.create_agent(mock_client)
    assert agent == mock_agent

    # Test budget analyst
    agent = budget_analyst.create_agent(mock_client, mock_code_interpreter, mcp_tool=None)
    assert agent == mock_agent

    # Test venue specialist
    agent = venue_specialist.create_agent(mock_client, mock_web_search, mcp_tool=None)
    assert agent == mock_agent
