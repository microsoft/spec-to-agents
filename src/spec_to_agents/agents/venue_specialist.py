# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable

from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.agents.factory import create_venue_specialist_agent


def create_agent(
    client: AzureAIAgentClient, web_search: Callable[..., Any], mcp_tool: MCPStdioTool | None
) -> ChatAgent:
    """
    Create Venue Specialist agent for event planning workflow.

    Deprecated: Use create_venue_specialist_agent from agents.factory instead.
    This function is maintained for backward compatibility.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    web_search : Callable
        Custom web search function decorated with @ai_function
    mcp_tool : MCPStdioTool | None, optional
        Sequential thinking tool for complex reasoning.
        If None, coordinator operates without MCP tool assistance.

    Returns
    -------
    ChatAgent
        Configured venue specialist agent with web search capabilities

    Notes
    -----
    MCP sequential-thinking tool was removed because it interferes with
    structured output generation (SpecialistOutput). The agent would complete
    its thinking process but fail to return a final structured response,
    causing ValueError in the workflow.

    Uses custom web_search @ai_function instead of HostedWebSearchTool for
    better control over response formatting for language models.
    """
    return create_venue_specialist_agent(client, web_search, mcp_tool)
