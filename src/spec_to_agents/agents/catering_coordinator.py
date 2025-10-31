# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable

from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.models.messages import SpecialistOutput
from spec_to_agents.prompts import catering_coordinator


def create_agent(
    client: AzureAIAgentClient, web_search: Callable[..., Any], mcp_tool: MCPStdioTool | None
) -> ChatAgent:
    """
    Create Catering Coordinator agent for event planning workflow.

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
        Configured catering coordinator agent with web search capabilities

    Notes
    -----
    MCP sequential-thinking tool was removed because it interferes with
    structured output generation (SpecialistOutput). The agent would complete
    its thinking process but fail to return a final structured response,
    causing ValueError in the workflow.

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
        response_format=SpecialistOutput,
        store=True,
    )
