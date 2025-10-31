# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import event_synthesizer


def create_agent(
    client: AzureAIAgentClient,
) -> ChatAgent:
    """
    Create Event Synthesizer agent for consolidating specialist recommendations.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation

    Returns
    -------
    ChatAgent
        Configured event synthesizer agent for creating final event plans
    """
    return client.create_agent(
        name="EventSynthesizer",
        instructions=event_synthesizer.SYSTEM_PROMPT,
        store=True,
    )
