# Copyright (c) Microsoft. All rights reserved.

"""Tests for human-in-the-loop workflow functionality."""

from unittest.mock import Mock

import pytest
from agent_framework import RequestInfoEvent

from spec_to_agents.workflow.core import build_event_planning_workflow


def test_workflow_builds_with_hitl_components():
    """Test that workflow builds successfully with HITL components."""
    mock_client = Mock()
    workflow = build_event_planning_workflow(mock_client)
    assert workflow is not None


@pytest.mark.skip(reason="Integration test requires real Azure credentials and agent setup")
@pytest.mark.asyncio
async def test_workflow_with_detailed_request_no_user_input():
    """
    Test workflow completes without user input when given detailed context.

    NOTE: This test requires Azure credentials and makes real API calls.
    It may be skipped in CI if credentials are not available.
    """
    import os

    from spec_to_agents.clients import create_agent_client

    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        workflow = build_event_planning_workflow(client)

    detailed_request = """
    Plan a corporate team building event:
    - 30 people
    - Budget: $3000
    - Location: Downtown Seattle
    - Date: 3 weeks from now, Friday evening
    - Dietary: vegetarian and gluten-free options required
    """

    events = []
    async for event in workflow.run_stream(detailed_request):
        events.append(event)

    # Should complete without requiring user input
    assert len(events) > 0

    # With detailed context, agents should not need to request user input
    # But this depends on LLM behavior, so we just verify workflow completes


@pytest.mark.skip(reason="Integration test requires real Azure credentials and agent setup")
@pytest.mark.asyncio
async def test_workflow_with_ambiguous_request_may_trigger_user_input():
    """
    Test workflow handles ambiguous requests (may trigger RequestInfoEvent).

    NOTE: This test requires Azure credentials and makes real API calls.
    Whether user input is requested depends on agent LLM behavior.
    """
    import os

    from spec_to_agents.clients import create_agent_client

    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        workflow = build_event_planning_workflow(client)

    # Ambiguous request that could trigger user input
    request = "Plan a party for 30 people"

    events = []
    async for event in workflow.run_stream(request):
        events.append(event)
        # If RequestInfoEvent occurs, workflow will pause
        # In real usage, DevUI would handle this
        if isinstance(event, RequestInfoEvent):
            # In test, we can't easily provide user response
            # This confirms HITL mechanism is working
            break

    # Workflow produces events
    assert len(events) > 0

    # Test validates workflow handles both cases (with or without user input)
    # depending on agent behavior
