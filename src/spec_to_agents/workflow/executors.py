# Copyright (c) Microsoft. All rights reserved.

"""Custom executors for event planning workflow with human-in-the-loop."""

from typing import Any

from agent_framework import (
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatMessage,
    Executor,
    Role,
    WorkflowContext,
    handler,
    response_handler,
)

from spec_to_agents.workflow.messages import HumanFeedbackRequest, SpecialistOutput, SummarizedContext


class EventPlanningCoordinator(Executor):
    """
    Coordinates event planning workflow with intelligent routing and human-in-the-loop.

    This coordinator manages the dynamic execution of specialist agents using
    structured output routing (next_agent field) and chained summarization.
    It detects when specialists need user input via request_user_input tool calls
    and handles human feedback using the @response_handler pattern.

    Architecture
    ------------
    - Star topology: Coordinator ←→ Each specialist (bidirectional edges)
    - Structured output routing: Specialists indicate next agent via response format
    - Handler-based routing: Logic in executor methods, not workflow edges
    - Framework-native HITL: Uses ctx.request_info() + @response_handler
    - Chained summarization: Context condensed after each specialist

    Responsibilities
    ----------------
    - Receive initial user requests and route to first specialist
    - Use structured output to determine next agent (no hardcoded sequence)
    - Detect request_user_input tool calls in specialist responses
    - Request human feedback via ctx.request_info() when needed
    - Route human responses back to requesting specialist
    - Maintain chained summaries of specialist outputs for context
    - Synthesize final event plan after all specialists complete

    Parameters
    ----------
    coordinator_agent : Agent
        The agent instance for synthesis and coordination logic
    summarizer_agent : Agent
        The agent instance for condensing context (max 150 words)
    """

    def __init__(self, coordinator_agent: Any, summarizer_agent: Any):
        super().__init__(id="event_coordinator")
        self._agent = coordinator_agent
        self._summarizer = summarizer_agent
        self._current_summary: str = ""

    @handler
    async def start(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        """
        Handle initial user request and route to venue specialist.

        This handler is invoked when the workflow starts with a user prompt.
        It initializes the summary with the user's request and routes to the
        venue specialist by default (typical first step for event planning).

        Parameters
        ----------
        prompt : str
            Initial user request (e.g., "Plan a corporate party for 50 people")
        ctx : WorkflowContext[AgentExecutorRequest]
            Workflow context for sending messages to specialists
        """
        # Initialize summary with user request
        self._current_summary = await self._summarize_context(prompt)

        # Route to venue specialist by default
        message = ChatMessage(
            Role.USER,
            text=f"Initial request: {prompt}\n\nContext summary: {self._current_summary}",
        )
        await ctx.send_message(
            AgentExecutorRequest(messages=[message], should_respond=True),
            target_id="venue",
        )

    @handler
    async def on_specialist_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Handle specialist response and route to next agent or request user input.

        This handler processes responses from specialist agents. It:
        1. Updates conversation history with specialist's output
        2. Checks for request_user_input tool calls
        3. Either requests human input OR routes to next specialist

        Parameters
        ----------
        response : AgentExecutorResponse
            Response from a specialist agent (venue, budget, catering, or logistics)
        ctx : WorkflowContext[AgentExecutorRequest, str]
            Workflow context for routing and requesting human input
        """
        # Update conversation history with specialist's full conversation
        if response.full_conversation:
            self._conversation_history = list(response.full_conversation)

        # Check if specialist called request_user_input tool
        user_request = self._extract_tool_call(response, "request_user_input")

        if user_request:
            # Specialist needs user input - pause workflow and request feedback
            await ctx.request_info(
                request_data=HumanFeedbackRequest(
                    prompt=user_request.get("prompt", ""),
                    context=user_request.get("context", {}),
                    request_type=user_request.get("request_type", "clarification"),
                    requesting_agent=self._specialist_sequence[self._current_index],
                ),
                request_type=HumanFeedbackRequest,
                response_type=str,
            )
        else:
            # No user input needed - continue to next specialist or synthesize
            self._current_index += 1

            if self._current_index < len(self._specialist_sequence):
                # Route to next specialist in sequence
                next_agent_id = self._specialist_sequence[self._current_index]
                await ctx.send_message(
                    AgentExecutorRequest(messages=self._conversation_history, should_respond=True),
                    target_id=next_agent_id,
                )
            else:
                # All specialists completed - synthesize final plan
                await self._synthesize_plan(ctx)

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanFeedbackRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest],
    ) -> None:
        """
        Handle human feedback and route back to requesting specialist.

        This handler is invoked after a human responds to a request_info() call.
        It appends the user's feedback to conversation history and routes back
        to the specialist that requested the input.

        Parameters
        ----------
        original_request : HumanFeedbackRequest
            The original request data containing requesting_agent ID
        feedback : str
            The human's response (selection, clarification, approval)
        ctx : WorkflowContext[AgentExecutorRequest]
            Workflow context for sending messages back to specialist
        """
        # Add user feedback to conversation history
        feedback_msg = ChatMessage(Role.USER, text=f"User feedback: {feedback}")
        self._conversation_history.append(feedback_msg)

        # Route back to specialist that requested input
        await ctx.send_message(
            AgentExecutorRequest(messages=self._conversation_history, should_respond=True),
            target_id=original_request.requesting_agent,
        )

    async def _synthesize_plan(self, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
        """
        Synthesize final event plan from all specialist recommendations.

        This method is called after all specialists have completed their work.
        It uses the coordinator agent to generate an integrated event plan
        and yields it as workflow output.

        Parameters
        ----------
        ctx : WorkflowContext[AgentExecutorRequest, str]
            Workflow context for yielding final output
        """
        # Add synthesis instruction to conversation
        synthesis_msg = ChatMessage(
            Role.USER,
            text=(
                "All specialists have provided their recommendations. "
                "Please synthesize a comprehensive event plan that integrates "
                "venue selection, budget allocation, catering options, and logistics coordination."
            ),
        )
        self._conversation_history.append(synthesis_msg)

        # Run coordinator agent to synthesize
        from spec_to_agents.clients import get_chat_client

        client = get_chat_client()
        synthesis_result = await client.get_response(agent=self._agent, messages=self._conversation_history)

        # Yield final plan as workflow output
        if synthesis_result.text:
            await ctx.yield_output(synthesis_result.text)

    def _parse_specialist_output(self, response: AgentExecutorResponse) -> SpecialistOutput:
        """
        Parse SpecialistOutput from agent response.

        Parameters
        ----------
        response : AgentExecutorResponse
            Agent's response containing structured output

        Returns
        -------
        SpecialistOutput
            Parsed structured output with routing decision

        Raises
        ------
        ValueError
            If response does not contain SpecialistOutput
        """
        if response.agent_run_response.value:
            return response.agent_run_response.value
        raise ValueError("Specialist must return SpecialistOutput")

    async def _route_to_agent(self, agent_id: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        """
        Route to specialist with condensed summary context.

        Sends only the current summary (≤150 words) to the target specialist,
        not the full conversation history. This enables stateless routing.

        Parameters
        ----------
        agent_id : str
            ID of specialist agent to route to ("venue", "budget", "catering", "logistics")
        ctx : WorkflowContext[AgentExecutorRequest]
            Workflow context for sending messages
        """
        message = ChatMessage(
            Role.USER, text=f"Context summary:\n{self._current_summary}\n\nPlease proceed with your analysis."
        )
        await ctx.send_message(AgentExecutorRequest(messages=[message], should_respond=True), target_id=agent_id)

    async def _summarize_context(self, new_content: str) -> str:
        """
        Chain previous summary with new content and condense to ≤150 words.

        This method implements stateless chained summarization by combining
        the existing summary with new specialist output, then using the
        summarizer agent to condense into a maximum of 150 words.

        Parameters
        ----------
        new_content : str
            New content from specialist to incorporate into summary

        Returns
        -------
        str
            Condensed summary containing both previous and new information (≤150 words)
        """
        from spec_to_agents.clients import get_chat_client

        # Build prompt combining previous summary and new content
        if self._current_summary:
            prompt = (
                f"Previous summary:\n{self._current_summary}\n\n"
                f"New content:\n{new_content}\n\n"
                "Please condense the above into a single summary of maximum 150 words. "
                "Preserve all critical information including: user requirements, decisions made, "
                "specialist recommendations, and key constraints (budget, dates, preferences). "
                "Remove unnecessary details while maintaining everything needed for decision-making."
            )
        else:
            prompt = (
                f"Content to summarize:\n{new_content}\n\n"
                "Please condense the above into a summary of maximum 150 words. "
                "Focus on: key decisions, recommendations, and critical constraints. "
                "Remove unnecessary details while preserving essential information."
            )

        # Use summarizer agent with structured output
        client = get_chat_client()
        result = await client.get_response(
            agent=self._summarizer,
            messages=[ChatMessage(Role.USER, text=prompt)],
        )

        # Parse structured output
        result.try_parse_value(SummarizedContext)

        # Extract and return condensed summary
        if result.value and isinstance(result.value, SummarizedContext):
            return result.value.condensed_summary

        # Fallback if structured output parsing fails
        return result.text or ""


__all__ = ["EventPlanningCoordinator"]
