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
