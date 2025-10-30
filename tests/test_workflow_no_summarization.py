# Copyright (c) Microsoft. All rights reserved.

"""Tests for simplified coordinator without summarization."""

from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentExecutorResponse, AgentRunResponse, WorkflowContext

from spec_to_agents.workflow.executors import EventPlanningCoordinator
from spec_to_agents.workflow.messages import SpecialistOutput


@pytest.mark.asyncio
async def test_coordinator_no_conversation_history_tracking():
    """Verify coordinator does not manually track conversation history."""
    # Arrange
    coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(coordinator_agent)

    # Act & Assert
    assert not hasattr(coordinator, "_conversation_history")
    assert not hasattr(coordinator, "_current_summary")
    assert not hasattr(coordinator, "_summarizer")


@pytest.mark.asyncio
async def test_coordinator_routes_without_summarization():
    """Verify coordinator routes without calling summarization."""
    # Arrange
    coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(coordinator_agent)

    ctx = Mock(spec=WorkflowContext)
    ctx.send_message = AsyncMock()

    specialist_response = AgentExecutorResponse(
        executor_id="venue",
        agent_run_response=AgentRunResponse(
            messages=[],
            value=SpecialistOutput(
                summary="Venue recommendation: Option B",
                next_agent="budget",
                user_input_needed=False,
            ),
        ),
    )

    # Act
    await coordinator.on_specialist_response(specialist_response, ctx)

    # Assert - should route directly without summarization
    ctx.send_message.assert_called_once()
    # Verify no _chain_summarize() method exists
    assert not hasattr(coordinator, "_chain_summarize")


@pytest.mark.asyncio
async def test_coordinator_start_routes_directly():
    """Verify coordinator start handler routes without building history."""
    # Arrange
    coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(coordinator_agent)

    ctx = Mock(spec=WorkflowContext)
    ctx.send_message = AsyncMock()

    # Act
    await coordinator.start("Plan a corporate event", ctx)

    # Assert - should route to venue immediately
    ctx.send_message.assert_called_once()
    call_kwargs = ctx.send_message.call_args[1]
    assert call_kwargs["target_id"] == "venue"
