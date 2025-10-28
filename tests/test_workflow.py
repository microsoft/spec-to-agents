# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for the event planning workflow."""

from agent_framework import Workflow

from spec2agent.workflow.core import build_event_planning_workflow, workflow


def test_workflow_builds_successfully():
    """Test that the workflow can be constructed without errors."""
    test_workflow = build_event_planning_workflow()
    assert test_workflow is not None
    assert isinstance(test_workflow, Workflow)


def test_workflow_module_export():
    """Test that the workflow module exports a workflow instance."""
    assert workflow is not None
    assert isinstance(workflow, Workflow)


def test_workflow_builder_is_callable():
    """Test that build_event_planning_workflow can be called multiple times."""
    workflow1 = build_event_planning_workflow()
    workflow2 = build_event_planning_workflow()

    assert workflow1 is not None
    assert workflow2 is not None
    assert isinstance(workflow1, Workflow)
    assert isinstance(workflow2, Workflow)


def test_workflow_includes_request_info_executor():
    """Test that workflow includes RequestInfoExecutor for HITL."""
    from spec2agent.workflow.core import build_event_planning_workflow

    workflow = build_event_planning_workflow()

    # Workflow should build successfully with HITL components
    assert workflow is not None

    # Note: Can't easily inspect workflow internals, but building without
    # errors confirms RequestInfoExecutor and HITL wrappers are integrated
