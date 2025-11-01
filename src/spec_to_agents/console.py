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
import json

from agent_framework import (
    AgentRunUpdateEvent,
    RequestInfoEvent,
    WorkflowOutputEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
)
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

from spec_to_agents.models.messages import HumanFeedbackRequest
from spec_to_agents.tools.mcp_tools import create_sequential_thinking_tool
from spec_to_agents.utils.clients import create_agent_client
from spec_to_agents.utils.display import display_agent_run_update
from spec_to_agents.workflow.core import build_event_planning_workflow

# Load environment variables at module import
load_dotenv()

# Initialize Rich console for styled output
console = Console()


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
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Event Planning Workflow[/bold cyan]\n[dim]Interactive CLI with AI-Powered Agents[/dim]",
            border_style="cyan",
        )
    )
    console.print()
    console.print(
        "[dim]This workflow uses specialized AI agents to help you plan events:\n"
        "  • [blue]Venue Specialist[/blue] - Researches and recommends venues\n"
        "  • [green]Budget Analyst[/green] - Manages costs and financial planning\n"
        "  • [yellow]Catering Coordinator[/yellow] - Handles food and beverage\n"
        "  • [cyan]Logistics Manager[/cyan] - Coordinates schedules and resources\n"
        "\n"
        "You may be asked for clarification or approval at various steps.[/dim]"
    )
    console.print()

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
        console.rule("[bold]Event Planning Request")
        console.print()
        console.print("[bold]Enter your event planning request[/bold]")
        console.print("[dim]Or select from these examples:[/dim]")
        console.print("  [cyan]1.[/cyan] Plan a corporate holiday party for 50 people, budget $5000")
        console.print("  [cyan]2.[/cyan] Organize a wedding reception for 150 guests in Seattle")
        console.print("  [cyan]3.[/cyan] Host a tech conference with 200 attendees, need catering and AV")
        console.print()

        # Predefined suggestions
        suggestions = [
            "Plan a corporate holiday party for 50 people, budget $5000",
            "Organize a wedding reception for 150 guests in Seattle",
            "Host a tech conference with 200 attendees, need catering and AV",
        ]

        try:
            user_input = Prompt.ask(
                "[bold cyan]Your request (or 1-3 for examples)[/bold cyan]", console=console
            ).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Input interrupted. Exiting.[/yellow]")
            return

        # Handle selection of predefined suggestions
        if user_input in ("1", "2", "3"):
            user_request = suggestions[int(user_input) - 1]
            console.print(f"[dim]Selected: {user_request}[/dim]")
        elif user_input.lower() in ("exit", "quit"):
            console.print("[yellow]Exiting.[/yellow]")
            return
        elif not user_input:
            console.print("[yellow]No request provided. Exiting.[/yellow]")
            return
        else:
            user_request = user_input

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
                    console.print()
                    console.print(
                        Panel(
                            "[bold yellow]Workflow paused - awaiting human input[/bold yellow]",
                            border_style="yellow",
                            padding=(0, 2),
                        )
                    )
                    console.print()

            # Prompt user for feedback if workflow requested input
            if human_requests:
                responses: dict[str, str] = {}

                for request_id, feedback_request in human_requests:
                    # Determine agent color for styling
                    agent_name = feedback_request.requesting_agent.upper()
                    agent_colors = {
                        "VENUE": "blue",
                        "BUDGET": "green",
                        "CATERING": "yellow",
                        "LOGISTICS": "cyan",
                        "COORDINATOR": "magenta",
                    }
                    agent_color = agent_colors.get(agent_name, "white")

                    # Build context display
                    context_display = ""
                    if feedback_request.context:
                        context_lines = ["[dim]Additional Context:[/dim]"]
                        for key, value in feedback_request.context.items():
                            if isinstance(value, list):
                                context_lines.append(f"[bold]{key}:[/bold]")
                                for item in value:  # type: ignore
                                    context_lines.append(f"  • {item}")
                            elif isinstance(value, dict):
                                context_lines.append(f"[bold]{key}:[/bold]")
                                for k, v in value.items():  # type: ignore
                                    context_lines.append(f"  {k}: {v}")
                            else:
                                context_lines.append(f"[bold]{key}:[/bold] {value}")
                        context_display = "\n" + "\n".join(context_lines)

                    # Display styled request panel
                    console.print(
                        Panel(
                            f"[bold {agent_color}]🤔 {agent_name} Agent Request[/bold {agent_color}]\n\n"
                            f"[bold]Type:[/bold] {feedback_request.request_type}\n\n"
                            f"[bold]Question:[/bold]\n{feedback_request.prompt}"
                            f"{context_display}",
                            border_style=agent_color,
                            padding=(1, 2),
                        )
                    )
                    console.print()

                    # Get user response
                    try:
                        user_response = Prompt.ask(
                            f"[bold {agent_color}]Your response[/bold {agent_color}]", console=console
                        ).strip()
                    except (EOFError, KeyboardInterrupt):
                        console.print("\n[yellow]Input interrupted. Exiting workflow...[/yellow]")
                        return

                    console.print()

                    if user_response.lower() in ("exit", "quit"):
                        console.print("[yellow]Exiting workflow...[/yellow]")
                        return

                    if not user_response:
                        user_response = "Continue with your best judgment"
                        console.print(f"[dim]Using default response: '{user_response}'[/dim]")
                        console.print()

                    responses[request_id] = user_response

                pending_responses = responses

        # Display final workflow output
        console.print()
        console.rule("[bold green]✓ Final Event Plan", style="green")
        console.print()

        # Parse and display the workflow output
        try:
            # Try to parse as JSON first
            output_data = json.loads(workflow_output)

            # Extract summary if it exists and is markdown
            if isinstance(output_data, dict) and "summary" in output_data:
                summary_content = output_data["summary"]

                # Render markdown summary
                console.print(
                    Panel(
                        Markdown(summary_content),
                        title="[bold green]Event Plan Summary[/bold green]",
                        border_style="green",
                        padding=(1, 2),
                    )
                )

                # Display other fields if present
                other_fields = {k: v for k, v in output_data.items() if k != "summary"}
                if other_fields:
                    console.print()
                    console.print(
                        Panel(
                            Syntax(
                                json.dumps(other_fields, indent=2, ensure_ascii=False),
                                "json",
                                theme="monokai",
                                line_numbers=False,
                            ),
                            title="[bold]Additional Details[/bold]",
                            border_style="dim",
                            padding=(1, 2),
                        )
                    )
            else:
                # Display entire JSON output with syntax highlighting
                console.print(
                    Panel(
                        Syntax(
                            json.dumps(output_data, indent=2, ensure_ascii=False),
                            "json",
                            theme="monokai",
                            line_numbers=False,
                        ),
                        title="[bold green]Event Plan[/bold green]",
                        border_style="green",
                        padding=(1, 2),
                    )
                )
        except json.JSONDecodeError:
            # If not JSON, try rendering as markdown
            try:
                console.print(
                    Panel(
                        Markdown(workflow_output),
                        title="[bold green]Event Plan[/bold green]",
                        border_style="green",
                        padding=(1, 2),
                    )
                )
            except Exception:
                # Fallback to plain text
                console.print(
                    Panel(
                        workflow_output,
                        title="[bold green]Event Plan[/bold green]",
                        border_style="green",
                        padding=(1, 2),
                    )
                )

        console.print()
        console.print("[bold green]✓ Event planning complete![/bold green]")
        console.print()

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
