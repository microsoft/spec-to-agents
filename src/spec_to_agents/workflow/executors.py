# Copyright (c) Microsoft. All rights reserved.

"""Custom executors for event planning workflow with human-in-the-loop."""

from agent_framework import (
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatAgent,
    ChatMessage,
    Executor,
    Role,
    WorkflowContext,
    handler,
    response_handler,
)

from spec_to_agents.workflow.messages import HumanFeedbackRequest, SpecialistOutput


class EventPlanningCoordinator(Executor):
    """
    Coordinates event planning workflow with intelligent routing and human-in-the-loop.

    This coordinator manages dynamic execution of specialist agents using
    structured output routing (next_agent field). It leverages service-managed
    threads for conversation history, eliminating manual state tracking.

    Architecture
    ------------
    - Star topology: Coordinator ←→ Each specialist (bidirectional edges)
    - Structured output routing: Specialists indicate next agent via response
    - Handler-based routing: Logic in executor methods, not workflow edges
    - Framework-native HITL: Uses ctx.request_info() + @response_handler
    - Service-managed threads: Framework handles conversation history automatically

    Responsibilities
    ----------------
    - Receive initial user requests and route to venue specialist
    - Use structured output (SpecialistOutput) to determine next agent
    - Detect user_input_needed and request human feedback via ctx.request_info()
    - Route human responses back to requesting specialist
    - Synthesize final event plan after all specialists complete

    Parameters
    ----------
    coordinator_agent : ChatAgent
        The agent instance for synthesis and coordination logic
    """

    def __init__(self, coordinator_agent: ChatAgent):
        super().__init__(id="event_coordinator")
        self._agent = coordinator_agent

    @handler
    async def start(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
        """
        Handle initial user request and route to venue specialist.

        Service-managed threads automatically maintain conversation context,
        so we simply route the user's request to the venue specialist.

        Parameters
        ----------
        prompt : str
            Initial user request (e.g., "Plan a corporate party for 50 people")
        ctx : WorkflowContext[AgentExecutorRequest]
            Workflow context for sending messages to specialists
        """
        # Route to venue specialist with user's initial request
        await self._route_to_agent("venue", prompt, ctx)

    @handler
    async def on_specialist_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Handle specialist response and route based on structured output.

        Uses SpecialistOutput fields to determine routing:
        - If user_input_needed=True: Pause for human input
        - Elif next_agent is set: Route to that specialist
        - Else: Synthesize final plan (workflow complete)

        Parameters
        ----------
        response : AgentExecutorResponse
            Response from specialist containing SpecialistOutput
        ctx : WorkflowContext[AgentExecutorRequest, str]
            Workflow context for routing and requesting input
        """
        # Parse structured output from specialist
        specialist_output = self._parse_specialist_output(response)

        # Route based ONLY on structured output fields
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
            # Route to next specialist (dynamic routing via structured output)
            next_context = f"Previous specialist ({response.executor_id}) completed. Continue with your analysis."
            await self._route_to_agent(specialist_output.next_agent, next_context, ctx)
        else:
            # Workflow complete: next_agent=None and no user input needed
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

        Service-managed threads automatically include the user's feedback
        in the conversation context, so we simply route back to the specialist.

        Parameters
        ----------
        original_request : HumanFeedbackRequest
            Original request containing requesting_agent ID
        feedback : str
            User's response (selection, clarification, approval)
        ctx : WorkflowContext[AgentExecutorRequest]
            Workflow context for routing
        """
        # Route back to specialist that requested input
        # Framework automatically includes user feedback in thread
        feedback_context = f"User provided: {feedback}. Please continue with your analysis."
        await self._route_to_agent(original_request.requesting_agent, feedback_context, ctx)

    async def _synthesize_plan(self, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
        """
        Synthesize final event plan from all specialist recommendations.

        This method is called after all specialists have completed their work.
        Service-managed threads provide full conversation context automatically,
        so the coordinator agent has access to all specialist outputs.

        Parameters
        ----------
        ctx : WorkflowContext[AgentExecutorRequest, str]
            Workflow context for yielding final output
        """
        # Create synthesis message (framework provides full context via thread)
        synthesis_msg = ChatMessage(
            Role.USER,
            text=(
                "Please synthesize a comprehensive event plan that integrates "
                "all specialist recommendations including venue selection, budget allocation, "
                "catering options, and logistics coordination. Provide a cohesive final plan."
            ),
        )

        # Run coordinator agent to synthesize
        synthesis_result = await self._agent.run(messages=[synthesis_msg])

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
            If response does not contain SpecialistOutput, includes actual response text for debugging
        """
        # Try to parse structured output if not already parsed
        if response.agent_run_response.value is None:
            response.agent_run_response.try_parse_value(SpecialistOutput)

        if response.agent_run_response.value and isinstance(response.agent_run_response.value, SpecialistOutput):
            return response.agent_run_response.value

        # Enhanced error message with debugging information
        response_text = response.agent_run_response.text if response.agent_run_response.text else "(empty)"
        num_messages = len(response.agent_run_response.messages) if response.agent_run_response.messages else 0
        error_msg = (
            f"Specialist '{response.executor_id}' must return SpecialistOutput.\n"
            f"Response text: '{response_text}'\n"
            f"Number of messages: {num_messages}\n"
            f"Value is None: {response.agent_run_response.value is None}"
        )
        raise ValueError(error_msg)

    async def _route_to_agent(
        self, agent_id: str, message: str, ctx: WorkflowContext[AgentExecutorRequest, str]
    ) -> None:
        """
        Route message to specialist agent.

        Service-managed threads automatically provide full conversation history
        to each agent, so we only need to send the new message.

        Parameters
        ----------
        agent_id : str
            ID of specialist to route to ("venue", "budget", "catering", "logistics")
        message : str
            New message/context for specialist
        ctx : WorkflowContext[AgentExecutorRequest]
            Workflow context for sending messages
        """
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[ChatMessage(Role.USER, text=message)],
                should_respond=True,
            ),
            target_id=agent_id,
        )


__all__ = ["EventPlanningCoordinator"]
