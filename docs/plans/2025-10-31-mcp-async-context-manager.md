# MCP Async Context Manager Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor sequential-thinking-tools MCP lifecycle from global singleton with manual cleanup to async context manager pattern.

**Architecture:** Convert `mcp_tools.py` to factory function, update `event_planning_workflow.py` to accept optional MCP tool parameter, refactor `console.py` to use `async with` pattern for automatic lifecycle management.

**Tech Stack:** Python 3.11+, Agent Framework MCPStdioTool, asyncio, pytest

---

## Task 1: Refactor MCP Tools Module to Factory Pattern

**Files:**
- Modify: `src/spec_to_agents/tools/mcp_tools.py`
- Test: `tests/test_tools_mcp.py`

**Step 1: Write the failing test**

Create test for factory function pattern:

```python
# tests/test_tools_mcp.py
import pytest
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools_mcp.py -v`

Expected: FAIL with "ImportError: cannot import name 'create_sequential_thinking_tool'"

**Step 3: Refactor mcp_tools.py to factory pattern**

```python
# src/spec_to_agents/tools/mcp_tools.py
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools_mcp.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/spec_to_agents/tools/mcp_tools.py tests/test_tools_mcp.py
git commit -m "refactor: convert MCP tools to factory pattern

Replace global singleton with factory function for better lifecycle
management and testability. Remove manual cleanup function.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Update Workflow Builder to Accept Optional MCP Tool

**Files:**
- Modify: `src/spec_to_agents/workflow/event_planning_workflow.py:31-80`
- Modify: `src/spec_to_agents/tools/__init__.py`

**Step 1: Update tools/__init__.py exports**

Remove old exports:

```python
# src/spec_to_agents/tools/__init__.py
# Remove these lines:
# from spec_to_agents.tools.mcp_tools import (
#     close_sequential_thinking_tool,
#     get_sequential_thinking_tool,
# )

# Update __all__ to remove:
# "close_sequential_thinking_tool",
# "get_sequential_thinking_tool",
```

**Step 2: Update workflow builder signature and implementation**

```python
# src/spec_to_agents/workflow/event_planning_workflow.py

# Update imports - remove get_sequential_thinking_tool
from spec_to_agents.tools import (
    create_calendar_event,
    delete_calendar_event,
    get_weather_forecast,
    list_calendar_events,
    web_search,
)

# Update function signature
def build_event_planning_workflow(
    mcp_tool: MCPStdioTool | None = None,
) -> Workflow:
    """
    Build the multi-agent event planning workflow with human-in-the-loop capabilities.

    Architecture
    ------------
    Uses coordinator-centric star topology with 5 executors:
    - EventPlanningCoordinator: Manages routing and human-in-the-loop using service-managed threads
    - VenueSpecialist: Venue research via custom web_search tool
    - BudgetAnalyst: Financial planning via Code Interpreter
    - CateringCoordinator: Food planning via custom web_search tool
    - LogisticsManager: Scheduling, weather, calendar management

    Conversation history is managed automatically by service-managed threads (store=True).
    No manual message tracking or summarization overhead.

    Workflow Pattern
    ----------------
    Star topology with bidirectional edges:
    - Coordinator ←→ Venue Specialist
    - Coordinator ←→ Budget Analyst
    - Coordinator ←→ Catering Coordinator
    - Coordinator ←→ Logistics Manager

    Human-in-the-Loop
    ------------------
    Specialists can call request_user_input tool when they need clarification,
    selection, or approval. The coordinator intercepts these tool calls and uses
    ctx.request_info() + @response_handler to pause the workflow, emit
    RequestInfoEvent, and resume with user responses via DevUI.

    Parameters
    ----------
    mcp_tool : MCPStdioTool | None, optional
        Connected MCP tool for coordinator's sequential thinking capabilities.
        If None, coordinator operates without MCP tool assistance.
        Must be connected (within async context manager) before passing to workflow.

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution via DevUI
        or programmatic invocation.

    Notes
    -----
    The workflow uses sequential orchestration managed by the coordinator.
    Human-in-the-loop is optional: the workflow can complete autonomously
    if agents have sufficient context and choose not to request user input.

    Requires Azure AI Foundry credentials configured via environment variables
    or Azure CLI authentication.
    """
    client = get_chat_client()

    # Create hosted tools
    code_interpreter = HostedCodeInterpreterTool(
        description=(
            "Execute Python code for complex financial calculations, budget analysis, "
            "cost projections, and data visualization. Creates a scratchpad for "
            "intermediate calculations and maintains calculation history."
        ),
    )

    # Create coordinator agent with optional MCP tool for advanced reasoning
    coordinator_agent = event_coordinator.create_agent(
        client,
        mcp_tool,
    )

    # Rest of function remains the same...
