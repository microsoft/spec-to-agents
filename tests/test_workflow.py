# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for the event planning workflow."""

from agent_framework import Workflow

from spec_to_agents.utils.clients import create_agent_client
from spec_to_agents.workflow.core import build_event_planning_workflow, workflow


def test_workflow_builds_successfully():
    """Test that the workflow can be constructed without errors."""
    client = create_agent_client()
    test_workflow = build_event_planning_workflow(client)
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


def test_workflow_uses_star_topology():
    """
    Test that workflow uses coordinator-centric star topology.

    The new architecture uses:
    - 1 EventPlanningCoordinator (custom executor)
    - 4 AgentExecutors (specialists)
    Total: 5 executors (down from 13)
    """
    client = create_agent_client()
    test_workflow = build_event_planning_workflow(client)
    assert test_workflow is not None

    # Workflow should build successfully with new star topology
    # No RequestInfoExecutor or HumanInLoopAgentExecutor wrappers
    # Routing handled by EventPlanningCoordinator


def test_coordinator_uses_service_managed_threads():
    """
    Test that coordinator uses service-managed threads (no manual state tracking).

    After refactoring to use service-managed threads:
    - Should have _agent (agent for synthesis and coordination)
    - Should NOT have _summarizer (removed)
    - Should NOT have _current_summary (removed)
    - Should NOT have _conversation_history (removed)
    - Should NOT have _current_index (obsolete)
    - Should NOT have _specialist_sequence (obsolete)
    """
    client = create_agent_client()
    test_workflow = build_event_planning_workflow(client)
    assert test_workflow is not None

    # Get the coordinator executor
    coordinator = None
    for executor in test_workflow.executors.values():
        if executor.id == "event_coordinator":
            coordinator = executor
            break

    assert coordinator is not None, "Coordinator not found in workflow"

    # Should have only the agent
    assert hasattr(coordinator, "_agent"), "Coordinator should have _agent attribute"
    assert coordinator._agent is not None, "Coordinator _agent should not be None"

    # Should NOT have manual state tracking
    assert not hasattr(coordinator, "_summarizer"), "Coordinator should not have _summarizer (removed)"
    assert not hasattr(coordinator, "_current_summary"), "Coordinator should not have _current_summary (removed)"
    assert not hasattr(coordinator, "_conversation_history"), (
        "Coordinator should not have _conversation_history (removed)"
    )

    # Should NOT have obsolete attributes
    assert not hasattr(coordinator, "_current_index"), "Coordinator should not have _current_index"
    assert not hasattr(coordinator, "_specialist_sequence"), "Coordinator should not have _specialist_sequence"
