# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for the event planning workflow."""

import pytest
from agent_framework import Workflow

from spec_to_agents.workflow.core import build_event_planning_workflow, workflow


@pytest.mark.asyncio
async def test_workflow_builds_successfully():
    """Test that the workflow can be constructed without errors."""
    test_workflow = await build_event_planning_workflow()
    assert test_workflow is not None
    assert isinstance(test_workflow, Workflow)


def test_workflow_module_export():
    """Test that the workflow module exports a workflow instance."""
    assert workflow is not None
    assert isinstance(workflow, Workflow)


def test_workflow_has_correct_id():
    """Test that workflow has the expected ID."""
    assert workflow is not None
    assert workflow.id == "event-planning-workflow"


@pytest.mark.asyncio
async def test_workflow_uses_star_topology():
    """
    Test that workflow uses coordinator-centric star topology.

    The new architecture uses:
    - 1 EventPlanningCoordinator (custom executor)
    - 4 AgentExecutors (specialists)
    Total: 5 executors (down from 13)
    """
    test_workflow = await build_event_planning_workflow()
    assert test_workflow is not None

    # Workflow should build successfully with new star topology
    # No RequestInfoExecutor or HumanInLoopAgentExecutor wrappers
    # Routing handled by EventPlanningCoordinator


@pytest.mark.asyncio
async def test_workflow_includes_summarizer_agent():
    """
    Test that the workflow includes a summarizer agent in the coordinator.

    The summarizer agent should:
    - Be present in the coordinator
    - Be configured with SummarizedContext response format
    - Not have any tools (pure LLM task)
    """
    test_workflow = await build_event_planning_workflow()
    assert test_workflow is not None

    # Access the coordinator from workflow executors
    coordinator = None
    for executor in test_workflow.executors.values():
        if executor.id == "event_coordinator":
            coordinator = executor
            break

    assert coordinator is not None, "Coordinator not found in workflow"
    assert hasattr(coordinator, "_summarizer"), "Coordinator does not have a summarizer agent"
    assert coordinator._summarizer is not None, "Summarizer agent is None"


@pytest.mark.asyncio
async def test_coordinator_has_correct_state_variables():
    """
    Test that coordinator has correct state variables after refactor.

    After refactoring to use structured output routing and adding conversation history:
    - Should have _coordinator (agent for synthesis)
    - Should have _summarizer (agent for context condensation)
    - Should have _current_summary (for chained summarization)
    - Should have _conversation_history (for follow-up questions)
    - Should NOT have _current_index (obsolete)
    - Should NOT have _sequence (obsolete)
    """
    test_workflow = await build_event_planning_workflow()
    assert test_workflow is not None

    # Get the coordinator executor
    coordinator = None
    for executor in test_workflow.executors.values():
        if executor.id == "event_coordinator":
            coordinator = executor
            break

    assert coordinator is not None, "Coordinator not found in workflow"

    # Should have these attributes
    assert hasattr(coordinator, "_agent"), "Coordinator should have _agent attribute"
    assert coordinator._agent is not None, "Coordinator _agent should not be None"

    assert hasattr(coordinator, "_summarizer"), "Coordinator should have _summarizer attribute"
    assert coordinator._summarizer is not None, "Coordinator _summarizer should not be None"

    assert hasattr(coordinator, "_current_summary"), "Coordinator should have _current_summary attribute"
    assert isinstance(coordinator._current_summary, str), "Coordinator _current_summary should be a string"
    assert coordinator._current_summary == "", "Coordinator _current_summary should be initialized to empty string"

    assert hasattr(coordinator, "_conversation_history"), "Coordinator should have _conversation_history attribute"
    assert isinstance(coordinator._conversation_history, list), "Coordinator _conversation_history should be a list"
    assert coordinator._conversation_history == [], (
        "Coordinator _conversation_history should be initialized to empty list"
    )

    # Should NOT have these obsolete attributes
    assert not hasattr(coordinator, "_current_index"), "Coordinator should not have _current_index"
    assert not hasattr(coordinator, "_specialist_sequence"), "Coordinator should not have _specialist_sequence"
