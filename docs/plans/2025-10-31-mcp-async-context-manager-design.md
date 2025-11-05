# MCP Async Context Manager Refactor Design

**Date:** 2025-10-31
**Status:** Approved
**Author:** Claude Code

## Overview

Refactor the sequential-thinking-tools MCP server lifecycle management from a global singleton with manual cleanup to proper async context manager pattern following Agent Framework best practices.

## Problem Statement

The current implementation has several issues:

1. **Global State**: `_mcp_sequential_thinking` global variable creates hidden state
2. **Manual Cleanup**: Requires explicit `close_sequential_thinking_tool()` call in finally blocks
3. **Error Suppression**: Cleanup errors are suppressed with `contextlib.suppress()` due to asyncio context issues
4. **Lifecycle Coupling**: Tool lifecycle tied to application lifecycle rather than usage scope

```python
# Current problematic pattern
try:
    workflow = build_event_planning_workflow()
    # ... use workflow ...
finally:
    with contextlib.suppress(RuntimeError, Exception):
        await close_sequential_thinking_tool()  # Fragile cleanup
```

## Design Goals

1. Eliminate global state
2. Follow Agent Framework's async context manager pattern
3. Ensure reliable cleanup without error suppression
4. Improve testability and composability
5. Maintain backwards compatibility where possible

## Architecture

### Component Changes

#### 1. MCP Tools Module (`mcp_tools.py`)

**Change:** Convert from singleton getter to factory function

**Before:**
```python
_mcp_sequential_thinking: MCPStdioTool | None = None

def get_sequential_thinking_tool() -> MCPStdioTool:
    global _mcp_sequential_thinking
    if _mcp_sequential_thinking is None:
        _mcp_sequential_thinking = MCPStdioTool(...)
    return _mcp_sequential_thinking

async def close_sequential_thinking_tool() -> None:
    global _mcp_sequential_thinking
    if _mcp_sequential_thinking is not None:
        await _mcp_sequential_thinking.close()
        _mcp_sequential_thinking = None
```

**After:**
```python
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
    """
    return MCPStdioTool(
        name="sequential-thinking-tools",
        command="npx",
        args=["-y", "mcp-sequentialthinking-tools"],
        env={"MAX_HISTORY_SIZE": os.getenv("MAX_HISTORY_SIZE", "1000")},
    )
```

**Benefits:**
- Pure function - no side effects
- No global state
- No manual cleanup function needed
- Clear documentation of usage pattern

#### 2. Workflow Builder (`event_planning_workflow.py`)

**Change:** Accept optional MCP tool parameter

**Signature:**
```python
def build_event_planning_workflow(
    mcp_tool: MCPStdioTool | None = None
) -> Workflow:
    """
    Build the multi-agent event planning workflow.

    Parameters
    ----------
    mcp_tool : MCPStdioTool | None, optional
        Connected MCP tool for coordinator's sequential thinking.
        If None, coordinator operates without MCP tool assistance.

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution
    """
```

**Implementation:**
```python
def build_event_planning_workflow(
    mcp_tool: MCPStdioTool | None = None
) -> Workflow:
    client = get_chat_client()

    # Create coordinator with optional MCP tool
    coordinator_agent = event_coordinator.create_agent(
        client,
        mcp_tool,  # Can be None
    )

    # ... rest of workflow setup ...
```

**Benefits:**
- Explicit dependency injection
- Testable (can inject mock tool)
- Backwards compatible (None default)
- Clear ownership (caller manages tool lifecycle)

#### 3. Console Main (`console.py`)

**Change:** Use async context manager for MCP tool lifecycle

**Before:**
```python
async def main() -> None:
    try:
        workflow = build_event_planning_workflow()
        # ... use workflow ...
    finally:
        with contextlib.suppress(RuntimeError, Exception):
            await close_sequential_thinking_tool()
```

**After:**
```python
async def main() -> None:
    print("Event Planning Workflow - Interactive CLI")
    # ... setup ...

    # Use async context manager for proper lifecycle
    async with create_sequential_thinking_tool() as mcp_tool:
        # Build workflow with connected tool
        workflow = build_event_planning_workflow(mcp_tool)

        # ... workflow execution loop ...

    # No cleanup needed - async with handles it
```

**Benefits:**
- Automatic connection on entry (`__aenter__` → `connect()`)
- Guaranteed cleanup on exit (`__aexit__` → `close()`)
- Handles exceptions properly
- No error suppression needed
- Cleaner code structure

### Lifecycle Flow

```
1. console.py:main() starts
2. async with create_sequential_thinking_tool():
   a. MCPStdioTool.__aenter__() called
   b. connect() establishes subprocess connection
3. build_event_planning_workflow(mcp_tool) receives connected tool
4. Workflow executes with MCP tool available
5. Context exits (normal or exception):
   a. MCPStdioTool.__aexit__() called
   b. close() terminates subprocess
   c. Resources cleaned up
```

### Error Handling

The async context manager pattern handles all scenarios:

| Scenario | Behavior |
|----------|----------|
| Normal completion | `__aexit__` called, cleanup guaranteed |
| User interrupt (Ctrl+C) | `__aexit__` called, cleanup guaranteed |
| Workflow exception | `__aexit__` called, cleanup guaranteed |
| Connection failure | `__aenter__` raises, no cleanup needed |

No error suppression required - Agent Framework's implementation handles asyncio context properly.

## Migration Impact

### Breaking Changes
- `get_sequential_thinking_tool()` removed (renamed to `create_sequential_thinking_tool()`)
- `close_sequential_thinking_tool()` removed (use async context manager)

### Affected Files
1. `src/spec_to_agents/tools/mcp_tools.py` - Factory function
2. `src/spec_to_agents/workflow/event_planning_workflow.py` - Signature change
3. `src/spec_to_agents/console.py` - Context manager usage
4. `tests/test_tools_mcp.py` - Update test patterns (if exists)

### Backwards Compatibility
- `build_event_planning_workflow()` defaults to `None` for MCP tool
- Existing code that doesn't use MCP tool continues to work
- Only console.py needs immediate update for proper lifecycle

## Testing Strategy

1. **Unit Tests**: Test `create_sequential_thinking_tool()` returns proper MCPStdioTool
2. **Integration Tests**: Test workflow builder with/without MCP tool
3. **Lifecycle Tests**: Verify cleanup happens on normal/exception paths
4. **Manual Testing**: Run console.py end-to-end with MCP tool

## References

- [Agent Framework DeepWiki - MCP Async Context Managers](https://deepwiki.com/search/how-do-i-properly-use-async-co_2929bb38-1aaa-48ff-9662-bbbb263da7f1)
- Agent Framework `MCPStdioTool` implementation
- Project: `CLAUDE.md` - Development Guidelines

## Implementation Checklist

- [ ] Refactor `mcp_tools.py` to factory pattern
- [ ] Update `event_planning_workflow.py` signature
- [ ] Refactor `console.py` to use async context manager
- [ ] Update tests for new patterns
- [ ] Verify cleanup with manual testing
- [ ] Remove deprecated functions from `__all__` exports
