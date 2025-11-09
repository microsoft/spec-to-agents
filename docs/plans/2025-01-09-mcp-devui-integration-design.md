# MCP Tools Integration with DevUI - Design Document

**Date:** 2025-01-09
**Status:** Approved for Implementation

## Purpose

Enable MCP (Model Context Protocol) tools, specifically the `sequential-thinking` tool, to work correctly in DevUI mode by aligning the tool lifecycle with DevUI's resource management patterns. Currently, MCP tools are disabled in DevUI due to async context manager lifecycle incompatibilities.

## Problem Statement

### Current Broken State

Between commits `05f04f8` (patched devui) and `6cf6f11` (removed workflow await), an attempt was made to enable MCP tools in DevUI by:

1. Removing the workaround: `container.global_tools.override({})`
2. Adding resource initialization: `await container.init_resources()` in `load_entities()`

This approach violates DevUI's architectural constraints:

- **MCP tools require async context managers** (`__aenter__`/`__aexit__`) for connection lifecycle
- **DevUI uses FastAPI's event loop** managed by `uvicorn`, not manual async context managers
- **Resource initialization happens in wrong event loop**: `asyncio.run(load_entities())` creates a separate, short-lived event loop that completes before DevUI's FastAPI server starts
- **Result**: MCP connections initialize, then immediately close when `load_entities()` completes, leaving tools disconnected when agents try to use them

### Root Cause

The DI container pattern (`dependency-injector` library) with `providers.Resource` for async context managers is incompatible with DevUI's lifecycle model:

1. Container resources need manual initialization via `container.init_resources()` and cleanup via `container.shutdown_resources()`
2. DevUI's lifecycle is managed by FastAPI lifespan hooks, not manual init/shutdown calls
3. The two lifecycles don't align: Container resources initialized in `asyncio.run()` → close immediately vs. DevUI server lifecycle → runs until shutdown

## Solution Overview

**Pattern:** Agent-Level Lazy Initialization

Both `console.py` (CLI mode) and `main.py` (DevUI mode) will use the same DI container pattern:
- Create MCP tool instances (not connected)
- Pass tools to agents via DI injection
- Let the framework manage `__aenter__` (lazy connection) and `__aexit__` (cleanup)

**Key architectural principle:** The framework handles MCP tool lifecycle automatically:
- **Console.py:** Agent Framework's `ChatAgent` manages tool lifecycle via its internal exit stack
- **Main.py:** DevUI's `_cleanup_entities()` manages tool lifecycle by calling `close()` on tools tracked in `_local_mcp_tools`

## Architecture

### Before (Broken)

```
main.py:
  asyncio.run(load_entities()):
    await container.init_resources()  # Opens MCP connections
    # Returns entities
  # asyncio.run() completes → MCP connections close
  serve(entities)  # Tools disconnected!
```

### After (Fixed)

```
main.py:
  container = AppContainer()
  container.wire()
  entities = export_agents()  # MCP tools passed but not connected
  serve(entities)
    ↓ DevUI startup
    ↓ Agent.run() → MCP tool.__aenter__() (lazy connection)
    ↓ Agent execution with connected tools
    ↓ DevUI shutdown → _cleanup_entities() → tool.close()
```

### Execution Flow Comparison

**Console.py (CLI Mode):**
```
async with container.client():
    workflow = build_workflow()
    # Agents have MCP tool instances
    await workflow.run()
        ↓ ChatAgent manages tool lifecycle via exit stack
        ↓ Tool.__aenter__() on first use
        ↓ Execution
        ↓ Tool.__aexit__() when agent completes
```

**Main.py (DevUI Mode):**
```
serve(entities):
    ↓ FastAPI lifespan startup
    ↓ DevUI discovers entities with MCP tools
    ↓ HTTP request → agent execution
        ↓ Tool.__aenter__() on first use (lazy)
        ↓ Execution
        ↓ Tool tracked in _local_mcp_tools
    ↓ FastAPI lifespan shutdown
    ↓ _cleanup_entities() → tool.close()
```

## Component Changes

### 1. MCP Tools Module (`src/spec_to_agents/tools/mcp_tools.py`)

**Before:**
```python
@asynccontextmanager
async def create_global_tools() -> AsyncGenerator[dict[str, ToolProtocol], None]:
    sequential_thinking_tool = MCPStdioTool(...)
    async with sequential_thinking_tool:
        yield {"sequential-thinking": sequential_thinking_tool}
```

