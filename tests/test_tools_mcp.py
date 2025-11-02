# Copyright (c) Microsoft. All rights reserved.

"""Tests for MCP tools factory pattern."""

from agent_framework import MCPStdioTool

from spec_to_agents.tools.mcp_tools import create_global_tools


def test_create_global_tools_returns_dict() -> None:
    """Test that factory returns dict of tools."""
    tools = create_global_tools()

    assert isinstance(tools, dict)
    assert "sequential-thinking" in tools
    assert isinstance(tools["sequential-thinking"], MCPStdioTool)


def test_create_global_tools_sequential_thinking_config() -> None:
    """Test sequential-thinking tool configuration."""
    tools = create_global_tools()
    tool = tools["sequential-thinking"]

    assert tool.name == "sequential-thinking"
