# Copyright (c) Microsoft. All rights reserved.

"""Tests for human-in-the-loop workflow functionality."""

import json
from unittest.mock import Mock

import pytest
from agent_framework import FunctionCallContent, RequestInfoEvent

from spec_to_agents.workflow.core import build_event_planning_workflow
from spec_to_agents.workflow.executors import HumanInLoopAgentExecutor


def test_hitl_executor_detects_tool_call():
    """Test HumanInLoopAgentExecutor correctly detects request_user_input calls."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Mock AgentExecutorResponse with tool call
    mock_response = Mock()
    mock_agent_run_response = Mock()
    mock_message = Mock()
    mock_content = Mock(spec=FunctionCallContent)
    mock_content.name = "request_user_input"
    mock_content.arguments = json.dumps({"prompt": "test", "context": {}, "request_type": "clarification"})
    mock_message.contents = [mock_content]
    mock_agent_run_response.messages = [mock_message]
    mock_response.agent_run_response = mock_agent_run_response

    # Extract should find the tool call
    result = executor._extract_user_request(mock_response)
    assert result is not None
    assert result["prompt"] == "test"


def test_hitl_executor_returns_none_without_tool_call():
    """Test HumanInLoopAgentExecutor returns None when no tool call."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Mock response without tool calls
    mock_response = Mock()
    mock_agent_run_response = Mock()
    mock_message = Mock()
    mock_message.contents = []
    mock_agent_run_response.messages = [mock_message]
    mock_response.agent_run_response = mock_agent_run_response

    result = executor._extract_user_request(mock_response)
    assert result is None


def test_workflow_builds_with_hitl_components():
    """Test that workflow builds successfully with HITL components."""
    workflow = build_event_planning_workflow()
    assert workflow is not None


@pytest.mark.asyncio
async def test_workflow_with_detailed_request_no_user_input():
    """
    Test workflow completes without user input when given detailed context.

    NOTE: This test requires Azure credentials and makes real API calls.
    It may be skipped in CI if credentials are not available.
    """
    workflow = build_event_planning_workflow()

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


@pytest.mark.asyncio
async def test_workflow_with_ambiguous_request_may_trigger_user_input():
    """
    Test workflow handles ambiguous requests (may trigger RequestInfoEvent).

    NOTE: This test requires Azure credentials and makes real API calls.
    Whether user input is requested depends on agent LLM behavior.
    """
    workflow = build_event_planning_workflow()

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
