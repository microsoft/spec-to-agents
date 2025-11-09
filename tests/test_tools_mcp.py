# Copyright (c) Microsoft. All rights reserved.

"""Tests for MCP tools factory pattern."""

from agent_framework import MCPStdioTool

from spec_to_agents.tools.mcp_tools import create_mcp_tool_instances


def test_create_mcp_tool_instances_returns_dict():
    """Test that factory returns dictionary of MCP tools."""
    tools = create_mcp_tool_instances()

    assert isinstance(tools, dict)
    assert "sequential-thinking" in tools
    assert isinstance(tools["sequential-thinking"], MCPStdioTool)


def test_create_mcp_tool_instances_returns_new_instances():
    """Test that factory returns new instances (not singleton)."""
    tools1 = create_mcp_tool_instances()
    tools2 = create_mcp_tool_instances()

    # Should be different dictionaries with different tool instances
    assert tools1 is not tools2
    assert tools1["sequential-thinking"] is not tools2["sequential-thinking"]