**After:**
```python
def create_mcp_tool_instances() -> dict[str, ToolProtocol]:
    """
    Create MCP tool instances for framework-managed lifecycle.

    Tools are NOT connected when created. They connect lazily on first use
    via __aenter__() and cleanup automatically via framework's exit stack
    or DevUI's _cleanup_entities().

    Returns
    -------
    dict[str, ToolProtocol]
        Dictionary of MCP tool instances (not connected)
        Keys:
        - "sequential-thinking": MCP sequential thinking tool
    """
    from agent_framework import MCPStdioTool

    return {
        "sequential-thinking": MCPStdioTool(
            name="sequential-thinking",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
        )
    }
```

**Changes:**
- Remove `@asynccontextmanager` decorator
- Remove `async with` context management
- Return raw tool instances
- Framework handles lifecycle via `__aenter__`/`__aexit__`

### 2. DI Container (`src/spec_to_agents/container.py`)

**Before:**
```python
class AppContainer(containers.DeclarativeContainer):
    client = providers.Singleton(create_agent_client_for_devui)
    global_tools = providers.Resource(create_global_tools)  # Async context manager
    model_config = providers.Singleton(get_default_model_config)
```

**After:**
```python
class AppContainer(containers.DeclarativeContainer):
    client = providers.Singleton(create_agent_client_for_devui)
    global_tools = providers.Singleton(create_mcp_tool_instances)  # Simple factory
    model_config = providers.Singleton(get_default_model_config)
```

**Changes:**
- Change `global_tools` from `providers.Resource` to `providers.Singleton`
- Use `create_mcp_tool_instances` instead of `create_global_tools`
- No more manual `init_resources()` / `shutdown_resources()` needed

**Docstring updates:**
- Remove references to `init_resources()` / `shutdown_resources()`
- Document that tools are framework-managed
- Update usage examples

### 3. Main.py (DevUI Entry Point)

**Before:**
```python
def main() -> None:
    container = AppContainer()
    container.wire(modules=[__name__])

    container.global_tools.override({})  # Disable MCP tools

    async def load_entities():
        await container.init_resources()  # Wrong event loop!
        workflows = export_workflow()
        agents = export_agents()
        return workflows + agents

    entities = asyncio.run(load_entities())
    serve(entities=entities, ...)
```

**After:**
```python
def main() -> None:
    container = AppContainer()
    container.wire(modules=[__name__])

    # No override needed - tools work now
    # No init_resources() - framework handles lifecycle

    workflows = export_workflow()
    agents = export_agents()

    serve(entities=workflows + agents, port=port, host="localhost", auto_open=auto_open)
    # DevUI's _cleanup_entities() handles MCP tool cleanup
```

**Changes:**
- Remove `container.global_tools.override({})`
- Remove `async def load_entities()`
- Remove `asyncio.run()` wrapper
- Remove `await container.init_resources()`
- Load entities synchronously
- Trust DevUI to manage tool lifecycle

### 4. Console.py (CLI Entry Point)

**Before:**
```python
async def main() -> None:
    container = AppContainer()
    container.wire(modules=[__name__])

    from spec_to_agents.tools.mcp_tools import create_global_tools

    async with container.client(), create_global_tools() as tools:
        container.global_tools.override(tools)
        try:
            workflow = build_event_planning_workflow()
            # ... execute workflow ...
        finally:
            container.global_tools.reset_override()
```

**After:**
```python
async def main() -> None:
    container = AppContainer()
    container.wire(modules=[__name__])

    # Agent client handles async context for itself
    async with container.client():
        # MCP tools automatically injected via DI
        # ChatAgent manages tool lifecycle via exit stack
        workflow = build_event_planning_workflow()
        # ... execute workflow ...
        # No manual override/reset needed
```

**Changes:**
- Remove `create_global_tools()` import and async context
- Remove `container.global_tools.override(tools)`
- Remove `try/finally` and `reset_override()`
- Simplify to just `async with container.client()`
- Trust Agent Framework's exit stack to manage tool lifecycle

### 5. Agent Factories (e.g., `budget_analyst.py`)

**No changes needed!** Current code already handles optional tools:

```python
@inject
def create_agent(
    client: BaseChatClient = Provide["client"],
    global_tools: dict[str, ToolProtocol] = Provide["global_tools"],
    model_config: dict[str, Any] = Provide["model_config"],
) -> ChatAgent:
    code_interpreter = HostedCodeInterpreterTool(...)
    agent_tools: list[ToolProtocol] = [code_interpreter]

    if global_tools.get("sequential-thinking"):
        agent_tools.append(global_tools["sequential-thinking"])

    return client.create_agent(
        name="budget_analyst",
        tools=agent_tools,
        # ...
    )
```

