# Copyright (c) Microsoft. All rights reserved.

"""Tests for coordinator architecture where only coordinator has structured output."""

from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentExecutorResponse, AgentRunResponse, WorkflowContext

from spec_to_agents.models.messages import SpecialistOutput
from spec_to_agents.workflow.executors import EventPlanningCoordinator


@pytest.mark.asyncio
async def test_coordinator_has_coordinator_agent():
    """Verify coordinator has a coordinator agent for routing decisions."""
    # Arrange
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    # Act & Assert
    assert hasattr(coordinator, "_coordinator_agent")
    assert coordinator._coordinator_agent == mock_coordinator_agent


@pytest.mark.asyncio
async def test_coordinator_analyzes_specialist_natural_text():
    """Verify coordinator calls coordinator agent to analyze specialist natural text."""
    # Arrange
    mock_coordinator_agent = AsyncMock()
    mock_coordinator_response = Mock(spec=AgentRunResponse)
    mock_coordinator_response.value = SpecialistOutput(
        summary="Venue recommendation: Option B",
        next_agent="budget",
        user_input_needed=False,
    )
    mock_coordinator_agent.run.return_value = mock_coordinator_response

    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    ctx = Mock(spec=WorkflowContext)
    ctx.send_message = AsyncMock()

    specialist_response = AgentExecutorResponse(
        executor_id="venue",
        agent_run_response=AgentRunResponse(
            messages=[],
        ),
        full_conversation=[],
    )

    # Act
    await coordinator.on_specialist_response(specialist_response, ctx)

    # Assert - coordinator agent should be called to analyze specialist output
    mock_coordinator_agent.run.assert_called_once()

    # Assert - should route to budget based on coordinator agent's decision
    ctx.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_start_routes_to_venue():
    """Verify coordinator start handler routes directly to venue specialist."""
    # Arrange
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    ctx = Mock(spec=WorkflowContext)
    ctx.send_message = AsyncMock()

    # Act
    await coordinator.start("Plan a corporate event", ctx)

    # Assert - should route directly to venue specialist
    ctx.send_message.assert_called_once()
    call_kwargs = ctx.send_message.call_args[1]
    assert call_kwargs["target_id"] == "venue"
