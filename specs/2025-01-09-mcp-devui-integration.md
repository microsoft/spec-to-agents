# MCP Tools DevUI Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable MCP tools (sequential-thinking) to work in DevUI mode by aligning tool lifecycle with framework-managed patterns.

**Architecture:** Refactor from DI container Resource provider (manual async context) to Singleton factory (framework-managed lifecycle). Both console.py and main.py use same DI pattern, framework handles `__aenter__`/`__aexit__` automatically.

**Tech Stack:** Python 3.11+, dependency-injector, agent-framework, pytest, playwright (for validation)

---

## Task 1: Refactor MCP Tools Module

**Files:**
- Modify: `src/spec_to_agents/tools/mcp_tools.py`
- Test: Manual testing (no unit test needed for simple factory)

**Step 1: Review current implementation**

Read: `src/spec_to_agents/tools/mcp_tools.py`

Current code has `create_global_tools()` async context manager. We need to replace it with a simple factory function.

**Step 2: Replace async context manager with factory function**

Replace entire content of `src/spec_to_agents/tools/mcp_tools.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""MCP (Model Context Protocol) tools integration."""

from agent_framework import MCPStdioTool, ToolProtocol


def create_mcp_tool_instances() -> dict[str, ToolProtocol]:
    """
    Create MCP tool instances for framework-managed lifecycle.

    Tools are NOT connected when created. They connect lazily on first use
    via __aenter__() and cleanup automatically via:
    - DevUI mode: DevUI's _cleanup_entities() calls tool.close()
    - Console mode: ChatAgent's exit stack manages __aenter__/__aexit__

    Returns
    -------
    dict[str, ToolProtocol]
        Dictionary of MCP tool instances (not connected yet)
        Keys:
        - "sequential-thinking": MCP sequential thinking tool for advanced reasoning

    Example
    -------
    Used with Singleton provider in DI container::

        class AppContainer(containers.DeclarativeContainer):
            global_tools = providers.Singleton(create_mcp_tool_instances)

        container = AppContainer()
        tools = container.global_tools()  # Get tool instances
        # Framework manages lifecycle from here

    Notes
    -----
    The MCP tools require async context management (__aenter__/__aexit__)
    for connection establishment and cleanup. This function creates the
    tool instances but does NOT connect them. The framework (Agent Framework
    or DevUI) handles the connection lifecycle automatically.
    """
    # Create MCP tool instance (not connected)
    sequential_thinking_tool = MCPStdioTool(
        name="sequential-thinking",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
    )

    # Return tools dict for injection (framework manages lifecycle)
    return {"sequential-thinking": sequential_thinking_tool}


__all__ = ["create_mcp_tool_instances"]
```

**Step 3: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/tools/mcp_tools.py`
Expected: No output (successful compilation)

**Step 4: Commit**

```bash
git add src/spec_to_agents/tools/mcp_tools.py
git commit -m "refactor: convert MCP tools to framework-managed lifecycle pattern

