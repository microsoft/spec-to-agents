# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import event_coordinator


def create_agent(
    client: AzureAIAgentClient,
    mcp_tool: MCPStdioTool,
) -> ChatAgent:
    """
    Create Event Coordinator agent for workflow orchestration.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    mcp_tool : MCPStdioTool
        Sequential thinking tool for complex reasoning

    Returns
    -------
    ChatAgent
        Configured event coordinator agent for workflow orchestration
    """
    return client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        tools=[mcp_tool],
        store=True,
    )
