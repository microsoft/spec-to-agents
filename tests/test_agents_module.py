# Copyright (c) Microsoft. All rights reserved.

"""Test that agents module exports workflow correctly."""


def test_workflow_builder_accessible_from_workflow():
    """Test that build_event_planning_workflow is accessible from workflow module."""
    from spec_to_agents.workflow.core import build_event_planning_workflow

    assert callable(build_event_planning_workflow)


def test_export_workflow_accessible_from_workflow():
    """Test that export_workflow is accessible from workflow module."""
    from spec_to_agents.workflow import export_workflow

    assert callable(export_workflow)


def test_workflow_builder_returns_workflow(setup_di_container):
    """Test that build_event_planning_workflow returns a Workflow instance."""
    from unittest.mock import Mock

    from agent_framework import Workflow

    from spec_to_agents.workflow.core import build_event_planning_workflow

    # Setup DI container with mocked client
    container = setup_di_container
    mock_client = Mock()
    container.client.override(mock_client)

    workflow = build_event_planning_workflow()
    assert isinstance(workflow, Workflow)
    assert workflow.id == "event-planning-workflow"