Replace async context manager with simple factory function.
Framework now handles __aenter__/__aexit__ automatically via:
- DevUI's _cleanup_entities() for main.py
- ChatAgent's exit stack for console.py"
```

---

## Task 2: Update DI Container

**Files:**
- Modify: `src/spec_to_agents/container.py`

**Step 1: Review current container configuration**

Read: `src/spec_to_agents/container.py`

Current code has `global_tools = providers.Resource(create_global_tools)`. We need to change it to Singleton.

**Step 2: Update global_tools provider**

In `src/spec_to_agents/container.py`, update the import and provider:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Dependency injection container for application-wide dependencies."""

from dependency_injector import containers, providers

from spec_to_agents.config import get_default_model_config
from spec_to_agents.tools.mcp_tools import create_mcp_tool_instances  # Changed import
from spec_to_agents.utils.clients import create_agent_client_for_devui


class AppContainer(containers.DeclarativeContainer):
    """
    Application-wide dependency injection container.

    Manages lifecycle and injection of:
    - Azure AI agent client (singleton)
    - Global tools dictionary (MCP tools, framework-managed lifecycle)
    - Model configuration (singleton)

    The tools provider returns a dict[str, ToolProtocol] containing globally
    shared tools (currently just MCP sequential-thinking tool). Agent-specific
    tools (web search, code interpreter, weather, calendar) are initialized
    inside each agent's create_agent() factory function, not via DI injection.

    Agent factories can selectively access global tools by key:
        global_tools["sequential-thinking"]

    Usage in main.py (DevUI mode):
        container = AppContainer()
        container.wire(modules=[...])
        workflows = export_workflow()
        agents = export_agents()
        serve(entities=workflows + agents)
        # DevUI's _cleanup_entities() handles MCP tool cleanup

    Usage in console.py (CLI mode):
        container = AppContainer()
        container.wire(modules=[...])
        async with container.client():
            workflow = build_event_planning_workflow()
            # ChatAgent's exit stack handles MCP tool lifecycle

    Notes
    -----
    MCP tools connect lazily on first use via __aenter__() and cleanup
    automatically via framework's exit stack (console.py) or DevUI's
    _cleanup_entities() (main.py). No manual init_resources() or
    shutdown_resources() needed.
    """

    # Configuration
    config = providers.Configuration()

    # Client provider (singleton factory)
    # Uses non-context-managed client for DI compatibility
    client = providers.Singleton(
        create_agent_client_for_devui,
    )

    # Global tools provider (singleton factory, framework-managed lifecycle)
    # Provides dict[str, ToolProtocol] with MCP tool instances
    # Framework handles async context management (__aenter__/__aexit__)
    global_tools = providers.Singleton(
        create_mcp_tool_instances,
    )

    model_config = providers.Singleton(
        get_default_model_config,
    )

    # Wiring configuration: modules that use @inject
    wiring_config = containers.WiringConfiguration(
        packages=[
            "spec_to_agents.agents",
            "spec_to_agents.workflow",
        ]
    )
```

**Step 3: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/container.py`
Expected: No output (successful compilation)

**Step 4: Commit**

```bash
git add src/spec_to_agents/container.py
git commit -m "refactor: change global_tools from Resource to Singleton provider

Update container to use simple factory pattern instead of async context
manager. Framework now manages MCP tool lifecycle automatically."
```

---

## Task 3: Simplify Main.py (DevUI Entry Point)

**Files:**
- Modify: `src/spec_to_agents/main.py`

**Step 1: Review current main.py**

Read: `src/spec_to_agents/main.py`

Current code has:
- `container.global_tools.override({})` - disables MCP tools
- `async def load_entities()` with `await container.init_resources()`
- `asyncio.run(load_entities())` wrapper

We need to remove all of these and simplify to synchronous loading.

**Step 2: Simplify main() function**

Replace the `main()` function in `src/spec_to_agents/main.py`:

```python
def main() -> None:
    """Launch the branching workflow in DevUI with DI container."""
    import logging

    from agent_framework.devui import serve

    from spec_to_agents.agents import export_agents
    from spec_to_agents.container import AppContainer
    from spec_to_agents.workflow import export_workflow

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    # Initialize DI container and wire modules for dependency injection
    container = AppContainer()
    container.wire(modules=[__name__])

    # MCP tools now work in DevUI mode - framework manages lifecycle
    # No override needed, no init_resources() needed

    # Get port from environment (for container deployments) or use default
    port = int(os.getenv("PORT", "8080"))
    # Disable auto_open in container environments
    auto_open = os.getenv("ENVIRONMENT") != "production"

    logger.info("Starting Agent Workflow DevUI...")
    logger.info(f"Available at: http://localhost:{port}")

    # Load entities synchronously (no async context needed)
    workflows = export_workflow()
    agents = export_agents()

    # DevUI's serve() handles MCP tool lifecycle via _cleanup_entities()
    # Use localhost for security; override with --host 0.0.0.0 if needed for external access
    # Dependencies (client, global_tools) are injected automatically into workflow/agent builders
    serve(entities=workflows + agents, port=port, host="localhost", auto_open=auto_open)
```

**Step 3: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/main.py`
Expected: No output (successful compilation)

**Step 4: Commit**

```bash
git add src/spec_to_agents/main.py
git commit -m "fix: enable MCP tools in DevUI by removing lifecycle workarounds

Remove container.global_tools.override({}) that disabled MCP tools.
Remove async load_entities() and init_resources() calls.
Load entities synchronously - DevUI manages tool lifecycle automatically."
```

---

## Task 4: Simplify Console.py (CLI Entry Point)

**Files:**
- Modify: `src/spec_to_agents/console.py`

**Step 1: Review current console.py**

