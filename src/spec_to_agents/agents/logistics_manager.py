# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts import logistics_manager
from spec_to_agents.prompts.logistics_manager import SYSTEM_PROMPT
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(
    client: AzureAIAgentClient,
    get_weather_forecast: Callable[..., str],
    create_calendar_event: Callable[..., str],
    list_calendar_events: Callable[..., str],
    delete_calendar_event: Callable[..., str],
    mcp_tool: MCPStdioTool,
    request_user_input: Callable[..., str],
) -> ChatAgent:
    """
    Create Logistics Manager agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    get_weather_forecast : Callable[..., str]
        Weather forecasting tool
    create_calendar_event : Callable[..., str]
        Calendar event creation tool
    list_calendar_events : Callable[..., str]
        Calendar event listing tool
    delete_calendar_event : Callable[..., str]
        Calendar event deletion tool
    mcp_tool : MCPStdioTool
        Sequential thinking tool for complex reasoning
    request_user_input : Callable[..., str]
        Tool for requesting user input/clarification

    Returns
    -------
    ChatAgent
        Configured logistics manager agent with weather and calendar capabilities
    """
    return client.create_agent(
        name="LogisticsManager",
        instructions=logistics_manager.SYSTEM_PROMPT,
        tools=[
            get_weather_forecast,
            create_calendar_event,
            list_calendar_events,
            delete_calendar_event,
            mcp_tool,
            request_user_input,
        ],
        response_format=SpecialistOutput,
        store=True,
    )


agent = get_chat_client().create_agent(
    name="LogisticsManagerAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
    additional_chat_options={
        "allow_multiple_tool_calls": True,
        "reasoning": {"effort": "minimal", "summary": "concise"},
    },
)

__all__ = ["agent", "create_agent"]
