# Copyright (c) Microsoft. All rights reserved.

"""Tests for MCP tool lifecycle management."""

import pytest

from spec_to_agents.tools import get_sequential_thinking_tool


def test_get_sequential_thinking_tool_returns_instance():
    """
    Test that get_sequential_thinking_tool returns an MCPStdioTool instance.

    This test verifies that the MCP tool can be created without errors.
    The tool should NOT be manually connected - the Agent Framework
    manages the lifecycle automatically.
    """
    tool = get_sequential_thinking_tool()

    assert tool is not None
    assert tool.name == "sequential-thinking-tools"
    # Tool should not be connected yet (lifecycle managed by Agent Framework)
    assert not tool.is_connected


def test_get_sequential_thinking_tool_returns_singleton():
    """
    Test that get_sequential_thinking_tool returns the same instance on multiple calls.

    This verifies the singleton pattern for the MCP tool.
    """
    tool1 = get_sequential_thinking_tool()
    tool2 = get_sequential_thinking_tool()

    assert tool1 is tool2


@pytest.mark.asyncio
async def test_sequential_thinking_tool_can_connect():
    """
    Test that the MCP tool can be connected via async context manager.

    This verifies the proper lifecycle management pattern.
    """
    tool = get_sequential_thinking_tool()

    async with tool:
        # Tool should be connected inside the context manager
        assert tool.is_connected

    # Tool should be disconnected after exiting context manager
    assert not tool.is_connected
