# Copyright (c) Microsoft. All rights reserved.

"""Integration tests for the event planning workflow."""

import os

import pytest

from spec_to_agents.workflow.core import build_event_planning_workflow


@pytest.mark.skip(reason="Integration test requires real Azure credentials and agent setup")
@pytest.mark.asyncio
async def test_workflow_execution_basic():
    """Test basic workflow execution with a simple event planning request."""
    from spec_to_agents.utils.clients import create_agent_client

    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        workflow = build_event_planning_workflow(client)

    # Submit a test event planning request
    request = "Plan a corporate holiday party for 50 people with a budget of $5000"

    # Execute workflow
    result = await workflow.run(request)

    # Validate that result is generated
    assert result is not None
    assert len(result) > 0


@pytest.mark.skip(reason="Integration test requires real Azure credentials and agent setup")
@pytest.mark.asyncio
async def test_workflow_execution_contains_sections():
    """Test that workflow output contains expected sections from all agents."""
    from spec_to_agents.utils.clients import create_agent_client

    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        workflow = build_event_planning_workflow(client)

    # Submit a test event planning request
    request = "Plan a team building event for 30 people in Seattle with a budget of $3000"

    # Execute workflow
    result = await workflow.run(request)

    # Convert result to lowercase for easier searching
    result_lower = str(result).lower()

    # Validate that result contains contributions from all specialists
    # These are flexible checks since exact wording may vary
    assert any(keyword in result_lower for keyword in ["venue", "location", "space"]), (
        "Result should contain venue information"
    )

    assert any(keyword in result_lower for keyword in ["budget", "cost", "allocation", "expense"]), (
        "Result should contain budget information"
    )

    assert any(keyword in result_lower for keyword in ["catering", "food", "menu", "beverage"]), (
        "Result should contain catering information"
    )

    assert any(keyword in result_lower for keyword in ["logistics", "timeline", "schedule"]), (
        "Result should contain logistics information"
    )


@pytest.mark.skip(reason="Integration test requires real Azure credentials and agent setup")
@pytest.mark.asyncio
async def test_workflow_execution_different_event_types():
    """Test workflow with different event types to ensure adaptability."""
    from spec_to_agents.utils.clients import create_agent_client

    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        workflow = build_event_planning_workflow(client)

    test_requests = [
        "Plan a wedding reception for 100 guests with a budget of $15000",
        "Organize a small conference for 75 attendees with a $10000 budget",
        "Arrange a birthday party for 25 people with a budget of $2000",
    ]

    for request in test_requests:
        result = await workflow.run(request)
        assert result is not None
        assert len(result) > 0, f"Workflow should produce output for: {request}"
