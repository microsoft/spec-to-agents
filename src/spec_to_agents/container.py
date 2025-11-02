# Copyright (c) Microsoft. All rights reserved.

"""Dependency injection container for application-wide dependencies."""

from dependency_injector import containers, providers

from spec_to_agents.tools.mcp_tools import create_global_tools
from spec_to_agents.utils.clients import create_agent_client_for_devui


class AppContainer(containers.DeclarativeContainer):
    """
    Application-wide dependency injection container.

    Manages lifecycle and injection of:
    - Azure AI agent client (singleton)
    - Global tools dictionary (MCP tools, singleton)

    The tools provider returns a dict[str, ToolProtocol] containing globally
    shared tools (currently just MCP sequential-thinking tool). Agent-specific
    tools (web search, code interpreter, weather, calendar) are initialized
    inside each agent's create_agent() factory function, not via DI injection.

    Agent factories can selectively access global tools by key:
        global_tools["sequential-thinking"]

    Usage in console.py:
        container = AppContainer()
        container.wire(modules=[...])
        client = container.client()  # Direct access to singleton client
        # Dependencies injected into agent factories
        # MCP tools are automatically connected by agent framework when agents are created
        workflow = build_event_planning_workflow()

    Note: The client uses create_agent_client_for_devui which doesn't auto-cleanup.
    For proper cleanup in console.py, manually manage client lifecycle.
    """

    # Configuration
    config = providers.Configuration()

    # Client provider (singleton factory)
    # Uses non-context-managed client for DI compatibility
    client = providers.Singleton(
        create_agent_client_for_devui,
    )

    # Global tools provider (singleton)
    # Provides dict[str, ToolProtocol] created once and injected into all agent factories
    global_tools = providers.Singleton(
        create_global_tools,
    )

    # Wiring configuration: modules that use @inject
    wiring_config = containers.WiringConfiguration(
        modules=[
            "spec_to_agents.agents.budget_analyst",
            "spec_to_agents.agents.catering_coordinator",
            "spec_to_agents.agents.logistics_manager",
            "spec_to_agents.agents.venue_specialist",
            "spec_to_agents.agents.supervisor",
            "spec_to_agents.workflow.core",
        ]
    )
