# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent, HostedCodeInterpreterTool


def export_agents() -> list[ChatAgent]:
    """
    Export individual agents for standalone testing in DevUI.

    This function creates and returns all specialist agents (Budget Analyst,
    Venue Specialist, Catering Coordinator, Logistics Manager) without the
    full workflow orchestration. This allows attendees to test and interact
    with individual agents directly in the DevUI.

    Returns
    -------
    list[ChatAgent]
        List containing individual agent instances for DevUI testing

    Notes
    -----
    Each agent is created with a fresh client instance. The agents use
    lazy initialization to avoid creating resources until actually needed.
    The agents are configured with their tools but without workflow coordination.
    """
    from spec_to_agents.agents import (
        budget_analyst,
        catering_coordinator,
        logistics_manager,
        venue_specialist,
    )
    from spec_to_agents.tools import (
        create_calendar_event,
        delete_calendar_event,
        get_weather_forecast,
        list_calendar_events,
        web_search,
    )
    from spec_to_agents.utils.clients import create_agent_client

    # Create client for agents
    # DevUI's FastAPI lifespan hooks call close() on each agent's chat_client
    # during shutdown, ensuring proper cleanup of Azure AI resources.
    # See: agent_framework_devui/_server.py::_cleanup_entities()
    client = create_agent_client()

    # Create code interpreter tool for budget analyst
    code_interpreter = HostedCodeInterpreterTool(
        description=(
            "Execute Python code for complex financial calculations, budget analysis, "
            "cost projections, and data visualization. Creates a scratchpad for "
            "intermediate calculations and maintains calculation history."
        ),
    )

    # Create individual agents with their respective tools
    return [
        budget_analyst.create_agent(client, code_interpreter, None),
        venue_specialist.create_agent(client, web_search, None),
        catering_coordinator.create_agent(client, web_search, None),
        logistics_manager.create_agent(
            client,
            get_weather_forecast,  # type: ignore
            create_calendar_event,  # type: ignore
            list_calendar_events,  # type: ignore
            delete_calendar_event,  # type: ignore
            None,
        ),
    ]


__all__ = ["export_agents"]