```

**Step 3: Verify workflow builder still works**

Run: `uv run pytest tests/ -k workflow -v` (if workflow tests exist)

Expected: PASS or no workflow-specific tests yet

**Step 4: Commit**

```bash
git add src/spec_to_agents/workflow/event_planning_workflow.py src/spec_to_agents/tools/__init__.py
git commit -m "refactor: accept optional MCP tool in workflow builder

Update build_event_planning_workflow to accept optional mcp_tool
parameter for dependency injection. Maintains backwards compatibility
with None default.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Refactor Console to Use Async Context Manager

**Files:**
- Modify: `src/spec_to_agents/console.py:43-65,117-324`

**Step 1: Update imports**

```python
# src/spec_to_agents/console.py

# Remove old import
# from spec_to_agents.tools import close_sequential_thinking_tool

# Add new import
from spec_to_agents.tools.mcp_tools import create_sequential_thinking_tool
```

**Step 2: Refactor main() to use async context manager**

Replace the entire `main()` function:

```python
async def main() -> None:
    """
    Run the event planning workflow with interactive CLI human-in-the-loop.

    This function implements the main event loop pattern from
    guessing_game_with_human_input.py, adapted for event planning:

    1. Build the workflow with connected MCP tool
    2. Loop until workflow completes:
       - Stream workflow events (run_stream or send_responses_streaming)
       - Collect RequestInfoEvents for human feedback
       - Collect WorkflowOutputEvents for final result
       - Prompt user for input when needed
       - Send responses back to workflow
    3. Display final event plan
    4. MCP tool cleanup handled automatically by async context manager

    The workflow alternates between executing agent logic and pausing
    for human input via the request_info/response_handler pattern.
    """
    print("\n" + "=" * 70)
    print("Event Planning Workflow - Interactive CLI")
    print("=" * 70)
    print()
    print("This workflow will help you plan an event with assistance from")
    print("specialized agents (Venue, Budget, Catering, Logistics).")
    print()
    print("You may be asked for clarification or approval at various steps.")
    print("Type 'exit' at any prompt to quit.")
    print()

    # Use async context manager for MCP tool lifecycle
    async with create_sequential_thinking_tool() as mcp_tool:
        # Build workflow with connected MCP tool
        print("Loading workflow...", end="", flush=True)
        workflow = build_event_planning_workflow(mcp_tool)
        print(" ✓")
        print()

        # Get initial event planning request from user
        print("-" * 70)
        print("Enter your event planning request:")
        print("(e.g., 'Plan a corporate holiday party for 50 people, budget $5000')")
        print("-" * 70)

        try:
            user_request = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nInput interrupted. Exiting.")
            return

        if not user_request:
            print("\nNo request provided. Exiting.")
            return

        print()
        print("=" * 70)
        print("Starting workflow execution...")
        print("=" * 70)
        print()

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

            # Collect all events from this execution cycle
            events = [event async for event in stream]
            pending_responses = None

            # Display tool calls and results for transparency
            for event in events:
                # Check if event has agent_run_response_update attribute
                if hasattr(event, "agent_run_response_update"):
                    update: AgentRunResponseUpdate = event.agent_run_response_update  # type: ignore
                    executor_id = getattr(event, "executor_id", "workflow")

                    # Extract tool calls and results
                    function_calls = [c for c in update.contents if isinstance(c, FunctionCallContent)]  # type: ignore
                    function_results = [c for c in update.contents if isinstance(c, FunctionResultContent)]  # type: ignore

                    # Show executor transition
                    if function_calls or function_results:
                        if executor_id != last_executor:
                            if last_executor is not None:
                                print()
                            last_executor = executor_id

                        # Print new tool calls
                        for call in function_calls:
                            if call.call_id in printed_tool_calls:
                                continue
                            printed_tool_calls.add(call.call_id)
                            print(f"   {format_tool_call(call, executor_id)}")

                        # Print new tool results
                        for result in function_results:
                            if result.call_id in printed_tool_results:
                                continue
                            printed_tool_results.add(result.call_id)
                            print(f"   {format_tool_result(result, executor_id)}")

            # Process events to extract human requests and workflow outputs
            human_requests: list[tuple[str, HumanFeedbackRequest]] = []
            for event in events:
                if isinstance(event, RequestInfoEvent) and isinstance(event.data, HumanFeedbackRequest):
                    # Workflow is requesting human input
                    human_requests.append((event.request_id, event.data))

                elif isinstance(event, WorkflowOutputEvent):
                    # Workflow has yielded final output
                    workflow_output = str(event.data)

            # Display workflow status transitions for transparency
            idle_with_requests = any(
                isinstance(e, WorkflowStatusEvent) and e.state == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS
                for e in events
            )

            if idle_with_requests:
                print("[Workflow paused - awaiting human input]")
                print()

            # Prompt user for feedback if workflow requested input
            if human_requests:
                responses: dict[str, str] = {}

                for request_id, feedback_request in human_requests:
                    print("─" * 70)
                    print(f"🤔 {feedback_request.requesting_agent.upper()} needs your input:")
                    print()
                    print(f"   Request Type: {feedback_request.request_type}")
                    print()
                    print(f"   {feedback_request.prompt}")
                    print()

                    # Display context if available
                    if feedback_request.context:
                        print("   Additional Context:")
                        for key, value in feedback_request.context.items():
                            # Format context nicely
                            if isinstance(value, (list, dict)):
                                print(f"   • {key}:")
                                if isinstance(value, list):
                                    for item in value:  # type: ignore
                                        print(f"     - {item}")
                                elif isinstance(value, dict):
                                    for k, v in value.items():  # type: ignore
                                        print(f"     {k}: {v}")
                            else:
                                print(f"   • {key}: {value}")
                        print()

                    # Get user response
                    try:
                        user_response = input("   Your response > ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\n\nInput interrupted. Exiting workflow...")
                        return

                    print()

                    if user_response.lower() in ("exit", "quit"):
                        print("Exiting workflow...")
                        return

                    if not user_response:
                        user_response = "Continue with your best judgment"
                        print(f"   [Using default response: '{user_response}']")
                        print()

                    responses[request_id] = user_response

                pending_responses = responses

        # Display final workflow output
        print()
        print("=" * 70)
        print("✓ FINAL EVENT PLAN")
        print("=" * 70)
        print()
        print(workflow_output)
        print()
        print("=" * 70)
        print("Event planning complete!")
        print("=" * 70)

    # MCP tool automatically cleaned up by async context manager
```

