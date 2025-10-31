# Copyright (c) Microsoft. All rights reserved.

"""Event planning multi-agent workflow definition."""

from agent_framework import (
    AgentExecutor,
    HostedCodeInterpreterTool,
    MCPStdioTool,
    Workflow,
    WorkflowBuilder,
)

from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.clients import get_chat_client
from spec_to_agents.tools import (
    create_calendar_event,
    delete_calendar_event,
    get_weather_forecast,
    list_calendar_events,
    web_search,
)
from spec_to_agents.workflow.executors import EventPlanningCoordinator


def build_event_planning_workflow(
    mcp_tool: MCPStdioTool | None = None,
) -> Workflow:
    """
    Build the multi-agent event planning workflow with human-in-the-loop capabilities.

    Architecture
    ------------
    Uses coordinator-centric star topology with 5 executors:
    - EventPlanningCoordinator: Manages routing and human-in-the-loop using service-managed threads
    - VenueSpecialist: Venue research via custom web_search tool
    - BudgetAnalyst: Financial planning via Code Interpreter
    - CateringCoordinator: Food planning via custom web_search tool
    - LogisticsManager: Scheduling, weather, calendar management

    Conversation history is managed automatically by service-managed threads (store=True).
    No manual message tracking or summarization overhead.

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

    Parameters
    ----------
    mcp_tool : MCPStdioTool | None, optional
        Connected MCP tool for coordinator's sequential thinking capabilities.
        If None, coordinator operates without MCP tool assistance.
        Must be connected (within async context manager) before passing to workflow.

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
    client = get_chat_client()

    # Create hosted tools
    code_interpreter = HostedCodeInterpreterTool(
        description=(
            "Execute Python code for complex financial calculations, budget analysis, "
            "cost projections, and data visualization. Creates a scratchpad for "
            "intermediate calculations and maintains calculation history."
        ),
    )

    # Create coordinator agent with optional MCP tool for advanced reasoning
    coordinator_agent = event_coordinator.create_agent(
        client,
        mcp_tool,
    )

    # Create specialist agents with domain-specific tools
    # NOTE: MCP tool removed from specialists - it interferes with structured output (SpecialistOutput)
    # The thinking process doesn't return a final structured response, causing ValueError
    # Using custom web_search @ai_function instead of HostedWebSearchTool for better LM formatting
    venue_agent = venue_specialist.create_agent(client, web_search)

    budget_agent = budget_analyst.create_agent(
        client,
        code_interpreter,
    )

    catering_agent = catering_coordinator.create_agent(client, web_search)

    logistics_agent = logistics_manager.create_agent(
        client,
        get_weather_forecast,  # type: ignore
        create_calendar_event,  # type: ignore
        list_calendar_events,  # type: ignore
        delete_calendar_event,  # type: ignore
    )

    # Create coordinator executor with routing logic
    coordinator = EventPlanningCoordinator(coordinator_agent)

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


__all__ = ["build_event_planning_workflow"]
