# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent, Workflow

from spec_to_agents.workflow.core import workflow as event_planning_workflow


def export_entities() -> list[Workflow | ChatAgent]:
    """Export all agents/workflows for registration in DevUI.

    Note: Only the workflow is exported. Individual agents are internal
    to the workflow and not meant to be used standalone in DevUI.
    """
    return [
        event_planning_workflow,
    ]