**Step 3: Verify console runs without errors**

Run: `uv run app` (or however the console is started)

Test: Enter a simple request and verify workflow starts (don't need to complete full workflow)

Expected: No connection errors, workflow initializes properly

**Step 4: Commit**

```bash
git add src/spec_to_agents/console.py
git commit -m "refactor: use async context manager for MCP tool in console

Replace manual cleanup with async with pattern for automatic MCP
tool lifecycle management. Removes error suppression in finally block.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Cleanup and Verification

**Files:**
- Verify: All imports updated
- Verify: No remaining references to old functions
- Test: End-to-end workflow execution

**Step 1: Search for old function references**

Run: `uv run rg "get_sequential_thinking_tool|close_sequential_thinking_tool" --type py`

Expected: No results (or only in tests/comments if documented for migration)

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`

Expected: All tests PASS

**Step 3: Run linting and formatting**

Run: `uv run ruff check . && uv run ruff format .`

Expected: No issues

**Step 4: Manual end-to-end test**

Run: `uv run app`

Test workflow:
1. Enter event request: "Plan a small team lunch for 10 people, budget $200"
2. Verify workflow starts and MCP tool is available to coordinator
3. Respond to any HITL prompts
4. Verify workflow completes successfully
5. Exit cleanly without errors

Expected: Clean execution and exit with no MCP cleanup errors

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: verify MCP async context manager refactor

All old function references removed, tests passing, manual
verification complete.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

Before marking complete, verify:

- [ ] `create_sequential_thinking_tool()` is a pure factory function
- [ ] No global state in `mcp_tools.py`
- [ ] `build_event_planning_workflow()` accepts optional `mcp_tool` parameter
- [ ] `console.py` uses `async with create_sequential_thinking_tool()`
- [ ] No manual cleanup in finally blocks
- [ ] All old function references removed from `__init__.py`
- [ ] Tests pass: `uv run pytest tests/ -v`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Manual test: workflow runs end-to-end without cleanup errors
- [ ] Design document committed to `docs/plans/`

---

## Skills Referenced

- Follow @superpowers:test-driven-development for writing tests
- Use @superpowers:verification-before-completion before marking tasks complete
- Follow @superpowers:systematic-debugging if issues arise during testing
