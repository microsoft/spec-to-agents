# Copyright (c) Microsoft. All rights reserved.

from agent_framework import AgentExecutor, RequestInfoExecutor, Workflow, WorkflowBuilder

from spec2agent.clients import get_chat_client
from spec2agent.prompts import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec2agent.tools.user_input import request_user_input
from spec2agent.workflow.executors import HumanInLoopAgentExecutor


def build_event_planning_workflow() -> Workflow:
    """
    Build the multi-agent event planning workflow with human-in-the-loop capabilities.

    The workflow orchestrates five specialized agents with optional user interaction:
    - Event Coordinator: Primary orchestrator and synthesizer
    - Venue Specialist: Venue research and recommendations (can request user input)
    - Budget Analyst: Financial planning and allocation (can request user input)
    - Catering Coordinator: Food and beverage planning (can request user input)
    - Logistics Manager: Scheduling and resource coordination (can request user input)

    Agents can call the request_user_input tool when they need clarification,
    selection, or approval from the user. HumanInLoopAgentExecutor wrappers
    intercept these tool calls and emit UserElicitationRequest to a shared
    RequestInfoExecutor, which pauses the workflow until the user responds via DevUI.

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution via DevUI
        or programmatic invocation.

    Notes
    -----
    The workflow uses sequential orchestration where the Event Coordinator
    delegates to each specialist in sequence, then synthesizes the final plan.

    Human-in-the-loop is optional: the workflow can complete autonomously
    if agents have sufficient context and choose not to request user input.

    Requires Azure AI Foundry credentials configured via environment variables
    or Azure CLI authentication.
    """
    client = get_chat_client()

    # Create coordinator agent (no HITL - doesn't request user input)
    coordinator_agent = client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        store=True,
    )

    # Create specialist agents WITH request_user_input tool
    venue_agent = client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    budget_agent = client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    catering_agent = client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    logistics_agent = client.create_agent(
        name="LogisticsManager",
        instructions=logistics_manager.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    # Create AgentExecutors
    coordinator_exec = AgentExecutor(agent=coordinator_agent, id="coordinator")
    venue_exec = AgentExecutor(agent=venue_agent, id="venue")
    budget_exec = AgentExecutor(agent=budget_agent, id="budget")
    catering_exec = AgentExecutor(agent=catering_agent, id="catering")
    logistics_exec = AgentExecutor(agent=logistics_agent, id="logistics")

    # Create RequestInfoExecutor for human-in-the-loop
    request_info = RequestInfoExecutor(id="user_input")

    # Create HITL wrappers for specialist agents
    venue_hitl = HumanInLoopAgentExecutor(agent_id="venue", request_info_id="user_input")
    budget_hitl = HumanInLoopAgentExecutor(agent_id="budget", request_info_id="user_input")
    catering_hitl = HumanInLoopAgentExecutor(agent_id="catering", request_info_id="user_input")
    logistics_hitl = HumanInLoopAgentExecutor(agent_id="logistics", request_info_id="user_input")

    # Build workflow with HITL integration
    return (
        WorkflowBuilder(
            name="Event Planning Workflow",
            description="Multi-agent event planning workflow",
        )
        # Set starting point
        .set_start_executor(coordinator_exec)
        # Sequential flow: Agent → HITL Wrapper → Next Agent
        .add_edge(coordinator_exec, venue_exec)
        .add_edge(venue_exec, venue_hitl)
        .add_edge(venue_hitl, budget_exec)
        .add_edge(budget_exec, budget_hitl)
        .add_edge(budget_hitl, catering_exec)
        .add_edge(catering_exec, catering_hitl)
        .add_edge(catering_hitl, logistics_exec)
        .add_edge(logistics_exec, logistics_hitl)
        .add_edge(logistics_hitl, coordinator_exec)  # Back to coordinator for synthesis
        # Bidirectional HITL edges: Wrapper ←→ RequestInfoExecutor
        .add_edge(venue_hitl, request_info)
        .add_edge(request_info, venue_hitl)
        .add_edge(budget_hitl, request_info)
        .add_edge(request_info, budget_hitl)
        .add_edge(catering_hitl, request_info)
        .add_edge(request_info, catering_hitl)
        .add_edge(logistics_hitl, request_info)
        .add_edge(request_info, logistics_hitl)
        .build()
    )


# Export workflow instance for DevUI discovery
workflow = build_event_planning_workflow()

__all__ = ["build_event_planning_workflow", "workflow"]
