# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent

from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.utils.clients import create_agent_client_for_devui


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

    # Create client for DevUI - DevUI will handle cleanup via FastAPI lifespan
    client = create_agent_client_for_devui()

    # Create agents
    coordinator_agent = event_coordinator.create_agent(client)
    venue_agent = venue_specialist.create_agent(client, mcp_tool=None)
    budget_agent = budget_analyst.create_agent(client, mcp_tool=None)
    catering_agent = catering_coordinator.create_agent(client, mcp_tool=None)
    logistics_agent = logistics_manager.create_agent(client, mcp_tool=None)

    return [coordinator_agent, venue_agent, budget_agent, catering_agent, logistics_agent]


__all__ = ["export_agents"]
