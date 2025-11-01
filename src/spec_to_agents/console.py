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

# Import specific components for custom display
import json
from typing import ClassVar

from agent_framework import (
    AgentRunUpdateEvent,
    FunctionCallContent,
    FunctionResultContent,
    RequestInfoEvent,
    WorkflowOutputEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
)
from dotenv import load_dotenv

from spec_to_agents.models.messages import HumanFeedbackRequest
from spec_to_agents.tools.mcp_tools import create_sequential_thinking_tool
from spec_to_agents.utils.clients import create_agent_client
from spec_to_agents.workflow.core import build_event_planning_workflow


# Console formatting helpers
class ConsoleFormatter:
    """Helper class for consistent console formatting."""

    # Color codes (basic ANSI colors for cross-platform compatibility)
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Agent-specific colors
    AGENT_COLORS: ClassVar[dict[str, str]] = {
        "event_coordinator": BLUE,
        "venue": GREEN,
        "budget": YELLOW,
        "catering": MAGENTA,
        "logistics": CYAN,
    }

    @classmethod
    def header(cls, text: str, width: int = 70) -> str:
        """Create a formatted header."""
        return f"\n{cls.BOLD}{cls.BLUE}{'=' * width}{cls.RESET}\n{cls.BOLD}{text.center(width)}{cls.RESET}\n{cls.BOLD}{cls.BLUE}{'=' * width}{cls.RESET}\n"

    @classmethod
    def section(cls, text: str, width: int = 70) -> str:
        """Create a formatted section header."""
        return f"\n{cls.BOLD}{cls.CYAN}{'-' * width}{cls.RESET}\n{cls.BOLD}{text}{cls.RESET}\n{cls.CYAN}{'-' * width}{cls.RESET}\n"

    @classmethod
    def agent_message(cls, agent_name: str, message: str) -> str:
        """Format an agent message with color coding."""
        color = cls.AGENT_COLORS.get(agent_name.lower(), cls.WHITE)
        agent_display = agent_name.replace("_", " ").title()
        return f"{color}{cls.BOLD}🤖 {agent_display}:{cls.RESET} {message}"

    @classmethod
    def user_prompt(cls, text: str) -> str:
        """Format a user input prompt."""
        return f"{cls.BOLD}{cls.GREEN}👤 {text}{cls.RESET}"

    @classmethod
    def system_message(cls, text: str) -> str:
        """Format a system message."""
        return f"{cls.GRAY}ⓘ  {text}{cls.RESET}"

    @classmethod
    def success(cls, text: str) -> str:
        """Format a success message."""
        return f"{cls.GREEN}{cls.BOLD}✅ {text}{cls.RESET}"

    @classmethod
    def warning(cls, text: str) -> str:
        """Format a warning message."""
        return f"{cls.YELLOW}{cls.BOLD}⚠️  {text}{cls.RESET}"

    @classmethod
    def error(cls, text: str) -> str:
        """Format an error message."""
        return f"{cls.RED}{cls.BOLD}❌ {text}{cls.RESET}"

    @classmethod
    def thinking(cls, text: str) -> str:
        """Format a 'thinking' or processing message."""
        return f"{cls.DIM}{cls.GRAY}💭 {text}{cls.RESET}"

    @classmethod
    def tool_call(cls, agent_name: str, tool_name: str, args: str) -> str:
        """Format a tool call message."""
        color = cls.AGENT_COLORS.get(agent_name.lower(), cls.WHITE)
        return f"{color}🔧 {agent_name} [tool-call] {tool_name}({args}){cls.RESET}"

    @classmethod
    def tool_result(cls, agent_name: str, call_id: str, result: str) -> str:
        """Format a tool result message."""
        color = cls.AGENT_COLORS.get(agent_name.lower(), cls.WHITE)
        # Truncate long results for readability
        if len(result) > 200:
            result = result[:197] + "..."
        return f"{color}📊 {agent_name} [tool-result] {call_id}: {result}{cls.RESET}"

    @classmethod
    def agent_text(cls, agent_name: str, text: str) -> str:
        """Format agent text output."""
        color = cls.AGENT_COLORS.get(agent_name.lower(), cls.WHITE)
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def format_event_plan(cls, text: str) -> str:
        """Format the final event plan output with improved readability."""
        if not text or text.strip() == "":
            return cls.warning("No event plan was generated.")

        # Extract markdown content from JSON if needed
        markdown_text = cls._extract_markdown_from_json(text)

        # Handle some common formatting issues in the raw text
        markdown_text = markdown_text.replace("\\n", "\n")  # Handle escaped newlines from JSON
        markdown_text = markdown_text.replace("\n\n\n", "\n\n")  # Remove excessive newlines

        lines = markdown_text.split("\n")
        formatted_lines: list[str] = []
        in_list_context = False

        for line in lines:
            original_line = line
            stripped_line = line.strip()

            # Skip empty lines but preserve spacing
            if not stripped_line:
                formatted_lines.append("")
                in_list_context = False
                continue

            # Handle various header patterns
            if stripped_line.startswith("# "):
                # Main title
                header_text = stripped_line[2:].strip()
                formatted_lines.append(f"\n{cls.BOLD}{cls.BLUE}🎉 {header_text}{cls.RESET}")
                formatted_lines.append("")
                in_list_context = False
            elif stripped_line.startswith("## "):
                # Section header
                header_text = stripped_line[3:].strip()
                formatted_lines.append(f"\n{cls.BOLD}{cls.BLUE}📋 {header_text}{cls.RESET}")
                formatted_lines.append("")
                in_list_context = False
            elif stripped_line.startswith("### "):
                # Subsection header
                header_text = stripped_line[4:].strip()
                formatted_lines.append(f"\n{cls.BOLD}{cls.CYAN}  📍 {header_text}{cls.RESET}")
                in_list_context = False
            elif stripped_line.startswith("#### "):
                # Sub-subsection header
                header_text = stripped_line[5:].strip()
                formatted_lines.append(f"{cls.BOLD}    🔸 {header_text}{cls.RESET}")
                in_list_context = False

            # Handle bullet points and lists
            elif stripped_line.startswith(("- ", "* ", "• ")):
                # Top-level bullet point
                bullet_text = stripped_line[2:].strip()
                if stripped_line.startswith("• "):
                    bullet_text = stripped_line[2:].strip()

                if ":" in bullet_text:
                    # Try to split on first colon for key-value pairs
                    parts = bullet_text.split(":", 1)
                    if len(parts) == 2 and len(parts[0]) < 50:  # Reasonable key length
                        key, value = parts
                        formatted_lines.append(f"    • {cls.BOLD}{key.strip()}:{cls.RESET} {value.strip()}")
                    else:
                        formatted_lines.append(f"    • {bullet_text}")
                else:
                    formatted_lines.append(f"    • {bullet_text}")
                in_list_context = True

            elif stripped_line.startswith(("  - ", "  * ", "    - ", "    * ")):
                # Nested bullet point
                bullet_text = stripped_line.split(" ", 2)[-1] if len(stripped_line.split(" ", 2)) > 2 else stripped_line.strip()
                if ":" in bullet_text:
                    parts = bullet_text.split(":", 1)
                    if len(parts) == 2 and len(parts[0]) < 50:
                        key, value = parts
                        formatted_lines.append(f"      ◦ {cls.BOLD}{key.strip()}:{cls.RESET} {value.strip()}")
                    else:
                        formatted_lines.append(f"      ◦ {bullet_text}")
                else:
                    formatted_lines.append(f"      ◦ {bullet_text}")
                in_list_context = True

            # Handle numbered lists
            elif cls._is_numbered_list_item(stripped_line):
                formatted_lines.append(f"    {stripped_line}")
                in_list_context = True

            # Handle key-value pairs at root level
            elif ":" in stripped_line and not stripped_line.startswith(" ") and len(stripped_line.split(":", 1)) == 2:
                key, value = stripped_line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Check if this looks like a key-value pair (key not too long, value exists)
                if len(key) < 50 and value and not key.lower().endswith(("http", "https")):
                    formatted_lines.append(f"\n{cls.BOLD}{key}:{cls.RESET} {value}")
                else:
                    # Treat as regular text
                    formatted_lines.append(f"  {stripped_line}")
                in_list_context = False

            # Handle lines that look like section dividers
            elif stripped_line.replace("=", "").replace("-", "").replace("_", "").strip() == "":
                # Skip visual separators
                formatted_lines.append("")
                in_list_context = False

            # Handle lines that are likely headers (all caps, short)
            elif stripped_line.upper() == stripped_line and len(stripped_line) < 50 and len(stripped_line) > 3 and stripped_line.replace(" ", "").isalpha():
                formatted_lines.append(f"\n{cls.BOLD}{cls.YELLOW}📌 {stripped_line}{cls.RESET}")
                in_list_context = False

            # Handle currency/price patterns
            elif cls._contains_price_pattern(stripped_line):
                formatted_lines.append(f"  💰 {cls.BOLD}{stripped_line}{cls.RESET}")
                in_list_context = False

            # Handle date/time patterns
            elif cls._contains_datetime_pattern(stripped_line):
                formatted_lines.append(f"  📅 {cls.BOLD}{stripped_line}{cls.RESET}")
                in_list_context = False

            # Handle contact information
            elif cls._contains_contact_pattern(stripped_line):
                formatted_lines.append(f"  📞 {stripped_line}")
                in_list_context = False

            else:
                # Regular text - handle indentation
                leading_spaces = len(original_line) - len(original_line.lstrip())

                if in_list_context and leading_spaces == 0:
                    # If we're in a list context and this line has no indentation,
                    # it might be a continuation of the previous item
                    formatted_lines.append(f"      {stripped_line}")
                elif leading_spaces > 0:
                    # Preserve original indentation with minimum of 2 spaces
                    indent = " " * max(2, leading_spaces)
                    formatted_lines.append(f"{indent}{stripped_line}")
                else:
                    # Regular paragraph text
                    formatted_lines.append(f"  {stripped_line}")

        return "\n".join(formatted_lines)

    @classmethod
    def _extract_markdown_from_json(cls, text: str) -> str:
        """Extract markdown content from JSON event plan format."""
        try:
            import json

            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "summary" in parsed_data:
                return str(parsed_data["summary"])
            # If it's JSON but doesn't have summary, convert to readable format
            return json.dumps(parsed_data, indent=2)
        except (json.JSONDecodeError, TypeError):
            # Not JSON, return original text
            return text

    @classmethod
    def _is_numbered_list_item(cls, line: str) -> bool:
        """Check if line is a numbered list item (1. , 2. , etc.)."""
        import re

        return bool(re.match(r"^\d+\.?\s+", line.strip()))

    @classmethod
    def _contains_price_pattern(cls, line: str) -> bool:
        """Check if line contains price/currency information."""
        import re

        return bool(re.search(r"[\$£€¥]\s*\d+([,\d]*)?(\.\d{2})?", line))

    @classmethod
    def _contains_datetime_pattern(cls, line: str) -> bool:
        """Check if line contains date or time information."""
        import re

        patterns = [
            r"\d{1,2}[:/]\d{1,2}[:/]\d{2,4}",  # Date patterns
            r"\d{1,2}:\d{2}\s*(AM|PM|am|pm)",  # Time patterns
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",  # Days
            r"(January|February|March|April|May|June|July|August|September|October|November|December)",  # Months
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)

    @classmethod
    def _contains_contact_pattern(cls, line: str) -> bool:
        """Check if line contains contact information."""
        import re

        patterns = [
            r"\(\d{3}\)\s*\d{3}[-.\s]?\d{4}",  # Phone numbers
            r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",  # Phone numbers
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email
        ]
        return any(re.search(pattern, line) for pattern in patterns)


