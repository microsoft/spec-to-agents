# Copyright (c) Microsoft. All rights reserved.
from agent_framework import Workflow


def export_workflow() -> list[Workflow]:
    """
    Export all workflows for registration in DevUI.

    Note: Only the workflow is exported. Individual agents are internal
    to the workflow and not meant to be used standalone in DevUI.

    Returns
    -------
    list[Workflow]
        List containing the event planning workflow instance
    """
    # Import and build workflow using lazy initialization pattern
    from spec_to_agents.workflow.core import build_event_planning_workflow

    workflow = build_event_planning_workflow()
    return [workflow]


__all__ = ["export_workflow"]
