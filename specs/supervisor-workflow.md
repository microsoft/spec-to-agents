# Supervisor Workflow

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `specs/PLANS.md` (from repository root).

## Purpose / Big Picture

Transform the event planning workflow from a coordinator-centric star topology with hardcoded routing logic into a lightweight supervisor pattern where a supervisor agent makes dynamic routing decisions via structured output. This change enables flexible participant topologies without modifying orchestrator code.

After implementation, developers can create supervisor-based workflows using a fluent builder API that automatically wires bidirectional edges between supervisor and participants. The supervisor agent dynamically determines which participant to call next based on conversation context, not hardcoded logic.

## Progress

- [ ] Add dependency-injector library to pyproject.toml dependencies
- [ ] Create DI container in src/spec_to_agents/container.py
- [ ] Create SupervisorDecision structured output model in src/spec_to_agents/models/messages.py
- [ ] Create SupervisorOrchestratorExecutor in src/spec_to_agents/workflow/supervisor.py
- [ ] Create SupervisorWorkflowBuilder in src/spec_to_agents/workflow/supervisor.py (generic, not event-planning specific)
- [ ] Create generic supervisor agent factory in src/spec_to_agents/agents/supervisor.py
- [ ] Refactor ALL agent factory functions to use @inject decorator for DI
- [ ] Refactor build_event_planning_workflow to use supervisor pattern and DI
- [ ] Update console.py to initialize DI container
- [ ] Write unit tests for SupervisorDecision model
- [ ] Write unit tests for SupervisorOrchestratorExecutor (mocked supervisor agent)
- [ ] Write unit tests for SupervisorWorkflowBuilder (topology validation)
- [ ] Write integration tests using workflow.run_stream() pattern (console.py style)
- [ ] Update specs/README.md with supervisor pattern documentation
- [ ] Validate workflow E2E via console.py

## Surprises & Discoveries

(To be filled during implementation)

## Decision Log

- **Decision**: Use Approach 1 (Full Magentic-Style with Manager Agent) over Approach 2 (Specialist-Driven Routing)
  **Rationale**: User requirement that "the executor should only be constrained to the structured output to choose the proper executor agent to route to" and need for supervisor to "freely define the participants" necessitates supervisor agent making routing decisions, not specialists distributing routing logic across agents.
  **Date/Author**: 2025-11-01 / Claude during brainstorming

- **Decision**: Make `next_agent` nullable (`str | None`) in SupervisorDecision
  **Rationale**: Workflow completion signal is `next_agent=None AND user_input_needed=False`. User clarified this design during Phase 1.
  **Date/Author**: 2025-11-01 / Claude with user clarification

- **Decision**: Skip auto-compaction feature for initial implementation
  **Rationale**: Keep implementation lightweight and simple. Service-managed threads handle participant context automatically. Supervisor's global context compaction can be added later if needed.
  **Date/Author**: 2025-11-01 / User decision

- **Decision**: Supervisor maintains global context, participants maintain local context
  **Rationale**: Supervisor needs full conversation history for informed routing decisions. Participants use service-managed threads (`store=True`) which automatically maintain their local conversation history, preventing token bloat and keeping participants focused on their domain.
  **Date/Author**: 2025-11-01 / User requirement

- **Decision**: Remove `summary` field from SupervisorDecision
  **Rationale**: Supervisor routes, it doesn't summarize. Summary field is not needed for routing decisions.
  **Date/Author**: 2025-11-01 / Design refinement

- **Decision**: Make supervisor abstractions generic (not event-planning specific)
  **Rationale**: The supervisor pattern should be reusable for any multi-agent workflow, not just event planning. Supervisor agent factory takes parameterized descriptions of participants.
  **Date/Author**: 2025-11-01 / User requirement

- **Decision**: Use dependency injection with dependency-injector library
  **Rationale**: Agent factory functions should not take client/tools as parameters. Use @inject decorator with Provide[] pattern. Tools initialized inside factory functions. Simplifies workflow building and enables better testing.
  **Date/Author**: 2025-11-01 / User requirement

- **Decision**: E2E testing via console.py pattern, not DevUI
  **Rationale**: Integration tests should use workflow.run_stream() and send_responses_streaming() (console.py pattern) for E2E validation. DevUI testing is secondary.
  **Date/Author**: 2025-11-01 / User requirement

## Outcomes & Retrospective

(To be filled at completion)

## Context and Orientation

This project uses **Microsoft Agent Framework** (Python) to build multi-agent workflows for event planning. The current architecture uses `EventPlanningCoordinator` (defined in `src/spec_to_agents/workflow/executors.py:89-409`) which manually handles routing via methods like `_route_to_agent()` and `on_specialist_response()`.

The workflow topology is defined in `src/spec_to_agents/workflow/core.py:111-137` with explicit bidirectional edge declarations between coordinator and each specialist (venue, budget, catering, logistics).

Current patterns:
- **Service-managed threads** (`store=True`): Azure AI service automatically manages conversation history for each agent
- **Tool content conversion**: `convert_tool_content_to_text()` helper converts tool calls/results to text for cross-thread communication
- **HITL pattern**: `ctx.request_info()` + `@response_handler` for human-in-the-loop interactions
- **Structured output**: `SpecialistOutput` Pydantic model with `next_agent`, `user_input_needed`, `user_prompt` fields

The supervisor pattern refactors this architecture to:
1. Move routing intelligence from coordinator code to a supervisor agent (LLM with structured output)
2. Provide fluent builder API (`SupervisorWorkflowBuilder`) that auto-wires topology
3. Create lightweight `SupervisorOrchestratorExecutor` that delegates decisions to supervisor agent
4. Enable arbitrary participant topologies without changing orchestrator code

Reference implementation: **MagenticWorkflowBuilder** and **MagenticOrchestratorExecutor** from microsoft/agent-framework (consulted via DeepWiki during design phase).