def display_colored_agent_update(
    event: AgentRunUpdateEvent,
    last_executor: str | None,
    printed_tool_calls: set[str],
    printed_tool_results: set[str],
) -> str | None:
    """
    Display an AgentRunUpdateEvent with color coding and improved formatting.

    This is an improved version of the original display_agent_run_update that uses
    our ConsoleFormatter color scheme.
    """
    executor_id = event.executor_id
    update = event.data

    # Safety check: ensure update has contents
    if update is None or update.contents is None:
        return last_executor

    # Extract function calls and results from the update
    function_calls = [c for c in update.contents if isinstance(c, FunctionCallContent)]
    function_results = [c for c in update.contents if isinstance(c, FunctionResultContent)]

    # Print executor ID when it changes with color coding
    if executor_id != last_executor:
        if last_executor is not None:
            print()  # Add newline between executor transitions

        # Format executor name nicely
        agent_display = executor_id.replace("_", " ").title()
        color = ConsoleFormatter.AGENT_COLORS.get(executor_id.lower(), ConsoleFormatter.WHITE)
        print(f"{color}{ConsoleFormatter.BOLD}🤖 {agent_display}:{ConsoleFormatter.RESET} ", end="", flush=True)
        last_executor = executor_id

    # Print any new tool calls before the text update
    for call in function_calls:
        if call.call_id in printed_tool_calls:
            continue
        printed_tool_calls.add(call.call_id)

        # Format arguments for display
        args = call.arguments
        args_preview = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else (args or "").strip()

        # Truncate long arguments for readability
        if len(args_preview) > 100:
            args_preview = args_preview[:97] + "..."

        print(f"\n{ConsoleFormatter.tool_call(executor_id, call.name, args_preview)}")

        # Continue the agent line
        color = ConsoleFormatter.AGENT_COLORS.get(executor_id.lower(), ConsoleFormatter.WHITE)
        agent_display = executor_id.replace("_", " ").title()
        print(f"{color}{ConsoleFormatter.BOLD}🤖 {agent_display}:{ConsoleFormatter.RESET} ", end="", flush=True)

    # Print any new tool results before the text update
    for result in function_results:
        if result.call_id in printed_tool_results:
            continue
        printed_tool_results.add(result.call_id)

        # Format result for display
        result_text = result.result
        if not isinstance(result_text, str):
            result_text = json.dumps(result_text, ensure_ascii=False)

        print(f"\n{ConsoleFormatter.tool_result(executor_id, result.call_id, result_text)}")

        # Continue the agent line
        color = ConsoleFormatter.AGENT_COLORS.get(executor_id.lower(), ConsoleFormatter.WHITE)
        agent_display = executor_id.replace("_", " ").title()
        print(f"{color}{ConsoleFormatter.BOLD}🤖 {agent_display}:{ConsoleFormatter.RESET} ", end="", flush=True)

    # Finally, print the text update with agent color
    if update.text is not None:
        colored_text = ConsoleFormatter.agent_text(executor_id, update.text)
        print(colored_text, end="", flush=True)

    return last_executor


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
    # Welcome header
    print(ConsoleFormatter.header("🎉 Event Planning Assistant 🎉"))
    print(f"{ConsoleFormatter.BOLD}Welcome to your AI-powered event planning experience!{ConsoleFormatter.RESET}")
    print()
    print("Our specialized AI agents will help you plan your event:")
    print(f"  {ConsoleFormatter.agent_message('venue', 'Venue Specialist - Finds perfect locations')}")
    print(f"  {ConsoleFormatter.agent_message('budget', 'Budget Analyst - Manages costs and finances')}")
    print(f"  {ConsoleFormatter.agent_message('catering', 'Catering Coordinator - Handles food & drinks')}")
    print(f"  {ConsoleFormatter.agent_message('logistics', 'Logistics Manager - Coordinates schedules & resources')}")
    print()
    print(f"{ConsoleFormatter.system_message('You may be asked for input or approval during the planning process.')}")
    exit_message = 'Type "exit" at any prompt to quit.'
    print(f"{ConsoleFormatter.system_message(exit_message)}")
    print()

    # Use async context managers for both MCP tool and agent client lifecycle
    async with (
        create_sequential_thinking_tool() as mcp_tool,
        create_agent_client() as client,
    ):
        # Build workflow with connected MCP tool and agent client
        print(f"{ConsoleFormatter.thinking('Initializing AI agents and tools...')}", end="", flush=True)
        workflow = build_event_planning_workflow(client, mcp_tool)
        print(f" {ConsoleFormatter.success('Ready!')}")
        print()

        # Get initial event planning request from user
        print(ConsoleFormatter.section("📝 Tell us about your event"))
        print("Please describe the event you'd like to plan:")
        print()
        print(f"{ConsoleFormatter.DIM}Examples:{ConsoleFormatter.RESET}")
        print(f"{ConsoleFormatter.DIM}  • 'Corporate holiday party for 50 people, budget $5,000'{ConsoleFormatter.RESET}")
        print(f"{ConsoleFormatter.DIM}  • 'Wedding reception for 150 guests in downtown area'{ConsoleFormatter.RESET}")
        print(f"{ConsoleFormatter.DIM}  • 'Tech conference for 200 attendees with catering'{ConsoleFormatter.RESET}")
        print()

        try:
            user_request = input(f"{ConsoleFormatter.user_prompt('Your event request')} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n{ConsoleFormatter.warning('Input interrupted. Exiting.')}")
            return

        if not user_request:
            print(f"\n{ConsoleFormatter.warning('No request provided. Exiting.')}")
            return

        print()
        print(ConsoleFormatter.header("🚀 Planning Your Event"))
        print(f"{ConsoleFormatter.system_message('Our AI agents are now working on your request...')}")
        print()

        # Configuration: Toggle to display streaming agent run updates
        # Set to True to see real-time tool calls, tool results, and text streaming
        # Set to False to only see human-in-the-loop prompts and final output
        display_streaming_updates = True

        if display_streaming_updates:
            print(ConsoleFormatter.system_message("Verbose mode: You'll see detailed agent activity."))
        else:
            print(ConsoleFormatter.system_message("Quiet mode: Only showing key decisions and final results."))
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
            stream = workflow.send_responses_streaming(pending_responses) if pending_responses else workflow.run_stream(user_request)

            pending_responses = None

            # Process events as they stream in
            human_requests: list[tuple[str, HumanFeedbackRequest]] = []

            async for event in stream:
                # Display streaming agent updates if enabled
                if isinstance(event, AgentRunUpdateEvent) and display_streaming_updates:
                    last_executor = display_colored_agent_update(event, last_executor, printed_tool_calls, printed_tool_results)

                # Collect human-in-the-loop requests
                elif isinstance(event, RequestInfoEvent) and isinstance(event.data, HumanFeedbackRequest):
                    # Workflow is requesting human input
                    human_requests.append((event.request_id, event.data))

                # Capture final workflow output
                elif isinstance(event, WorkflowOutputEvent):
                    # Workflow has yielded final output
                    workflow_output = str(event.data)

                # Display workflow status transitions for transparency
                elif isinstance(event, WorkflowStatusEvent) and event.state == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS:
                    print(f"\n{ConsoleFormatter.thinking('Workflow paused - waiting for your input...')}")
                    print()

            # Prompt user for feedback if workflow requested input
            if human_requests:
                responses: dict[str, str] = {}

                for i, (request_id, feedback_request) in enumerate(human_requests, 1):
                    print(ConsoleFormatter.section(f"❓ Input Needed ({i}/{len(human_requests)})"))

                    # Show which agent needs input with color coding
                    agent_name = feedback_request.requesting_agent
                    print(ConsoleFormatter.agent_message(agent_name, "I need your input to continue..."))
                    print()

                    # Show the request type in a friendlier way
                    request_type_display = feedback_request.request_type.replace("_", " ").title()
                    print(f"{ConsoleFormatter.BOLD}Request Type:{ConsoleFormatter.RESET} {request_type_display}")
                    print()

                    # Show the main question/prompt
                    print(f"{ConsoleFormatter.BOLD}Question:{ConsoleFormatter.RESET}")
                    print(f"  {feedback_request.prompt}")
                    print()

                    # Display context if available in a more readable format
                    if feedback_request.context:
                        print(f"{ConsoleFormatter.BOLD}Additional Context:{ConsoleFormatter.RESET}")
                        for key, value in feedback_request.context.items():
                            key_display = key.replace("_", " ").title()
                            # Format context nicely
                            if isinstance(value, (list, dict)):
                                print(f"  📋 {key_display}:")
                                if isinstance(value, list):
                                    for item in value:  # type: ignore
                                        print(f"     • {item}")
                                elif isinstance(value, dict):
                                    for k, v in value.items():  # type: ignore
                                        print(f"     {k}: {v}")
                            else:
                                print(f"  📋 {key_display}: {value}")
                        print()

                    # Get user response with better formatting
                    try:
                        user_response = input(f"{ConsoleFormatter.user_prompt('Your response')} > ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print(f"\n\n{ConsoleFormatter.warning('Input interrupted. Exiting workflow...')}")
                        return

                    print()

                    if user_response.lower() in ("exit", "quit"):
                        print(f"{ConsoleFormatter.warning('Exiting workflow...')}")
                        return

                    if not user_response:
                        user_response = "Continue with your best judgment"
                        message = f'Using default response: "{user_response}"'
                        print(f"{ConsoleFormatter.system_message(message)}")
                        print()

                    responses[request_id] = user_response

                    # Show confirmation of response
                    print(f"{ConsoleFormatter.success('Response recorded. Continuing workflow...')}")
                    print()

                pending_responses = responses

        # Display final workflow output
        print()
        print(ConsoleFormatter.header("🎉 Your Complete Event Plan"))

        # Format the output nicely
        formatted_output = ConsoleFormatter.format_event_plan(workflow_output or "No event plan generated.")
        print(formatted_output)

        print()
        print(ConsoleFormatter.success("Event planning complete! 🎊"))
        print()
        print(f"{ConsoleFormatter.system_message('Thank you for using the AI Event Planning Assistant!')}")

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
