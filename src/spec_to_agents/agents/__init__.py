# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent, Workflow


def export_entities() -> list[Workflow | ChatAgent]:
    """
    Export all agents/workflows for registration in DevUI.

    Note: Only the workflow is exported. Individual agents are internal
    to the workflow and not meant to be used standalone in DevUI.

    Returns
    -------
    list[Workflow | ChatAgent]
        List containing the event planning workflow instance
    """
    # Import workflow using lazy initialization pattern
    from spec_to_agents.workflow.core import workflow

    return [workflow]


__all__ = ["export_entities"]
