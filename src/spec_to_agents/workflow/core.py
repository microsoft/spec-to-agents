# Copyright (c) Microsoft. All rights reserved.

"""Event planning multi-agent workflow definition and lazy initialization."""

from agent_framework import BaseChatClient, Workflow
from dependency_injector.wiring import Provide, inject

from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.workflow.supervisor import SupervisorWorkflowBuilder

__all__ = ["build_event_planning_workflow"]


@inject
def build_event_planning_workflow(
    client: BaseChatClient = Provide["client"],
) -> Workflow:
    """
    Build event planning workflow using supervisor pattern with DI.

    Dependencies (client, tools) are injected via DI container.
    All agent factories use @inject to receive dependencies automatically.

    Architecture
    ------------
    - Supervisor agent makes routing decisions via structured output
    - Participants use service-managed threads for local context
    - Supervisor maintains global context for informed decisions
    - Builder automatically wires bidirectional edges and creates supervisor

    Workflow Pattern
    ----------------
    Star topology with bidirectional edges:
    - Supervisor ←→ Venue Specialist
    - Supervisor ←→ Budget Analyst
    - Supervisor ←→ Catering Coordinator
    - Supervisor ←→ Logistics Manager

    Returns
    -------
    Workflow
        Configured event planning workflow ready for execution
    """
    # Create participant agents (dependencies injected automatically)
    venue_agent = venue_specialist.create_agent()
    budget_agent = budget_analyst.create_agent()
    catering_agent = catering_coordinator.create_agent()
    logistics_agent = logistics_manager.create_agent()

    # Build workflow using supervisor pattern
    # Builder automatically:
    # 1. Extracts participant descriptions from agent properties
    # 2. Creates supervisor agent with those descriptions
    # 3. Creates SupervisorOrchestratorExecutor
    # 4. Wires bidirectional edges
    return (
        SupervisorWorkflowBuilder(
            name="Event Planning Workflow",
            id="event-planning-workflow",
            description="Multi-agent event planning with supervisor orchestration",
            max_iterations=30,
            client=client,  # Required for creating supervisor agent internally
        )
        .participants(
            venue=venue_agent,
            budget=budget_agent,
            catering=catering_agent,
            logistics=logistics_agent,
        )
        .with_standard_manager(store=True)  # optional, allows passing custom ChatOptions to supervisor agent
        .build()
    )
