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

from agent_framework import (
    AgentRunResponseUpdate,
    FunctionCallContent,
    FunctionResultContent,
    RequestInfoEvent,
    WorkflowOutputEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
)

from spec_to_agents.workflow.core import build_event_planning_workflow
from spec_to_agents.workflow.messages import HumanFeedbackRequest


def format_tool_call(content: FunctionCallContent) -> str:
    """
    Format a tool call for console display.

    Parameters
    ----------
    content : FunctionCallContent
        The function call content to format

    Returns
    -------
    str
        Formatted tool call string
    """
    args_preview = str(content.arguments)[:100]
    if len(str(content.arguments)) > 100:
        args_preview += "..."
    return f"🔧 Tool Call: {content.name}({args_preview})"


def format_tool_result(content: FunctionResultContent) -> str:
    """
    Format a tool result for console display.

    Parameters
    ----------
    content : FunctionResultContent
        The function result content to format

    Returns
    -------
    str
        Formatted tool result string
    """
    result_preview = str(content.result)[:150]
    if len(str(content.result)) > 150:
        result_preview += "..."
    return f"   ✓ Result: {result_preview}"


async def main() -> None:
    """
    Run the event planning workflow with interactive CLI human-in-the-loop.

    This function implements the main event loop pattern from
    guessing_game_with_human_input.py, adapted for event planning:

    1. Build the workflow
    2. Loop until workflow completes:
       - Stream workflow events (run_stream or send_responses_streaming)
       - Collect RequestInfoEvents for human feedback
       - Collect WorkflowOutputEvents for final result
       - Prompt user for input when needed
       - Send responses back to workflow
    3. Display final event plan

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

    # Build workflow
    print("Loading workflow...", end="", flush=True)
    workflow = await build_event_planning_workflow()
    print(" ✓")
    print()

    # Get initial event planning request from user
    print("-" * 70)
    print("Enter your event planning request:")
    print("(e.g., 'Plan a corporate holiday party for 50 people, budget $5000')")
    print("-" * 70)
    user_request = input("> ").strip()

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
                update: AgentRunResponseUpdate = event.agent_run_response_update

                # Log tool calls
                for content in update.contents:
                    if isinstance(content, FunctionCallContent):
                        print(f"   {format_tool_call(content)}")
                    elif isinstance(content, FunctionResultContent):
                        print(f"   {format_tool_result(content)}")

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
                                for item in value:
                                    print(f"     - {item}")
                            elif isinstance(value, dict):
                                for k, v in value.items():
                                    print(f"     {k}: {v}")
                        else:
                            print(f"   • {key}: {value}")
                    print()

                # Get user response
                user_response = input("   Your response > ").strip()
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


def cli() -> None:
    """
    Synchronous entry point for the console command.

    This wrapper is required for pyproject.toml script entry points,
    which expect a synchronous callable.
    """
    asyncio.run(main())


if __name__ == "__main__":
    cli()
