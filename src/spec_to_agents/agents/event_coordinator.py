# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts import event_coordinator
from spec_to_agents.prompts.event_coordinator import SYSTEM_PROMPT


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


agent = get_chat_client().create_agent(
    name="EventCoordinatorAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
    additional_chat_options={
        "allow_multiple_tool_calls": True,
        "reasoning": {"effort": "minimal", "summary": "concise"},
    },
)

__all__ = ["agent", "create_agent"]
