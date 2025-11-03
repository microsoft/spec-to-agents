# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for calendar tools."""

from pathlib import Path

import pytest
from pytest import MonkeyPatch

from spec_to_agents.tools.calendar import create_calendar_event, delete_calendar_event, list_calendar_events


@pytest.fixture
def temp_calendar_path(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    """Create temporary calendar directory."""
    calendar_dir = tmp_path / "calendars"
    calendar_dir.mkdir()
    monkeypatch.setenv("CALENDAR_STORAGE_PATH", str(calendar_dir))
    # Re-import the module to pick up the new environment variable
    import importlib

    import spec_to_agents.tools.calendar

    importlib.reload(spec_to_agents.tools.calendar)
    return calendar_dir


@pytest.mark.asyncio
async def test_create_calendar_event(temp_calendar_path: Path) -> None:
    """Test creating a calendar event."""
    result: str = await create_calendar_event(
        event_title="Test Event",
        start_date="2025-12-01",
        start_time="14:00",
        duration_hours=2,
        location="Test Location",
        description="Test Description",
    )

    assert "Successfully created event" in result
    assert "Test Event" in result
    calendar_file = temp_calendar_path / "event_planning.ics"
    assert calendar_file.exists()


@pytest.mark.asyncio
async def test_create_calendar_event_default_calendar(temp_calendar_path: Path) -> None:
    """Test creating event in default calendar."""
    result: str = await create_calendar_event(
        event_title="Meeting", start_date="2025-12-15", start_time="10:00", duration_hours=1
    )

    assert "Successfully created event 'Meeting'" in result
    calendar_file = temp_calendar_path / "event_planning.ics"
    assert calendar_file.exists()


@pytest.mark.asyncio
async def test_create_calendar_event_custom_calendar(temp_calendar_path: Path) -> None:
    """Test creating event in custom calendar."""
    result: str = await create_calendar_event(
        event_title="Team Meeting",
        start_date="2025-12-20",
        start_time="15:30",
        duration_hours=1,
        calendar_name="team_events",
    )

    assert "Successfully created event" in result
    assert "team_events" in result
    calendar_file = temp_calendar_path / "team_events.ics"
    assert calendar_file.exists()


@pytest.mark.asyncio
async def test_create_calendar_event_invalid_date(temp_calendar_path: Path) -> None:
    """Test error handling for invalid date format."""
    result: str = await create_calendar_event(
        event_title="Test Event", start_date="2025/12/01", start_time="14:00", duration_hours=1
    )

    assert "Error parsing date/time" in result
    assert "YYYY-MM-DD" in result


@pytest.mark.asyncio
async def test_list_calendar_events(temp_calendar_path: Path) -> None:
    """Test listing calendar events."""
    # Create event first
    await create_calendar_event(
        event_title="Test Event", start_date="2025-12-01", start_time="14:00", duration_hours=2, location="Test Hall"
    )

    # List events
    result: str = await list_calendar_events()
    assert "Test Event" in result
    assert "2025-12-01" in result
    assert "Test Hall" in result


@pytest.mark.asyncio
async def test_list_calendar_events_empty(temp_calendar_path: Path) -> None:
    """Test listing events from non-existent calendar."""
    result: str = await list_calendar_events(calendar_name="nonexistent")
    assert "Calendar 'nonexistent' does not exist" in result


@pytest.mark.asyncio
async def test_list_calendar_events_with_date_filter(temp_calendar_path: Path) -> None:
    """Test listing events with date filters."""
    # Create multiple events
    await create_calendar_event(event_title="Event 1", start_date="2025-12-01", start_time="10:00")
    await create_calendar_event(event_title="Event 2", start_date="2025-12-15", start_time="14:00")
    await create_calendar_event(event_title="Event 3", start_date="2025-12-30", start_time="18:00")

    # List events in December 1-20
    result: str = await list_calendar_events(start_date="2025-12-01", end_date="2025-12-20")
    assert "Event 1" in result
    assert "Event 2" in result
    assert "Event 3" not in result


@pytest.mark.asyncio
async def test_delete_calendar_event(temp_calendar_path: Path) -> None:
    """Test deleting a calendar event."""
    # Create event
    await create_calendar_event(event_title="Test Event", start_date="2025-12-01", start_time="14:00")

    # Delete event
    result: str = await delete_calendar_event(event_title="Test Event")
    assert "Successfully deleted" in result
    assert "Test Event" in result

    # Verify deletion
    list_result = await list_calendar_events()
    assert "No events found" in list_result


@pytest.mark.asyncio
async def test_delete_calendar_event_not_found(temp_calendar_path: Path) -> None:
    """Test deleting a non-existent event."""
    # Create a calendar first
    await create_calendar_event(event_title="Some Event", start_date="2025-12-01", start_time="10:00")

    result: str = await delete_calendar_event(event_title="Nonexistent Event")
    assert "Event 'Nonexistent Event' not found" in result


@pytest.mark.asyncio
async def test_delete_calendar_event_from_nonexistent_calendar(temp_calendar_path: Path) -> None:
    """Test deleting event from non-existent calendar."""
    result: str = await delete_calendar_event(event_title="Test Event", calendar_name="nonexistent")
    assert "Calendar 'nonexistent' does not exist" in result


@pytest.mark.asyncio
async def test_multiple_events_same_calendar(temp_calendar_path: Path) -> None:
    """Test creating and listing multiple events in same calendar."""
    # Create multiple events
    await create_calendar_event(event_title="Morning Meeting", start_date="2025-12-01", start_time="09:00")
    await create_calendar_event(event_title="Lunch", start_date="2025-12-01", start_time="12:00")
    await create_calendar_event(event_title="Afternoon Workshop", start_date="2025-12-01", start_time="14:00")

    # List all events
    result: str = await list_calendar_events()
    assert "Morning Meeting" in result
    assert "Lunch" in result
    assert "Afternoon Workshop" in result
