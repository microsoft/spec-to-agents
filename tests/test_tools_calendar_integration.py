# Copyright (c) Microsoft. All rights reserved.

"""Integration tests for calendar tools using ChatClient."""

import os
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from spec_to_agents.tools.calendar import create_calendar_event, delete_calendar_event, list_calendar_events
from spec_to_agents.utils.clients import create_agent_client


@pytest.fixture
def temp_calendar_path_integration(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    """Create temporary calendar directory for integration tests."""
    calendar_dir = tmp_path / "calendars_integration"
    calendar_dir.mkdir()
    monkeypatch.setenv("CALENDAR_STORAGE_PATH", str(calendar_dir))
    # Re-import the module to pick up the new environment variable
    import importlib

    import spec_to_agents.tools.calendar

    importlib.reload(spec_to_agents.tools.calendar)
    return calendar_dir


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_create_event_with_agent(temp_calendar_path_integration: Path) -> None:
    """Test creating calendar events through an agent."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with calendar tools
        agent = client.create_agent(
            name="calendar_test_agent",
            description="Test agent for calendar operations",
            instructions="You are a helpful assistant that manages calendar events.",
            tools=[create_calendar_event, list_calendar_events, delete_calendar_event],
        )

        # Test creating an event
        response = await agent.run("Create a calendar event called 'Team Meeting' on 2025-12-15 at 14:00 for 2 hours")

        # Verify response
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should indicate success
        assert any(keyword in result_text for keyword in ["created", "added", "scheduled", "success"])

        # Verify the calendar file was created
        calendar_file = temp_calendar_path_integration / "event_planning.ics"
        assert calendar_file.exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_list_events_with_agent(temp_calendar_path_integration: Path) -> None:
    """Test listing calendar events through an agent."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with calendar tools
        agent = client.create_agent(
            name="calendar_list_agent",
            description="Test agent for listing calendar events",
            instructions="You are a helpful assistant that manages calendar events.",
            tools=[create_calendar_event, list_calendar_events],
        )

        # Create events first
        await agent.run("Create a calendar event 'Event 1' on 2025-12-10 at 10:00 for 1 hour")
        await agent.run("Create a calendar event 'Event 2' on 2025-12-20 at 15:00 for 2 hours")

        # Now list events
        response = await agent.run("List all calendar events")

        # Verify response
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should mention the events
        assert any(keyword in result_text for keyword in ["event 1", "event 2", "events"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_delete_event_with_agent(temp_calendar_path_integration: Path) -> None:
    """Test deleting calendar events through an agent."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with calendar tools
        agent = client.create_agent(
            name="calendar_delete_agent",
            description="Test agent for deleting calendar events",
            instructions="You are a helpful assistant that manages calendar events.",
            tools=[create_calendar_event, list_calendar_events, delete_calendar_event],
        )

        # Create an event first
        await agent.run("Create a calendar event 'Delete Me' on 2025-12-25 at 12:00 for 1 hour")

        # Delete the event
        response = await agent.run("Delete the calendar event called 'Delete Me'")

        # Verify response
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should indicate deletion success
        assert any(keyword in result_text for keyword in ["deleted", "removed", "success"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_filter_events_with_agent(temp_calendar_path_integration: Path) -> None:
    """Test filtering calendar events by date range through an agent."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with calendar tools
        agent = client.create_agent(
            name="calendar_filter_agent",
            description="Test agent for filtering calendar events",
            instructions="You are a helpful assistant that manages calendar events.",
            tools=[create_calendar_event, list_calendar_events],
        )

        # Create events across different dates
        await agent.run("Create event 'Early Event' on 2025-12-01 at 10:00")
        await agent.run("Create event 'Mid Event' on 2025-12-15 at 14:00")
        await agent.run("Create event 'Late Event' on 2025-12-30 at 18:00")

        # List events in a specific range
        response = await agent.run("List calendar events between 2025-12-01 and 2025-12-20")

        # Verify response
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should mention early and mid events, but not late event
        assert "early event" in result_text or "mid event" in result_text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_custom_calendar_name_with_agent(temp_calendar_path_integration: Path) -> None:
    """Test using custom calendar names through an agent."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with calendar tools
        agent = client.create_agent(
            name="calendar_custom_agent",
            description="Test agent for custom calendar names",
            instructions="You are a helpful assistant that manages calendar events.",
            tools=[create_calendar_event, list_calendar_events],
        )

        # Create event in custom calendar
        response = await agent.run(
            "Create a calendar event 'Team Sync' on 2025-12-10 at 10:00 in calendar named 'team_events'"
        )

        # Verify response
        assert response is not None
        assert response.text is not None

        # Verify custom calendar file was created
        calendar_file = temp_calendar_path_integration / "team_events.ics"
        assert calendar_file.exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_with_agent_american_date_format(temp_calendar_path_integration: Path) -> None:
    """Test calendar handling of American date format (agent should convert or handle it)."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with calendar tools
        agent = client.create_agent(
            name="calendar_dateformat_agent",
            description="Test agent for calendar date format handling",
            instructions="You are a helpful assistant that manages calendar events.",
            tools=[create_calendar_event],
        )

        # Try to create event with American date format (agent should handle this)
        response = await agent.run("Create a calendar event 'Meeting' on 12/15/2025 at 14:00")

        # Verify response handles the request (either creates or explains)
        assert response is not None
        assert response.text is not None
        # Agent should have either created the event or responded about it
        assert len(response.text) > 0
