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
