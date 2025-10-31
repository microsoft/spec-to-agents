# Copyright (c) Microsoft. All rights reserved.

"""Event planning multi-agent workflow definition and lazy initialization."""

from agent_framework import (
    AgentExecutor,
    HostedCodeInterpreterTool,
    MCPStdioTool,
    Workflow,
    WorkflowBuilder,
)
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    event_synthesizer,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.tools import (
    create_calendar_event,
    delete_calendar_event,
    get_weather_forecast,
    list_calendar_events,
    web_search,
)
from spec_to_agents.utils.clients import create_agent_client

# Declare lazy-loaded attribute for type checking
workflow: Workflow

__all__ = ["build_event_planning_workflow", "workflow"]

# Private cache for lazy initialization
_workflow_cache: Workflow | None = None


def build_event_planning_workflow(
    client: AzureAIAgentClient,
    mcp_tool: MCPStdioTool | None = None,
) -> Workflow:
    """
    Build the multi-agent event planning workflow with declarative fan-out/fan-in pattern.

    Architecture
    ------------
    Uses a simple, declarative fan-out/fan-in topology with 6 executors:
    - InitialCoordinator: Receives user request and provides initial context
    - VenueSpecialist: Venue research via custom web_search tool
    - BudgetAnalyst: Financial planning via Code Interpreter
    - CateringCoordinator: Food planning via custom web_search tool
    - LogisticsManager: Scheduling, weather, calendar management
    - EventSynthesizer: Consolidates all specialist outputs into final plan

    Conversation history is managed automatically by service-managed threads (store=True).
    No manual message tracking or summarization overhead.

    Workflow Pattern
    ----------------
    Declarative fan-out/fan-in pattern:
    - InitialCoordinator → (fan-out to all specialists in parallel)
    - Venue Specialist →
    - Budget Analyst → (fan-in to synthesizer)
    - Catering Coordinator →
    - Logistics Manager →
    - EventSynthesizer → Final Plan

    This pattern is fully declarative using WorkflowBuilder edges, with no custom
    Executor classes. All routing logic is handled by agent prompts and the framework.

    Human-in-the-Loop
    ------------------
    Specialists can request user input when they need clarification, selection, or
    approval. This is handled natively by the framework through the agent's interaction
    patterns, not through custom routing logic.

    Parameters
    ----------
    client : AzureAIAgentClient
        Azure AI agent client for creating workflow agents.
        Should be managed via async context manager in calling code for automatic cleanup.
    mcp_tool : MCPStdioTool | None, optional
        Connected MCP tool for specialist sequential thinking capabilities.
        If None, specialists operate without MCP tool assistance.
        Must be connected (within async context manager) before passing to workflow.

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution via DevUI
        or programmatic invocation.

    Notes
    -----
    The workflow uses parallel execution for specialists followed by a synthesis step.
    This is more efficient than sequential routing and easier to understand.

    Requires Azure AI Foundry credentials configured via environment variables
    or Azure CLI authentication.

    The client parameter should be managed as an async context manager in the
    calling code to ensure proper cleanup of agents when the workflow is done.
    """
    # Create hosted tools
    code_interpreter = HostedCodeInterpreterTool(
        description=(
            "Execute Python code for complex financial calculations, budget analysis, "
            "cost projections, and data visualization. Creates a scratchpad for "
            "intermediate calculations and maintains calculation history."
        ),
    )

    # Create initial coordinator agent (simple AgentExecutor, no custom routing logic)
    coordinator_agent = event_coordinator.create_agent(
        client,
    )

    # Create specialist agents
    venue_agent = venue_specialist.create_agent(
        client,
        web_search,
        mcp_tool,
    )

    budget_agent = budget_analyst.create_agent(client, code_interpreter, mcp_tool)

    catering_agent = catering_coordinator.create_agent(
        client,
        web_search,
        mcp_tool,
    )

    logistics_agent = logistics_manager.create_agent(
        client,
        get_weather_forecast,  # type: ignore
        create_calendar_event,  # type: ignore
        list_calendar_events,  # type: ignore
        delete_calendar_event,  # type: ignore
        mcp_tool,
    )

    # Create synthesizer agent to consolidate all specialist outputs
    synthesizer_agent = event_synthesizer.create_agent(
        client,
    )

    # Create executors - all using simple AgentExecutor (no custom routing logic)
    coordinator_exec = AgentExecutor(agent=coordinator_agent, id="coordinator")
    venue_exec = AgentExecutor(agent=venue_agent, id="venue")
    budget_exec = AgentExecutor(agent=budget_agent, id="budget")
    catering_exec = AgentExecutor(agent=catering_agent, id="catering")
    logistics_exec = AgentExecutor(agent=logistics_agent, id="logistics")
    synthesizer_exec = AgentExecutor(agent=synthesizer_agent, id="synthesizer")

    # Build workflow with declarative fan-out/fan-in pattern
    workflow = (
        WorkflowBuilder(
            name="Event Planning Workflow",
            description=(
                "Multi-agent event planning workflow with venue selection, budgeting, "
                "catering, and logistics coordination. Uses declarative fan-out/fan-in "
                "pattern for parallel specialist execution."
            ),
            max_iterations=10,  # Simpler flow, fewer iterations needed
        )
        # Set coordinator as start executor
        .set_start_executor(coordinator_exec)
        # Fan-out: Coordinator to all specialists (parallel execution)
        .add_edge(coordinator_exec, venue_exec)
        .add_edge(coordinator_exec, budget_exec)
        .add_edge(coordinator_exec, catering_exec)
        .add_edge(coordinator_exec, logistics_exec)
        # Fan-in: All specialists to synthesizer
        .add_edge(venue_exec, synthesizer_exec)
        .add_edge(budget_exec, synthesizer_exec)
        .add_edge(catering_exec, synthesizer_exec)
        .add_edge(logistics_exec, synthesizer_exec)
        .build()
    )

    # Set stable ID to prevent URL issues on restart
    workflow.id = "event-planning-workflow"
    return workflow


def __getattr__(name: str) -> Workflow:
    """
    Lazy initialization hook for the workflow module attribute.

    This enables lazy loading of the workflow instance for DevUI integration.
    The workflow is created with a non-context-managed client, which will be
    cleaned up by DevUI's FastAPI lifespan hooks.

    Parameters
    ----------
    name : str
        The attribute name being accessed

    Returns
    -------
    Workflow
        The workflow instance

    Raises
    ------
    AttributeError
        If the attribute name is not 'workflow'

    Notes
    -----
    For programmatic usage (console.py, tests), prefer using
    build_event_planning_workflow() with an async context-managed client
    for proper cleanup. This lazy-loaded instance is intended for DevUI,
    which handles cleanup through FastAPI lifespan hooks.
    """
    if name == "workflow":
        global _workflow_cache
        if _workflow_cache is None:
            # Create client for DevUI - DevUI will handle cleanup via FastAPI lifespan
            client = create_agent_client()
            _workflow_cache = build_event_planning_workflow(client, mcp_tool=None)
        return _workflow_cache
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
