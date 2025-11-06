# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.models.messages import SpecialistOutput
from spec_to_agents.prompts import event_coordinator


def create_agent(
    client: AzureAIAgentClient,
) -> ChatAgent:
    """
    Create Event Coordinator agent for workflow orchestration.

    The coordinator uses store=False because it receives full conversation
    history from specialists (who have their own service-managed threads).
    Passing full conversation history with store=True would cause duplication
    and the agent echoing previous outputs.

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
        response_format=SpecialistOutput,
        store=False,  # Manual conversation management since we pass full history
    )
