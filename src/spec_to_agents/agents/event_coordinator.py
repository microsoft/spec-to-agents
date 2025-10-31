# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import event_coordinator


def create_agent(
    client: AzureAIAgentClient,
) -> ChatAgent:
    """
    Create Event Coordinator agent for workflow orchestration.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation

    Returns
    -------
    ChatAgent
        Configured event coordinator agent for workflow orchestration
    """
    return client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        store=True,
    )
