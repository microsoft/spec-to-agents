# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.models.messages import SpecialistOutput
from spec_to_agents.prompts import logistics_manager
from spec_to_agents.tools import (
    create_calendar_event,
    delete_calendar_event,
    get_weather_forecast,
    list_calendar_events,
)


def create_agent(
    client: AzureAIAgentClient,
    mcp_tool: MCPStdioTool | None,
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
    mcp_tool : MCPStdioTool | None, optional
        Sequential thinking tool for complex reasoning.
        If None, coordinator operates without MCP tool assistance.

    Returns
    -------
    ChatAgent
        Configured logistics manager agent with weather and calendar capabilities

    Notes
    -----
    MCP sequential-thinking tool was removed because it interferes with
    structured output generation (SpecialistOutput). The agent would complete
    its thinking process but fail to return a final structured response,
    causing ValueError in the workflow.
    """
    tools = [
        get_weather_forecast,
        create_calendar_event,
        list_calendar_events,
        delete_calendar_event,
    ]

    if mcp_tool is not None:
        tools.append(mcp_tool)  # type: ignore

    return client.create_agent(
        name="LogisticsManager",
        instructions=logistics_manager.SYSTEM_PROMPT,
        tools=tools,
        response_format=SpecialistOutput,
        store=True,
    )
