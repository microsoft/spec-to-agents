# Copyright (c) Microsoft. All rights reserved.

"""MCP (Model Context Protocol) tools integration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from agent_framework import MCPStdioTool, ToolProtocol


@asynccontextmanager
async def create_global_tools() -> AsyncGenerator[dict[str, ToolProtocol], None]:
    """
    Create and manage a global toolset including MCP tools.

    This async context manager initializer properly manages the lifecycle
    of MCP tools by entering their async context on initialization and
    exiting on cleanup.

    Yields
    ------
    dict[str, ToolProtocol]
        Tools dictionary containing connected MCP tools for advanced reasoning

    Example
    -------
    Used with Resource provider in DI container::

        class AppContainer(containers.DeclarativeContainer):
            global_tools = providers.Resource(create_global_tools)


        async with container:
            await container.init_resources()
            # tools are connected
            await container.shutdown_resources()
            # tools are properly cleaned up

    Notes
    -----
    The MCP tools require async context management to ensure proper
    connection establishment via __aenter__ and cleanup via __aexit__.
    This function wraps the MCPStdioTool instances in an async context
    manager to handle their lifecycle automatically.
    """
    # Create MCP tool instances
    sequential_thinking_tool = MCPStdioTool(
        name="sequential-thinking", command="npx", args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
    )

    # Enter async context for each MCP tool
    async with sequential_thinking_tool:
        # Yield tools dict for injection
        yield {"sequential-thinking": sequential_thinking_tool}
    # Cleanup happens automatically when async context exits


__all__ = ["create_global_tools"]
