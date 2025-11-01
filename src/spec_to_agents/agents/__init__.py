# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent


def export_agents() -> list[ChatAgent]:
    """
    Export all agents for registration in DevUI.

    Note: Only the workflow is exported. Individual agents are internal
    to the workflow and not meant to be used standalone in DevUI.

    Returns
    -------
    list[Workflow | ChatAgent]
        List containing the event planning workflow instance
    """
    # Import agents using lazy initialization pattern

    return []


__all__ = ["export_agents"]
