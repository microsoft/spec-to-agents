# Copyright (c) Microsoft. All rights reserved.

import json

from agent_framework import (
    AgentRunUpdateEvent,
    FunctionCallContent,
    FunctionResultContent,
)
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Initialize Rich console
console = Console()


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
