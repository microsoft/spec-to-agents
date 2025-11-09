# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent

from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.utils.clients import create_agent_client_for_devui


def export_agents() -> list[ChatAgent]:
    """
    Export all agents for registration in DevUI.

    Note: Only the workflow is exported. Individual agents are internal
    to the workflow and not meant to be used standalone in DevUI.

    Dependencies are injected via DI container which must be wired before
    calling this function (done in main.py and console.py).

    Returns
    -------
    list[ChatAgent]
        List containing all specialist agents
    """
    # Create agents (dependencies injected automatically via @inject)
    venue_agent = venue_specialist.create_agent()
    budget_agent = budget_analyst.create_agent()
    catering_agent = catering_coordinator.create_agent()
    logistics_agent = logistics_manager.create_agent()

    return [venue_agent, budget_agent, catering_agent, logistics_agent]


__all__ = ["create_agent_client_for_devui", "export_agents"]
