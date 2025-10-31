# Copyright (c) Microsoft. All rights reserved.

"""
Centralized agent factory for creating all event planning agents.

This module provides a single location for configuring and creating all agents
in the event planning workflow, making it easier to:
- Audit which tools each agent uses
- Change agent types or show alternatives
- Maintain consistent agent configuration patterns
"""

from typing import Any, Callable

from agent_framework import ChatAgent, HostedCodeInterpreterTool, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.models.messages import SpecialistOutput
from spec_to_agents.prompts import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)


def create_event_coordinator_agent(
    client: AzureAIAgentClient,
) -> ChatAgent:
    """
    Create Event Coordinator agent for workflow orchestration.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation

    Returns
    -------
    ChatAgent
        Configured event coordinator agent for workflow orchestration
    """
    return client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        store=True,
    )


def create_venue_specialist_agent(
    client: AzureAIAgentClient, web_search: Callable[..., Any], mcp_tool: MCPStdioTool | None
) -> ChatAgent:
    """
    Create Venue Specialist agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    web_search : Callable
        Custom web search function decorated with @ai_function
    mcp_tool : MCPStdioTool | None, optional
        Sequential thinking tool for complex reasoning.
        If None, venue specialist operates without MCP tool assistance.

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
    tools = [web_search]
    if mcp_tool is not None:
        tools.append(mcp_tool)  # type: ignore
    return client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        tools=tools,
        response_format=SpecialistOutput,
        store=True,
    )


def create_budget_analyst_agent(
    client: AzureAIAgentClient, code_interpreter: HostedCodeInterpreterTool, mcp_tool: MCPStdioTool | None
) -> ChatAgent:
    """
    Create Budget Analyst agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    code_interpreter : HostedCodeInterpreterTool
        Python code execution tool for financial calculations
    mcp_tool : MCPStdioTool | None, optional
        Sequential thinking tool for complex reasoning.
        If None, the budget analyst agent operates without MCP tool assistance.

    Returns
    -------
    ChatAgent
        Configured budget analyst agent with code interpreter capabilities

    Notes
    -----
    MCP sequential-thinking tool was removed because it interferes with
    structured output generation (SpecialistOutput). The agent would complete
    its thinking process but fail to return a final structured response,
    causing ValueError in the workflow.

    User input is handled through SpecialistOutput.user_input_needed field,
    not through a separate tool.
    """
    tools = [code_interpreter]
    if mcp_tool is not None:
        tools.append(mcp_tool)  # type: ignore
    return client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=tools,
        response_format=SpecialistOutput,
        store=True,
    )


def create_catering_coordinator_agent(
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
        If None, catering coordinator agent operates without MCP tool assistance.

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


def create_logistics_manager_agent(
    client: AzureAIAgentClient,
    get_weather_forecast: Callable[..., str],
    create_calendar_event: Callable[..., str],
    list_calendar_events: Callable[..., str],
    delete_calendar_event: Callable[..., str],
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
        If None, the logistics manager agent operates without MCP tool assistance.

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


__all__ = [
    "create_budget_analyst_agent",
    "create_catering_coordinator_agent",
    "create_event_coordinator_agent",
    "create_logistics_manager_agent",
    "create_venue_specialist_agent",
]
