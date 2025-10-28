# Copyright (c) Microsoft. All rights reserved.

from agent_framework import Workflow, WorkflowBuilder

from spec2agent.clients import get_chat_client
from spec2agent.prompts import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)


def build_event_planning_workflow() -> Workflow:
    """
    Build the multi-agent event planning workflow.

    The workflow orchestrates five specialized agents:
    - Event Coordinator: Primary orchestrator and synthesizer
    - Venue Specialist: Venue research and recommendations
    - Budget Analyst: Financial planning and allocation
    - Catering Coordinator: Food and beverage planning
    - Logistics Manager: Scheduling and resource coordination

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution via DevUI
        or programmatic invocation.

    Notes
    -----
    Agent Handoff Mechanism:
    The workflow uses WorkflowBuilder with add_edge() for automatic agent handoff.
    Each edge triggers the following sequence:

    1. Source agent completes and produces AgentExecutorResponse with:
       - agent_run_response: Agent's output messages
       - full_conversation: Complete conversation history (all prior + new messages)

    2. Target agent's from_response() handler automatically:
       - Receives the AgentExecutorResponse
       - Loads full_conversation into message cache
       - Runs with complete context from workflow start

    3. Context accumulates naturally through the workflow:
       User → Coordinator → [User, Coordinator] → Venue → [User, Coord, Venue] → ...

    This ensures each specialist sees the full conversation context without manual
    message passing or state management.

    User Handoff Capability:
    Agent prompts have been updated with guidelines for when and how to request user
    input. While the current workflow implementation (Phase 1) doesn't include
    programmatic user handoff via RequestInfoExecutor, the foundation is in place:

    - Custom RequestInfoMessage types are defined in workflow.messages
    - Agent prompts instruct when clarification would be valuable
    - Agents can communicate need for user input in their responses

    Phase 2 enhancement would add custom executors that programmatically detect
    when user input is needed and route through RequestInfoExecutor.

    Workflow Flow:
    User Input → EventCoordinator (initial) → VenueSpecialist → BudgetAnalyst →
    CateringCoordinator → LogisticsManager → EventCoordinator (synthesis) → Output

    Requires Azure AI Foundry credentials configured via environment variables
    or Azure CLI authentication.
    """
    client = get_chat_client()

    # Create all five agents with their specialized system prompts
    # Note: Agent names must be unique within the workflow for proper routing
    coordinator = client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        store=True,
    )

    venue = client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        store=True,
    )

    budget = client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        store=True,
    )

    catering = client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        store=True,
    )

    logistics = client.create_agent(
        name="LogisticsManager",
        instructions=logistics_manager.SYSTEM_PROMPT,
        store=True,
    )

    # Build the workflow with sequential orchestration pattern
    # Each add_edge() creates automatic handoff via full_conversation field
    return (
        WorkflowBuilder()
        .set_start_executor(coordinator)
        # Coordinator delegates to venue specialist
        .add_edge(coordinator, venue)
        # Venue hands off to budget analyst (with venue recommendations in context)
        .add_edge(venue, budget)
        # Budget hands off to catering (with venue + budget in context)
        .add_edge(budget, catering)
        # Catering hands off to logistics (with venue + budget + catering in context)
        .add_edge(catering, logistics)
        # Logistics hands back to coordinator for final synthesis (with all specialist outputs)
        .add_edge(logistics, coordinator)
        .build()
    )


# Export workflow instance for DevUI discovery
workflow = build_event_planning_workflow()

__all__ = ["build_event_planning_workflow", "workflow"]