Read: `src/spec_to_agents/console.py`

Current code manually manages MCP tools lifecycle with:
- `from spec_to_agents.tools.mcp_tools import create_global_tools`
- `async with create_global_tools() as tools:`
- `container.global_tools.override(tools)`
- `finally: container.global_tools.reset_override()`

We need to simplify to trust framework's exit stack.

**Step 2: Simplify async main() function**

In `src/spec_to_agents/console.py`, replace the `main()` function:

```python
async def main() -> None:
    """
    Run the event planning workflow with interactive CLI human-in-the-loop.

    This function implements the main event loop pattern from
    guessing_game_with_human_input.py, adapted for event planning:

    1. Build the workflow with MCP tools injected via DI
    2. Loop until workflow completes:
       - Stream workflow events (run_stream or send_responses_streaming)
       - Collect RequestInfoEvents for human feedback
       - Collect WorkflowOutputEvents for final result
       - Prompt user for input when needed
       - Send responses back to workflow
    3. Display final event plan
    4. MCP tool cleanup handled automatically by ChatAgent's exit stack
    """
    # Display welcome header
    display_welcome_header()

    # Initialize DI container and wire modules for dependency injection
    container = AppContainer()
    container.wire(modules=[__name__])

    # Agent client handles async context for itself
    # MCP tools injected via DI, ChatAgent manages their lifecycle via exit stack
    async with container.client():
        try:
            # Build workflow with MCP tools automatically injected
            with console.status("[bold green]Loading workflow...", spinner="dots"):
                workflow = build_event_planning_workflow()
            console.print("[green]✓[/green] Workflow loaded successfully")
            console.print()

            # Get initial event planning request from user with suggestions
            user_request = prompt_for_event_request()
            if user_request is None:
                return

            console.print()
            console.rule("[bold green]Workflow Execution")
            console.print()

            # Configuration: Toggle to display streaming agent run updates
            # Set to True to see real-time tool calls, tool results, and text streaming
            # Set to False to only see human-in-the-loop prompts and final output
            display_streaming_updates = True

            # Main workflow loop: alternate between workflow execution and human input
            pending_responses: dict[str, str] | None = None
            workflow_output: str | None = None

            # Track printed tool calls/results to avoid duplication in streaming
            printed_tool_calls: set[str] = set()
            printed_tool_results: set[str] = set()
            last_executor: str | None = None

            while workflow_output is None:
                # Execute workflow: first iteration uses run_stream(), subsequent use send_responses_streaming()
                if pending_responses:
                    stream = workflow.send_responses_streaming(pending_responses)
                else:
                    stream = workflow.run_stream(user_request)

                pending_responses = None

                # Process events as they stream in
                human_requests: list[tuple[str, HumanFeedbackRequest]] = []

                async for event in stream:
                    # Display streaming agent updates if enabled
                    if isinstance(event, AgentRunUpdateEvent) and display_streaming_updates:
                        last_executor = display_agent_run_update(
                            event, last_executor, printed_tool_calls, printed_tool_results
                        )

                    # Collect human-in-the-loop requests
                    elif isinstance(event, RequestInfoEvent) and isinstance(event.data, HumanFeedbackRequest):
                        # Workflow is requesting human input
                        human_requests.append((event.request_id, event.data))

                    # Capture final workflow output
                    elif isinstance(event, WorkflowOutputEvent):
                        # Workflow has yielded final output
                        workflow_output = str(event.data)

                    # Display workflow status transitions for transparency
                    elif (
                        isinstance(event, WorkflowStatusEvent)
                        and event.state == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS
                    ):
                        display_workflow_pause()

                # Prompt user for feedback if workflow requested input
                if human_requests:
                    responses: dict[str, str] = {}

                    for request_id, feedback_request in human_requests:
                        user_response = display_human_feedback_request(feedback_request)
                        if user_response is None:
                            return

                        responses[request_id] = user_response

                    pending_responses = responses

            # Display final workflow output
            display_final_output(workflow_output)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise

    # MCP tools and agent client automatically cleaned up by async context managers
```

**Step 3: Remove unused import**

The import `from spec_to_agents.tools.mcp_tools import create_global_tools` is no longer needed. It should already be removed by the replacement above.

**Step 4: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/console.py`
Expected: No output (successful compilation)

**Step 5: Commit**

```bash
git add src/spec_to_agents/console.py
git commit -m "refactor: simplify console.py to use framework-managed MCP lifecycle