## Plan of Work

### 0. Setup Dependency Injection

This section sets up the dependency injection (DI) infrastructure that will eliminate manual client/tool passing. The DI container provides:
1. **Client provider**: Singleton Azure AI agent client with automatic cleanup
2. **Global tools provider**: Singleton dictionary of globally shared tools (MCP tools)

**Tool architecture**:
- **Global tools** (DI-managed): Dictionary `dict[str, ToolProtocol]` containing MCP tools that any agent can selectively use by key
  - `"sequential-thinking"`: MCP sequential thinking tool for complex reasoning
  - Agents pick which global tools they need: `global_tools["sequential-thinking"]`
  - **No explicit async context managers needed**: Agent framework automatically connects MCP tools when agents are created
- **Agent-specific tools** (local): Web search, code interpreter, weather, calendar tools remain initialized inside each agent's `create_agent()` factory function for better encapsulation

The dictionary approach allows agents to selectively add only the global tools they need, avoiding unnecessary tool injection. MCP tool connection lifecycle is automatically managed by the agent framework.

**File**: `pyproject.toml`

Add dependency-injector library to dependencies:

```bash
uv add dependency-injector
```

**File**: `src/spec_to_agents/tools/mcp_tools.py`

The existing `create_global_tools` factory already exists and returns a `dict[str, ToolProtocol]` containing MCP tools. This factory will be used as-is by the DI container. No changes needed to this file.

Current implementation:

    """MCP (Model Context Protocol) tools integration."""

    from agent_framework import MCPStdioTool, ToolProtocol


    def create_global_tools() -> dict[str, ToolProtocol]:
        """
        Create a global toolset including MCP tools.

        Returns a dict containing ToolProtocol that interface with the
        async context manager pattern for proper lifecycle management.

        Returns
        -------
        dict[str, ToolProtocol]
            Unconnected MCP tools for advanced reasoning and tool orchestration
            Keys:
            - "sequential-thinking": MCP sequential thinking tool for complex reasoning

        Example
        -------
        >>> global_tools = create_global_tools()
        >>> # Tools are automatically connected by agent framework when passed to agents
        >>> agent = client.create_agent(
        ...     name="MyAgent",
        ...     tools=[global_tools["sequential-thinking"]],
        ...     ...
        ... )

        Notes
        -----
        The MCP tools are automatically connected by the agent framework when
        agents are created or when agent.run() is called. You do NOT need to
        manually open them with async context managers. The framework handles
        the connection lifecycle internally.
        """
        return {
            "sequential-thinking": MCPStdioTool(
                name="sequential-thinking",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
            )
        }


    __all__ = ["create_global_tools"]

**Note**: The existing implementation is correct. The DI container will provide this dict to all agent factories via dependency injection. MCP tools are automatically connected by the agent framework when agents are created - no explicit async context managers needed.

**File**: `src/spec_to_agents/container.py` (new file)

Create DI container for managing client and tool dependencies:

    """Dependency injection container for application-wide dependencies."""

    from dependency_injector import containers, providers
    from agent_framework import ToolProtocol

    from spec_to_agents.utils.clients import create_agent_client
    from spec_to_agents.tools.mcp_tools import create_global_tools


    class AppContainer(containers.DeclarativeContainer):
        """
        Application-wide dependency injection container.

        Manages lifecycle and injection of:
        - Azure AI agent client (singleton)
        - Global tools dictionary (MCP tools, singleton)

        The tools provider returns a dict[str, ToolProtocol] containing globally
        shared tools (currently just MCP sequential-thinking tool). Agent-specific
        tools (web search, code interpreter, weather, calendar) are initialized
        inside each agent's create_agent() factory function, not via DI injection.

        Agent factories can selectively access global tools by key:
            global_tools["sequential-thinking"]

        Usage in console.py:
            container = AppContainer()
            container.wire(modules=[...])
            async with container.client() as client:
                # Dependencies injected into agent factories
                # MCP tools are automatically connected by agent framework when agents are created
                workflow = build_event_planning_workflow()
        """

        # Configuration
        config = providers.Configuration()

        # Client provider (singleton factory)
        client = providers.Singleton(
            create_agent_client,
        )

        # Global tools provider (singleton)
        # Returns: dict[str, ToolProtocol]
        # The dict is created once and injected into all agent factories
        global_tools = providers.Singleton(
            create_global_tools,
        )

        # Wiring configuration: modules that use @inject
        wiring_config = containers.WiringConfiguration(
            modules=[
                "spec_to_agents.agents.budget_analyst",
                "spec_to_agents.agents.catering_coordinator",
                "spec_to_agents.agents.event_coordinator",
                "spec_to_agents.agents.logistics_manager",
                "spec_to_agents.agents.venue_specialist",
                "spec_to_agents.agents.supervisor",
                "spec_to_agents.workflow.core",
            ]
        )

This container is initialized in `console.py` before building the workflow, enabling all agent factory functions to use injected dependencies via `@inject` decorator.

### 1. Create SupervisorDecision Model

**File**: `src/spec_to_agents/models/messages.py`

Add new Pydantic model after the existing `SpecialistOutput` class:

    class SupervisorDecision(BaseModel):
        """
        Structured output from supervisor agent for routing decisions.

        The supervisor evaluates conversation history and decides which
        participant to route to next, whether to request user input,
        or whether the workflow is complete.

        Workflow completion occurs when next_agent=None AND user_input_needed=False.
        """

        next_agent: str | None = Field(
            description=(
                "ID of next participant to route to"
                "or None if workflow is complete and ready for final synthesis"
            )
        )
        user_input_needed: bool = Field(
            default=False,
            description="Whether user input is required before continuing"
        )
        user_prompt: str | None = Field(
            default=None,
            description="Question to ask user if user_input_needed=True"
        )

