# Copyright (c) Microsoft. All rights reserved.

from agent_framework import (
    AgentExecutor,
    HostedCodeInterpreterTool,
    HostedWebSearchTool,
    RequestInfoExecutor,
    Workflow,
    WorkflowBuilder,
)

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.tools import (
    create_calendar_event,
    delete_calendar_event,
    get_sequential_thinking_tool,
    get_weather_forecast,
    list_calendar_events,
    request_user_input,
)
from spec_to_agents.workflow.executors import HumanInLoopAgentExecutor


async def build_event_planning_workflow() -> Workflow:
    """
    Build the multi-agent event planning workflow with human-in-the-loop capabilities.

    The workflow orchestrates five specialized agents with optional user interaction:
    - Event Coordinator: Primary orchestrator and synthesizer (MCP sequential-thinking)
    - Venue Specialist: Venue research via Bing Search (can request user input)
    - Budget Analyst: Financial planning via Code Interpreter (can request user input)
    - Catering Coordinator: Food planning via Bing Search (can request user input)
    - Logistics Manager: Scheduling, weather, calendar management (can request user input)

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

    # Get MCP tool for all agents
    mcp_tool = await get_sequential_thinking_tool()

    # Create hosted tools
    bing_search = HostedWebSearchTool(
        name="Bing Search",
        description="Search the web for current information using Bing with grounding (source citations)",
    )

    code_interpreter = HostedCodeInterpreterTool(
        description=(
            "Execute Python code for complex financial calculations, budget analysis, "
            "cost projections, and data visualization. Creates a scratchpad for "
            "intermediate calculations and maintains calculation history."
        ),
    )

    # Create coordinator agent with MCP tool for advanced reasoning
    coordinator_agent = client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        tools=[mcp_tool],
        store=True,
    )

    # Create specialist agents with domain-specific tools
    venue_agent = client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        tools=[bing_search, mcp_tool, request_user_input],
        store=True,
    )

    budget_agent = client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=[code_interpreter, mcp_tool, request_user_input],
        store=True,
    )

    catering_agent = client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        tools=[bing_search, mcp_tool, request_user_input],
        store=True,
    )

    logistics_agent = client.create_agent(
        name="LogisticsManager",
        instructions=logistics_manager.SYSTEM_PROMPT,
        tools=[
            get_weather_forecast,
            create_calendar_event,
            list_calendar_events,
            delete_calendar_event,
            mcp_tool,
            request_user_input,
        ],
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
    workflow = (
        WorkflowBuilder(
            name="Event Planning Workflow",
            description=(
                "Multi-agent event planning workflow with venue selection, budgeting, "
                "catering, and logistics coordination"
            ),
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

    # Set stable ID to prevent URL issues on restart
    workflow.id = "event-planning-workflow"
    return workflow


# Export workflow instance for DevUI discovery
# Note: Workflow is built asynchronously, so we create a placeholder
# that will be initialized when imported
workflow: Workflow | None = None


def _get_workflow() -> Workflow:
    """
    Get or build the workflow instance.

    Returns
    -------
    Workflow
        The event planning workflow instance

    Notes
    -----
    This function handles the async workflow building.
    The workflow instance is cached after first call.
    """
    import asyncio

    global workflow
    if workflow is None:
        workflow = asyncio.run(build_event_planning_workflow())
    return workflow


# Initialize workflow on module import
workflow = _get_workflow()

__all__ = ["build_event_planning_workflow", "workflow"]
