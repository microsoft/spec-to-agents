# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for workflow executors using service-managed threads."""

from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import ChatMessage, FunctionCallContent, FunctionResultContent, Role, TextContent

from spec_to_agents.workflow.executors import convert_tool_content_to_text


def test_parse_specialist_output_with_valid_structured_output():
    """Test parsing SpecialistOutput from agent response."""
    from agent_framework import AgentRunResponse

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create mock response with structured output
    specialist_output = SpecialistOutput(
        summary="Researched 3 venues", next_agent="budget", user_input_needed=False, user_prompt=None
    )

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = specialist_output

    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)
    result = coordinator._parse_specialist_output(mock_run_response)

    assert result.summary == "Researched 3 venues"
    assert result.next_agent == "budget"
    assert result.user_input_needed is False


def test_parse_specialist_output_with_try_parse_fallback():
    """Test parsing with try_parse_value fallback when value is None."""
    from agent_framework import AgentRunResponse

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

    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)
    result = coordinator._parse_specialist_output(mock_run_response)

    # Verify try_parse_value was called
    mock_run_response.try_parse_value.assert_called_once()

    # Verify result is correct
    assert result.summary == "Researched 3 venues"
    assert result.next_agent == "budget"
    assert result.user_input_needed is False


def test_parse_specialist_output_raises_when_missing():
    """Test error raised when no structured output present even after try_parse_value."""
    from agent_framework import AgentRunResponse

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    mock_run_response = Mock(spec=AgentRunResponse)
    mock_run_response.value = None
    mock_run_response.try_parse_value = Mock()  # Does nothing, value stays None
    mock_run_response.text = ""
    mock_run_response.messages = []

    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    with pytest.raises(ValueError, match=r"Coordinator agent.*must return SpecialistOutput"):
        coordinator._parse_specialist_output(mock_run_response)


def test_parse_specialist_output_with_tool_calls_but_no_text():
    """Test error when agent makes tool calls but doesn't generate final structured output."""
    from agent_framework import AgentRunResponse, ChatMessage, FunctionCallContent, Role

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

    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    with pytest.raises(ValueError) as exc_info:
        coordinator._parse_specialist_output(mock_run_response)

    error_msg = str(exc_info.value)
    # Verify error includes debugging info about tool calls
    assert "(empty)" in error_msg or "empty" in error_msg.lower()


@pytest.mark.asyncio
async def test_on_specialist_request_sends_message():
    """Test on_specialist_request sends message to specialist."""
    from agent_framework import AgentExecutorRequest, Role

    from spec_to_agents.models.messages import SpecialistRequest
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    mock_ctx = AsyncMock()

    # Create specialist request
    request = SpecialistRequest(
        specialist_id="budget",
        message="Continue with your analysis",
    )

    await coordinator.on_specialist_request(request, mock_ctx)

    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args

    # Verify AgentExecutorRequest with single message
    sent_request = call_args[0][0]
    assert isinstance(sent_request, AgentExecutorRequest)
    # Should only include new message (framework provides history)
    assert len(sent_request.messages) == 1
    assert sent_request.messages[0].text == "Continue with your analysis"
    assert sent_request.messages[0].role == Role.USER
    assert sent_request.should_respond is True

    # Verify target_id
    assert call_args[1]["target_id"] == "budget"


@pytest.mark.asyncio
async def test_on_specialist_response_routes_to_next_agent():
    """Test that specialist responses are analyzed by coordinator agent for routing."""
    from agent_framework import AgentRunResponse, ChatMessage, Role

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create mock coordinator agent that returns routing decision
    mock_coordinator_agent = AsyncMock()
    mock_coordinator_response = Mock(spec=AgentRunResponse)
    mock_coordinator_response.value = SpecialistOutput(
        summary="Venue selected, proceeding to budget",
        next_agent="budget",
        user_input_needed=False,
        user_prompt=None,
    )
    mock_coordinator_agent.run.return_value = mock_coordinator_response

    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    # Create mock specialist response (natural text, no SpecialistOutput)
    mock_response = Mock()
    mock_response.executor_id = "venue"
    mock_response.full_conversation = [
        ChatMessage(Role.USER, text="Find venues"),
        ChatMessage(Role.ASSISTANT, text="I recommend The Foundry ($3k, 60 capacity)"),
    ]
    mock_response.agent_run_response = Mock(spec=AgentRunResponse)
    mock_response.agent_run_response.messages = []

    mock_ctx = AsyncMock()

    await coordinator.on_specialist_response(mock_response, mock_ctx)

    # Verify coordinator agent was called to analyze specialist output
    mock_coordinator_agent.run.assert_called_once()

    # Verify routed to budget specialist
    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args
    assert call_args[1]["target_id"] == "budget"


