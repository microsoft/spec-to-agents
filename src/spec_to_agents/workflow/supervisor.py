# Copyright (c) Microsoft. All rights reserved.

"""Supervisor pattern workflow components for dynamic agent orchestration."""

import warnings

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    BaseChatClient,
    ChatAgent,
    ChatMessage,
    Executor,
    Role,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    response_handler,
)
from agent_framework._workflows._const import DEFAULT_MAX_ITERATIONS

from spec_to_agents.models.messages import HumanFeedbackRequest, SupervisorDecision
from spec_to_agents.workflow.utils import convert_messages_to_text


class SupervisorOrchestratorExecutor(Executor):
    """
    Lightweight orchestrator that delegates routing decisions to supervisor agent.

    This executor runs the supervisor agent and follows its structured output decisions
    for dynamic routing between participants.

    Architecture
    ------------
    - Supervisor maintains global conversation context
    - Participants use service-managed threads for local context
    - Routing decisions made by supervisor agent via SupervisorDecision structured output
    - Supports human-in-the-loop via user_input_needed flag

    Parameters
    ----------
    supervisor_agent : ChatAgent
        Agent with SupervisorDecision structured output that makes routing decisions
    participant_ids : list[str]
        List of valid participant IDs that supervisor can route to
    """

    def __init__(
        self,
        supervisor_agent: ChatAgent,
        participant_ids: list[str],
    ) -> None:
        """Initialize supervisor orchestrator with agent and participant IDs."""
        super().__init__(id="supervisor")
        self._supervisor_agent = supervisor_agent
        self._participant_ids = participant_ids
        self._conversation_history: list[ChatMessage] = []

    @handler
    async def start(
        self,
        prompt: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Start workflow with user request.

        Adds user request to global context and gets routing decision from supervisor.

        Parameters
        ----------
        prompt : str
            Initial user request for the workflow
        ctx : WorkflowContext
            Workflow context for routing and state management
        """
        # Add user request to global context
        user_message = ChatMessage(role=Role.USER, text=prompt)
        self._conversation_history.append(user_message)

        # Get routing decision from supervisor
        await self._get_supervisor_decision_and_route(ctx)

    @handler
    async def on_participant_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Handle participant response and route to next participant.

        Adds participant response to global context and gets next routing decision.

        Parameters
        ----------
        response : AgentExecutorResponse
            Response from participant agent
        ctx : WorkflowContext
            Workflow context for routing and state management
        """
        # Add participant response to global context
        # Extract messages from agent_run_response
        messages = response.agent_run_response.messages
        if messages:
            # Convert tool content to text for cross-thread compatibility
            converted_messages = convert_messages_to_text(messages)
            self._conversation_history.extend(converted_messages)

        # Get next routing decision from supervisor
        await self._get_supervisor_decision_and_route(ctx)

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanFeedbackRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Handle human feedback and continue workflow.

        Adds user feedback to global context and resumes routing.

        Parameters
        ----------
        original_request : HumanFeedbackRequest
            Original request that triggered human input
        feedback : str
            User's response to the request
        ctx : WorkflowContext
            Workflow context for routing and state management
        """
        # Add user feedback to global context
        feedback_message = ChatMessage(role=Role.USER, text=feedback)
        self._conversation_history.append(feedback_message)

        # Continue routing after human input
        await self._get_supervisor_decision_and_route(ctx)

    async def _get_supervisor_decision_and_route(
        self,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Run supervisor agent and execute routing decision.

        Parameters
        ----------
        ctx : WorkflowContext
            Workflow context for routing and state management
        """
        # Run supervisor with global context
        response = await self._supervisor_agent.run(messages=self._conversation_history)

        # Add supervisor response to global context
        if response.messages:
            self._conversation_history.extend(response.messages)

        response.try_parse_value(SupervisorDecision)

        # Extract decision from structured output
        if response.value is None:
            raise ValueError("Supervisor agent did not return SupervisorDecision structured output")

        decision: SupervisorDecision = response.value  # type: ignore

        # Handle decision
        if decision.user_input_needed:
            # Request human input
            await ctx.request_info(
                request_data=HumanFeedbackRequest(
                    prompt=decision.user_prompt or "Please provide additional information.",
                    context={},
                    request_type="clarification",
                    requesting_agent="supervisor",
                    conversation=list(self._conversation_history),
                ),
                response_type=str,
            )
        elif decision.next_agent is not None:
            # Route to next participant
            await self._route_to_participant(decision.next_agent, ctx)
        else:
            # Workflow complete - synthesize final result
            await self._synthesize_plan(ctx)

    async def _route_to_participant(
        self,
        participant_id: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Route to specified participant with focused context.

        Parameters
        ----------
        participant_id : str
            ID of participant to route to
        ctx : WorkflowContext
            Workflow context for sending messages
        """
        if participant_id not in self._participant_ids:
            raise ValueError(
                f"Supervisor requested invalid participant '{participant_id}'. "
                f"Valid participants: {self._participant_ids}"
            )

        # Extract most recent user request from conversation
        user_messages = [msg for msg in self._conversation_history if msg.role == Role.USER]
        latest_user_request = user_messages[-1].text if user_messages else "Continue working on the task."

        # Create focused request for participant
        # Participant sees: user request + instruction to contribute their expertise
        request_message = (
            f"{latest_user_request}\n\n"
            f"Please provide your expertise for this request. "
            f"Focus on your domain and provide actionable recommendations."
        )

        # Build conversation with routing message
        conversation = [ChatMessage(role=Role.USER, text=request_message)]

        # Route to participant
        await ctx.send_message(
            AgentExecutorRequest(
                messages=conversation,
                should_respond=True,
            ),
            participant_id,
        )

    async def _synthesize_plan(
        self,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Synthesize final comprehensive plan from conversation history.

        Parameters
        ----------
        ctx : WorkflowContext
            Workflow context for yielding final output
        """
        # Create synthesis prompt
        synthesis_prompt = (
            "Based on the entire conversation, synthesize a comprehensive event plan. "
            "Include all recommendations from participants and present them in a clear, "
            "organized format. The plan should be actionable and complete."
        )

        synthesis_message = ChatMessage(role=Role.USER, text=synthesis_prompt)
        synthesis_context = [*self._conversation_history, synthesis_message]

        # Run supervisor to generate final synthesis
        response = await self._supervisor_agent.run(messages=synthesis_context)

        # Extract final plan text
        final_plan = response.text or "Event planning complete."

        # Yield final output
        await ctx.yield_output(final_plan)


class SupervisorWorkflowBuilder:
    """
    Fluent builder for creating supervisor-based workflows.

    This builder provides a clean API for constructing workflows where a supervisor
    agent makes dynamic routing decisions. The builder automatically:
    1. Extracts participant descriptions from agent properties
    2. Creates supervisor agent with those descriptions
    3. Creates SupervisorOrchestratorExecutor
    4. Wires bidirectional edges in star topology

    Parameters
    ----------
    name : str
        Name of the workflow
    id : str, optional
        Unique identifier for the workflow
    description : str, optional
        Description of the workflow's purpose
    max_iterations : int
        Maximum number of workflow iterations (default: DEFAULT_MAX_ITERATIONS)
    client : BaseChatClient, optional
        Chat client for creating supervisor agent (required for build())

    Examples
    --------
    >>> workflow = (
    ...     SupervisorWorkflowBuilder(
    ...         name="Event Planning Workflow",
    ...         id="event-planning-workflow",
    ...         max_iterations=DEFAULT_MAX_ITERATIONS,
    ...         client=client,
    ...     )
    ...     .participants(
    ...         venue=venue_agent,
    ...         budget=budget_agent,
    ...         catering=catering_agent,
    ...     )
    ...     .build()
    ... )
    """

    def __init__(
        self,
        name: str,
        client: BaseChatClient,
        id: str | None = None,
        description: str | None = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        """Initialize supervisor workflow builder."""
        self.name = name
        self.id = id
        self.description = description
        self.max_iterations = max_iterations
        self._client = client
        self._participants: dict[str, ChatAgent] = {}

    def participants(self, **participants: ChatAgent) -> "SupervisorWorkflowBuilder":
        """
        Add participant agents to the workflow.

        Participants are specified as keyword arguments where keys are participant IDs
        and values are ChatAgent instances.

        Parameters
        ----------
        **participants : ChatAgent
            Participant agents keyed by their IDs

        Returns
        -------
        SupervisorWorkflowBuilder
            Self for method chaining

        Examples
        --------
        >>> builder.participants(venue=venue_agent, budget=budget_agent)
        """
        self._participants.update(participants)
        return self

    def build(self) -> Workflow:
        """
        Build the workflow with supervisor orchestration.

        This method:
        1. Validates that client was provided
        2. Extracts participant descriptions from agent properties
        3. Creates supervisor agent with those descriptions
        4. Creates SupervisorOrchestratorExecutor
        5. Wraps participants in AgentExecutor instances
        6. Wires bidirectional edges in star topology

        Returns
        -------
        Workflow
            Configured workflow ready for execution

        Raises
        ------
        ValueError
            If client was not provided or no participants were added
        """
        if not self._participants:
            raise ValueError("At least one participant must be added via .participants()")

        # Import here to avoid circular dependency
        from spec_to_agents.agents.supervisor import create_supervisor_agent

        # Extract participant descriptions for supervisor agent
        participant_descriptions: list[str] = []
        for agent_id, agent in self._participants.items():
            # Get name from agent.name or fallback to agent_id
            name = getattr(agent, "name", None) or agent_id

            # Get description from agent.description or first line of instructions
            description = getattr(agent, "description", None)
            if description is None and hasattr(agent, "chat_options") and agent.chat_options.instructions:
                # Fallback: use first line of instructions
                warnings.warn(
                    f"Agent description for {agent_id} missing; using first line of instructions as fallback. "
                    "For best results, provide a description attribute for your agent",
                    stacklevel=1,
                )
                description = agent.chat_options.instructions.split("\n")[0]
            else:
                description = f"Agent responsible for {agent_id}"

            participant_descriptions.append(f"- **{agent_id}** ({name}): {description}")

        participants_description = "Available participants:\n\n" + "\n".join(participant_descriptions)

        # Create supervisor agent
        supervisor_agent = create_supervisor_agent(
            client=self._client,
            participants_description=participants_description,
            supervisor_name=self.name + " Supervisor",
        )

        # Create SupervisorOrchestratorExecutor
        supervisor_exec = SupervisorOrchestratorExecutor(
            supervisor_agent=supervisor_agent,
            participant_ids=list(self._participants.keys()),
        )

        # Wrap participants in AgentExecutor instances
        participant_execs = {
            agent_id: AgentExecutor(agent=agent, id=agent_id) for agent_id, agent in self._participants.items()
        }

        # Wire graph with bidirectional edges
        builder = WorkflowBuilder(
            name=self.name,
            description=self.description,
            max_iterations=self.max_iterations,
        ).set_start_executor(supervisor_exec)

        # Add bidirectional edges for each participant
        for participant_exec in participant_execs.values():
            builder.add_edge(supervisor_exec, participant_exec)
            builder.add_edge(participant_exec, supervisor_exec)

        workflow = builder.build()

        if self.id:
            workflow.id = self.id

        return workflow


__all__ = ["SupervisorOrchestratorExecutor", "SupervisorWorkflowBuilder"]
