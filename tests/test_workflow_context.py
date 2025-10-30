# Copyright (c) Microsoft. All rights reserved.

"""Tests for workflow context handling and follow-up questions."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from agent_framework import AgentExecutorRequest, ChatMessage, Role

from spec_to_agents.workflow.executors import EventPlanningCoordinator


@pytest.mark.asyncio
async def test_coordinator_preserves_conversation_history():
    """Test that coordinator preserves full conversation history when routing."""
    mock_coordinator_agent = Mock()
    mock_summarizer_agent = Mock()

    coordinator = EventPlanningCoordinator(mock_coordinator_agent, mock_summarizer_agent)

    # Create mock context
    mock_ctx = AsyncMock()

    # Mock _chain_summarize to return a summary
    with patch.object(coordinator, "_chain_summarize", new_callable=AsyncMock) as mock_summarize:
        mock_summarize.return_value = "Corporate party, 50 people, outdoor preference"

        # Initialize conversation history by calling start
        await coordinator.start("Plan a corporate party for 50 people", mock_ctx)

        # Verify conversation history was initialized
        assert hasattr(coordinator, "_conversation_history")
        assert len(coordinator._conversation_history) == 1
        assert coordinator._conversation_history[0].text == "Plan a corporate party for 50 people"

        # Add follow-up messages to conversation history
        coordinator._conversation_history.extend([
            ChatMessage(Role.ASSISTANT, text="I'll help you plan that event."),
            ChatMessage(Role.USER, text="Actually, make it outdoor if possible"),
        ])

        # Reset mock to track new calls
        mock_ctx.send_message.reset_mock()

        # Route to venue specialist
        await coordinator._route_to_agent("venue", mock_ctx)

        # Verify the context sent includes recent conversation history
        mock_ctx.send_message.assert_called_once()
        sent_request = mock_ctx.send_message.call_args[0][0]
        assert isinstance(sent_request, AgentExecutorRequest)
        assert len(sent_request.messages) > 1  # Should include recent history + context message

        # Should include recent conversation turns
        message_texts = [msg.text for msg in sent_request.messages]
        # Recent history should be included
        assert any("outdoor" in text.lower() for text in message_texts)
