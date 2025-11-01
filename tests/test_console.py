# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for console.py display_agent_run_update function."""

from io import StringIO
from unittest.mock import Mock, patch

from agent_framework import (
    AgentRunResponseUpdate,
    AgentRunUpdateEvent,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
)

from spec_to_agents.utils.display import display_agent_run_update


def test_display_agent_run_update_with_text_only() -> None:
    """Test displaying a simple text update without tool calls."""
    # Create mock event with text update
    update = Mock(spec=AgentRunResponseUpdate)
    update.contents = [TextContent(text="Hello, world!")]
    update.text = "Hello, world!"

    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "venue"
    event.data = update

    printed_calls: set[str] = set()
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        result = display_agent_run_update(event, None, printed_calls, printed_results)

        output = mock_stdout.getvalue()
        # Rich output uses a rule separator with agent name
        assert "venue" in output
        assert "Hello, world!" in output
        assert result == "venue"


def test_display_agent_run_update_with_function_call() -> None:
    """Test displaying a function call update."""
    # Create mock event with function call
    call_content = FunctionCallContent(
        name="web_search",
        arguments={"query": "event venues in Seattle"},
        call_id="call_123",
    )

    update = Mock(spec=AgentRunResponseUpdate)
    update.contents = [call_content]
    update.text = None

    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "venue"
    event.data = update

    printed_calls: set[str] = set()
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        result = display_agent_run_update(event, None, printed_calls, printed_results)

        output = mock_stdout.getvalue()
        # Rich output uses panels and styled text
        assert "venue" in output
        assert "Function Call" in output or "Tool Call" in output
        assert "web_search" in output
        # The arguments are rendered as JSON in a Syntax object, so just check the call was added
        assert "call_123" in printed_calls
        assert result == "venue"


def test_display_agent_run_update_with_function_result() -> None:
    """Test displaying a function result update."""
    # Create mock event with function result
    result_content = FunctionResultContent(
        call_id="call_123",
        result="Found 5 venues in Seattle area",
        name="web_search",
    )

    update = Mock(spec=AgentRunResponseUpdate)
    update.contents = [result_content]
    update.text = None

    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "venue"
    event.data = update

    printed_calls: set[str] = set()
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        result = display_agent_run_update(event, None, printed_calls, printed_results)

        output = mock_stdout.getvalue()
        # Rich output uses panels for results
        assert "venue" in output
        assert "Tool Result" in output or "Result" in output
        assert "call_123" in output
        assert "Found 5 venues in Seattle area" in output
        assert "call_123" in printed_results
        assert result == "venue"


def test_display_agent_run_update_with_mixed_content() -> None:
    """Test displaying mixed content (text + tool call + tool result)."""
    # Create mock event with mixed content
    text_content = TextContent(text="Let me search for venues. ")
    call_content = FunctionCallContent(
        name="web_search",
        arguments={"query": "venues"},
        call_id="call_456",
    )
    result_content = FunctionResultContent(
        call_id="call_456",
        result="Found 3 options",
        name="web_search",
    )

    update = Mock(spec=AgentRunResponseUpdate)
    update.contents = [text_content, call_content, result_content]
    update.text = "Let me search for venues. "

    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "budget"
    event.data = update

    printed_calls: set[str] = set()
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        result = display_agent_run_update(event, None, printed_calls, printed_results)

        output = mock_stdout.getvalue()
        # Rich output for mixed content
        assert "budget" in output
        assert "Function Call" in output or "Tool Call" in output
        assert "web_search" in output
        assert "Tool Result" in output or "Result" in output
        assert "Found 3 options" in output
        assert "Let me search for venues." in output
        assert "call_456" in printed_calls
        assert "call_456" in printed_results
        assert result == "budget"


def test_display_agent_run_update_executor_transition() -> None:
    """Test displaying executor transitions."""
    # Create first event
    update1 = Mock(spec=AgentRunResponseUpdate)
    update1.contents = [TextContent(text="Venue analysis")]
    update1.text = "Venue analysis"

    event1 = Mock(spec=AgentRunUpdateEvent)
    event1.executor_id = "venue"
    event1.data = update1

    # Create second event with different executor
    update2 = Mock(spec=AgentRunResponseUpdate)
    update2.contents = [TextContent(text="Budget analysis")]
    update2.text = "Budget analysis"

    event2 = Mock(spec=AgentRunUpdateEvent)
    event2.executor_id = "budget"
    event2.data = update2

    printed_calls: set[str] = set()
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        # First call
        last_exec = display_agent_run_update(event1, None, printed_calls, printed_results)
        assert last_exec == "venue"

        # Second call should print a newline before the new executor
        last_exec = display_agent_run_update(event2, last_exec, printed_calls, printed_results)

        output = mock_stdout.getvalue()
        # Should have both executors (Rich uses rules, not colons)
        assert "venue" in output
        assert "budget" in output
        # Should have transitions between them
        assert last_exec == "budget"


def test_display_agent_run_update_deduplicate_tool_calls() -> None:
    """Test that duplicate tool calls are not printed twice."""
    # Create two events with the same tool call
    call_content = FunctionCallContent(
        name="web_search",
        arguments={"query": "test"},
        call_id="call_789",
    )

    update = Mock(spec=AgentRunResponseUpdate)
    update.contents = [call_content]
    update.text = None

    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "venue"
    event.data = update

    printed_calls: set[str] = {"call_789"}  # Already printed
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_agent_run_update(event, None, printed_calls, printed_results)

        output = mock_stdout.getvalue()
        # Should NOT print the tool call again
        assert "[tool-call]" not in output
        assert "web_search" not in output


def test_display_agent_run_update_deduplicate_tool_results() -> None:
    """Test that duplicate tool results are not printed twice."""
    # Create event with tool result
    result_content = FunctionResultContent(
        call_id="call_999",
        result="Result data",
        name="web_search",
    )

    update = Mock(spec=AgentRunResponseUpdate)
    update.contents = [result_content]
    update.text = None

    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "venue"
    event.data = update

    printed_calls: set[str] = set()
    printed_results: set[str] = {"call_999"}  # Already printed

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        display_agent_run_update(event, None, printed_calls, printed_results)

        output = mock_stdout.getvalue()
        # Should NOT print the tool result again
        assert "[tool-result]" not in output
        assert "Result data" not in output


def test_display_agent_run_update_with_none_data() -> None:
    """Test handling of event with None data."""
    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "venue"
    event.data = None

    printed_calls: set[str] = set()
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        result = display_agent_run_update(event, "previous", printed_calls, printed_results)

        # Should return last_executor unchanged and not print anything
        assert result == "previous"
        output = mock_stdout.getvalue()
        assert output == ""


def test_display_agent_run_update_with_none_contents() -> None:
    """Test handling of event with None contents."""
    update = Mock(spec=AgentRunResponseUpdate)
    update.contents = None
    update.text = None

    event = Mock(spec=AgentRunUpdateEvent)
    event.executor_id = "venue"
    event.data = update

    printed_calls: set[str] = set()
    printed_results: set[str] = set()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        result = display_agent_run_update(event, "previous", printed_calls, printed_results)

        # Should return last_executor unchanged and not print anything
        assert result == "previous"
        output = mock_stdout.getvalue()
        assert output == ""
