# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.agents.factory import create_event_coordinator_agent


def create_agent(
    client: AzureAIAgentClient,
) -> ChatAgent:
    """
    Create Event Coordinator agent for workflow orchestration.

    Deprecated: Use create_event_coordinator_agent from agents.factory instead.
    This function is maintained for backward compatibility.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation

    Returns
    -------
    ChatAgent
        Configured event coordinator agent for workflow orchestration
    """
    return create_event_coordinator_agent(client)