@pytest.mark.asyncio
async def test_on_human_feedback_routes_to_requesting_agent():
    """Test human feedback routes directly back to the specialist that requested it."""

    from spec_to_agents.models.messages import HumanFeedbackRequest
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    original_request = HumanFeedbackRequest(
        prompt="Which venue?",
        context={},
        request_type="selection",
        requesting_agent="venue",  # Venue specialist requested the input
    )

    # Create coordinator (no need to mock coordinator agent for this simplified flow)
    mock_coordinator_agent = AsyncMock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)
    mock_ctx = AsyncMock()

    await coordinator.on_human_feedback(original_request, "Venue B", mock_ctx)

    # Verify routed directly back to venue specialist (no coordinator agent call)
    mock_coordinator_agent.run.assert_not_called()

    # Verify routed back to venue specialist
    mock_ctx.send_message.assert_called_once()
    call_args = mock_ctx.send_message.call_args
    assert call_args[1]["target_id"] == "venue"


@pytest.mark.asyncio
async def test_full_flow_venue_to_budget():
    """Integration test: Venue specialist natural text → Coordinator analyzes → Routes to Budget."""
    from agent_framework import AgentRunResponse, ChatMessage, Role

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create mock coordinator agent that returns routing decision
    mock_coordinator_agent = AsyncMock()
    mock_coordinator_response = Mock(spec=AgentRunResponse)
    mock_coordinator_response.value = SpecialistOutput(
        summary="Venue selected, proceeding to budget analysis",
        next_agent="budget",
        user_input_needed=False,
        user_prompt=None,
    )
    mock_coordinator_agent.run.return_value = mock_coordinator_response

    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    # Step 1: Venue specialist completes and returns natural text
    venue_response = Mock()
    venue_response.executor_id = "venue"
    venue_response.full_conversation = [
        ChatMessage(Role.USER, text="Plan a corporate party for 50 people in Seattle"),
        ChatMessage(Role.ASSISTANT, text="I recommend The Foundry ($3k, 60 capacity, downtown)"),
    ]
    venue_response.agent_run_response = Mock(spec=AgentRunResponse)
    venue_response.agent_run_response.messages = []

    mock_ctx = AsyncMock()

    # Step 2: Coordinator analyzes specialist output and routes
    await coordinator.on_specialist_response(venue_response, mock_ctx)

    # Verify coordinator agent was called to analyze specialist output
    mock_coordinator_agent.run.assert_called_once()

    # Verify routed to budget specialist
    mock_ctx.send_message.assert_called_once()
    budget_call = mock_ctx.send_message.call_args
    assert budget_call[1]["target_id"] == "budget"


@pytest.mark.asyncio
async def test_synthesize_plan_simple_summary():
    """Test final synthesis creates a simple summary from conversation."""
    from agent_framework import ChatMessage, Role

    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)
    mock_ctx = AsyncMock()

    # Provide conversation history
    conversation = [
        ChatMessage(Role.USER, text="Plan event"),
        ChatMessage(Role.ASSISTANT, text="Venue specialist work: Selected The Foundry venue"),
        ChatMessage(Role.ASSISTANT, text="Budget analyst work: Allocated $5k budget"),
    ]

    await coordinator._synthesize_plan(mock_ctx, conversation)

    # Verify output yielded
    mock_ctx.yield_output.assert_called_once()
    output = mock_ctx.yield_output.call_args[0][0]
    assert "Event Planning Complete" in output


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


@pytest.mark.asyncio
async def test_on_specialist_request_sends_only_new_message():
    """Test on_specialist_request sends only new message with service-managed threads."""
    from agent_framework import AgentExecutorRequest, WorkflowContext

    from spec_to_agents.models.messages import SpecialistRequest
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create specialist request without conversation (service manages history)
    request = SpecialistRequest(
        specialist_id="budget",
        message="Please analyze budget options",
    )

    # Create coordinator and mock context
    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)
    mock_ctx = AsyncMock(spec=WorkflowContext)

    # Execute handler
    await coordinator.on_specialist_request(request, mock_ctx)

    # Verify ctx.send_message was called once
    assert mock_ctx.send_message.call_count == 1

    # Extract the sent message
    sent_message = mock_ctx.send_message.call_args[0][0]
    target_id = mock_ctx.send_message.call_args[1]["target_id"]

    # Verify target is correct specialist
    assert target_id == "budget"

    # Verify sent message is AgentExecutorRequest
    assert isinstance(sent_message, AgentExecutorRequest)
    assert sent_message.should_respond is True

    # Verify only one message (the new one) - service manages history
    messages = sent_message.messages
    assert len(messages) == 1
    assert messages[0].role == Role.USER
    assert "Please analyze budget options" in messages[0].text


