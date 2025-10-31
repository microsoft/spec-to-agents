# Copyright (c) Microsoft. All rights reserved.

"""MCP (Model Context Protocol) tools integration."""

import os

from agent_framework import MCPStdioTool


def create_sequential_thinking_tool() -> MCPStdioTool:
    """
    Create a new sequential-thinking-tools MCP server instance.

    Returns an unconnected MCPStdioTool that should be used with
    async context manager pattern for proper lifecycle management.

    Returns
    -------
    MCPStdioTool
        Unconnected MCP tool for advanced reasoning and tool orchestration

    Example
    -------
    >>> async with create_sequential_thinking_tool() as tool:
    ...     workflow = build_event_planning_workflow(tool)
    ...     # tool auto-cleanup on exit

    Notes
    -----
    The MCP tool must be used within an async context manager to ensure
    proper connection establishment and cleanup. The tool connects on
    __aenter__ and closes on __aexit__.
    """
    return MCPStdioTool(
        name="sequential-thinking-tools",
        command="npx",
        args=["-y", "mcp-sequentialthinking-tools"],
        env={
            "MAX_HISTORY_SIZE": os.getenv("MAX_HISTORY_SIZE", "1000"),
        },
    )


__all__ = ["create_sequential_thinking_tool"]
