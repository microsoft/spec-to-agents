# Copyright (c) Microsoft. All rights reserved.

"""Tests for MCP tools factory pattern."""

from agent_framework import MCPStdioTool

from spec_to_agents.tools.mcp_tools import create_sequential_thinking_tool


def test_create_sequential_thinking_tool_returns_mcp_stdio_tool():
    """Test that factory returns MCPStdioTool instance."""
    tool = create_sequential_thinking_tool()

    assert isinstance(tool, MCPStdioTool)
    assert tool.name == "sequential-thinking-tools"


def test_create_sequential_thinking_tool_returns_new_instance():
    """Test that factory returns new instances (not singleton)."""
    tool1 = create_sequential_thinking_tool()
    tool2 = create_sequential_thinking_tool()

    # Should be different instances
    assert tool1 is not tool2
