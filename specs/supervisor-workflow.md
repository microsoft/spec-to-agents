# Supervisor Workflow

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `specs/PLANS.md` (from repository root).

## Purpose / Big Picture

Transform the event planning workflow from a coordinator-centric star topology with hardcoded routing logic into a lightweight supervisor pattern where a supervisor agent makes dynamic routing decisions via structured output. This change enables flexible participant topologies without modifying orchestrator code.

After implementation, developers can create supervisor-based workflows using a fluent builder API that automatically wires bidirectional edges between supervisor and participants. The supervisor agent dynamically determines which participant to call next based on conversation context, not hardcoded logic.

## Progress

- [ ] Create SupervisorDecision structured output model in src/spec_to_agents/models/messages.py
- [ ] Create SupervisorOrchestratorExecutor in src/spec_to_agents/workflow/supervisor.py
- [ ] Create SupervisorWorkflowBuilder in src/spec_to_agents/workflow/supervisor.py
- [ ] Create supervisor agent factory in src/spec_to_agents/agents/supervisor.py
- [ ] Refactor build_event_planning_workflow to use supervisor pattern
- [ ] Write unit tests for SupervisorOrchestratorExecutor
- [ ] Write unit tests for SupervisorWorkflowBuilder
- [ ] Write integration test for supervisor workflow
- [ ] Update specs/README.md with supervisor pattern documentation
- [ ] Validate workflow via DevUI end-to-end test

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
                "ID of next participant to route to (e.g., 'venue', 'budget', 'catering', 'logistics'), "
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

Key implementation details:
- `SupervisorOrchestratorExecutor.__init__`: Takes `supervisor_agent` and `participant_ids` list
- `SupervisorOrchestratorExecutor._conversation_history`: List of ChatMessage for global context
- `SupervisorOrchestratorExecutor._get_supervisor_decision_and_route`: Core routing logic, runs supervisor agent and executes decision
- `SupervisorOrchestratorExecutor._route_to_participant`: Sends focused request to participant (user request + instruction)
- `SupervisorOrchestratorExecutor._synthesize_plan`: Supervisor synthesizes final plan from global context
- `SupervisorWorkflowBuilder.with_participants`: Accepts kwargs of `AgentExecutor` instances keyed by ID
- `SupervisorWorkflowBuilder.with_manager`: Accepts `SupervisorOrchestratorExecutor` instance
- `SupervisorWorkflowBuilder.build`: Creates bidirectional edges between manager and all participants

### 3. Create Supervisor Agent Factory

**File**: `src/spec_to_agents/agents/supervisor.py` (new file)

Create factory function and system prompt:

    from agent_framework import ChatAgent, BaseChatClient
    from agent_framework.azure import AzureAIAgentClient
    from langchain_core.prompts import PromptTemplate
    from typing import Any

    from spec_to_agents.models.messages import SupervisorDecision

    __all__ = ["create_supervisor_agent"]


    def create_supervisor_agent(client: BaseChatClient, participants_description_block: str, **kwargs: Any) -> BaseChatClient:
        """
        Create supervisor agent for workflow orchestration.

        The supervisor uses structured output (SupervisorDecision) to make
        dynamic routing decisions based on conversation context.

        Parameters
        ----------
        client : BaseChatClient
            Chat client protocol for creating the agent
        participants_description_block : str
            Description block listing all available participants
            e.g.,
            "
            Available participants:
            - Venue Specialist: Expert in finding and booking venues
            - Budget Analyst: Skilled in cost estimation and budget planning
            - Catering Coordinator: Knowledgeable in menu planning and catering options
            - Logistics Manager: Experienced in event logistics and scheduling
            "
        **kwargs : Any
            Additional keyword arguments for BaseChatClient.create_agent()
        

        Returns
        -------
        BaseChatClient
            Supervisor agent with SupervisorDecision structured output
        """
        instructions = SUPERVISOR_PROMPT_TEMPLATE.format(
            participant_description_block=participants_description_block
        )
        return client.create_agent(
            name="Event Planning Supervisor",
            instructions=instructions,
            response_format=SupervisorDecision,
            **kwargs,
        )

    SUPERVISOR_SYSTEM_PROMPT_TEMPLATE = PromptTemplate.from_template(template="""
    You are the supervisor for a multi-agent workflow. Your role is to orchestrate
    multiple specialist agents to create a comprehensive event plan.

    Available participants:
    {participants_description_block}

    Your responsibilities:
    1. Analyze the conversation history (you have global context)
    2. Decide which participant should work next
    3. Determine when enough information has been gathered
    4. Request user input when clarification is needed
    5. Synthesize the final plan when all participants complete their work

    Routing strategy:
    - IMPORTANT: Use the conversation history to inform your decisions
    - Use the `next_agent` field to specify which participant to call next
    - If you need more information from the user, set `user_input_needed` to True
    - If the workflow is complete, set `next_agent` to None and `user_input_needed` to False
    
    Respond with SupervisorDecision containing:
    - next_agent: ID of participant to call, or None if ready to synthesize
    - user_input_needed: True if you need user clarification
    - user_prompt: Question for user (if needed)
    """)

