# Copyright (c) Microsoft. All rights reserved.

from agent_framework import (
    AgentExecutor,
    HostedCodeInterpreterTool,
    HostedWebSearchTool,
    Workflow,
    WorkflowBuilder,
)
from dotenv import load_dotenv

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
from spec_to_agents.workflow.executors import EventPlanningCoordinator
from spec_to_agents.workflow.messages import SpecialistOutput, SummarizedContext


async def build_event_planning_workflow() -> Workflow:
    """
    Build the multi-agent event planning workflow with human-in-the-loop capabilities.

    Architecture
    ------------
    Uses coordinator-centric star topology with 5 executors:
    - EventPlanningCoordinator: Manages routing and human-in-the-loop
    - VenueSpecialist: Venue research via Bing Search
    - BudgetAnalyst: Financial planning via Code Interpreter
    - CateringCoordinator: Food planning via Bing Search
    - LogisticsManager: Scheduling, weather, calendar management

    Workflow Pattern
    ----------------
    Star topology with bidirectional edges:
    - Coordinator ←→ Venue Specialist
    - Coordinator ←→ Budget Analyst
    - Coordinator ←→ Catering Coordinator
    - Coordinator ←→ Logistics Manager

    Human-in-the-Loop
    ------------------
    Specialists can call request_user_input tool when they need clarification,
    selection, or approval. The coordinator intercepts these tool calls and uses
    ctx.request_info() + @response_handler to pause the workflow, emit
    RequestInfoEvent, and resume with user responses via DevUI.

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution via DevUI
        or programmatic invocation.

    Notes
    -----
    The workflow uses sequential orchestration managed by the coordinator.
    Human-in-the-loop is optional: the workflow can complete autonomously
    if agents have sufficient context and choose not to request user input.

    Requires Azure AI Foundry credentials configured via environment variables
    or Azure CLI authentication.
    """
    load_dotenv()
    client = get_chat_client()

    # Get MCP tool for all agents
    mcp_tool = await get_sequential_thinking_tool()

    # Create summarizer agent for context condensation
    summarizer_agent = client.create_agent(
        name="ContextSummarizer",
        instructions=(
            "You are a context summarization specialist. Your task is to condense "
            "conversation history and specialist recommendations into a maximum of 150 words. "
            "Focus on: user requirements, decisions made, specialist recommendations, "
            "and key constraints (budget, dates, preferences). Remove unnecessary details "
            "while preserving all critical information needed for decision-making."
        ),
        response_format=SummarizedContext,
        store=True,
    )

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
        response_format=SpecialistOutput,
        store=True,
    )

    budget_agent = client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=[code_interpreter, mcp_tool, request_user_input],
        response_format=SpecialistOutput,
        store=True,
    )

    catering_agent = client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        tools=[bing_search, mcp_tool, request_user_input],
        response_format=SpecialistOutput,
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
        response_format=SpecialistOutput,
        store=True,
    )

    # Create coordinator executor with routing logic
    coordinator = EventPlanningCoordinator(coordinator_agent, summarizer_agent)

    # Create specialist executors
    venue_exec = AgentExecutor(agent=venue_agent, id="venue")
    budget_exec = AgentExecutor(agent=budget_agent, id="budget")
    catering_exec = AgentExecutor(agent=catering_agent, id="catering")
    logistics_exec = AgentExecutor(agent=logistics_agent, id="logistics")

    # Build workflow with bidirectional star topology
    workflow = (
        WorkflowBuilder(
            name="Event Planning Workflow",
            description=(
                "Multi-agent event planning workflow with venue selection, budgeting, "
                "catering, and logistics coordination. Supports human-in-the-loop for "
                "clarification and approval."
            ),
        )
        # Set coordinator as start executor
        .set_start_executor(coordinator)
        # Bidirectional edges: Coordinator ←→ Each Specialist
        .add_edge(coordinator, venue_exec)
        .add_edge(venue_exec, coordinator)
        .add_edge(coordinator, budget_exec)
        .add_edge(budget_exec, coordinator)
        .add_edge(coordinator, catering_exec)
        .add_edge(catering_exec, coordinator)
        .add_edge(coordinator, logistics_exec)
        .add_edge(logistics_exec, coordinator)
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