The injected `global_tools` will now contain MCP tool instances instead of empty dict.

## Framework Lifecycle Details

### How DevUI Manages MCP Tools

DevUI's `_cleanup_entities()` method (in `agent_framework_devui/_server.py:181-266`) handles cleanup:

```python
async def _cleanup_entities(self) -> None:
    for entity_info in entities:
        entity_obj = self.executor.entity_discovery.get_entity_object(entity_id)

        # Close MCP tools (framework tracks them in _local_mcp_tools)
        if entity_obj and hasattr(entity_obj, "_local_mcp_tools"):
            for mcp_tool in entity_obj._local_mcp_tools:
                if hasattr(mcp_tool, "close") and callable(mcp_tool.close):
                    if inspect.iscoroutinefunction(mcp_tool.close):
                        await mcp_tool.close()
                    else:
                        mcp_tool.close()
```

### How Agent Framework Manages MCP Tools

`ChatAgent` uses internal `_async_exit_stack` to manage tool lifecycle:
- Tools with `__aenter__` are entered into the exit stack on first use
- Connections remain open for the agent's lifetime
- Cleanup happens automatically when exit stack closes

## Testing Strategy

### Validation Steps

1. **DevUI Mode Testing:**
   ```bash
   uv run app
   # Navigate to http://localhost:8080
   # Create a workflow execution
   # Verify MCP sequential-thinking tool appears in tool list
   # Execute workflow and verify tool calls succeed
   # Check browser console for no connection errors
   ```

2. **CLI Mode Testing:**
   ```bash
   uv run console
   # Enter event planning request
   # Verify MCP tool available and working
   # Check no lifecycle errors in output
   ```

3. **Playwright Automated Testing:**
   - Launch DevUI via playwright
   - Navigate to workflow page
   - Verify entities load successfully
   - Check browser console logs for errors
   - Verify network requests show no failed connections
   - Execute a test workflow and verify completion

### Expected Outcomes

**DevUI Mode:**
- MCP tools appear in agent tool lists
- Tool calls execute successfully
- No "No thread ID was provided" errors
- No "connections will close before execution" warnings
- Clean shutdown with no connection errors

**CLI Mode:**
- MCP tools work identically to before
- No behavior changes for console users
- Clean lifecycle management maintained

## Risk Mitigation

### Potential Issues

1. **Multiple tool instances per agent:** Each agent gets its own MCP tool instance
   - **Mitigation:** Acceptable for dev environments; future optimization can share instances if needed
   - **Trade-off:** Simplicity over resource efficiency

2. **DevUI cleanup failure:** If `_cleanup_entities()` fails to close tools
   - **Mitigation:** Framework's cleanup is battle-tested; error handling already in place
   - **Fallback:** Process termination will close connections anyway

3. **Lazy initialization delay:** First tool use incurs connection overhead
   - **Mitigation:** MCP tool connections are fast (< 1s); acceptable for dev UX
   - **Trade-off:** No eager initialization complexity

## Implementation Checklist

- [ ] Refactor `mcp_tools.py`: Remove async context manager, add simple factory
- [ ] Update `container.py`: Change `Resource` to `Singleton`, update docstrings
- [ ] Simplify `main.py`: Remove override, async loading, init_resources
- [ ] Simplify `console.py`: Remove manual override/reset pattern
- [ ] Test DevUI mode: Verify MCP tools work end-to-end
- [ ] Test CLI mode: Verify no regressions
- [ ] Playwright test: Automate DevUI validation
- [ ] Update CLAUDE.md if needed: Document new pattern

## Success Criteria

1. MCP `sequential-thinking` tool successfully invocable in DevUI mode
2. No connection lifecycle errors in DevUI startup/shutdown
3. Console.py maintains existing functionality without changes to user experience
4. Playwright tests pass showing successful tool integration
5. Code is simpler with less manual lifecycle management

## References

- **Agent Framework DevUI Source:** `.venv/lib/python3.13/site-packages/agent_framework_devui/_server.py`
- **DeepWiki Research:** Comprehensive analysis of DevUI lifecycle patterns and constraints
- **PLANS.md:** `specs/PLANS.md` - ExecPlan authoring guidelines (for future detailed specs)
