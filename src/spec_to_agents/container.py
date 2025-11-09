# Copyright (c) Microsoft. All rights reserved.

"""Dependency injection container for application-wide dependencies."""

from dependency_injector import containers, providers

from spec_to_agents.config import get_default_model_config
from spec_to_agents.tools.mcp_tools import create_global_tools
from spec_to_agents.utils.clients import create_agent_client_for_devui


class AppContainer(containers.DeclarativeContainer):
    """
    Application-wide dependency injection container.

    Manages lifecycle and injection of:
    - Azure AI agent client (singleton)
    - Global tools dictionary (MCP tools, resource with async context management)

    The tools provider returns a dict[str, ToolProtocol] containing globally
    shared tools (currently just MCP sequential-thinking tool). Agent-specific
    tools (web search, code interpreter, weather, calendar) are initialized
    inside each agent's create_agent() factory function, not via DI injection.

    Agent factories can selectively access global tools by key:
        global_tools["sequential-thinking"]

    Usage in console.py:
        container = AppContainer()
        container.wire(modules=[...])
        async with container.client():
            await container.init_resources()  # Initialize and connect MCP tools
            # Dependencies injected into agent factories
            workflow = build_event_planning_workflow()
            # Use workflow...
            await container.shutdown_resources()  # Cleanup MCP tools
        # Client automatically cleaned up by async context manager

    Notes
    -----
    The global_tools Resource provider manages the async context lifecycle
    of MCP tools. Call container.init_resources() to connect tools and
    container.shutdown_resources() to properly cleanup connections.
    """

    # Configuration
    config = providers.Configuration()

    # Client provider (singleton factory)
    # Uses non-context-managed client for DI compatibility
    client = providers.Singleton(
        create_agent_client_for_devui,
    )

    # Global tools provider (async resource with lifecycle management)
    # Provides dict[str, ToolProtocol] with proper async context management for MCP tools
    global_tools = providers.Resource(
        create_global_tools,
    )

    model_config = providers.Singleton(
        get_default_model_config,
    )

    # Wiring configuration: modules that use @inject
    wiring_config = containers.WiringConfiguration(
        packages=[
            "spec_to_agents.agents",
            "spec_to_agents.workflow",
        ]
    )
