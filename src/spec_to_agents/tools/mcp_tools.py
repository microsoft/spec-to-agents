# Copyright (c) Microsoft. All rights reserved.

"""MCP (Model Context Protocol) tools integration."""

import os

from agent_framework import MCPStdioTool

# Global MCP tool instance
_mcp_sequential_thinking: MCPStdioTool | None = None


def get_sequential_thinking_tool() -> MCPStdioTool:
    """
    Get or create the sequential-thinking-tools MCP server connection.

    Returns
    -------
    MCPStdioTool
        MCP tool for advanced reasoning and tool orchestration

    Notes
    -----
    The MCP tool lifecycle is managed by the Agent Framework.
    Connection is established automatically when the tool is first used.
    The MCP server is spawned as a subprocess using npx.
    """
    global _mcp_sequential_thinking

    if _mcp_sequential_thinking is None:
        _mcp_sequential_thinking = MCPStdioTool(
            name="sequential-thinking-tools",
            command="npx",
            args=["-y", "mcp-sequentialthinking-tools"],
            env={
                "MAX_HISTORY_SIZE": os.getenv("MAX_HISTORY_SIZE", "1000"),
            },
        )

    return _mcp_sequential_thinking


async def close_sequential_thinking_tool() -> None:
    """
    Close the sequential-thinking-tools MCP server connection.

    Notes
    -----
    Should be called during application shutdown to cleanup resources.
    """
    global _mcp_sequential_thinking
    if _mcp_sequential_thinking is not None:
        await _mcp_sequential_thinking.close()
        _mcp_sequential_thinking = None


__all__ = ["close_sequential_thinking_tool", "get_sequential_thinking_tool"]
