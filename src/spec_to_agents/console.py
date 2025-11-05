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
"""

import asyncio
import logging
import os

from agent_framework import (
    AgentRunUpdateEvent,
    RequestInfoEvent,
    WorkflowOutputEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
)
from agent_framework._workflows._handoff import HandoffUserInputRequest
from agent_framework.observability import setup_observability
from dotenv import load_dotenv

from spec_to_agents.container import AppContainer
from spec_to_agents.utils.display import (
    console,
    display_agent_run_update,
    display_final_output,
    display_welcome_header,
    display_workflow_pause,
    prompt_for_event_request,
)
from spec_to_agents.workflow.core import build_event_planning_workflow

# Load environment variables at module import
load_dotenv()

if os.getenv("ENABLE_OTEL", "false").lower() == "true":
    setup_observability()

logging.getLogger("agent_framework._clients").setLevel(logging.ERROR)
logging.getLogger("agent_framework._workflows._validation").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)


async def main() -> None:
    """
    Run the event planning workflow with DI and interactive CLI HITL.

    This function implements the main event loop pattern:
    1. Initialize DI container and wire modules
    2. Build the workflow with injected dependencies
    3. Loop until workflow completes:
       - Stream workflow events (run_stream or send_responses_streaming)
       - Collect RequestInfoEvents for human feedback
       - Collect WorkflowOutputEvents for final result
       - Prompt user for input when needed
       - Send responses back to workflow
    4. Display final event plan
    """
    # Display welcome header
    display_welcome_header()

    # Initialize DI container and wire modules for dependency injection
    container = AppContainer()
    container.wire(modules=[__name__])

    # Use async context manager for client lifecycle only
    # global_tools dict is automatically injected into agent factories via @inject
    # MCP tools are automatically connected by agent framework when agents are created
    async with container.client():
        # Build workflow - ALL dependencies (client, global_tools) injected automatically
        with console.status("[bold green]Loading workflow...", spinner="dots"):
            workflow = build_event_planning_workflow()  # No parameters needed!
        console.print("[green]✓[/green] Workflow loaded successfully")
        console.print()

        # Get initial event planning request from user with suggestions
        user_request = prompt_for_event_request()
        if user_request is None:
            return

        console.print()
        console.rule("[bold gray]Workflow Execution")
        console.print()

        # Configuration: Toggle to display streaming agent run updates
        # Set to True to see real-time tool calls, tool results, and text streaming
        # Set to False to only see human-in-the-loop prompts and final output
        display_streaming_updates = True

        # Main workflow loop: alternate between workflow execution and human input
        pending_responses: dict[str, str] | None = None
        workflow_output: str | None = None

        # Track printed tool calls/results/code blocks to avoid duplication in streaming
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
            human_requests: list[tuple[str, HandoffUserInputRequest]] = []

            async for event in stream:
                # Display streaming agent updates if enabled
                if isinstance(event, AgentRunUpdateEvent) and display_streaming_updates:
                    last_executor = display_agent_run_update(
                        event, last_executor, printed_tool_calls, printed_tool_results
                    )

                # Collect human-in-the-loop requests
                elif isinstance(event, RequestInfoEvent) and isinstance(event.data, HandoffUserInputRequest):
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

                for request_id, handoff_request in human_requests:
                    # Display prompt from HandoffUserInputRequest
                    console.print()
                    console.print(f"[bold cyan]User Input Requested:[/bold cyan] {handoff_request.prompt}")
                    console.print()

                    # Get user input
                    user_response = console.input("[bold green]You:[/bold green] ")

                    if not user_response or user_response.strip().lower() in ("exit", "quit"):
                        return

                    responses[request_id] = user_response

                pending_responses = responses

        # Display final workflow output
        display_final_output(workflow_output)

    # MCP tool and agent client automatically cleaned up by async context managers


def cli() -> None:
    """
    Synchronous entry point for the console command.

    This wrapper is required for pyproject.toml script entry points,
    which expect a synchronous callable.
    """
    asyncio.run(main())


if __name__ == "__main__":
    cli()
