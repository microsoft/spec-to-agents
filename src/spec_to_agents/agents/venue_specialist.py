# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

from agent_framework import ChatAgent, HostedWebSearchTool, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts import venue_specialist
from spec_to_agents.prompts.venue_specialist import SYSTEM_PROMPT
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(
    client: AzureAIAgentClient,
    bing_search: HostedWebSearchTool,
    mcp_tool: MCPStdioTool,
    request_user_input: Callable[..., str],
) -> ChatAgent:
    """
    Create Venue Specialist agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    bing_search : HostedWebSearchTool
        Web search tool for venue research
    mcp_tool : Tool
        Sequential thinking tool for complex reasoning
    request_user_input : Tool
        Tool for requesting user input/clarification

    Returns
    -------
    ChatAgent
        Configured venue specialist agent with Bing search capabilities
    """
    return client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        tools=[bing_search, mcp_tool, request_user_input],
        response_format=SpecialistOutput,
        store=True,
    )


agent = get_chat_client().create_agent(
    name="VenueSpecialistAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
)

__all__ = ["agent", "create_agent"]