### 4. Refactor Event Planning Workflow

**File**: `src/spec_to_agents/workflow/core.py`

Update `build_event_planning_workflow` function (lines 32-137) to use supervisor pattern:

    from spec_to_agents.agents.supervisor import create_supervisor_agent
    from spec_to_agents.workflow.supervisor import (
        SupervisorOrchestratorExecutor,
        SupervisorWorkflowBuilder,
    )
    from agent_framework import ToolProtocol, ChatClientProtocol, Workflow
    from typing import Callable, MutableMapping, Sequence, Any

    def build_event_planning_workflow(
        client: ChatClientProtocol,
        tools: ToolProtocol
        | Callable[..., Any]
        | MutableMapping[str, Any]
        | Sequence[ToolProtocol | Callable[..., Any] | MutableMapping[str, Any]]
        | None = None,
    ) -> Workflow:
        """
        Build event planning workflow using supervisor pattern.

        Architecture:
        - Supervisor agent makes routing decisions via structured output
        - Participants use service-managed threads for local context
        - Supervisor maintains global context for informed decisions
        - Builder automatically wires bidirectional edges
        """
        # Create participant agents
        venue_agent = venue_specialist.create_agent() # will use dependency injection for client and mcp_tools using dependency-injector library
        budget_agent = budget_analyst.create_agent()
        catering_agent = catering_coordinator.create_agent()
        logistics_agent = logistics_manager.create_agent()

        # Build workflow using supervisor pattern
        workflow = (
            SupervisorWorkflowBuilder(
                name="Event Planning Workflow",
                id="event-planning-workflow",
                description="Multi-agent event planning with supervisor orchestration",
                max_iterations=30,
                client=client # the chat client, accepts any BaseChatClient instance
            )
            .participants(
                venue=venue_agent,
                budget=budget_agent,
                catering=catering_agent,
                logistics=logistics_agent,
            )
        .build()
        )

        ###### Internals ######

        # When a SupervisorWorkflowBuilder is used, the following are created internally:

        supervisor_agent = create_supervisor_agent(client)

        supervisor_exec = SupervisorOrchestratorExecutor(
            supervisor_agent=supervisor_agent,
            participant_ids=..., # derived from workflow builder
        )

        #######################

        return workflow

Remove the old `EventPlanningCoordinator` import and manual edge wiring code.

### 5. Update Module Exports

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

Add supervisor agent export:

    from spec_to_agents.agents.supervisor import create_supervisor_agent

    __all__ = [
        # ... existing exports
        "create_supervisor_agent",
    ]

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

1. **Create supervisor workflows with fluent API:**

       workflow = (
           SupervisorWorkflowBuilder(name="My Workflow")
           .with_participants(agent1=exec1, agent2=exec2)
           .with_manager(supervisor_exec)
           .build()
       )

2. **See supervisor making routing decisions** in DevUI message history (structured output shows `next_agent` values)

3. **Add/remove participants without changing orchestrator code** (just update builder `.participants()` call)

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
- Auto-wires bidirectional edges: Manager ←→ Each Participant
- Validates participant IDs match between builder and executor
- Clean API for workflow construction

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
- `agent_framework`: `ChatAgent`
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
            description: str | None = None,
            max_iterations: int = 30,
        ) -> None: ...

        def participants(
            self,
            **participants: AgentExecutor,
        ) -> "SupervisorWorkflowBuilder": ...

        def build(self) -> Workflow: ...

**create_supervisor_agent:**

    create_supervisor_agent(
        client: BaseChatClient,
        participants_description_block: str,
        **kwargs: Any
    ) -> BaseChatClient: ...