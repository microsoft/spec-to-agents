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
from spec_to_agents.workflow.auto_handoff import AutoHandoffBuilder

__all__ = ["build_event_planning_workflow"]


@inject
def build_event_planning_workflow(
    client: BaseChatClient = Provide["client"],
) -> Workflow:
    """
    Build event planning workflow using AutoHandoffBuilder with automatic coordinator creation.

    Dependencies (client, tools) are injected via dependency injection container.
    All agent factories use @inject to receive dependencies automatically.

    Architecture
    ------------
    - Coordinator agent routes to specialists via handoff tools (auto-created from descriptions)
    - HandoffBuilder automatically synthesizes handoff tools and intercepts invocations
    - Full conversation history maintained by _HandoffCoordinator
    - User input automatically requested after each specialist response
    - Termination condition: stops after 10 user messages (default, customizable)

    Handoff Flow
    ------------
    1. User provides initial request
    2. Auto-created coordinator analyzes and decides whether to handle or hand off
    3. If handoff: Coordinator invokes handoff tool (e.g., handoff_to_venue)
    4. Specialist receives full conversation and responds
    5. Workflow automatically requests user input
    6. User provides more input, returns to step 2
    7. Repeat until termination condition met

    Returns
    -------
    Workflow
        Configured event planning workflow ready for execution

    Examples
    --------
    Running the workflow:

    >>> workflow = build_event_planning_workflow()
    >>> async for event in workflow.run_stream("Plan a party for 50 people"):
    ...     if isinstance(event, RequestInfoEvent):
    ...         # HandoffBuilder automatically requests user input
    ...         user_response = input("You: ")
    ...         await workflow.send_response(event.request_id, user_response)
    ...     elif isinstance(event, WorkflowOutputEvent):
    ...         print("Final output:", event.data)
    """
    # Create participant agents (dependencies injected automatically)
    venue_agent = venue_specialist.create_agent()
    budget_agent = budget_analyst.create_agent()
    catering_agent = catering_coordinator.create_agent()
    logistics_agent = logistics_manager.create_agent()

    # Build workflow using AutoHandoffBuilder
    # Coordinator is automatically created from participant descriptions
    # No need to include coordinator in participants list or call .set_coordinator()
    return AutoHandoffBuilder(
        name="Event Planning Workflow",
        participants=[venue_agent, budget_agent, catering_agent, logistics_agent],
        description="Multi-agent event planning with coordinator orchestration",
        client=client,  # Required for auto-coordinator creation
        coordinator_name="Event Planning Coordinator",  # Optional: customize name
    ).build()