Remove manual override/reset of global_tools.
Trust ChatAgent's exit stack to manage MCP tool lifecycle.
Consistent pattern with main.py - both use DI container the same way."
```

---

## Task 5: Validate DevUI Mode with Playwright

**Files:**
- No code changes, validation only

**Step 1: Start DevUI server**

Run: `uv run app`
Expected: Server starts on http://localhost:8080

**Step 2: Use Playwright to verify MCP tools loaded**

Use playwright MCP tools to:
1. Navigate to http://localhost:8080
2. Take snapshot of the page
3. Verify entities are loaded (no errors in console)
4. Check that agents appear in the UI

**Step 3: Stop server**

Kill the running `uv run app` process.

**Step 4: Verify no errors in terminal output**

Check terminal output from Step 1 for:
- No "connections will close before execution" warnings
- No async context manager errors
- Clean startup and shutdown

If errors found, investigate and fix before proceeding.

---

## Task 6: Validate CLI Mode

**Files:**
- No code changes, validation only

**Step 1: Run console mode**

Run: `uv run console`

**Step 2: Enter test request**

When prompted, enter: "Plan a small team lunch for 10 people next Friday in downtown Seattle"

**Step 3: Verify MCP tools work**

Watch the output for:
- Sequential-thinking tool appearing in tool list (if used)
- No connection errors
- Workflow completes successfully

**Step 4: Exit gracefully**

Let workflow complete or Ctrl+C to interrupt.

Check terminal output for clean shutdown (no leaked connections or errors).

---

## Task 7: Run Full Test Suite

**Files:**
- No code changes, validation only

**Step 1: Run pytest**

Run: `uv run pytest -v`
Expected: All tests pass (no regressions from refactor)

**Step 2: Review any failures**

If failures occur:
- Check if they're related to MCP tool changes
- Fix if needed
- Re-run tests until passing

**Step 3: Commit if any fixes were needed**

If you had to fix test failures:

```bash
git add <fixed-files>
git commit -m "fix: resolve test failures from MCP lifecycle refactor"
```

---

## Task 8: Update Documentation (Optional)

**Files:**
- Potentially modify: `CLAUDE.md`

**Step 1: Review CLAUDE.md for outdated MCP references**

Read: `CLAUDE.md`

Check for any references to:
- `init_resources()` / `shutdown_resources()`
- Manual MCP lifecycle management
- `container.global_tools.override({})`

**Step 2: Update if needed**

If outdated patterns are documented, update to reflect new pattern:
- MCP tools work in both DevUI and console modes
- Framework manages lifecycle automatically
- Simple Singleton provider, no manual context management

**Step 3: Commit if changes made**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md to reflect MCP framework-managed lifecycle"
```

---

## Task 9: Final Verification with Playwright E2E Test

**Files:**
- No code changes, comprehensive validation

**Step 1: Start DevUI in background**

Run: `uv run app &`

Wait for "Starting Agent Workflow DevUI..." message.

**Step 2: Run Playwright comprehensive test**

Using playwright MCP:
1. Navigate to http://localhost:8080
2. Take screenshot of main page
3. Click on workflow/agent
4. Take screenshot of detail page
5. Check browser console for errors
6. Check network tab for failed requests

**Step 3: Kill background server**

```bash
pkill -f "uv run app"
```

**Step 4: Document results**

If everything passes:
- MCP tools appear in agent configurations
- No console errors
- No network failures
- UI loads cleanly

This confirms the integration is working.

---

## Success Criteria

After completing all tasks:

- [ ] MCP tools module refactored to simple factory
- [ ] DI container updated to Singleton provider
- [ ] Main.py simplified (no override, no async loading)
- [ ] Console.py simplified (no manual override/reset)
- [ ] DevUI mode validated with Playwright (tools loaded, no errors)
- [ ] CLI mode validated (workflow completes, tools work)
- [ ] All tests passing
- [ ] Documentation updated if needed
- [ ] Playwright E2E test confirms integration working

**Definition of Done:**
1. Can run `uv run app` and see MCP tools in agent tool lists in DevUI
2. Can execute workflow in DevUI that uses sequential-thinking tool
3. Can run `uv run console` and complete workflow with no errors
4. All commits follow conventional commit format
5. No manual lifecycle management in either entry point
