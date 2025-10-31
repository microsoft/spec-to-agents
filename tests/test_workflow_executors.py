# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for workflow executors using service-managed threads.

NOTE: Most tests in this file are now obsolete after refactoring to declarative
fan-out/fan-in pattern. The EventPlanningCoordinator custom executor has been
removed in favor of simple AgentExecutor instances with declarative workflow edges.

The convert_tool_content_to_text utility function tests are preserved as they may
still be useful for other purposes.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import ChatMessage, FunctionCallContent, FunctionResultContent, Role, TextContent

from spec_to_agents.workflow.executors import convert_tool_content_to_text


# Skip all tests that reference EventPlanningCoordinator since it's been removed
pytestmark = pytest.mark.skip(reason="EventPlanningCoordinator removed in favor of declarative workflow pattern")


def test_parse_specialist_output_with_valid_structured_output():
    """Test parsing SpecialistOutput from agent response."""
    from agent_framework import AgentExecutorResponse, AgentRunResponse

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create mock response with structured output
    specialist_output = SpecialistOutput(
        summary="Researched 3 venues", next_agent="budget", user_input_needed=False, user_prompt=None
    )

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = specialist_output

    mock_response = Mock(spec=AgentExecutorResponse)
    mock_response.agent_run_response = mock_run_response

    coordinator = EventPlanningCoordinator(Mock())
    result = coordinator._parse_specialist_output(mock_response)

    assert result.summary == "Researched 3 venues"
    assert result.next_agent == "budget"
    assert result.user_input_needed is False


def test_parse_specialist_output_with_try_parse_fallback():
    """Test parsing with try_parse_value fallback when value is None."""
    from agent_framework import AgentExecutorResponse, AgentRunResponse

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create mock response where value is initially None
    specialist_output = SpecialistOutput(
        summary="Researched 3 venues", next_agent="budget", user_input_needed=False, user_prompt=None
    )

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = None

    # Mock try_parse_value to populate value
    def mock_try_parse(model_type):
        mock_run_response.value = specialist_output

    mock_run_response.try_parse_value = Mock(side_effect=mock_try_parse)

    mock_response = Mock(spec=AgentExecutorResponse)
    mock_response.agent_run_response = mock_run_response

    coordinator = EventPlanningCoordinator(Mock())
    result = coordinator._parse_specialist_output(mock_response)

    # Verify try_parse_value was called
    mock_run_response.try_parse_value.assert_called_once()

    # Verify result is correct
    assert result.summary == "Researched 3 venues"
    assert result.next_agent == "budget"
    assert result.user_input_needed is False


def test_parse_specialist_output_raises_when_missing():
    """Test error raised when no structured output present even after try_parse_value."""
    from agent_framework import AgentExecutorResponse, AgentRunResponse

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = None
    mock_run_response.try_parse_value = Mock()  # Does nothing, value stays None
    mock_run_response.text = ""
    mock_run_response.messages = []

    mock_response = Mock(spec=AgentExecutorResponse)
    mock_response.agent_run_response = mock_run_response
    mock_response.executor_id = "test_specialist"

    coordinator = EventPlanningCoordinator(Mock())

    with pytest.raises(ValueError, match=r"Specialist.*must return SpecialistOutput"):
        coordinator._parse_specialist_output(mock_response)


def test_parse_specialist_output_with_tool_calls_but_no_text():
    """Test error when agent makes tool calls but doesn't generate final structured output."""
    from agent_framework import AgentExecutorResponse, AgentRunResponse, ChatMessage, FunctionCallContent, Role

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Simulate agent that made tool calls but didn't return final TextContent
    tool_call_content = FunctionCallContent(
        call_id="call_123",
        name="web_search",
        arguments='{"query": "venues in Seattle"}',
    )

    message_with_tool_call = Mock(spec=ChatMessage)
    message_with_tool_call.role = Role.ASSISTANT
    message_with_tool_call.contents = [tool_call_content]

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = None
    mock_run_response.try_parse_value = Mock()  # Does nothing, value stays None
    mock_run_response.text = ""  # No TextContent in response
    mock_run_response.messages = [message_with_tool_call]

    mock_response = Mock(spec=AgentExecutorResponse)
    mock_response.agent_run_response = mock_run_response
    mock_response.executor_id = "venue"

    coordinator = EventPlanningCoordinator(Mock())

    with pytest.raises(ValueError) as exc_info:
        coordinator._parse_specialist_output(mock_response)

    error_msg = str(exc_info.value)
    # Verify error includes debugging info about tool calls
    assert "venue" in error_msg
    assert "(empty)" in error_msg or "empty" in error_msg.lower()


