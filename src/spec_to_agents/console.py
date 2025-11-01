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

from agent_framework import (
    AgentRunUpdateEvent,
    RequestInfoEvent,
    WorkflowOutputEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
)
from dotenv import load_dotenv

from spec_to_agents.models.messages import HumanFeedbackRequest
from spec_to_agents.tools.mcp_tools import create_sequential_thinking_tool
from spec_to_agents.utils.clients import create_agent_client
from spec_to_agents.utils.display import (
    console,
    display_agent_run_update,
    display_final_output,
    display_human_feedback_request,
    display_welcome_header,
    display_workflow_pause,
    prompt_for_event_request,
)
from spec_to_agents.workflow.core import build_event_planning_workflow

# Load environment variables at module import
load_dotenv()


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
    # Display welcome header
    display_welcome_header()

    # Use async context managers for both MCP tool and agent client lifecycle
    async with (
        create_sequential_thinking_tool() as mcp_tool,
        create_agent_client() as client,
    ):
        # Build workflow with connected MCP tool and agent client
        with console.status("[bold green]Loading workflow...", spinner="dots"):
            workflow = build_event_planning_workflow(client, mcp_tool)
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
