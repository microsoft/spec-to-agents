# Copyright (c) Microsoft. All rights reserved.


from agent_framework import ChatAgent, HostedWebSearchTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import catering_coordinator
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(client: AzureAIAgentClient, bing_search: HostedWebSearchTool) -> ChatAgent:
    """
    Create Catering Coordinator agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    bing_search : HostedWebSearchTool
        Web search tool for catering research

    Returns
    -------
    ChatAgent
        Configured catering coordinator agent with Bing search capabilities

    Notes
    -----
    MCP sequential-thinking tool was removed because it interferes with
    structured output generation (SpecialistOutput). The agent would complete
    its thinking process but fail to return a final structured response,
    causing ValueError in the workflow.
    """
    return client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        tools=[bing_search],
        response_format=SpecialistOutput,
        store=True,
    )
