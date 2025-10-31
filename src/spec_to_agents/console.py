# Copyright (c) Microsoft. All rights reserved.

"""
Interactive CLI for event planning workflow with human-in-the-loop.

This module provides a command-line interface for running the event planning
workflow with real-time human feedback. It handles RequestInfoEvents and
prompts the user for input via stdin.

Pattern
-------
This follows the human-in-the-loop pattern from guessing_game_with_human_input.py:
1. Call workflow.run_stream() with initial prompt
2. Collect RequestInfoEvents during streaming
3. Prompt user for responses via input()
4. Call workflow.send_responses_streaming() with collected responses
5. Repeat until WorkflowOutputEvent is received

Usage
-----
    uv run python -m spec_to_agents.console

Example
-------
    $ uv run python -m spec_to_agents.console
    Event Planning Workflow - Interactive CLI
    ===========================================

    Enter your event planning request:
    > Plan a corporate holiday party for 50 people with a budget of $5000

    [Workflow executes...]

    HITL> The Venue Specialist found 3 options. Which do you prefer? (A/B/C)
    > B

    [Workflow continues...]

    Final Event Plan:
    [Comprehensive plan output]
"""

import asyncio
import json

from agent_framework import (
    AgentRunResponseUpdate,
    FunctionCallContent,
    FunctionResultContent,
    RequestInfoEvent,
    WorkflowOutputEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
)
from dotenv import load_dotenv

from spec_to_agents.tools.mcp_tools import create_sequential_thinking_tool
from spec_to_agents.workflow.core import build_event_planning_workflow
from spec_to_agents.workflow.messages import HumanFeedbackRequest

# Load environment variables at module import
load_dotenv()


def format_tool_call(content: FunctionCallContent, executor_id: str) -> str:
    """
    Format a tool call for console display with proper JSON serialization.

    This follows the pattern from microsoft/agent-framework samples for
    displaying tool execution feedback with full context.

    Parameters
    ----------
    content : FunctionCallContent
        The function call content to format
    executor_id : str
        ID of the executor making the call (e.g., "venue", "budget")

    Returns
    -------
    str
        Formatted tool call: "venue [tool-call] web_search({...})"
    """
    args = content.arguments
    args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else (args or "").strip()

    return f"{executor_id} [tool-call] {content.name}({args_str})"


def format_tool_result(content: FunctionResultContent, executor_id: str) -> str:
    """
    Format a tool result for console display with call_id linkage.

    This follows the pattern from microsoft/agent-framework samples for
    displaying tool execution feedback with proper result formatting.

    Parameters
    ----------
    content : FunctionResultContent
        The function result content to format
    executor_id : str
        ID of the executor that made the call

    Returns
    -------
    str
        Formatted tool result: "venue [tool-result] abc123: {...}"
    """
    result = content.result
    if not isinstance(result, str):
        result = json.dumps(result, ensure_ascii=False)

    return f"{executor_id} [tool-result] {content.call_id}: {result}"


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


def cli() -> None:
    """
    Synchronous entry point for the console command.

    This wrapper is required for pyproject.toml script entry points,
    which expect a synchronous callable.
    """
    asyncio.run(main())


if __name__ == "__main__":
    cli()
