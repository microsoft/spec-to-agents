# Copyright (c) Microsoft. All rights reserved.

"""Test that agents module exports workflow correctly."""

import pytest


def test_workflow_builder_accessible_from_agents():
    """Test that build_event_planning_workflow is accessible from agents module."""
    from spec_to_agents.agents import build_event_planning_workflow

    assert callable(build_event_planning_workflow)


def test_export_entities_accessible_from_agents():
    """Test that export_entities is accessible from agents module."""
    from spec_to_agents.agents import export_entities

    assert callable(export_entities)


@pytest.mark.asyncio
async def test_workflow_builder_returns_workflow():
    """Test that build_event_planning_workflow returns a Workflow instance."""
    from agent_framework import Workflow

    from spec_to_agents.agents import build_event_planning_workflow

    workflow = await build_event_planning_workflow()
    assert isinstance(workflow, Workflow)
    assert workflow.id == "event-planning-workflow"
