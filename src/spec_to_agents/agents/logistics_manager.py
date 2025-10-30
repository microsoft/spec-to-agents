# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import logistics_manager
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(
    client: AzureAIAgentClient,
    get_weather_forecast: Callable[..., str],
    create_calendar_event: Callable[..., str],
    list_calendar_events: Callable[..., str],
    delete_calendar_event: Callable[..., str],
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
    return client.create_agent(
        name="LogisticsManager",
        instructions=logistics_manager.SYSTEM_PROMPT,
        tools=[
            get_weather_forecast,
            create_calendar_event,
            list_calendar_events,
            delete_calendar_event,
        ],
        response_format=SpecialistOutput,
        store=True,
    )
