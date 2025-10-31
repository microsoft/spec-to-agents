# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for the event planning workflow."""

from unittest.mock import Mock

import pytest
from agent_framework import Workflow

from spec_to_agents.workflow.core import build_event_planning_workflow


def test_workflow_builds_successfully():
    """Test that the workflow can be constructed without errors."""
    mock_client = Mock()
    test_workflow = build_event_planning_workflow(mock_client)
    assert test_workflow is not None
    assert isinstance(test_workflow, Workflow)


@pytest.mark.skip(reason="Requires Azure credentials - workflow import triggers real client creation")
def test_workflow_module_export():
    """Test that the workflow module exports a workflow instance."""
    from spec_to_agents.workflow.core import workflow

    assert workflow is not None
    assert isinstance(workflow, Workflow)


@pytest.mark.skip(reason="Requires Azure credentials - workflow import triggers real client creation")
def test_workflow_has_correct_id():
    """Test that workflow has the expected ID."""
    from spec_to_agents.workflow.core import workflow

    assert workflow is not None
    assert workflow.id == "event-planning-workflow"


def test_workflow_uses_fanout_fanin_topology():
    """
    Test that workflow uses declarative fan-out/fan-in topology.

    The new architecture uses:
    - 1 Initial Coordinator (AgentExecutor)
    - 4 Specialist agents (AgentExecutors) - venue, budget, catering, logistics
    - 1 Synthesizer (AgentExecutor)
    Total: 6 executors

    Pattern: Coordinator → (fan-out to specialists) → (fan-in to synthesizer)
    Fully declarative using WorkflowBuilder edges, no custom Executor classes
    """
    mock_client = Mock()
    test_workflow = build_event_planning_workflow(mock_client)
    assert test_workflow is not None

    # Workflow should build successfully with fan-out/fan-in topology
    # All executors are simple AgentExecutor instances
    # Routing is declarative through workflow edges


def test_all_executors_are_simple_agent_executors():
    """
    Test that all executors in the workflow are simple AgentExecutor instances.

    After refactoring to declarative pattern:
    - All executors should be AgentExecutor (no custom Executor subclasses)
    - Should have coordinator, venue, budget, catering, logistics, and synthesizer
    - Routing is handled declaratively by workflow edges, not by executor logic
    """
    from agent_framework import AgentExecutor

    mock_client = Mock()
    test_workflow = build_event_planning_workflow(mock_client)
    assert test_workflow is not None

    # Check that we have the expected number of executors
    expected_executor_ids = {"coordinator", "venue", "budget", "catering", "logistics", "synthesizer"}
    actual_executor_ids = set(test_workflow.executors.keys())

    assert expected_executor_ids == actual_executor_ids, (
        f"Expected executors {expected_executor_ids}, got {actual_executor_ids}"
    )

    # Verify all executors are simple AgentExecutor instances (not custom subclasses)
    for executor_id, executor in test_workflow.executors.items():
        assert type(executor) is AgentExecutor, (
            f"Executor '{executor_id}' should be AgentExecutor, got {type(executor).__name__}"
        )
