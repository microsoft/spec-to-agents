# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent, Workflow


def export_workflows() -> list[Workflow | ChatAgent]:
    """
    Export all workflows for registration in DevUI.

    This function exports the event planning workflow for use in the DevUI.
    Individual agents are internal to the workflow and not meant to be used
    standalone in DevUI through this function. Use export_agents() from the
    agents module to test individual agents.

    Returns
    -------
    list[Workflow | ChatAgent]
        List containing the event planning workflow instance

    Notes
    -----
    The workflow is lazy-loaded on first access to avoid unnecessary
    initialization overhead.
    """
    # Import workflow using lazy initialization pattern
    from spec_to_agents.workflow.core import workflow

    return [workflow]


__all__ = ["export_workflows"]
