# Copyright (c) Microsoft. All rights reserved.

"""Test that agents and workflow modules export correctly."""


def test_workflow_builder_accessible_from_workflow():
    """Test that build_event_planning_workflow is accessible from workflow module."""
    from spec_to_agents.workflow.core import build_event_planning_workflow

    assert callable(build_event_planning_workflow)


def test_export_workflows_accessible_from_workflow():
    """Test that export_workflows is accessible from workflow module."""
    from spec_to_agents.workflow import export_workflows

    assert callable(export_workflows)


def test_export_agents_accessible_from_agents():
    """Test that export_agents is accessible from agents module."""
    from spec_to_agents.agents import export_agents

    assert callable(export_agents)


def test_workflow_builder_returns_workflow():
    """Test that build_event_planning_workflow returns a Workflow instance."""
    from unittest.mock import Mock

    from agent_framework import Workflow

    from spec_to_agents.workflow.core import build_event_planning_workflow

    mock_client = Mock()
    workflow = build_event_planning_workflow(mock_client)
    assert isinstance(workflow, Workflow)
    assert workflow.id == "event-planning-workflow"
