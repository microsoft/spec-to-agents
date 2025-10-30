# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for workflow executors including chained summarization."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from spec_to_agents.workflow.core import build_event_planning_workflow
from spec_to_agents.workflow.messages import SummarizedContext


@pytest.mark.asyncio
async def test_summarize_context_first_call():
    """
    Test summarization with empty previous summary.

    This verifies that _summarize_context works correctly on the first call
    when there's no existing summary (empty string). The result should:
    - Be non-empty
    - Contain the new content information
    - Be within the 150-word limit
    """
    # Build workflow and get coordinator
    workflow = await build_event_planning_workflow()
    coordinator = workflow.executors["event_coordinator"]

    # First call with no previous summary
    new_content = (
        "The venue specialist found three options: "
        "Option A ($2,000, capacity 40), "
        "Option B ($3,500, capacity 60), "
        "Option C ($5,000, capacity 100). "
        "All venues have excellent reviews and are available on the requested date."
    )

    # Mock the chat client's get_response method
    mock_summary = (
        "Venue specialist identified three options: "
        "A ($2k, 40 cap), B ($3.5k, 60 cap), C ($5k, 100 cap). "
        "All have excellent reviews and availability."
    )

    mock_response = Mock()
    mock_response.value = SummarizedContext(condensed_summary=mock_summary)
    mock_response.text = f'{{"condensed_summary": "{mock_summary}"}}'

    with patch("spec_to_agents.clients.get_chat_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_response = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await coordinator._summarize_context(new_content)

    # Verify the result
    assert result is not None, "Summary should not be None"
    assert isinstance(result, str), "Summary should be a string"
    assert len(result) > 0, "Summary should not be empty"

    # Verify word count is within limit (150 words)
    word_count = len(result.split())
    assert word_count <= 150, f"Summary should be ≤150 words, got {word_count}"

    # Verify it contains key information
    assert "venue" in result.lower(), "Summary should mention venues"


@pytest.mark.asyncio
async def test_summarize_context_chained():
    """
    Test chained summarization with existing summary.

    This verifies that _summarize_context correctly chains the previous
    summary with new content and produces a condensed result that:
    - Incorporates both old and new information
    - Stays within the 150-word limit
    - Preserves critical details from both sources
    """
    # Build workflow and get coordinator
    workflow = await build_event_planning_workflow()
    coordinator = workflow.executors["event_coordinator"]

    # Set initial summary
    initial_summary = (
        "User wants a corporate event for 50 people on March 15, 2025. "
        "Venue specialist found three options: Option A ($2k), Option B ($3.5k), Option C ($5k). "
        "User selected Option B."
    )
    coordinator._current_summary = initial_summary

    # New content from budget analyst
    new_content = (
        "Budget analysis complete. Total allocated: $10,000. "
        "Venue cost: $3,500 (35%). Catering budget: $4,000 (40%). "
        "Logistics and miscellaneous: $2,500 (25%). "
        "Budget is sufficient for high-quality catering with the selected venue."
    )

    # Mock the chat client's get_response method
    mock_summary = (
        "Corporate event for 50 people on March 15, 2025. "
        "Venue: Option B ($3.5k) selected. "
        "Budget: $10k total - venue $3.5k (35%), catering $4k (40%), logistics $2.5k (25%). "
        "Sufficient for high-quality catering."
    )

    mock_response = Mock()
    mock_response.value = SummarizedContext(condensed_summary=mock_summary)
    mock_response.text = f'{{"condensed_summary": "{mock_summary}"}}'

    with patch("spec_to_agents.clients.get_chat_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_response = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await coordinator._summarize_context(new_content)

    # Verify the result
    assert result is not None, "Summary should not be None"
    assert isinstance(result, str), "Summary should be a string"
    assert len(result) > 0, "Summary should not be empty"

    # Verify word count is within limit (150 words)
    word_count = len(result.split())
    assert word_count <= 150, f"Summary should be ≤150 words, got {word_count}"

    # Verify it incorporates old information (from mock summary)
    assert "50" in result, "Summary should preserve guest count"
    assert "march" in result.lower() or "15" in result, "Summary should preserve date"

    # Verify it incorporates new information (from mock summary)
    assert "budget" in result.lower() or "$10k" in result or "10k" in result, "Summary should mention budget"

    # Verify it has critical venue information (from mock summary)
    assert "option b" in result.lower() or "venue" in result.lower(), "Summary should mention venue selection"


@pytest.mark.asyncio
async def test_start_handler_initializes_summary():
    """
    Test that start handler initializes summary and routes to venue.

    This verifies that the start handler:
    - Initializes self._current_summary with the user's request
    - Routes to the venue specialist by default
    - Sends a message containing both the original input and summary
    """
    # Build workflow and get coordinator
    workflow = await build_event_planning_workflow()
    coordinator = workflow.executors["event_coordinator"]

    # Mock the workflow context
    mock_ctx = AsyncMock()
    mock_ctx.send_message = AsyncMock()

    # Mock the chain_summarize method to avoid external dependencies
    mock_summary = "User wants a corporate party for 50 people with a budget of $5,000."
    coordinator._chain_summarize = AsyncMock(return_value=mock_summary)

    # Initial user request
    test_input = "I need to plan a corporate party for 50 people with a budget of $5,000"

    # Call the start handler
    await coordinator.start(test_input, mock_ctx)

    # Verify self._current_summary was initialized
    assert coordinator._current_summary == mock_summary, "Summary should be initialized with user request"

    # Verify chain_summarize was called with the initial input
    coordinator._chain_summarize.assert_called_once_with(prev="", new=test_input)

    # Verify ctx.send_message was called with target_id="venue"
    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args

    # Check target_id is venue
    assert call_args.kwargs.get("target_id") == "venue", "Should route to venue specialist"

    # Check that the message is an AgentExecutorRequest
    from agent_framework import AgentExecutorRequest

    message_arg = call_args.args[0] if call_args.args else None
    assert isinstance(message_arg, AgentExecutorRequest), "Message should be an AgentExecutorRequest"

    # Check that the messages list contains our expected content
    assert len(message_arg.messages) > 0, "Should have at least one message"
    message_text = message_arg.messages[0].text
    assert test_input in message_text, "Message should contain original input"
    assert mock_summary in message_text, "Message should contain summary"


def test_parse_specialist_output_with_valid_structured_output():
    """Test parsing SpecialistOutput from agent response."""
    from agent_framework import AgentExecutorResponse, AgentRunResponse

    from spec_to_agents.workflow.executors import EventPlanningCoordinator
    from spec_to_agents.workflow.messages import SpecialistOutput

    # Create mock response with structured output
    specialist_output = SpecialistOutput(
        summary="Researched 3 venues", next_agent="budget", user_input_needed=False, user_prompt=None
    )

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = specialist_output

    mock_response = Mock(spec=AgentExecutorResponse)
    mock_response.agent_run_response = mock_run_response

    coordinator = EventPlanningCoordinator(Mock(), Mock())
    result = coordinator._parse_specialist_output(mock_response)

    assert result.summary == "Researched 3 venues"
    assert result.next_agent == "budget"
    assert result.user_input_needed is False


def test_parse_specialist_output_raises_when_missing():
    """Test error raised when no structured output present."""
    from agent_framework import AgentExecutorResponse, AgentRunResponse

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = None

    mock_response = Mock(spec=AgentExecutorResponse)
    mock_response.agent_run_response = mock_run_response

    coordinator = EventPlanningCoordinator(Mock(), Mock())

    with pytest.raises(ValueError, match="Specialist must return SpecialistOutput"):
        coordinator._parse_specialist_output(mock_response)


@pytest.mark.asyncio
async def test_route_to_agent_sends_summary_message():
    """Test routing sends condensed summary to target agent."""
    from agent_framework import AgentExecutorRequest

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    coordinator = EventPlanningCoordinator(Mock(), Mock())
    coordinator._current_summary = "User wants party for 50 people. Budget $5k."

    mock_ctx = AsyncMock()

    await coordinator._route_to_agent("budget", mock_ctx)

    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args

    # Verify AgentExecutorRequest with summary message
    request = call_args[0][0]
    assert isinstance(request, AgentExecutorRequest)
    assert len(request.messages) == 1
    assert "User wants party for 50 people" in request.messages[0].text
    assert request.should_respond is True

    # Verify target_id
    assert call_args[1]["target_id"] == "budget"


@pytest.mark.asyncio
async def test_chain_summarize_with_previous_summary():
    """Test chaining previous summary with new content."""
    from spec_to_agents.workflow.executors import EventPlanningCoordinator
    from spec_to_agents.workflow.messages import SummarizedContext

    mock_agent = Mock()
    mock_summarizer = Mock()

    # Mock client.get_response
    mock_result = Mock()
    mock_result.value = SummarizedContext(condensed_summary="Party for 50. Venue selected. Budget allocated.")
    mock_result.text = "Party for 50. Venue selected. Budget allocated."

    with patch("spec_to_agents.clients.get_chat_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_response = AsyncMock(return_value=mock_result)
        mock_get_client.return_value = mock_client

        coordinator = EventPlanningCoordinator(mock_agent, mock_summarizer)
        coordinator._current_summary = "Party for 50 people."

        result = await coordinator._chain_summarize(
            prev="Party for 50 people.", new="Venue specialist selected Option B ($3k)."
        )

        assert result == "Party for 50. Venue selected. Budget allocated."
        mock_client.get_response.assert_called_once()


@pytest.mark.asyncio
async def test_chain_summarize_without_previous_summary():
    """Test initial summarization without previous content."""
    from spec_to_agents.workflow.executors import EventPlanningCoordinator
    from spec_to_agents.workflow.messages import SummarizedContext

    mock_agent = Mock()
    mock_summarizer = Mock()

    mock_result = Mock()
    mock_result.value = SummarizedContext(condensed_summary="User wants corporate party, 50 people, $5k budget.")
    mock_result.text = "User wants corporate party, 50 people, $5k budget."

    with patch("spec_to_agents.clients.get_chat_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_response = AsyncMock(return_value=mock_result)
        mock_get_client.return_value = mock_client

        coordinator = EventPlanningCoordinator(mock_agent, mock_summarizer)

        result = await coordinator._chain_summarize(prev="", new="Plan a corporate party for 50 people with $5k budget")

        assert result == "User wants corporate party, 50 people, $5k budget."
