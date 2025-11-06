# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import catering_coordinator
from spec_to_agents.tools import web_search


def create_agent(client: AzureAIAgentClient, mcp_tool: MCPStdioTool | None) -> ChatAgent:
    """
    Create Catering Coordinator agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    mcp_tool : MCPStdioTool | None, optional
        Sequential thinking tool for complex reasoning.
        If None, coordinator operates without MCP tool assistance.

    Returns
    -------
    ChatAgent
        Configured catering coordinator agent with web search capabilities

    Notes
    -----
    Returns natural text responses instead of structured output. The coordinator
    will parse the catering recommendations and make routing decisions.

    Uses custom web_search @ai_function instead of HostedWebSearchTool for
    better control over response formatting for language models.
    """
    tools = [web_search]

    if mcp_tool is not None:
        tools.append(mcp_tool)  # type: ignore

    return client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        tools=tools,
        store=True,
    )