@pytest.mark.asyncio
async def test_route_to_agent_sends_single_message():
    """Test routing sends only new message (framework provides history via threads)."""
    from agent_framework import AgentExecutorRequest, Role

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    coordinator = EventPlanningCoordinator(Mock())

    mock_ctx = AsyncMock()

    await coordinator._route_to_agent("budget", "Continue with your analysis", mock_ctx)

    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args

    # Verify AgentExecutorRequest with single message
    request = call_args[0][0]
    assert isinstance(request, AgentExecutorRequest)
    # Should only include new message (framework provides history)
    assert len(request.messages) == 1
    assert request.messages[0].text == "Continue with your analysis"
    assert request.messages[0].role == Role.USER
    assert request.should_respond is True

    # Verify target_id
    assert call_args[1]["target_id"] == "budget"


@pytest.mark.asyncio
async def test_on_specialist_response_routes_to_next_agent():
    """Test routing to next agent based on structured output."""
    from agent_framework import ChatMessage, Role

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    mock_response = Mock()
    mock_response.executor_id = "venue"
    mock_response.agent_run_response.value = SpecialistOutput(
        summary="Researched 3 venues: A ($2k), B ($3k), C ($4k)",
        next_agent="budget",
        user_input_needed=False,
        user_prompt=None,
    )
    # Mock conversation history
    mock_response.full_conversation = [ChatMessage(Role.USER, text="Find venues")]
    mock_response.agent_run_response.messages = []

    coordinator = EventPlanningCoordinator(Mock())

    mock_ctx = AsyncMock()

    await coordinator.on_specialist_response(mock_response, mock_ctx)

    # Verify routed to budget
    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args
    assert call_args[1]["target_id"] == "budget"


@pytest.mark.asyncio
async def test_on_specialist_response_requests_user_input():
    """Test requesting user input when specialist needs it."""
    from agent_framework import ChatMessage, Role

    from spec_to_agents.models.messages import HumanFeedbackRequest, SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    mock_response = Mock()
    mock_response.executor_id = "venue"
    mock_response.agent_run_response.value = SpecialistOutput(
        summary="Found 3 venue options",
        next_agent=None,
        user_input_needed=True,
        user_prompt="Which venue do you prefer: A, B, or C?",
    )
    # Mock conversation history
    mock_response.full_conversation = [ChatMessage(Role.USER, text="Find venues")]
    mock_response.agent_run_response.messages = []

    coordinator = EventPlanningCoordinator(Mock())

    mock_ctx = AsyncMock()

    await coordinator.on_specialist_response(mock_response, mock_ctx)

    # Verify request_info called
    mock_ctx.request_info.assert_called_once()
    call_args = mock_ctx.request_info.call_args[1]

    request = call_args["request_data"]
    assert isinstance(request, HumanFeedbackRequest)
    assert request.prompt == "Which venue do you prefer: A, B, or C?"
    assert request.requesting_agent == "venue"


@pytest.mark.asyncio
async def test_on_specialist_response_synthesizes_when_done():
    """Test final synthesis when next_agent is None and no user input needed."""
    from unittest.mock import patch

    from agent_framework import ChatMessage, Role

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    mock_response = Mock()
    mock_response.executor_id = "logistics"
    mock_response.agent_run_response.value = SpecialistOutput(
        summary="Timeline and coordination complete",
        next_agent=None,
        user_input_needed=False,
        user_prompt=None,
    )
    # Mock conversation history
    mock_response.full_conversation = [ChatMessage(Role.USER, text="Plan event")]
    mock_response.agent_run_response.messages = []

    coordinator = EventPlanningCoordinator(Mock())

    with patch.object(coordinator, "_synthesize_plan", new_callable=AsyncMock) as mock_synthesize:
        mock_ctx = AsyncMock()

        await coordinator.on_specialist_response(mock_response, mock_ctx)

        # Verify synthesis called with ctx and conversation
        mock_synthesize.assert_called_once()
        call_args = mock_synthesize.call_args[0]
        assert call_args[0] == mock_ctx
        assert isinstance(call_args[1], list)  # conversation list


@pytest.mark.asyncio
async def test_on_human_feedback_routes_back():
    """Test human feedback is routed back to requester."""
    from spec_to_agents.models.messages import HumanFeedbackRequest
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    original_request = HumanFeedbackRequest(
        prompt="Which venue?", context={}, request_type="selection", requesting_agent="venue"
    )

    coordinator = EventPlanningCoordinator(Mock())

    mock_ctx = AsyncMock()

    await coordinator.on_human_feedback(original_request, "Venue B", mock_ctx)

    # Verify routed back to venue specialist
    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args
    assert call_args[1]["target_id"] == "venue"
    # Verify message includes user feedback
    request = call_args[0][0]
    assert "Venue B" in request.messages[0].text