@pytest.mark.asyncio
async def test_on_specialist_request_minimal_message():
    """Test on_specialist_request with minimal message only."""
    from agent_framework import AgentExecutorRequest, WorkflowContext

    from spec_to_agents.models.messages import SpecialistRequest
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create specialist request without conversation (service manages history)
    request = SpecialistRequest(
        specialist_id="venue",
        message="Please find venue options",
    )

    # Create coordinator and mock context
    # Create coordinator with mock coordinator agent
    mock_coordinator_agent = Mock()
    coordinator = EventPlanningCoordinator(mock_coordinator_agent)
    mock_ctx = AsyncMock(spec=WorkflowContext)

    # Execute handler
    await coordinator.on_specialist_request(request, mock_ctx)

    # Verify ctx.send_message was called once
    assert mock_ctx.send_message.call_count == 1

    # Extract the sent message
    sent_message = mock_ctx.send_message.call_args[0][0]
    target_id = mock_ctx.send_message.call_args[1]["target_id"]

    # Verify target is correct specialist
    assert target_id == "venue"

    # Verify sent message is AgentExecutorRequest
    assert isinstance(sent_message, AgentExecutorRequest)
    assert sent_message.should_respond is True

    # Verify only one message (the new one)
    messages = sent_message.messages
    assert len(messages) == 1
    assert messages[0].role == Role.USER
    assert "Please find venue options" in messages[0].text


@pytest.mark.asyncio
async def test_venue_to_budget_after_user_question():
    """
    Test routing from venue to budget when user asks budget-related question.

    This test covers the scenario where:
    1. Venue specialist provides venue recommendations
    2. User asks: "Can you check which of these options falls in budget?"
    3. Coordinator should recognize budget-related question and route to budget analyst

    This was a bug where coordinator received only latest message without context,
    causing it to terminate workflow instead of routing to budget.
    """
    from agent_framework import AgentRunResponse, ChatMessage, Role

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create mock coordinator agent that recognizes budget question
    mock_coordinator_agent = AsyncMock()
    mock_coordinator_response = Mock(spec=AgentRunResponse)
    mock_coordinator_response.value = SpecialistOutput(
        summary="User asked about budget for venues. Routing to budget analyst.",
        next_agent="budget",
        user_input_needed=False,
        user_prompt=None,
    )
    mock_coordinator_agent.run.return_value = mock_coordinator_response

    coordinator = EventPlanningCoordinator(mock_coordinator_agent)

    # Simulate venue specialist's full conversation including user's budget question
    venue_response = Mock()
    venue_response.executor_id = "venue"
    venue_response.full_conversation = [
        ChatMessage(Role.USER, text="Plan a corporate party for 50 people in Seattle, budget $5k"),
        ChatMessage(Role.ASSISTANT, text="I found several venues: Alley MIC ($3k), Creative Block ($2.5k), ..."),
        ChatMessage(Role.USER, text="Can you check which of these options falls in budget?"),
        ChatMessage(Role.ASSISTANT, text="To determine budget fit, I recommend consulting with the budget analyst."),
    ]
    venue_response.agent_run_response = Mock(spec=AgentRunResponse)
    venue_response.agent_run_response.text = "To determine budget fit, I recommend consulting with the budget analyst."
    venue_response.agent_run_response.messages = []

    mock_ctx = AsyncMock()

    # Execute coordinator's routing logic
    await coordinator.on_specialist_response(venue_response, mock_ctx)

    # Verify coordinator agent received FULL conversation context
    mock_coordinator_agent.run.assert_called_once()
    coordinator_call = mock_coordinator_agent.run.call_args
    messages_to_coordinator = coordinator_call[1]["messages"]

    # Verify full conversation was passed (4 original messages + 1 routing prompt)
    assert len(messages_to_coordinator) == 5, (
        "Coordinator should receive full conversation history to make context-aware routing decisions"
    )

    # Verify conversation context includes user's budget question
    user_messages = [msg for msg in messages_to_coordinator if msg.role == Role.USER]
    budget_question_present = any("budget" in msg.text.lower() for msg in user_messages)
    assert budget_question_present, "Coordinator should see user's budget-related question in context"

    # Verify routed to budget specialist (not terminated)
    mock_ctx.send_message.assert_called_once()
    budget_call = mock_ctx.send_message.call_args
    assert budget_call[1]["target_id"] == "budget", "Should route to budget analyst when user asks budget question"
