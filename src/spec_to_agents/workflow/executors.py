# Copyright (c) Microsoft. All rights reserved.

"""Custom executors for event planning workflow with human-in-the-loop."""

import json
from typing import Any, Mapping

from agent_framework import (
    AgentExecutorRequest,
    AgentExecutorResponse,
    AgentRunResponse,
    ChatAgent,
    ChatMessage,
    Contents,
    Executor,
    FunctionCallContent,
    FunctionResultContent,
    Role,
    TextContent,
    WorkflowContext,
    handler,
    response_handler,
)

from spec_to_agents.models.messages import HumanFeedbackRequest, SpecialistOutput, SpecialistRequest


def convert_tool_content_to_text(messages: list[ChatMessage]) -> list[ChatMessage]:
    """
    Convert tool calls and results to text summaries for cross-agent communication.

    When passing conversation history between agents with different service thread IDs,
    tool calls and results must be converted to text to avoid thread ID validation errors
    in Azure AI Agent Client. This preserves the context of what tools were used and their
    outcomes while making the messages compatible with a different agent's thread.

    Parameters
    ----------
    messages : list[ChatMessage]
        Original messages that may contain FunctionCallContent and FunctionResultContent

    Returns
    -------
    list[ChatMessage]
        New messages with tool content converted to TextContent summaries

    Notes
    -----
    This addresses the error: "No thread ID was provided, but chat messages includes tool results."
    Tool calls and results are inherently tied to the service thread where they were executed.
    When routing between agents in a workflow, each agent has its own thread ID, so we must
    convert tool-related content to plain text to avoid thread ID conflicts.
    """
    converted_messages: list[ChatMessage] = []
    for message in messages:
        new_contents: list[Contents | Mapping[str, Any]] = []
        for content in message.contents:
            if isinstance(content, FunctionCallContent):
                # Convert function call to descriptive text
                if isinstance(content.arguments, dict):
                    args_str = json.dumps(content.arguments)
                else:
                    args_str = str(content.arguments)
                text_repr = f"[Tool Call: {content.name}({args_str})]"
                new_contents.append(TextContent(text=text_repr))
            elif isinstance(content, FunctionResultContent):
                # Convert function result to descriptive text
                if content.result is not None:
                    result_str = content.result if isinstance(content.result, str) else json.dumps(content.result)
                    text_repr = f"[Tool Result for call {content.call_id}: {result_str}]"
                elif content.exception is not None:
                    text_repr = f"[Tool Error for call {content.call_id}: {content.exception}]"
                else:
                    text_repr = f"[Tool Result for call {content.call_id}: No result]"
                new_contents.append(TextContent(text=text_repr))
            else:
                # Keep other content types as-is (TextContent, ImageContent, etc.)
                new_contents.append(content)

        # Create new message with converted contents, preserving role and metadata
        converted_messages.append(
            ChatMessage(
                role=message.role,
                contents=new_contents,
                author_name=message.author_name,
                message_id=message.message_id,
            )
        )
    return converted_messages


