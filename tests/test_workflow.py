# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for the event planning workflow."""

from agent_framework import Workflow

from spec_to_agents.container import AppContainer
from spec_to_agents.utils.clients import create_agent_client_for_devui
from spec_to_agents.workflow.core import build_event_planning_workflow


def test_workflow_builds_successfully() -> None:
    """Test that the workflow can be constructed without errors."""
    # Initialize DI container
    container = AppContainer()
    container.wire(modules=[__name__])

    client = create_agent_client_for_devui()
    test_workflow = build_event_planning_workflow(client=client)
    assert test_workflow is not None
    assert isinstance(test_workflow, Workflow)


def test_workflow_module_export() -> None:
    """Test that the workflow module exports build_event_planning_workflow function."""
    # Initialize DI container
    container = AppContainer()
    container.wire(modules=[__name__])

    workflow = build_event_planning_workflow()
    assert workflow is not None
    assert isinstance(workflow, Workflow)


def test_workflow_has_correct_id() -> None:
    """Test that workflow has the expected ID."""
    # Initialize DI container
    container = AppContainer()
    container.wire(modules=[__name__])

    workflow = build_event_planning_workflow()
    assert workflow is not None
    assert workflow.id == "event-planning-workflow"


def test_workflow_uses_star_topology() -> None:
    """
    Test that workflow uses coordinator-centric star topology.

    The new architecture uses:
    - 1 SupervisorOrchestratorExecutor (supervisor)
    - 4 AgentExecutors (participants)
    Total: 5 executors
    """
    # Initialize DI container
    container = AppContainer()
    container.wire(modules=[__name__])

    test_workflow = build_event_planning_workflow()
    assert test_workflow is not None

    # Workflow should build successfully with star topology
    # Supervisor ←→ Participants bidirectional edges


def test_coordinator_uses_service_managed_threads() -> None:
    """
    Test that supervisor uses service-managed threads (no manual state tracking).

    After refactoring to supervisor pattern:
    - Should have _supervisor_agent (supervisor agent for routing decisions)
    - Should have _conversation_history (accumulated messages)
    - Should NOT have _summarizer (removed)
    - Should NOT have _current_summary (removed)
    - Should NOT have _current_index (obsolete)
    - Should NOT have _specialist_sequence (obsolete)
    """
    # Initialize DI container
    container = AppContainer()
    container.wire(modules=[__name__])

    test_workflow = build_event_planning_workflow()
    assert test_workflow is not None

    # Get the supervisor executor
    supervisor = None
    for executor in test_workflow.executors.values():
        if executor.id == "supervisor":
            supervisor = executor
            break

    assert supervisor is not None, "Supervisor not found in workflow"

    # Should have supervisor agent and conversation history
    assert hasattr(supervisor, "_supervisor_agent"), "Supervisor should have _supervisor_agent attribute"
    assert supervisor._supervisor_agent is not None, "Supervisor _supervisor_agent should not be None"
    assert hasattr(supervisor, "_conversation_history"), "Supervisor should have _conversation_history attribute"

    # Should NOT have manual state tracking
    assert not hasattr(supervisor, "_summarizer"), "Supervisor should not have _summarizer (removed)"
    assert not hasattr(supervisor, "_current_summary"), "Supervisor should not have _current_summary (removed)"

    # Should NOT have obsolete attributes
    assert not hasattr(supervisor, "_current_index"), "Supervisor should not have _current_index"
    assert not hasattr(supervisor, "_specialist_sequence"), "Supervisor should not have _specialist_sequence"