@pytest.mark.asyncio
async def test_synthesize_plan_uses_framework_context():
    """Test final synthesis relies on framework-provided context via threads."""
    from agent_framework import ChatMessage, Role

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    mock_agent = Mock()
    mock_result = Mock()
    mock_result.text = "Complete event plan with all specialist recommendations."

    mock_agent_instance = AsyncMock()
    mock_agent_instance.run = AsyncMock(return_value=mock_result)

    coordinator = EventPlanningCoordinator(mock_agent)
    coordinator._agent = mock_agent_instance

    mock_ctx = AsyncMock()

    # Provide conversation history
    conversation = [
        ChatMessage(Role.USER, text="Plan event"),
        ChatMessage(Role.ASSISTANT, text="Venue specialist work done"),
    ]

    await coordinator._synthesize_plan(mock_ctx, conversation)

    # Verify run called with conversation + synthesis instruction
    call_args = mock_agent_instance.run.call_args
    messages = call_args[1]["messages"]

    # Should include original conversation + synthesis instruction
    assert len(messages) == 3  # 2 original + 1 synthesis instruction
    assert "synthesize a comprehensive event plan" in messages[-1].text
    # Should NOT contain manual summary (relies on framework context)
    assert "Summary of specialist work" not in messages[-1].text

    # Verify output yielded
    mock_ctx.yield_output.assert_called_once_with("Complete event plan with all specialist recommendations.")


def test_convert_tool_content_to_text_function_calls():
    """Test converting function calls to text summaries."""
    messages = [
        ChatMessage(
            Role.ASSISTANT,
            contents=[
                TextContent(text="Let me search for venues."),
                FunctionCallContent(name="web_search", arguments={"query": "event venues"}, call_id="call_123"),
            ],
        )
    ]

    converted = convert_tool_content_to_text(messages)

    assert len(converted) == 1
    assert len(converted[0].contents) == 2
    # First content should be original text
    assert isinstance(converted[0].contents[0], TextContent)
    assert converted[0].contents[0].text == "Let me search for venues."
    # Second content should be converted tool call
    assert isinstance(converted[0].contents[1], TextContent)
    assert "Tool Call: web_search" in converted[0].contents[1].text
    assert "event venues" in converted[0].contents[1].text


def test_convert_tool_content_to_text_function_results():
    """Test converting function results to text summaries."""
    messages = [
        ChatMessage(
            Role.TOOL,
            contents=[
                FunctionResultContent(call_id="call_123", result="Found 5 venues", name="web_search"),
            ],
        )
    ]

    converted = convert_tool_content_to_text(messages)

    assert len(converted) == 1
    assert len(converted[0].contents) == 1
    assert isinstance(converted[0].contents[0], TextContent)
    assert "Tool Result for call call_123" in converted[0].contents[0].text
    assert "Found 5 venues" in converted[0].contents[0].text


def test_convert_tool_content_to_text_preserves_role_and_metadata():
    """Test that message role and metadata are preserved during conversion."""
    messages = [
        ChatMessage(
            Role.ASSISTANT,
            contents=[FunctionCallContent(name="test_tool", arguments={}, call_id="call_456")],
            author_name="VenueAgent",
            message_id="msg_789",
        )
    ]

    converted = convert_tool_content_to_text(messages)

    assert converted[0].role == Role.ASSISTANT
    assert converted[0].author_name == "VenueAgent"
    assert converted[0].message_id == "msg_789"


def test_convert_tool_content_to_text_handles_mixed_content():
    """Test converting messages with mixed text and tool content."""
    messages = [
        ChatMessage(
            Role.ASSISTANT,
            contents=[
                TextContent(text="Searching venues..."),
                FunctionCallContent(name="web_search", arguments={"q": "venues"}, call_id="call_1"),
            ],
        ),
        ChatMessage(
            Role.TOOL,
            contents=[FunctionResultContent(call_id="call_1", result="Result data", name="web_search")],
        ),
        ChatMessage(Role.ASSISTANT, contents=[TextContent(text="Found results!")]),
    ]

    converted = convert_tool_content_to_text(messages)

    # Should have all 3 messages
    assert len(converted) == 3
    # First message: text + converted tool call
    assert len(converted[0].contents) == 2
    assert isinstance(converted[0].contents[0], TextContent)
    assert converted[0].contents[0].text == "Searching venues..."
    assert isinstance(converted[0].contents[1], TextContent)
    assert "Tool Call: web_search" in converted[0].contents[1].text
    # Second message: converted tool result
    assert len(converted[1].contents) == 1
    assert isinstance(converted[1].contents[0], TextContent)
    assert "Tool Result" in converted[1].contents[0].text
    # Third message: original text preserved
    assert len(converted[2].contents) == 1
    assert isinstance(converted[2].contents[0], TextContent)
    assert converted[2].contents[0].text == "Found results!"