class EventPlanningCoordinator(Executor):
    """
    Coordinates event planning workflow by using coordinator agent for routing decisions.

    This coordinator manages dynamic execution of specialist agents by:
    1. Specialists do their specialized work and return natural text
    2. Coordinator agent analyzes specialist output and returns SpecialistOutput for routing
    3. Coordinator executor extracts routing decision and sends to next specialist

    Architecture
    ------------
    - Star topology: Coordinator ←→ Each specialist (bidirectional edges)
    - Structured output routing: Coordinator agent returns SpecialistOutput
    - Handler-based routing: Logic in executor methods extracts and executes routing decisions
    - Framework-native HITL: Uses ctx.request_info() + @response_handler
    - Service-managed threads: Specialists use service threads; coordinator uses stateless calls

    Responsibilities
    ----------------
    - Receive initial user requests and route to first specialist (venue)
    - Call coordinator agent with specialist output to get routing decision
    - Extract SpecialistOutput from coordinator agent to determine next agent
    - Detect user_input_needed and request human feedback via ctx.request_info()
    - Route human responses back to requesting specialist
    - Synthesize final event plan after all specialists complete

    Parameters
    ----------
    coordinator_agent : ChatAgent
        Agent configured with response_format=SpecialistOutput and store=False
        for making routing decisions
    """

    def __init__(self, coordinator_agent: ChatAgent):
        super().__init__(id="event_coordinator")
        self._coordinator_agent = coordinator_agent

    @handler
    async def start(
        self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str]
    ) -> None:
        """
        Handle initial user request and route to first specialist.

        Sends initial request directly to venue specialist as the starting point
        for event planning workflows.

        Parameters
        ----------
        prompt : str
            Initial user request (e.g., "Plan a corporate party for 50 people")
        ctx : WorkflowContext
            Workflow context for sending messages to specialists
        """
        # Route initial request to venue specialist (typical starting point for event planning)
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[ChatMessage(Role.USER, text=prompt)],
                should_respond=True,
            ),
            target_id="venue",
        )

    @handler
    async def on_specialist_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
    ) -> None:
        """
        Handle responses from specialist agents.

        Calls coordinator agent with full conversation context to analyze
        specialist output and make routing decisions.

        The coordinator agent needs conversation context to make informed routing
        decisions. For example, if the user asks "Which venue fits the budget?",
        the coordinator needs to see both the venue recommendations AND the
        original event requirements to determine routing to the budget analyst.

        Parameters
        ----------
        response : AgentExecutorResponse
            Response from specialist agent executor with natural text output
        ctx : WorkflowContext
            Workflow context for routing and requesting input
        """
        # Get full conversation from specialist's service-managed thread
        # This provides context for coordinator's routing decision
        full_conversation = response.full_conversation or []

        # Convert tool calls/results to text for cross-thread compatibility
        converted_messages = convert_tool_content_to_text(full_conversation)

        # Add coordinator's routing analysis prompt
        messages_with_routing_prompt = [
            *converted_messages,
            ChatMessage(
                Role.USER,
                text=f"The {response.executor_id} specialist has completed their work. "
                f"Based on the full conversation above, decide the next step: "
                f"route to another specialist, request user input, or complete the workflow.",
            ),
        ]

        # Ask coordinator agent to analyze conversation and make routing decision
        coordinator_response = await self._coordinator_agent.run(messages=messages_with_routing_prompt)

        # Parse SpecialistOutput from coordinator agent's response
        specialist_output = self._parse_specialist_output(coordinator_response)

        # Route based on coordinator's routing decision
        if specialist_output.user_input_needed:
            # Pause workflow for human input
            await ctx.request_info(
                request_data=HumanFeedbackRequest(
                    prompt=specialist_output.user_prompt or "Please provide input",
                    context={},
                    request_type="clarification",
                    requesting_agent=response.executor_id,
                ),
                response_type=str,
            )
        elif specialist_output.next_agent:
            # Route to next specialist
            target_id = specialist_output.next_agent
            specialist_request = SpecialistRequest(
                specialist_id=target_id,
                message="Please analyze the event planning requirements and provide your recommendations.",
            )
            await ctx.send_message(specialist_request, target_id=target_id)
        else:
            # Workflow complete: next_agent=None and no user input needed
            # For synthesis, we could get full_conversation if needed, but for now keep it simple
            await ctx.yield_output(
                "Event Planning Complete\n\n"
                "The event planning workflow has completed with recommendations from all specialists."
            )

    @handler
    async def on_specialist_request(
        self,
        request: SpecialistRequest,
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
    ) -> None:
        """
        Handle routing requests to specialist agents.

        With service-managed threads (store=True), specialists maintain their own
        conversation history via service_thread_id. We only pass the NEW message
        for this turn, not the full conversation history.

        Parameters
        ----------
        request : SpecialistRequest
            Routing request containing specialist_id and new message
        ctx : WorkflowContext
            Workflow context for sending messages to specialists
        """
        # Only send the new message - service manages full conversation history
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[ChatMessage(Role.USER, text=request.message)],
                should_respond=True,
            ),
            target_id=request.specialist_id,
        )

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanFeedbackRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
    ) -> None:
        """
        Handle human feedback by routing back to requesting agent.

        With service-managed threads (store=True), specialists maintain their own
        conversation history. We only send the user's feedback as a NEW message,
        not the full conversation history.

        Parameters
        ----------
        original_request : HumanFeedbackRequest
            Original request containing requesting agent ID
        feedback : str
            User's response (selection, clarification, approval)
        ctx : WorkflowContext
            Workflow context for routing
        """
        # Route back to the specialist that requested the input
        # Only send the new user feedback - service manages full conversation history
        target_id = original_request.requesting_agent
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[ChatMessage(Role.USER, text=feedback)],
                should_respond=True,
            ),
            target_id=target_id,
        )

    async def _synthesize_plan(
        self,
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
        conversation: list[ChatMessage],
    ) -> None:
        """
        Synthesize final event plan from all specialist recommendations.

        This method is called after all specialists have completed their work.
        Creates a concise summary from the conversation history.

        Parameters
        ----------
        ctx : WorkflowContext
            Workflow context for yielding final output
        conversation : list[ChatMessage]
            Complete conversation history including all specialist interactions
        """
        # Extract specialist summaries from conversation
        specialist_summaries = []
        for msg in conversation:
            if msg.role == Role.ASSISTANT and msg.text:
                # Extract first 200 chars as summary
                summary = msg.text[:200] + "..." if len(msg.text) > 200 else msg.text
                specialist_summaries.append(summary)

        # Create final synthesis
        synthesis = (
            "Event Planning Complete\n\n"
            "The event planning workflow has completed with recommendations from all specialists:\n\n"
            + "\n\n".join(f"- {summary}" for summary in specialist_summaries[-4:])  # Last 4 specialists
        )

        # Yield final plan as workflow output
        await ctx.yield_output(synthesis)

    def _parse_specialist_output(self, response: AgentRunResponse) -> SpecialistOutput:
        """
        Parse SpecialistOutput from agent run response.

        Parameters
        ----------
        response : AgentRunResponse
            Agent's run response containing structured output

        Returns
        -------
        SpecialistOutput
            Parsed structured output with routing decision

        Raises
        ------
        ValueError
            If response does not contain SpecialistOutput, includes actual response text for debugging
        """
        # Try to parse structured output if not already parsed
        if response.value is None:
            response.try_parse_value(SpecialistOutput)

        if response.value and isinstance(response.value, SpecialistOutput):
            return response.value  # type: ignore[no-any-return]

        # Enhanced error message with debugging information
        response_text = response.text if response.text else "(empty)"
        num_messages = len(response.messages) if response.messages else 0

        # Analyze message contents to understand what's in the response
        content_analysis = self._analyze_message_contents(response.messages)

        error_msg = (
            f"Coordinator agent must return SpecialistOutput.\n"
            f"Response text: '{response_text}'\n"
            f"Number of messages: {num_messages}\n"
            f"Value is None: {response.value is None}\n"
            f"\nMessage content analysis:\n{content_analysis}\n"
            f"\nPossible causes:\n"
            f"- Agent made tool calls but didn't generate final structured JSON output\n"
            f"- Agent response was truncated or incomplete\n"
            f"- Agent hit token limits before generating structured output\n"
            f"- Tool execution failed, preventing agent from completing response"
        )
        raise ValueError(error_msg)

    def _analyze_message_contents(self, messages: list[ChatMessage] | None) -> str:
        """
        Analyze message contents to understand what types of content are present.

        Parameters
        ----------
        messages : list[ChatMessage] | None
            List of ChatMessage objects from AgentRunResponse

        Returns
        -------
        str
            Human-readable analysis of message contents
        """
        if not messages:
            return "  No messages in response"

        analysis_lines: list[str] = []
        for i, msg in enumerate(messages):
            if not hasattr(msg, "contents") or not msg.contents:
                analysis_lines.append(f"  Message {i}: No contents")
                continue

            content_types: list[str] = []
            for content in msg.contents:
                content_type = type(content).__name__
                content_types.append(content_type)

                # Add details for specific content types
                if hasattr(content, "name"):  # FunctionCallContent
                    content_types[-1] += f"(name={content.name})"  # type: ignore
                elif hasattr(content, "text") and content.text:  # type: ignore # TextContent
                    preview = content.text[:50] + "..." if len(content.text) > 50 else content.text  # type: ignore
                    content_types[-1] += f'(text="{preview}")'

            role = getattr(msg, "role", "unknown")
            analysis_lines.append(f"  Message {i} ({role}): {', '.join(content_types)}")

        return "\n".join(analysis_lines)