Update `__all__` export at bottom of file to include `SupervisorDecision`.

### 2. Create Supervisor Module

**File**: `src/spec_to_agents/workflow/supervisor.py` (new file)

Create new module containing:
- `SupervisorOrchestratorExecutor` class (full implementation in Phase 3 design section above)
- `SupervisorWorkflowBuilder` class (full implementation in Phase 3 design section above)
- Module exports: `__all__ = ["SupervisorOrchestratorExecutor", "SupervisorWorkflowBuilder"]`

Import required dependencies at top of file:

    from agent_framework import (
        AgentExecutor,
        AgentExecutorRequest,
        AgentExecutorResponse,
        AgentRunResponse,
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

    from spec_to_agents.models.messages import HumanFeedbackRequest, SupervisorDecision
    from spec_to_agents.workflow.executors import convert_tool_content_to_text
    from spec_to_agents.agents.supervisor import create_supervisor_agent

Key implementation details:

**SupervisorOrchestratorExecutor** (internal class, created by builder):
- `__init__`: Takes `supervisor_agent` and `participant_ids` list
- `_conversation_history`: List of ChatMessage for global context
- `_get_supervisor_decision_and_route`: Core routing logic, runs supervisor agent and executes decision
- `_route_to_participant`: Sends focused request to participant (user request + instruction)
- `_synthesize_plan`: Supervisor synthesizes final plan from global context

**SupervisorWorkflowBuilder** (public API):
- `__init__`: Takes `name`, `id`, `description`, `max_iterations`, `client` parameters
- `.participants(**kwargs)`: Accepts kwargs of `ChatAgent` instances keyed by participant ID
- `.build()`: Returns `Workflow` by performing these steps internally:
  1. Extracting participant descriptions from agent properties (agent.name, agent.description, or instructions)
  2. Creating supervisor agent via `create_supervisor_agent(client, participants_description)`
  3. Creating `SupervisorOrchestratorExecutor` with supervisor agent and participant IDs
  4. Wrapping participant agents in `AgentExecutor` instances with their IDs
  5. Using `WorkflowBuilder` to wire the graph with bidirectional star topology

**Internal implementation of `.build()` method** (pseudocode showing what happens inside):

```python
def build(self) -> Workflow:
    """Build workflow - this is the INTERNAL implementation."""
    # 1. Extract participant descriptions
    participant_descriptions = []
    for agent_id, agent in self._participants.items():
        name = agent.name or agent_id
        desc = agent.description or agent.chat_options.instructions.split('\n')[0]
        participant_descriptions.append(f"- **{agent_id}** ({name}): {desc}")

    participants_description = "Available participants:\n\n" + "\n".join(participant_descriptions)

    # 2. Create supervisor agent
    supervisor_agent = create_supervisor_agent(
        client=self._client,
        participants_description=participants_description,
        supervisor_name=self.name + " Supervisor",
    )

    # 3. Create SupervisorOrchestratorExecutor
    supervisor_exec = SupervisorOrchestratorExecutor(
        supervisor_agent=supervisor_agent,
        participant_ids=list(self._participants.keys()),
    )

    # 4. Wrap participants in AgentExecutor instances
    participant_execs = {
        agent_id: AgentExecutor(agent=agent, id=agent_id)
        for agent_id, agent in self._participants.items()
    }

    # 5. Wire graph with bidirectional edges
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
```

**Users never write this code** - it's all handled automatically by calling `.build()`.

### 3. Create Generic Supervisor Agent Factory

**File**: `src/spec_to_agents/agents/supervisor.py` (new file)

Create **generic** supervisor agent factory (not event-planning specific):

    """Generic supervisor agent factory for multi-agent workflows."""

    from typing import Any

    from agent_framework import ChatAgent, BaseChatClient

    from spec_to_agents.models.messages import SupervisorDecision

    __all__ = ["create_supervisor_agent"]


    def create_supervisor_agent(
        client: BaseChatClient,
        participants_description: str,
        supervisor_name: str = "Supervisor",
        **kwargs: Any,
    ) -> ChatAgent:
        """
        Create generic supervisor agent for multi-agent workflow orchestration.

        IMPORTANT: This factory is GENERIC and reusable for any multi-agent workflow.
        It is NOT specific to event planning.

        This function is typically called internally by SupervisorWorkflowBuilder,
        which automatically extracts participant descriptions from agent properties.

        Parameters
        ----------
        client : BaseChatClient
            Chat client for creating the agent (injected by SupervisorWorkflowBuilder)
        participants_description : str
            Description block listing all available participants with their IDs and roles.
            This is automatically generated by SupervisorWorkflowBuilder from agent properties.
            Format:
            "Available participants:

            - **participant_id_1** (ParticipantName): Description of participant 1's role
            - **participant_id_2** (ParticipantName): Description of participant 2's role
            ..."
        supervisor_name : str
            Name for the supervisor agent (default: "Supervisor")
        **kwargs : Any
            Additional keyword arguments for client.create_agent()

        Returns
        -------
        ChatAgent
            Supervisor agent with SupervisorDecision structured output

        Examples
        --------
        Typically called by SupervisorWorkflowBuilder:
        >>> # Builder automatically extracts participant descriptions
        >>> supervisor_agent = create_supervisor_agent(
        ...     client=client,
        ...     participants_description=builder._extract_descriptions(),
        ...     supervisor_name="Event Planning Supervisor",
        ... )

        Manual usage (if needed):
        >>> participants_desc = '''Available participants:
        ... - **venue** (Venue Specialist): Finds suitable event venues
        ... - **budget** (Budget Analyst): Analyzes event costs
        ... '''
        >>> supervisor_agent = create_supervisor_agent(
        ...     client=client,
        ...     participants_description=participants_desc,
        ...     supervisor_name="Event Planning Supervisor",
        ... )
        """
        instructions = SUPERVISOR_SYSTEM_PROMPT_TEMPLATE.format(
            supervisor_name=supervisor_name,
            participants_description=participants_description,
        )

        # Supervisor does not need tools for routing decisions
        # Tools can be added via kwargs if needed for specific workflows
        return client.create_agent(
            name=supervisor_name,
            instructions=instructions,
            response_format=SupervisorDecision,
            tools=None,
            store=True,  # Use service-managed thread for global context
            **kwargs,
        )


    SUPERVISOR_SYSTEM_PROMPT_TEMPLATE = """
You are the {supervisor_name}, responsible for orchestrating a team of specialist agents to fulfill the user's request.

# Available Participants

{participants_description}

# Your Responsibilities

1. **Route intelligently**: Analyze the conversation history and current state to determine which participant should contribute next
2. **Maintain global context**: You see the entire conversation; participants see only their local history
3. **Avoid redundancy**: Don't route to a participant if they've already provided sufficient information
4. **Request clarification**: If the user's request is ambiguous or you need additional context, ask the user directly
5. **Know when to finish**: When all necessary information has been gathered, synthesize the final result

# Routing Strategy

Apply these general principles when deciding which participant to route to next:

- **Start with foundation**: Route to participants that gather foundational information (requirements, constraints) before those that build upon it
- **Consider dependencies**: If one participant's work depends on another's output, route in dependency order
- **Maximize parallelism**: When multiple participants can work independently, you may route to them in any order
- **Skip unnecessary work**: Don't route to a participant whose expertise isn't needed for the current request
- **Iterate when needed**: Return to participants if their earlier output needs refinement based on new information or user feedback
- **Balance thoroughness and efficiency**: Gather sufficient information without unnecessary redundancy

# Decision Format

Respond with SupervisorDecision structured output:

- **next_agent**:
  - Participant ID (e.g., 'venue', 'budget') to route to next
  - `null` when ready to synthesize final result

- **user_input_needed**:
  - `true` if you need user clarification before proceeding
  - `false` otherwise

- **user_prompt**:
  - Question for the user (required if user_input_needed=true)
  - `null` otherwise

**Workflow completion signal**: Set `next_agent=null` AND `user_input_needed=false` when all necessary work is complete and you're ready to provide the final synthesized result.
"""

### 4. Refactor ALL Agent Factory Functions for DI

Refactor ALL agent factory functions in `src/spec_to_agents/agents/*.py` to use `@inject` decorator:

**Pattern for ALL agent factories** (example: `budget_analyst.py`):

Note: The injected `global_tools` parameter is a dict containing globally shared tools. Agents can selectively pick which global tools they need by key. Agent-specific tools (web search, code interpreter, weather, calendar) should be initialized INSIDE each create_agent() factory function.

    from dependency_injector.wiring import inject, Provide
    from agent_framework import ChatAgent, HostedCodeInterpreterTool, ToolProtocol, BaseChatClient
    from agent_framework.azure import AzureAIAgentClient

    from spec_to_agents.models.messages import SpecialistOutput
    from spec_to_agents.prompts import budget_analyst


    @inject
    def create_agent(
        client: BaseChatClient = Provide["client"],
        global_tools: dict[str, ToolProtocol] = Provide["global_tools"],
    ) -> ChatAgent:
        """
        Create Budget Analyst agent for event planning workflow.

        IMPORTANT: This function uses dependency injection. ALL parameters are
        automatically injected via the DI container. DO NOT pass any arguments
        when calling this function.

        Usage
        -----
        After container is wired:
            agent = budget_analyst.create_agent()  # No arguments - DI handles it!

        Parameters
        ----------
        client : BaseChatClient
            Automatically injected via Provide["client"]
        global_tools : dict[str, ToolProtocol]
            Automatically injected via Provide["global_tools"]
            Dictionary of globally shared tools. Keys:
            - "sequential-thinking": MCP sequential thinking tool
        """
        # Initialize agent-specific tools
        code_interpreter = HostedCodeInterpreterTool(
            description=(
                "Execute Python code for complex financial calculations, budget analysis, "
                "cost projections, and data visualization."
            ),
        )

        # Agent-specific tools only (Budget Analyst doesn't need MCP tool)
        # If you want to add a global tool:
        #   agent_tools = [code_interpreter, global_tools["sequential-thinking"]]
        agent_tools = [code_interpreter]

        return client.create_agent(
            name="BudgetAnalyst",
            instructions=budget_analyst.SYSTEM_PROMPT,
            tools=agent_tools,
            response_format=SpecialistOutput,
            store=True,
        )

Apply this pattern to ALL agent factories:
- `src/spec_to_agents/agents/budget_analyst.py` - Initialize `code_interpreter` (optionally add `global_tools["sequential-thinking"]`)
- `src/spec_to_agents/agents/catering_coordinator.py` - Initialize `web_search` (optionally add global tools)
- `src/spec_to_agents/agents/event_coordinator.py` - No agent-specific tools (optionally add global tools)
- `src/spec_to_agents/agents/logistics_manager.py` - Initialize weather and calendar tools (optionally add global tools)
- `src/spec_to_agents/agents/venue_specialist.py` - Initialize `web_search` (optionally add global tools)

Each factory should:
1. Add `@inject` decorator
2. Change parameters to use `Provide["client"]` and `Provide["global_tools"]` defaults
3. Use type annotation: `dict[str, ToolProtocol]` for `global_tools` parameter
4. Initialize agent-specific tools INSIDE the function (HostedCodeInterpreterTool, web_search, weather, calendar)
5. Optionally select global tools by key: `global_tools["sequential-thinking"]`
6. Keep existing tool configuration and prompts

**Important**: The `global_tools` parameter is a dictionary containing globally shared tools with string keys. Agents can selectively pick which global tools they need. Currently available:
- `"sequential-thinking"`: MCP sequential thinking tool for complex reasoning

All other tools (web search, code interpreter, weather, calendar) are agent-specific and must be initialized inside create_agent().

### 5. Refactor Event Planning Workflow with DI

**File**: `src/spec_to_agents/workflow/core.py`

Update `build_event_planning_workflow` to use supervisor pattern and DI:

    """Event planning multi-agent workflow definition."""

    from agent_framework import Workflow, BaseChatClient
    from dependency_injector.wiring import inject, Provide
    from agent_framework.azure import AzureAIAgentClient

    from spec_to_agents.agents import (
        budget_analyst,
        catering_coordinator,
        logistics_manager,
        venue_specialist,
        supervisor,
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

        Architecture:
        - Supervisor agent makes routing decisions via structured output
        - Participants use service-managed threads for local context
        - Supervisor maintains global context for informed decisions
        - Builder automatically wires bidirectional edges and creates supervisor

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
        workflow = (
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
            .build()
        )

        return workflow

Remove:
- `EventPlanningCoordinator` import
- Manual edge wiring code
- Manual supervisor agent creation
- Manual participant description extraction

Add:
- `client` parameter passed to `SupervisorWorkflowBuilder.__init__` for internal supervisor creation

### 6. Update console.py for DI Container

**File**: `src/spec_to_agents/console.py`

Update console.py to initialize DI container before building workflow:

    """Interactive CLI for event planning workflow with human-in-the-loop."""

    import asyncio

    from agent_framework import (
        AgentRunUpdateEvent,
        RequestInfoEvent,
        WorkflowOutputEvent,
        WorkflowRunState,
        WorkflowStatusEvent,
    )
    from dotenv import load_dotenv

    from spec_to_agents.container import AppContainer  # NEW: Import DI container
    from spec_to_agents.models.messages import HumanFeedbackRequest
    from spec_to_agents.utils.display import (
        console,
        display_agent_run_update,
        display_final_output,
        display_human_feedback_request,
        display_welcome_header,
        display_workflow_pause,
        prompt_for_event_request,
    )
    from spec_to_agents.workflow.core import build_event_planning_workflow

    load_dotenv()


    async def main() -> None:
        """Run the event planning workflow with DI and interactive CLI HITL."""
        display_welcome_header()

        # Initialize DI container and wire modules for dependency injection
        container = AppContainer()
        container.wire(modules=[__name__])  # Wire this module if needed

        # Use async context manager for client lifecycle only
        # global_tools dict is automatically injected into agent factories via @inject
        # MCP tools are automatically connected by agent framework when agents are created
        async with container.client() as client:
            # Build workflow - ALL dependencies (client, global_tools) injected automatically
            with console.status("[bold green]Loading workflow...", spinner="dots"):
                workflow = build_event_planning_workflow()  # No parameters needed!
            console.print("[green]✓[/green] Workflow loaded successfully")
            console.print()

            # Get initial event planning request from user
            user_request = prompt_for_event_request()
            if user_request is None:
                return

            console.print()
            console.rule("[bold green]Workflow Execution")
            console.print()

            # Configuration: Toggle streaming updates display
            display_streaming_updates = True

            # Main workflow loop: alternate between workflow execution and human input
            pending_responses: dict[str, str] | None = None
            workflow_output: str | None = None

            # Track printed tool calls/results to avoid duplication
            printed_tool_calls: set[str] = set()
            printed_tool_results: set[str] = set()
            last_executor: str | None = None

            while workflow_output is None:
                # Execute workflow: first iteration uses run_stream(), subsequent use send_responses_streaming()
                if pending_responses:
                    stream = workflow.send_responses_streaming(pending_responses)
                else:
                    stream = workflow.run_stream(user_request)

                pending_responses = None

                # Process events as they stream in
                human_requests: list[tuple[str, HumanFeedbackRequest]] = []

                async for event in stream:
                    # Display streaming agent updates if enabled
                    if isinstance(event, AgentRunUpdateEvent) and display_streaming_updates:
                        last_executor = display_agent_run_update(
                            event, last_executor, printed_tool_calls, printed_tool_results
                        )

                    # Collect human-in-the-loop requests
                    elif isinstance(event, RequestInfoEvent) and isinstance(event.data, HumanFeedbackRequest):
                        human_requests.append((event.request_id, event.data))

                    # Capture final workflow output
                    elif isinstance(event, WorkflowOutputEvent):
                        workflow_output = str(event.data)

                    # Display workflow status transitions
                    elif (
                        isinstance(event, WorkflowStatusEvent)
                        and event.state == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS
                    ):
                        display_workflow_pause()

                # Prompt user for feedback if workflow requested input
                if human_requests:
                    responses: dict[str, str] = {}

                    for request_id, feedback_request in human_requests:
                        user_response = display_human_feedback_request(feedback_request)
                        if user_response is None:
                            return

                        responses[request_id] = user_response

                    pending_responses = responses

            # Display final workflow output
            display_final_output(workflow_output)

        # Client and MCP tool automatically cleaned up by async context managers


    def cli() -> None:
        """Synchronous entry point for the console command."""
        asyncio.run(main())


    if __name__ == "__main__":
        cli()

Key changes:
- Import `AppContainer` from `spec_to_agents.container`
- Initialize container and wire modules before building workflow
- Use `async with container.client()` and `container.tools()` context managers
- Remove client/mcp_tool parameters from `build_event_planning_workflow()` call
- Dependencies automatically injected into all agent factories

### 7. Update Module Exports

**File**: `src/spec_to_agents/workflow/__init__.py`

Update exports to include supervisor pattern:

    from spec_to_agents.workflow.core import build_event_planning_workflow, workflow
    from spec_to_agents.workflow.supervisor import (
        SupervisorOrchestratorExecutor,
        SupervisorWorkflowBuilder,
    )

    __all__ = [
        "build_event_planning_workflow",
        "workflow",
        "SupervisorOrchestratorExecutor",
        "SupervisorWorkflowBuilder",
    ]

**File**: `src/spec_to_agents/agents/__init__.py`

Add supervisor module to imports (but no need to export `create_supervisor_agent` since it's only used internally by SupervisorWorkflowBuilder):

    from spec_to_agents.agents import supervisor

    # Existing exports remain unchanged - supervisor is used internally

## Concrete Steps

### Run Tests

Before making changes, verify existing tests pass:
    uv run pytest tests/

Expected: All tests pass (baseline).

### Implementation Phase

Implement changes in order of Plan of Work sections 1-5:

1. Create `SupervisorDecision` model
2. Create `supervisor.py` module with executor and builder
3. Create supervisor agent factory
4. Refactor `build_event_planning_workflow`
5. Update module exports

After each file creation/modification:

    uv run ruff .
    uv run mypy .

Expected: No linting or type errors.

### Write Tests

Create comprehensive test suite for supervisor pattern.

**File**: `tests/workflow/test_supervisor_unit.py` (new file)

Unit tests for supervisor components with mocked dependencies:

    """Unit tests for supervisor pattern components."""

    import pytest
    from unittest.mock import AsyncMock, MagicMock, Mock

    from agent_framework import AgentExecutor, AgentRunResponse, ChatMessage, Role
    from spec_to_agents.models.messages import SupervisorDecision
    from spec_to_agents.workflow.supervisor import (
        SupervisorOrchestratorExecutor,
        SupervisorWorkflowBuilder,
    )


    class TestSupervisorDecision:
        """Test SupervisorDecision model validation."""

        def test_supervisor_decision_with_next_agent(self):
            """Test decision with next_agent set."""
            decision = SupervisorDecision(
                next_agent="venue",
                user_input_needed=False,
            )
            assert decision.next_agent == "venue"
            assert decision.user_input_needed is False
            assert decision.user_prompt is None

        def test_supervisor_decision_workflow_complete(self):
            """Test completion signal: next_agent=None and user_input_needed=False."""
            decision = SupervisorDecision(
                next_agent=None,
                user_input_needed=False,
            )
            assert decision.next_agent is None
            assert decision.user_input_needed is False

        def test_supervisor_decision_user_input_needed(self):
            """Test decision requesting user input."""
            decision = SupervisorDecision(
                next_agent=None,
                user_input_needed=True,
                user_prompt="Which venue do you prefer?",
            )
            assert decision.next_agent is None
            assert decision.user_input_needed is True
            assert decision.user_prompt == "Which venue do you prefer?"


    class TestSupervisorOrchestratorExecutor:
        """Test SupervisorOrchestratorExecutor routing logic."""

        @pytest.mark.asyncio
        async def test_start_routes_to_first_participant(self):
            """Test that start() routes to participant chosen by supervisor."""
            # Mock supervisor agent
            supervisor_agent = MagicMock()
            supervisor_agent.run = AsyncMock(
                return_value=AgentRunResponse(
                    messages=[ChatMessage(Role.ASSISTANT, text="Starting with venue")],
                    value=SupervisorDecision(next_agent="venue", user_input_needed=False),
                )
            )

            executor = SupervisorOrchestratorExecutor(
                supervisor_agent=supervisor_agent,
                participant_ids=["venue", "budget", "catering"],
            )

            ctx = MagicMock()
            ctx.send_message = AsyncMock()

            # Execute
            await executor.start("Plan a party for 50 people", ctx)

            # Verify supervisor was called with user request
            supervisor_agent.run.assert_called_once()
            call_args = supervisor_agent.run.call_args[1]
            assert len(call_args["messages"]) == 1
            assert call_args["messages"][0].text == "Plan a party for 50 people"

            # Verify routing to venue
            ctx.send_message.assert_called_once()

        @pytest.mark.asyncio
        async def test_invalid_participant_raises_error(self):
            """Test that routing to invalid participant raises ValueError."""
            supervisor_agent = MagicMock()
            supervisor_agent.run = AsyncMock(
                return_value=AgentRunResponse(
                    messages=[ChatMessage(Role.ASSISTANT, text="Routing")],
                    value=SupervisorDecision(next_agent="invalid_id", user_input_needed=False),
                )
            )

            executor = SupervisorOrchestratorExecutor(
                supervisor_agent=supervisor_agent,
                participant_ids=["venue", "budget"],
            )

            ctx = MagicMock()
            ctx.send_message = AsyncMock()

            # Expect ValueError for invalid participant
            with pytest.raises(ValueError, match="invalid participant"):
                await executor.start("Test request", ctx)


    class TestSupervisorWorkflowBuilder:
        """Test SupervisorWorkflowBuilder topology creation."""

        @patch("spec_to_agents.workflow.supervisor.create_supervisor_agent")
        def test_builder_creates_bidirectional_edges(self, mock_create_supervisor):
            """Test that builder creates supervisor ↔ participant edges."""
            # Mock supervisor agent creation
            mock_supervisor_agent = MagicMock()
            mock_create_supervisor.return_value = mock_supervisor_agent

            # Mock client
            mock_client = MagicMock()

            # Mock participant agents
            venue_agent = MagicMock()
            venue_agent.name = "Venue Specialist"
            budget_agent = MagicMock()
            budget_agent.name = "Budget Analyst"

            workflow = (
                SupervisorWorkflowBuilder(
                    name="Test Workflow",
                    client=mock_client,
                )
                .participants(venue=venue_agent, budget=budget_agent)
                .build()
            )

            assert workflow.name == "Test Workflow"
            # Verify 3 executors: supervisor + 2 participants
            assert len(workflow.executors) == 3

            # Verify supervisor agent was created with extracted descriptions
            mock_create_supervisor.assert_called_once()
            call_kwargs = mock_create_supervisor.call_args[1]
            assert "venue" in call_kwargs["participants_description"]
            assert "budget" in call_kwargs["participants_description"]

        def test_builder_requires_client(self):
            """Test that builder requires client parameter."""
            with pytest.raises(ValueError, match="client"):
                SupervisorWorkflowBuilder(name="Test Workflow").participants(
                    venue=MagicMock()
                ).build()

**File**: `tests/workflow/test_supervisor_integration.py` (new file)

Integration tests using workflow.run_stream() pattern (console.py style):

    """Integration tests for supervisor workflow using streaming pattern."""

    import pytest
    from unittest.mock import AsyncMock, MagicMock, patch

    from agent_framework import (
        AgentRunUpdateEvent,
        WorkflowOutputEvent,
        WorkflowStatusEvent,
        WorkflowRunState,
    )
    from spec_to_agents.models.messages import SupervisorDecision
    from spec_to_agents.workflow.core import build_event_planning_workflow


    @pytest.mark.asyncio
    @patch("spec_to_agents.workflow.core.venue_specialist.create_agent")
    @patch("spec_to_agents.workflow.core.budget_analyst.create_agent")
    @patch("spec_to_agents.workflow.core.supervisor.create_supervisor_agent")
    async def test_supervisor_workflow_e2e_streaming(
        mock_supervisor,
        mock_budget,
        mock_venue,
    ):
        """Test E2E workflow execution using run_stream() pattern."""
        # Mock venue agent
        venue_agent = MagicMock()
        venue_agent.run = AsyncMock(return_value=MagicMock(text="Venue recommendations"))
        mock_venue.return_value = venue_agent

        # Mock budget agent
        budget_agent = MagicMock()
        budget_agent.run = AsyncMock(return_value=MagicMock(text="Budget breakdown"))
        mock_budget.return_value = budget_agent

        # Mock supervisor agent with routing decisions
        supervisor_agent = MagicMock()
        call_count = 0

        async def supervisor_routing(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: route to venue
                return MagicMock(
                    value=SupervisorDecision(next_agent="venue", user_input_needed=False),
                    messages=[],
                )
            elif call_count == 2:
                # Second call: route to budget
                return MagicMock(
                    value=SupervisorDecision(next_agent="budget", user_input_needed=False),
                    messages=[],
                )
            else:
                # Third call: workflow complete
                return MagicMock(
                    value=SupervisorDecision(next_agent=None, user_input_needed=False),
                    messages=[],
                    text="Final comprehensive event plan",
                )

        supervisor_agent.run = AsyncMock(side_effect=supervisor_routing)
        mock_supervisor.return_value = supervisor_agent

        # Build workflow
        workflow = build_event_planning_workflow()

        # Execute workflow using streaming pattern (console.py style)
        user_request = "Plan a corporate party for 50 people"
        output_received = False
        final_output = None

        async for event in workflow.run_stream(user_request):
            if isinstance(event, WorkflowOutputEvent):
                output_received = True
                final_output = str(event.data)
                break

        # Verify workflow completed
        assert output_received, "Workflow should yield final output"
        assert final_output is not None
        assert "event plan" in final_output.lower()

Run tests:

    uv run pytest tests/workflow/test_supervisor_unit.py -v
    uv run pytest tests/workflow/test_supervisor_integration.py -v

Expected: All tests pass.

### Integration Test via DevUI

Start the DevUI:

    uv run app

Navigate to http://localhost:8000 in browser. Select "Event Planning Workflow" and submit test prompt:

    "Plan a corporate holiday party for 50 people in Seattle on December 15th"

Expected observable behavior:
1. Supervisor routes to venue specialist (see agent selection in DevUI)
2. Venue specialist responds with venue options
3. Supervisor routes to budget analyst
4. Budget analyst provides cost breakdown
5. Supervisor routes to catering coordinator
6. Catering coordinator provides menu options
7. Supervisor routes to logistics manager
8. Logistics manager provides schedule/weather
9. Supervisor synthesizes final comprehensive plan

Verify in DevUI:
- Message history shows supervisor routing decisions
- Each participant responds with domain-specific analysis
- Final output is cohesive event plan integrating all recommendations

## Validation and Acceptance

### Acceptance Criteria

The implementation is complete when:

1. **SupervisorDecision model exists** at `src/spec_to_agents/models/messages.py` with fields: `next_agent`, `user_input_needed`, `user_prompt`
2. **SupervisorOrchestratorExecutor exists** at `src/spec_to_agents/workflow/supervisor.py` with handlers: `start`, `on_participant_response`, `on_human_feedback`
3. **SupervisorWorkflowBuilder exists** at `src/spec_to_agents/workflow/supervisor.py` with fluent API: `.with_participants()`, `.with_manager()`, `.build()`
4. **Supervisor agent factory exists** at `src/spec_to_agents/agents/supervisor.py` with `create_supervisor_agent()` function
5. **Event planning workflow refactored** in `src/spec_to_agents/workflow/core.py` to use supervisor pattern
6. **All tests pass**: `uv run pytest tests/` completes without errors
7. **Type checking passes**: `uv run mypy .` reports no errors
8. **Linting passes**: `uv run ruff .` reports no issues
9. **DevUI integration works**: Workflow executes end-to-end with visible supervisor routing decisions
10. **Documentation updated**: `specs/README.md` includes link to this spec

### Verification Commands

Run full validation suite:

    cd /home/alexlavaee/source/repos/spec-to-agents

    # Run tests
    uv run pytest tests/ -v

    # Type checking
    uv run mypy .

    # Linting
    uv run ruff .

    # Start DevUI for manual testing
    uv run app

Expected outputs:
- pytest: All tests pass, no failures
- mypy: Success: no issues found
- ruff: All checks passed
- DevUI: Workflow executes successfully with supervisor routing visible

### Observable Outcomes

After implementation, developers can:

1. **Create supervisor workflows with minimal API surface:**

       workflow = (
           SupervisorWorkflowBuilder(
               name="My Workflow",
               client=client,
           )
           .participants(agent1=agent1, agent2=agent2)
           .build()  # Returns Workflow - all internal wiring handled automatically
       )

   The builder abstracts away:
   - Supervisor agent creation
   - `SupervisorOrchestratorExecutor` creation
   - `AgentExecutor` wrapping
   - Bidirectional edge wiring

2. **See supervisor making routing decisions** in DevUI message history (structured output shows `next_agent` values)

3. **Add/remove participants without changing orchestrator code** (just update builder `.participants()` call, supervisor agent automatically updated with new descriptions)

4. **Supervisor maintains global context** while participants maintain local context via service-managed threads

5. **Human-in-the-loop works** when supervisor sets `user_input_needed=True`

## Idempotence and Recovery

This implementation is idempotent and safe:

- **File creation**: New files can be created multiple times (overwrite with same content)
- **Refactoring**: Replacing `EventPlanningCoordinator` with supervisor pattern is a clean substitution
- **Tests**: Can be run repeatedly without side effects
- **DevUI testing**: Each workflow execution is independent

If implementation fails midway:
1. Check which files were created (`ls src/spec_to_agents/workflow/supervisor.py`, etc.)
2. Review git diff to see partial changes: `git diff`
3. Either complete remaining files or revert: `git checkout .`
4. Re-run tests to identify failures: `uv run pytest tests/ -v`

## Artifacts and Notes

### Key Architectural Patterns

**Context Management:**
- Supervisor: Global context (all conversation history in `_conversation_history`)
- Participants: Local context (service-managed threads via `store=True`)

**Routing Flow:**
```
User Request → start() → Supervisor Agent (decides venue) → _route_to_participant(venue)
Venue Response → on_participant_response() → Supervisor Agent (decides budget) → _route_to_participant(budget)
...
Final Specialist → Supervisor Agent (next_agent=None, user_input_needed=False) → _synthesize_plan() → yield_output()
```

**HITL Flow:**
```
Supervisor Agent (user_input_needed=True) → ctx.request_info() → DevUI emits RequestInfoEvent
User Responds → on_human_feedback() → Supervisor Agent (continues routing)
```

**Builder Pattern:**
- Creates supervisor agent from participant descriptions
- Creates `SupervisorOrchestratorExecutor` internally
- Auto-wires bidirectional edges: Supervisor ←→ Each Participant
- Clean API for workflow construction without exposing internal executor details

### Comparison to Current Architecture

**Before (EventPlanningCoordinator):**
- Routing logic in Python code (`on_specialist_response` method)
- Hardcoded decision tree parsing `SpecialistOutput.next_agent`
- Manual edge wiring in `build_event_planning_workflow`
- Specialists drive routing decisions

**After (SupervisorOrchestratorExecutor):**
- Routing logic in supervisor agent (LLM with structured output)
- Dynamic decisions based on conversation context
- Automatic edge wiring via builder
- Supervisor drives routing decisions

**Benefits:**
- More flexible (supervisor can adapt routing based on context)
- Less code (builder eliminates manual edge declarations)
- Easier to extend (add participants without changing orchestrator)
- Cleaner separation (orchestration vs domain logic)

## Interfaces and Dependencies

### Module Dependencies

New module `src/spec_to_agents/workflow/supervisor.py` depends on:
- `agent_framework`: Core workflow/executor classes
- `spec_to_agents.models.messages`: `HumanFeedbackRequest`, `SupervisorDecision`
- `spec_to_agents.workflow.executors`: `convert_tool_content_to_text` helper

New module `src/spec_to_agents/agents/supervisor.py` depends on:
- `agent_framework`: `ChatAgent`, `BaseChatClient`
- `agent_framework.azure`: `AzureAIAgentClient`
- `spec_to_agents.models.messages`: `SupervisorDecision`

### Type Signatures

**SupervisorDecision:**

    class SupervisorDecision(BaseModel):
        next_agent: str | None
        user_input_needed: bool
        user_prompt: str | None

**SupervisorOrchestratorExecutor:**

    class SupervisorOrchestratorExecutor(Executor):
        def __init__(
            self,
            supervisor_agent: ChatAgent,
            participant_ids: list[str],
        ) -> None: ...

        @handler
        async def start(
            self,
            prompt: str,
            ctx: WorkflowContext[AgentExecutorRequest, str],
        ) -> None: ...

        @handler
        async def on_participant_response(
            self,
            response: AgentExecutorResponse,
            ctx: WorkflowContext[AgentExecutorRequest, str],
        ) -> None: ...

        @response_handler
        async def on_human_feedback(
            self,
            original_request: HumanFeedbackRequest,
            feedback: str,
            ctx: WorkflowContext[AgentExecutorRequest, str],
        ) -> None: ...

**SupervisorWorkflowBuilder:**

    class SupervisorWorkflowBuilder:
        def __init__(
            self,
            name: str,
            id: str | None = None,
            description: str | None = None,
            max_iterations: int = 30,
            client: BaseChatClient | None = None,
        ) -> None: ...

        def participants(
            self,
            **participants: ChatAgent,
        ) -> "SupervisorWorkflowBuilder": ...

        def build(self) -> Workflow: ...

**create_supervisor_agent:**

    def create_supervisor_agent(
        client: BaseChatClient,
        participants_description: str,
        supervisor_name: str = "Supervisor",
        **kwargs: Any,
    ) -> ChatAgent: ...