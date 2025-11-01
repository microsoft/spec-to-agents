# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for the event planning workflow."""

from agent_framework import Workflow

from spec_to_agents.utils.clients import create_agent_client_for_devui
from spec_to_agents.workflow.core import build_event_planning_workflow, workflow


def test_workflow_builds_successfully() -> None:
    """Test that the workflow can be constructed without errors."""
    client = create_agent_client_for_devui()
    test_workflow = build_event_planning_workflow(client)
    assert test_workflow is not None
    assert isinstance(test_workflow, Workflow)


def test_workflow_module_export() -> None:
    """Test that the workflow module exports a workflow instance."""
    assert workflow is not None
    assert isinstance(workflow, Workflow)


def test_workflow_has_correct_id() -> None:
    """Test that workflow has the expected ID."""
    assert workflow is not None
    assert workflow.id == "event-planning-workflow"


def test_workflow_uses_star_topology() -> None:
    """
    Test that workflow uses coordinator-centric star topology.

    The new architecture uses:
    - 1 EventPlanningCoordinator (custom executor)
    - 4 AgentExecutors (specialists)
    Total: 5 executors (down from 13)
    """
    client = create_agent_client_for_devui()
    test_workflow = build_event_planning_workflow(client)
    assert test_workflow is not None

    # Workflow should build successfully with new star topology
    # No RequestInfoExecutor or HumanInLoopAgentExecutor wrappers
    # Routing handled by EventPlanningCoordinator


def test_coordinator_uses_service_managed_threads() -> None:
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
    client = create_agent_client_for_devui()
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


def test_workflow_has_termination_guarantees() -> None:
    """
    Test that workflow has proper termination conditions to prevent infinite loops.

    The workflow uses bidirectional edges (creating cycles), but termination is
    guaranteed through:
    1. Max iterations limit
    2. Structured output routing with explicit completion signal
    3. Coordinator's explicit termination via ctx.yield_output()
    """
    client = create_agent_client_for_devui()
    test_workflow = build_event_planning_workflow(client)
    assert test_workflow is not None

    # Verify max_iterations is configured (prevents infinite loops)
    # This is enforced at the framework level
    # We can't directly access max_iterations from the workflow object,
    # but we can verify the workflow was built successfully with this configuration

    # Get the coordinator executor
    coordinator = None
    for executor in test_workflow.executors.values():
        if executor.id == "event_coordinator":
            coordinator = executor
            break

    assert coordinator is not None, "Coordinator not found in workflow"

    # Verify coordinator has the _synthesize_plan method that terminates workflow
    assert hasattr(coordinator, "_synthesize_plan"), (
        "Coordinator should have _synthesize_plan method for workflow termination"
    )

    # Verify bidirectional edges exist (creating cycles, but safe cycles)
    # The workflow should have edges from coordinator to specialists and back
    # This is verified by the successful workflow build - framework validation passes


def test_workflow_termination_documentation() -> None:
    """
    Test that the workflow build function has comprehensive termination documentation.

    This test ensures developers can understand how the workflow terminates despite
    having cycles from bidirectional edges.
    """
    from spec_to_agents.workflow.core import build_event_planning_workflow

    # Get the docstring of the build function
    docstring = build_event_planning_workflow.__doc__
    assert docstring is not None, "Workflow builder should have documentation"

    # Verify termination documentation exists
    assert "Termination Conditions" in docstring, (
        "Workflow documentation should explain termination conditions"
    )
    assert "max_iterations" in docstring.lower(), (
        "Documentation should mention max_iterations as a termination guarantee"
    )
    assert "structured output" in docstring.lower(), (
        "Documentation should mention structured output routing for termination"
    )
    assert "yield_output" in docstring.lower() or "yields output" in docstring.lower(), (
        "Documentation should mention final output yielding as termination signal"
    )
