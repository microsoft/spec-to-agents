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
        # Initialize summary with user request (stateless chaining)
        self._current_summary = await self._chain_summarize(prev="", new=prompt)

        # Route to venue specialist by default
        await self._route_to_agent("venue", ctx)

    @handler
    async def on_specialist_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Handle specialist response and route to next agent or request user input.

        This handler processes responses from specialist agents. It:
        1. Parses structured output (SpecialistOutput)
        2. Chains summaries (stateless)
        3. Routes based on structured output fields (next_agent, user_input_needed)

        Parameters
        ----------
        response : AgentExecutorResponse
            Response from a specialist agent (venue, budget, catering, or logistics)
        ctx : WorkflowContext[AgentExecutorRequest, str]
            Workflow context for routing and requesting human input
        """
        # Parse structured output from specialist
        specialist_output = self._parse_specialist_output(response)

        # Chain summaries (stateless)
        self._current_summary = await self._chain_summarize(prev=self._current_summary, new=specialist_output.summary)

        # Route based ONLY on structured output
        if specialist_output.user_input_needed:
            # Pause workflow for human input
            await ctx.request_info(
                request_data=HumanFeedbackRequest(
                    prompt=specialist_output.user_prompt or "Please provide input",
                    context={},
                    request_type="clarification",
                    requesting_agent=response.executor_id,
                ),
                request_type=HumanFeedbackRequest,
                response_type=str,
            )
        elif specialist_output.next_agent:
            # Dynamic routing - specialist decides next agent
            await self._route_to_agent(specialist_output.next_agent, ctx)
        else:
            # next_agent=None and no user input needed = workflow complete
            await self._synthesize_plan(ctx)

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanFeedbackRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Handle human feedback and route back to requesting specialist.

        This handler is invoked after a human responds to a request_info() call.
        It chains the user's feedback into the summary and routes back
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
        # Chain user feedback into summary (stateless)
        self._current_summary = await self._chain_summarize(
            prev=self._current_summary, new=f"User feedback: {feedback}"
        )

        # Route back to specialist that requested input
        await self._route_to_agent(original_request.requesting_agent, ctx)

    async def _synthesize_plan(self, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
        """
        Synthesize final event plan from summary of all specialist recommendations.

        This method is called after all specialists have completed their work.
        It uses the coordinator agent with the condensed summary to generate
        an integrated event plan and yields it as workflow output.

        Parameters
        ----------
        ctx : WorkflowContext[AgentExecutorRequest, str]
            Workflow context for yielding final output
        """
        from spec_to_agents.clients import get_chat_client

        # Create synthesis message from summary
        synthesis_msg = ChatMessage(
            Role.USER,
            text=(
                f"Summary of specialist work:\n{self._current_summary}\n\n"
                "Please synthesize a comprehensive event plan that integrates "
                "all specialist recommendations including venue selection, budget allocation, "
                "catering options, and logistics coordination. Provide a cohesive final plan."
            ),
        )

        # Run coordinator agent to synthesize
        client = get_chat_client()
        synthesis_result = await client.get_response(agent=self._agent, messages=[synthesis_msg])

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
        if response.agent_run_response.value and isinstance(response.agent_run_response.value, SpecialistOutput):
            return response.agent_run_response.value
        raise ValueError("Specialist must return SpecialistOutput")

    async def _route_to_agent(self, agent_id: str, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
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

    async def _chain_summarize(self, prev: str, new: str) -> str:
        """
        Chain previous summary with new content and condense to ≤150 words.

        This method implements stateless chained summarization by combining
        the existing summary with new specialist output, then using the
        summarizer agent to condense into a maximum of 150 words.

        Parameters
        ----------
        prev : str
            Previous summary (empty string if first call)
        new : str
            New content from specialist or user to incorporate into summary

        Returns
        -------
        str
            Condensed summary containing both previous and new information (≤150 words)
        """
        from spec_to_agents.clients import get_chat_client

        # Build prompt combining previous summary and new content
        if prev:
            prompt = (
                f"Previous summary:\n{prev}\n\n"
                f"New content:\n{new}\n\n"
                "Please condense the above into a single summary of maximum 150 words. "
                "Preserve all critical information including: user requirements, decisions made, "
                "specialist recommendations, and key constraints (budget, dates, preferences). "
                "Remove unnecessary details while maintaining everything needed for decision-making."
            )
        else:
            prompt = (
                f"Content to summarize:\n{new}\n\n"
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
        condensed_summary: str
        if result.value and isinstance(result.value, SummarizedContext):
            condensed_summary = result.value.condensed_summary
        else:
            # Fallback if structured output parsing fails
            condensed_summary = result.text or ""

        return condensed_summary


__all__ = ["EventPlanningCoordinator"]
