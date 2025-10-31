# Copyright (c) Microsoft. All rights reserved.

import json

from agent_framework import (
    AgentRunUpdateEvent,
    FunctionCallContent,
    FunctionResultContent,
)


def display_agent_run_update(
    event: AgentRunUpdateEvent,
    last_executor: str | None,
    printed_tool_calls: set[str],
    printed_tool_results: set[str],
) -> str | None:
    """
    Display an AgentRunUpdateEvent in a readable format.

    Streams agent execution updates including tool calls, tool results, and text output.
    Tracks which tool calls and results have been displayed to avoid duplication
    during streaming.

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
    This function prints directly to stdout and modifies the printed_tool_calls
    and printed_tool_results sets in place. The function handles three types of
    content updates:
    - FunctionCallContent: Displayed as [tool-call] with function name and arguments
    - FunctionResultContent: Displayed as [tool-result] with call ID and result
    - Text updates: Streamed character by character

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

    # Print executor ID when it changes
    if executor_id != last_executor:
        if last_executor is not None:
            print()  # Add newline between executor transitions  # noqa: T201
        print(f"{executor_id}:", end=" ", flush=True)  # noqa: T201
        last_executor = executor_id

    # Print any new tool calls before the text update
    for call in function_calls:
        if call.call_id in printed_tool_calls:
            continue
        printed_tool_calls.add(call.call_id)

        # Format arguments for display
        args = call.arguments
        args_preview = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else (args or "").strip()

        print(  # noqa: T201
            f"\n{executor_id} [tool-call] {call.name}({args_preview})",
            flush=True,
        )
        print(f"{executor_id}:", end=" ", flush=True)  # noqa: T201

    # Print any new tool results before the text update
    for result in function_results:
        if result.call_id in printed_tool_results:
            continue
        printed_tool_results.add(result.call_id)

        # Format result for display
        result_text = result.result
        if not isinstance(result_text, str):
            result_text = json.dumps(result_text, ensure_ascii=False)

        print(  # noqa: T201
            f"\n{executor_id} [tool-result] {result.call_id}: {result_text}",
            flush=True,
        )
        print(f"{executor_id}:", end=" ", flush=True)  # noqa: T201

    # Finally, print the text update
    if update.text is not None:
        print(update.text, end="", flush=True)  # noqa: T201

    return last_executor
