# Copyright (c) Microsoft. All rights reserved.

"""MCP (Model Context Protocol) tools integration."""

from agent_framework import MCPStdioTool, ToolProtocol


def create_global_tools() -> dict[str, ToolProtocol]:
    """
    Create a global toolset including MCP tools.

    Returns a dict containing ToolProtocol that interface with the
    async context manager pattern for proper lifecycle management.

    Returns
    -------
    dict[str, ToolProtocol]
        Tools and unconnected MCP tools for advanced reasoning and tool orchestration
    Example
    -------
    >>> async with create_global_tools() as tools:
    ...     workflow = build_event_planning_workflow(tools)
    ...     # tools auto-cleanup on exit

    Notes
    -----
    The MCP tools must be used within an async context manager to ensure
    proper connection establishment and cleanup. The tools connect on
    __aenter__ and close on __aexit__.
    """
    return {
        "sequential-thinking": MCPStdioTool(
            name="sequential-thinking", command="npx", args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
        )
    }


__all__ = ["create_global_tools"]
