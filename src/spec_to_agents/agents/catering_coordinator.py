# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

from agent_framework import ChatAgent, HostedWebSearchTool, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts import catering_coordinator
from spec_to_agents.prompts.catering_coordinator import SYSTEM_PROMPT
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(
    client: AzureAIAgentClient,
    bing_search: HostedWebSearchTool,
    mcp_tool: MCPStdioTool,
    request_user_input: Callable[..., str],
) -> ChatAgent:
    """
    Create Catering Coordinator agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    bing_search : HostedWebSearchTool
        Web search tool for catering research
    mcp_tool : MCPStdioTool
        Sequential thinking tool for complex reasoning
    request_user_input : Callable[..., str]
        Tool for requesting user input/clarification

    Returns
    -------
    ChatAgent
        Configured catering coordinator agent with Bing search capabilities
    """
    return client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        tools=[bing_search, mcp_tool, request_user_input],
        response_format=SpecialistOutput,
        store=True,
    )


agent = get_chat_client().create_agent(
    name="CateringCoordinatorAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
    additional_chat_options={
        "allow_multiple_tool_calls": True,
        "reasoning": {"effort": "minimal", "summary": "concise"},
    },
)

__all__ = ["agent", "create_agent"]
