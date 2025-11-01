# Copyright (c) Microsoft. All rights reserved.

import json

from agent_framework import (
    AgentRunUpdateEvent,
    FunctionCallContent,
    FunctionResultContent,
)
from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

from spec_to_agents.models.messages import HumanFeedbackRequest

# Initialize Rich console
console = Console()


def display_welcome_header() -> None:
    """
    Display the welcome header with agent information.

    Shows a styled panel with the workflow title and descriptions of all
    available specialist agents.
    """
    console.print()
    console.print(
        Panel(
            Align.center(
                "[bold cyan]Event Planning Workflow[/bold cyan]\n[dim]Interactive CLI with AI-Powered Agents[/dim]"
            ),
            border_style="cyan",
            expand=True,
            padding=(1, 2),
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


def prompt_for_event_request() -> str | None:
    """
    Prompt user for an event planning request with predefined suggestions.

    Displays numbered examples that users can select by typing 1-3, or allows
    them to enter a custom request.

    Returns
    -------
    str | None
        The user's event planning request, or None if they want to exit
    """
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
        user_input = Prompt.ask("[bold cyan]Your request (or 1-3 for examples)[/bold cyan]", console=console).strip()
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Input interrupted. Exiting.[/yellow]")
        return None

    # Handle selection of predefined suggestions
    if user_input in ("1", "2", "3"):
        user_request = suggestions[int(user_input) - 1]
        console.print(f"[dim]Selected: {user_request}[/dim]")
        return user_request
    if user_input.lower() in ("exit", "quit"):
        console.print("[yellow]Exiting.[/yellow]")
        return None
    if not user_input:
        console.print("[yellow]No request provided. Exiting.[/yellow]")
        return None
    return user_input


def display_workflow_pause() -> None:
    """Display a status message when workflow pauses for human input."""
    console.print()
    console.print(
        Panel(
            "[bold yellow]Workflow paused - awaiting human input[/bold yellow]",
            border_style="yellow",
            padding=(0, 2),
        )
    )
    console.print()


def display_human_feedback_request(
    feedback_request: HumanFeedbackRequest,
) -> str | None:
    """
    Display a human feedback request and prompt for user response.

    Parameters
    ----------
    feedback_request : HumanFeedbackRequest
        The feedback request containing prompt, context, and metadata

    Returns
    -------
    str | None
        The user's response, or None if they want to exit
    """
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
        user_response = Prompt.ask(f"[bold {agent_color}]Your response[/bold {agent_color}]", console=console).strip()
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Input interrupted. Exiting workflow...[/yellow]")
        return None

    console.print()

    if user_response.lower() in ("exit", "quit"):
        console.print("[yellow]Exiting workflow...[/yellow]")
        return None

    if not user_response:
        user_response = "Continue with your best judgment"
        console.print(f"[dim]Using default response: '{user_response}'[/dim]")
        console.print()

    return user_response


def display_final_output(workflow_output: str) -> None:
    """
    Display the final workflow output with intelligent formatting.

    Attempts to parse as JSON and render with appropriate styling:
    - JSON with 'summary' field: Markdown summary + JSON details
    - Pure JSON: Syntax-highlighted JSON
    - Markdown text: Rendered markdown
    - Fallback: Plain text in styled panel

    Parameters
    ----------
    workflow_output : str
        The final output from the workflow
    """
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


def _get_agent_color(executor_id: str) -> str:
    """
    Get the color associated with an agent type.

    Parameters
    ----------
    executor_id : str
        The executor/agent ID

    Returns
    -------
    str
        Rich color name for the agent
    """
    agent_colors = {
        "venue": "blue",
        "budget": "green",
        "catering": "yellow",
        "logistics": "cyan",
        "coordinator": "magenta",
    }

    # Match executor_id to agent type
    for agent_type, color in agent_colors.items():
        if agent_type in executor_id.lower():
            return color

    return "white"


def display_agent_run_update(
    event: AgentRunUpdateEvent,
    last_executor: str | None,
    printed_tool_calls: set[str],
    printed_tool_results: set[str],
) -> str | None:
    """
    Display an AgentRunUpdateEvent in a readable format using Rich styling.

    Streams agent execution updates including tool calls, tool results, and text output.
    Tracks which tool calls and results have been displayed to avoid duplication
    during streaming. Uses Rich library for color-coded, styled output.

    Parameters
    ----------
    event : AgentRunUpdateEvent
        The workflow event containing an agent run update
    last_executor : str | None
        The ID of the last executor that was displayed. Used to print executor
        transitions.
    printed_tool_calls : set[str]
        Set of call IDs that have already been printed. Modified in place.
    printed_tool_results : set[str]
        Set of call IDs for results that have already been printed. Modified in place.

    Returns
    -------
    str | None
        The executor_id if it changed, None otherwise. Use this to track executor
        transitions between calls.

    Notes
    -----
    This function prints directly to stdout using Rich Console and modifies the
    printed_tool_calls and printed_tool_results sets in place. The function handles
    three types of content updates:
    - FunctionCallContent: Displayed as styled panel with function name and arguments
    - FunctionResultContent: Displayed as styled panel with call ID and result
    - Text updates: Streamed with agent-specific color coding

    Examples
    --------
    >>> printed_calls = set()
    >>> printed_results = set()
    >>> last_exec = None
    >>> async for event in workflow.run_stream(prompt):
    ...     if isinstance(event, AgentRunUpdateEvent):
    ...         last_exec = display_agent_run_update(event, last_exec, printed_calls, printed_results)
    """
    executor_id = event.executor_id
    update = event.data

    # Safety check: ensure update has contents
    if update is None or update.contents is None:
        return last_executor

    # Extract function calls and results from the update
    function_calls = [c for c in update.contents if isinstance(c, FunctionCallContent)]
    function_results = [c for c in update.contents if isinstance(c, FunctionResultContent)]

    # Get agent-specific color
    agent_color = _get_agent_color(executor_id)

    # Print executor ID when it changes
    if executor_id != last_executor:
        if last_executor is not None:
            console.print()  # Add newline between executor transitions

        # Display agent header with color-coded styling
        console.print()
        console.rule(f"[bold {agent_color}]{executor_id}[/bold {agent_color}]", style=agent_color)
        last_executor = executor_id

    # Print any new tool calls before the text update
    for call in function_calls:
        if call.call_id in printed_tool_calls:
            continue
        printed_tool_calls.add(call.call_id)

        # Format arguments for display
        args = call.arguments
        if isinstance(args, dict):
            args_display = Syntax(
                json.dumps(args, indent=2, ensure_ascii=False),
                "json",
                theme="monokai",
                line_numbers=False,
                background_color="default",
            )
        else:
            args_str = (args or "").strip()
            args_display = f"[dim]{args_str}[/dim]"

        console.print(
            Panel(
                f"[bold]🔧 Tool Call:[/bold] [cyan]{call.name}[/cyan]\n"
                f"[bold]Call ID:[/bold] [dim]{call.call_id}[/dim]\n\n"
                f"{args_display}",
                title=f"[{agent_color}]Function Call[/{agent_color}]",
                border_style=agent_color,
                padding=(0, 1),
                expand=False,
            )
        )

    # Print any new tool results before the text update
    for result in function_results:
        if result.call_id in printed_tool_results:
            continue
        printed_tool_results.add(result.call_id)

        # Format result for display
        result_text = result.result
        if not isinstance(result_text, str):
            result_display = Syntax(
                json.dumps(result_text, indent=2, ensure_ascii=False),
                "json",
                theme="monokai",
                line_numbers=False,
                background_color="default",
            )
        else:
            # Truncate very long results for readability
            if len(result_text) > 500:
                result_text = result_text[:500] + f"... [dim](truncated, {len(result_text)} chars total)[/dim]"
            result_display = result_text

        console.print(
            Panel(
                f"[bold]Call ID:[/bold] [dim]{result.call_id}[/dim]\n\n{result_display}",
                title=f"[{agent_color}]Tool Result[/{agent_color}]",
                border_style="dim",
                padding=(0, 1),
                expand=False,
            )
        )

    # Finally, print the text update with agent-specific color
    if update.text is not None:
        console.print(f"[{agent_color}]{update.text}[/{agent_color}]", end="")

    return last_executor
