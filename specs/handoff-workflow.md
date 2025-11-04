# Handoff Workflow Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `specs/PLANS.md` (from repository root).

## Purpose / Big Picture

Replace the custom SupervisorWorkflowBuilder implementation with Microsoft Agent Framework's built-in **HandoffBuilder**, extending it with automatic coordinator creation from participant descriptions. This migration leverages the framework's native handoff pattern while preserving the valuable auto-configuration logic that made SupervisorWorkflowBuilder developer-friendly.

After implementation, the event planning workflow will use HandoffBuilder's proven handoff mechanism (tool-based routing with middleware interception) while maintaining the same clean builder API that automatically creates a coordinator agent from specialist agent descriptions.

## Progress

- [ ] Create HandoffBuilderExtensions module with auto-coordinator creation
- [ ] Update prompts module with coordinator prompt template
- [ ] Refactor build_event_planning_workflow to use HandoffBuilder
- [ ] Remove SupervisorWorkflowBuilder and SupervisorOrchestratorExecutor
- [ ] Remove SupervisorDecision model (no longer needed)
- [ ] Update tests to use HandoffBuilder pattern
- [ ] Update CLAUDE.md documentation
- [ ] Validate workflow E2E via DevUI and console.py

## Surprises & Discoveries

(To be filled during implementation)

## Decision Log

- **Decision**: Use HandoffBuilder instead of SupervisorWorkflowBuilder
  **Rationale**: HandoffBuilder is built-in to Agent Framework with proven handoff tool synthesis, middleware interception, and conversation management. Reduces custom code maintenance burden.
  **Date/Author**: 2025-01-04 / User requirement

- **Decision**: Extend HandoffBuilder with `.with_auto_coordinator()` method pattern
  **Rationale**: Preserves the valuable auto-configuration feature while keeping the API extension minimal and focused. Alternative of wrapping HandoffBuilder would create unnecessary abstraction layers.
  **Date/Author**: 2025-01-04 / Claude with user approval

- **Decision**: Adopt HandoffBuilder's automatic user input pattern
  **Rationale**: Framework's built-in pattern (request input after every specialist) is battle-tested and eliminates need for custom HITL logic in coordinator.
  **Date/Author**: 2025-01-04 / User requirement

- **Decision**: Big bang replacement (not gradual deprecation)
  **Rationale**: Clean cut reduces maintenance burden and prevents developer confusion about which builder to use. Project is early enough that migration impact is minimal.
  **Date/Author**: 2025-01-04 / User requirement

- **Decision**: Use "coordinator" terminology consistently (not "supervisor")
  **Rationale**: Align with HandoffBuilder's terminology for consistency with framework documentation and developer expectations.
  **Date/Author**: 2025-01-04 / User requirement

## Outcomes & Retrospective

(To be filled at completion)

## Context and Orientation

This project uses **Microsoft Agent Framework** (Python) to build multi-agent workflows for event planning. The current architecture uses `SupervisorWorkflowBuilder` (custom implementation) which:
- Creates a supervisor agent that makes routing decisions via `SupervisorDecision` structured output
- Automatically extracts participant descriptions and creates supervisor agent
- Uses custom `SupervisorOrchestratorExecutor` for routing logic

Microsoft Agent Framework now provides **HandoffBuilder** (built-in, located at `.venv/lib/python3.13/site-packages/agent_framework/_workflows/_handoff.py`) which:
- Uses handoff tools (e.g., `handoff_to_refund_agent`) for routing
- Automatically synthesizes handoff tools and intercepts them via middleware
- Maintains full conversation history via `_HandoffCoordinator`
- Requests user input automatically after each specialist response
- Supports termination conditions

The migration will replace SupervisorWorkflowBuilder with HandoffBuilder + extension methods.

## Plan of Work

### 1. Create HandoffBuilder Extension Module

**File**: `src/spec_to_agents/workflow/handoff_extensions.py` (new file)

Create extension methods for HandoffBuilder to support automatic coordinator creation:

```python
"""Extensions for HandoffBuilder to support automatic coordinator creation."""

from typing import Any

from agent_framework import BaseChatClient, ChatAgent, HandoffBuilder
from agent_framework._workflows._handoff import HandoffBuilder as _HandoffBuilder


def with_auto_coordinator(
    builder: HandoffBuilder,
    *,
    client: BaseChatClient,
    coordinator_name: str | None = None,
    coordinator_instructions_template: str | None = None,
    **agent_kwargs: Any,
) -> HandoffBuilder:
    """
    Extend HandoffBuilder to automatically create and configure a coordinator agent.

    This method analyzes the participants already registered with the builder,
    extracts their descriptions, and creates a coordinator agent with handoff tools
    pre-configured for routing to all specialists.

    Usage Pattern (Extension Method Style):
    ----------------------------------------

    >>> from agent_framework import HandoffBuilder
    >>> from spec_to_agents.workflow.handoff_extensions import with_auto_coordinator
    >>>
    >>> # Create specialist agents
    >>> venue = client.create_agent(name="venue", description="Finds event venues", ...)
    >>> budget = client.create_agent(name="budget", description="Analyzes budgets", ...)
    >>>
    >>> # Build workflow with auto-coordinator
    >>> workflow = with_auto_coordinator(
    ...     HandoffBuilder(
    ...         name="Event Planning",
    ...         participants=[venue, budget],
    ...     ),
    ...     client=client,
    ...     coordinator_name="Event Planning Coordinator",
    ... ).build()

    Parameters
    ----------
    builder : HandoffBuilder
        HandoffBuilder instance with participants already registered via constructor
        or .participants() method
    client : BaseChatClient
        Chat client for creating the coordinator agent
    coordinator_name : str, optional
        Name for the coordinator agent. Defaults to "{workflow_name} Coordinator"
    coordinator_instructions_template : str, optional
        Custom instructions template. Must include {coordinator_name} and
        {participants_description} placeholders. If not provided, uses default template.
    **agent_kwargs : Any
        Additional keyword arguments passed to client.create_agent() for coordinator

    Returns
    -------
    HandoffBuilder
        The same builder instance with coordinator configured, ready for .build()

    Raises
    ------
    ValueError
        If builder has no participants registered
    RuntimeError
        If builder._executors or builder._aliases are not accessible (internal API change)

    Notes
    -----
    This function accesses HandoffBuilder's private attributes (_executors, _aliases, _name)
    to extract participant metadata. If Agent Framework changes these internals, this
    function will need updates.

    The coordinator agent is created with:
    - Instructions that describe all participants and their roles
    - Handoff tools automatically registered for each specialist
    - Description set to coordinator_name for clarity

    Examples
    --------
    Minimal usage:

    >>> workflow = with_auto_coordinator(
    ...     HandoffBuilder(participants=[venue, budget, catering]),
    ...     client=client,
    ... ).build()

    With custom coordinator name:

    >>> workflow = with_auto_coordinator(
    ...     HandoffBuilder(name="Support", participants=[tier1, tier2, escalation]),
    ...     client=client,
    ...     coordinator_name="Support Triage Agent",
    ... ).build()

    With custom instructions template:

    >>> custom_template = '''
    ... You are {coordinator_name}.
    ... Route requests to specialists:
    ... {participants_description}
    ... Always handoff, never handle directly.
    ... '''
    >>> workflow = with_auto_coordinator(
    ...     HandoffBuilder(participants=[agent1, agent2]),
    ...     client=client,
    ...     coordinator_instructions_template=custom_template,
    ... ).build()
    """
    # Access private attributes to extract participant metadata
    # NOTE: This is brittle - if HandoffBuilder internals change, this breaks
    if not hasattr(builder, '_executors') or not hasattr(builder, '_aliases'):
        raise RuntimeError(
            "HandoffBuilder internal API changed. Expected _executors and _aliases attributes."
        )

    executors = getattr(builder, '_executors')
    aliases = getattr(builder, '_aliases')
    workflow_name = getattr(builder, '_name', None)

    if not executors:
        raise ValueError(
            "with_auto_coordinator() requires participants to be registered first. "
            "Call HandoffBuilder(participants=[...]) or .participants([...]) before using this extension."
        )

    # Extract participant descriptions for coordinator instructions
    participant_descriptions = []
    for exec_id, executor in executors.items():
        # Get agent from executor
        agent = getattr(executor, '_agent', None)
        if agent:
            name = getattr(agent, 'name', exec_id)
            description = getattr(agent, 'description', None)
            if description is None:
                # Fallback: use first line of instructions
                instructions = getattr(agent.chat_options, 'instructions', None)
                if instructions:
                    description = instructions.split('\n')[0]
                else:
                    description = f"Agent responsible for {exec_id}"
            participant_descriptions.append(f"- **{exec_id}** ({name}): {description}")
        else:
            # Executor without agent - use exec_id
            participant_descriptions.append(f"- **{exec_id}**: {exec_id}")

    participants_description = "Available participants:\n\n" + "\n".join(participant_descriptions)

    # Determine coordinator name
    final_coordinator_name = coordinator_name
    if final_coordinator_name is None:
        if workflow_name:
            final_coordinator_name = f"{workflow_name} Coordinator"
        else:
            final_coordinator_name = "Coordinator"

    # Build coordinator instructions
    if coordinator_instructions_template:
        instructions = coordinator_instructions_template.format(
            coordinator_name=final_coordinator_name,
            participants_description=participants_description,
        )
    else:
        # Use default template
        from spec_to_agents.prompts.coordinator import COORDINATOR_SYSTEM_PROMPT_TEMPLATE
        instructions = COORDINATOR_SYSTEM_PROMPT_TEMPLATE.format(
            coordinator_name=final_coordinator_name,
            participants_description=participants_description,
        )

    # Create coordinator agent
    coordinator = client.create_agent(
        name=f"{final_coordinator_name.lower().replace(' ', '_')}",
        description=final_coordinator_name,
        instructions=instructions,
        store=True,  # Use service-managed threads
        **agent_kwargs,
    )

    # Register coordinator as a participant and set as starting agent
    # Need to create a new HandoffBuilder with updated participants list
    all_participants = [coordinator] + list(executors.values())
    builder.participants(all_participants)
    builder.set_coordinator(coordinator)

    return builder


__all__ = ["with_auto_coordinator"]
```

**Key Design Decisions**:
- Extension function pattern (not subclass) for flexibility
- Accesses HandoffBuilder private attributes with clear warnings about brittleness
- Extracts descriptions using same fallback logic as SupervisorWorkflowBuilder
- Returns builder for method chaining

### 2. Create Coordinator Prompt Template

**File**: `src/spec_to_agents/prompts/coordinator.py` (new file)

Adapt the supervisor prompt template to coordinator terminology:

```python
"""System prompt template for auto-generated coordinator agents."""

COORDINATOR_SYSTEM_PROMPT_TEMPLATE = """
You are the {coordinator_name}, responsible for orchestrating a team of specialist agents to fulfill the user's request.

# Available Participants

{participants_description}

# Your Responsibilities

1. **Route intelligently**: Analyze the conversation history and current state to determine which participant should contribute next
2. **Use handoff tools**: When you need a specialist's expertise, invoke the appropriate handoff tool (e.g., `handoff_to_venue` for venue specialist)
3. **Maintain context awareness**: You see the entire conversation; specialists receive the full conversation history when you hand off to them
4. **Avoid redundancy**: Don't hand off to a participant if they've already provided sufficient information for the current request
5. **Handle directly when appropriate**: If you can answer the user's question without specialist help, do so
6. **Natural conversation**: After a specialist responds, the user will provide more input. Continue the conversation naturally.

# Routing Strategy

Apply these general principles when deciding whether to hand off:

- **Start with foundation**: Route to participants that gather foundational information (requirements, constraints) before those that build upon it
- **Consider dependencies**: If one participant's work depends on another's output, route in dependency order
- **Skip unnecessary work**: Don't route to a participant whose expertise isn't needed for the current request
- **Iterate when needed**: Return to participants if their earlier output needs refinement based on new information or user feedback
- **Balance thoroughness and efficiency**: Gather sufficient information without unnecessary redundancy

# Handoff Mechanism

To hand off to a specialist, invoke the handoff tool for that specialist:
- For the venue specialist: Call `handoff_to_venue()`
- For the budget specialist: Call `handoff_to_budget()`
- And so on for each participant

After you hand off, the specialist will respond, and then the user will provide their next input.

# Important Notes

- The workflow will automatically request user input after each specialist responds
- You don't need to explicitly ask "what would you like to know next?" - this happens automatically
- Focus on routing decisions and providing value-added coordination
"""

__all__ = ["COORDINATOR_SYSTEM_PROMPT_TEMPLATE"]
```

**Key Changes from Supervisor Prompt**:
- Removed `SupervisorDecision` structured output references
- Added handoff tool invocation instructions
- Clarified automatic user input pattern
- Updated terminology to "coordinator" and "participants"

### 3. Refactor Event Planning Workflow

**File**: `src/spec_to_agents/workflow/core.py`

Replace SupervisorWorkflowBuilder usage with HandoffBuilder + extension:

```python
"""Event planning multi-agent workflow definition."""

from agent_framework import Workflow, BaseChatClient, HandoffBuilder
from dependency_injector.wiring import inject, Provide

from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.workflow.handoff_extensions import with_auto_coordinator

__all__ = ["build_event_planning_workflow"]


@inject
def build_event_planning_workflow(
    client: BaseChatClient = Provide["client"],
) -> Workflow:
    """
    Build event planning workflow using HandoffBuilder with automatic coordinator creation.

    Dependencies (client, tools) are injected via DI container.
    All agent factories use @inject to receive dependencies automatically.

    Architecture:
    - Coordinator agent routes to specialists via handoff tools
    - HandoffBuilder automatically synthesizes handoff tools and intercepts invocations
    - Full conversation history maintained by _HandoffCoordinator
    - User input automatically requested after each specialist response
    - Termination condition: stops after 10 user messages (customizable)

    Handoff Flow:
    1. User provides initial request
    2. Coordinator analyzes and decides whether to handle or hand off
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

    # Build workflow using HandoffBuilder with auto-coordinator extension
    # Extension automatically:
    # 1. Extracts participant descriptions from agent properties
    # 2. Creates coordinator agent with handoff tools for all specialists
    # 3. Configures coordinator as starting agent
    # 4. Registers handoff middleware for tool interception
    workflow = with_auto_coordinator(
        HandoffBuilder(
            name="Event Planning Workflow",
            participants=[venue_agent, budget_agent, catering_agent, logistics_agent],
            description="Multi-agent event planning with coordinator orchestration",
        ),
        client=client,
        coordinator_name="Event Planning Coordinator",
    ).build()

    return workflow
```

**Key Changes**:
- Replaced `SupervisorWorkflowBuilder` with `HandoffBuilder`
- Use `with_auto_coordinator()` extension for automatic coordinator creation
- Removed manual `SupervisorOrchestratorExecutor` creation
- Simplified to single fluent chain

### 4. Remove Obsolete Code

**File**: `src/spec_to_agents/workflow/supervisor.py`

**Action**: Delete entire file (no longer needed)

**File**: `src/spec_to_agents/models/messages.py`

**Action**: Remove `SupervisorDecision` model:

```python
# DELETE THIS CLASS:
# class SupervisorDecision(BaseModel):
#     next_agent: str | None = ...
#     user_input_needed: bool = ...
#     user_prompt: str | None = ...
```

Update `__all__` to remove `SupervisorDecision` export.

Keep `HumanFeedbackRequest` and `SpecialistOutput` (still used by specialists for internal routing hints, though coordinator makes final decisions).

**File**: `src/spec_to_agents/agents/supervisor.py`

**Action**: Delete entire file (no longer needed, coordinator created by extension)

**File**: `src/spec_to_agents/prompts/supervisor.py`

**Action**: Delete entire file (replaced by coordinator.py)

### 5. Update Module Exports

**File**: `src/spec_to_agents/workflow/__init__.py`

Update exports to remove supervisor pattern:

```python
from spec_to_agents.workflow.core import build_event_planning_workflow, workflow
from spec_to_agents.workflow.handoff_extensions import with_auto_coordinator

__all__ = [
    "build_event_planning_workflow",
    "workflow",
    "with_auto_coordinator",
]
```

### 6. Update Tests

**File**: `tests/workflow/test_handoff_workflow.py` (new file, replaces supervisor tests)

Create tests for HandoffBuilder + extension pattern:

```python
"""Tests for event planning workflow using HandoffBuilder."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_framework import (
    HandoffBuilder,
    RequestInfoEvent,
    WorkflowOutputEvent,
)

from spec_to_agents.workflow.core import build_event_planning_workflow
from spec_to_agents.workflow.handoff_extensions import with_auto_coordinator


class TestHandoffExtensions:
    """Test with_auto_coordinator extension method."""

    def test_with_auto_coordinator_creates_coordinator(self):
        """Test that extension creates coordinator from participant descriptions."""
        # Mock client
        mock_client = MagicMock()
        mock_coordinator = MagicMock()
        mock_coordinator.name = "coordinator"
        mock_client.create_agent.return_value = mock_coordinator

        # Mock participant agents
        venue_agent = MagicMock()
        venue_agent.name = "venue"
        venue_agent.description = "Finds event venues"

        budget_agent = MagicMock()
        budget_agent.name = "budget"
        budget_agent.description = "Analyzes budgets"

        # Build workflow with extension
        builder = HandoffBuilder(
            name="Test Workflow",
            participants=[venue_agent, budget_agent],
        )

        extended_builder = with_auto_coordinator(
            builder,
            client=mock_client,
            coordinator_name="Test Coordinator",
        )

        # Verify coordinator agent was created
        mock_client.create_agent.assert_called_once()
        call_kwargs = mock_client.create_agent.call_args[1]

        # Check instructions contain participant descriptions
        assert "venue" in call_kwargs["instructions"]
        assert "budget" in call_kwargs["instructions"]
        assert "Finds event venues" in call_kwargs["instructions"]
        assert "Analyzes budgets" in call_kwargs["instructions"]

    def test_with_auto_coordinator_requires_participants(self):
        """Test that extension requires participants to be registered first."""
        mock_client = MagicMock()
        empty_builder = HandoffBuilder(name="Empty")

        with pytest.raises(ValueError, match="requires participants"):
            with_auto_coordinator(empty_builder, client=mock_client)


class TestEventPlanningWorkflow:
    """Test event planning workflow with HandoffBuilder."""

    @pytest.mark.asyncio
    @patch("spec_to_agents.workflow.core.venue_specialist.create_agent")
    @patch("spec_to_agents.workflow.core.budget_analyst.create_agent")
    @patch("spec_to_agents.workflow.core.catering_coordinator.create_agent")
    @patch("spec_to_agents.workflow.core.logistics_manager.create_agent")
    async def test_workflow_handoff_flow(
        self,
        mock_logistics,
        mock_catering,
        mock_budget,
        mock_venue,
    ):
        """Test E2E workflow execution with handoff pattern."""
        # Mock specialist agents
        venue_agent = MagicMock()
        venue_agent.name = "venue"
        venue_agent.run = AsyncMock(return_value=MagicMock(text="Venue recommendations"))
        mock_venue.return_value = venue_agent

        budget_agent = MagicMock()
        budget_agent.name = "budget"
        budget_agent.run = AsyncMock(return_value=MagicMock(text="Budget analysis"))
        mock_budget.return_value = budget_agent

        # Build workflow
        workflow = build_event_planning_workflow()

        # Execute workflow
        user_request = "Plan a corporate party for 50 people"

        # Collect events
        events = []
        async for event in workflow.run_stream(user_request):
            events.append(event)
            if isinstance(event, WorkflowOutputEvent):
                break
            if isinstance(event, RequestInfoEvent):
                # Simulate user response
                await workflow.send_response(event.request_id, "Sounds good, continue")

        # Verify workflow executed
        assert len(events) > 0
```

**File**: `tests/workflow/test_supervisor_unit.py`

**Action**: Delete file (replaced by test_handoff_workflow.py)

**File**: `tests/workflow/test_supervisor_integration.py`

**Action**: Delete file (replaced by test_handoff_workflow.py)

### 7. Update Documentation

**File**: `CLAUDE.md`

Update the Architecture section to reflect HandoffBuilder usage:

Replace the entire "Workflow Architecture" section with:

```markdown
## Workflow Architecture

**Handoff Pattern with Coordinator Hub:**
```
User Request
    ↓
Event Planning Coordinator (HandoffBuilder)
    ↓ (handoff tool invocation)
    ├── Venue Specialist (handoff_to_venue)
    ├── Budget Analyst (handoff_to_budget)
    ├── Catering Coordinator (handoff_to_catering)
    └── Logistics Manager (handoff_to_logistics)
    ↓ (automatic user input request)
User Input
    ↓
Event Planning Coordinator
    ↓
[Repeat until termination condition]
```

**Key Architectural Patterns:**

1. **HandoffBuilder**: Built-in Microsoft Agent Framework pattern for coordinator-based routing
2. **Automatic Coordinator Creation**: Extension method (`with_auto_coordinator()`) creates coordinator from specialist descriptions
3. **Handoff Tool Routing**: Coordinator invokes handoff tools (e.g., `handoff_to_venue`) to transfer control
4. **Full Conversation History**: All agents receive complete conversation via `_HandoffCoordinator`
5. **Automatic User Input**: Framework requests user input after each specialist responds (cyclical flow)
6. **Termination Condition**: Workflow stops after 10 user messages (default, customizable)

![Workflow Architecture](assets/workflow_architecture.png)

## Agents and Tools

Each specialist agent has access to domain-specific tools:

![Agents and Tools](assets/agent_tools.png)

**Tool Integration:**
- **Custom Web Search**: Used by Venue Specialist and Catering Coordinator
- **Weather Tool**: Open-Meteo API, used by Logistics Manager
- **Calendar Tools**: iCalendar (.ics) management, used by Logistics Manager
- **Code Interpreter**: Python REPL for financial calculations, used by Budget Analyst
- **MCP Tool Orchestration**: sequential-thinking-tools for complex reasoning (optional, all agents)
- **Handoff Tools**: Automatically synthesized by HandoffBuilder for coordinator routing
```

Update the "Key Implementation Patterns" section:

```markdown
## Key Implementation Patterns

### 1. HandoffBuilder with Auto-Coordinator Extension

The workflow uses HandoffBuilder with `with_auto_coordinator()` extension for automatic coordinator creation:

- **Receives initial requests** via HandoffBuilder's input normalization
- **Coordinator routes via handoff tools** (e.g., `handoff_to_venue`)
- **Automatic user input** after each specialist response
- **Termination condition** controls workflow completion

**Code Location:** `src/spec_to_agents/workflow/core.py:26-71`

### 2. Handoff Tool Routing

Coordinator routes to specialists by invoking handoff tools:

```python
# Coordinator invokes: handoff_to_venue()
# Framework intercepts via _AutoHandoffMiddleware
# Routes to venue specialist with full conversation
```

**Benefits:**
- Framework-native pattern (no custom routing code)
- Automatic tool synthesis and middleware interception
- Clean separation: coordinator decides, framework routes
- Full conversation history preserved

**Code Location:** `agent_framework/_workflows/_handoff.py`

### 3. Auto-Coordinator Extension Pattern

The `with_auto_coordinator()` extension automatically creates coordinator agent:

```python
workflow = with_auto_coordinator(
    HandoffBuilder(
        name="Event Planning Workflow",
        participants=[venue_agent, budget_agent, catering_agent, logistics_agent],
    ),
    client=client,
    coordinator_name="Event Planning Coordinator",
).build()
```

**Benefits:**
- Extracts participant descriptions automatically
- Creates coordinator with handoff tools pre-configured
- No manual coordinator agent creation needed
- Clean fluent API

**Code Location:** `src/spec_to_agents/workflow/handoff_extensions.py:21-188`
```

Remove all references to:
- `SupervisorWorkflowBuilder`
- `SupervisorOrchestratorExecutor`
- `SupervisorDecision`
- Supervisor pattern

### 8. Update specs/README.md

Add link to this spec and remove supervisor-workflow.md:

```markdown
# Specifications

This directory contains ExecPlans for major features and refactors.

## Active Specs

- [Handoff Workflow Migration](./handoff-workflow.md) - Migration from SupervisorWorkflowBuilder to HandoffBuilder

## Completed Specs

- ~~[Supervisor Workflow](./supervisor-workflow.md)~~ - Replaced by Handoff Workflow Migration
```

## Concrete Steps

### Validation Commands

Run full validation suite after implementation:

```bash
cd /home/alexlavaee/source/repos/spec-to-agents

# Run tests
uv run pytest tests/ -v

# Type checking
uv run mypy .

# Linting
uv run ruff .

# Start DevUI for manual testing
uv run app
```

Expected outputs:
- pytest: All tests pass, no failures
- mypy: Success: no issues found
- ruff: All checks passed
- DevUI: Workflow executes successfully with coordinator routing visible

### Observable Outcomes

After implementation, developers can:

1. **Create handoff workflows with automatic coordinator:**

```python
workflow = with_auto_coordinator(
    HandoffBuilder(
        name="My Workflow",
        participants=[agent1, agent2, agent3],
    ),
    client=client,
    coordinator_name="My Coordinator",
).build()
```

The extension automatically:
- Extracts agent descriptions
- Creates coordinator agent with appropriate instructions
- Registers handoff tools for all specialists
- Configures coordinator as starting agent

2. **See coordinator making routing decisions** via handoff tool invocations in DevUI

3. **Experience automatic user input pattern** - workflow requests user input after each specialist

4. **Customize termination conditions** via `.with_termination_condition()`

5. **Leverage framework-native patterns** - no custom routing executors needed

## Validation and Acceptance

### Acceptance Criteria

The implementation is complete when:

1. **with_auto_coordinator extension exists** at `src/spec_to_agents/workflow/handoff_extensions.py`
2. **Coordinator prompt template exists** at `src/spec_to_agents/prompts/coordinator.py`
3. **Event planning workflow refactored** in `src/spec_to_agents/workflow/core.py` to use HandoffBuilder
4. **Obsolete code removed**:
   - `src/spec_to_agents/workflow/supervisor.py` deleted
   - `src/spec_to_agents/agents/supervisor.py` deleted
   - `src/spec_to_agents/prompts/supervisor.py` deleted
   - `SupervisorDecision` model removed from `models/messages.py`
5. **Tests updated**: New tests for HandoffBuilder pattern, old supervisor tests removed
6. **All tests pass**: `uv run pytest tests/` completes without errors
7. **Type checking passes**: `uv run mypy .` reports no errors
8. **Linting passes**: `uv run ruff .` reports no issues
9. **DevUI integration works**: Workflow executes end-to-end with visible coordinator handoff routing
10. **Documentation updated**: `CLAUDE.md` reflects HandoffBuilder architecture

### DevUI Testing Scenario

Start the DevUI:

```bash
uv run app
```

Navigate to http://localhost:8000 in browser. Select "Event Planning Workflow" and submit test prompt:

```
"Plan a corporate holiday party for 50 people in Seattle on December 15th"
```

Expected observable behavior:
1. Coordinator receives initial request
2. Coordinator analyzes and invokes handoff tool (e.g., `handoff_to_venue`)
3. Venue specialist responds with venue options
4. Workflow automatically requests user input
5. User provides more input ("That looks good, what about budget?")
6. Coordinator invokes `handoff_to_budget`
7. Budget analyst provides cost breakdown
8. Workflow requests user input again
9. Continue until user says "that's all" or 10 messages reached
10. Workflow yields final comprehensive plan

Verify in DevUI:
- Handoff tool invocations visible in message history
- Each specialist responds with domain-specific analysis
- User input requested automatically after each specialist
- Final output is cohesive event plan

## Idempotence and Recovery

This implementation is idempotent and safe:

- **File creation**: New files can be created multiple times (overwrite with same content)
- **File deletion**: Deleting already-deleted files is idempotent via git
- **Refactoring**: Replacing code is a clean substitution
- **Tests**: Can be run repeatedly without side effects
- **DevUI testing**: Each workflow execution is independent

If implementation fails midway:
1. Check which files were created/modified: `git status`
2. Review changes: `git diff`
3. Either complete remaining files or revert: `git checkout .` or `git reset --hard`
4. Re-run tests to identify failures: `uv run pytest tests/ -v`
5. Check for import errors: `uv run python -c "from spec_to_agents.workflow.core import build_event_planning_workflow"`

## Artifacts and Notes

### Key Architectural Changes

**Before (SupervisorWorkflowBuilder):**
```python
workflow = (
    SupervisorWorkflowBuilder(
        name="Event Planning Workflow",
        client=client,
    )
    .participants(venue=venue, budget=budget, catering=catering, logistics=logistics)
    .build()
)
# Internally:
# - Creates SupervisorOrchestratorExecutor
# - Supervisor makes routing decisions via SupervisorDecision structured output
# - Manual HITL via ctx.request_info() when user_input_needed=True
```

**After (HandoffBuilder + Extension):**
```python
workflow = with_auto_coordinator(
    HandoffBuilder(
        name="Event Planning Workflow",
        participants=[venue, budget, catering, logistics],
    ),
    client=client,
    coordinator_name="Event Planning Coordinator",
).build()
# Internally:
# - Uses _HandoffCoordinator (framework built-in)
# - Coordinator routes via handoff tool invocations
# - Automatic HITL via _UserInputGateway after each specialist
```

**Benefits:**
- Leverage framework-native patterns (less custom code)
- Automatic handoff tool synthesis and middleware interception
- Proven conversation management via _HandoffCoordinator
- Automatic user input pattern (no manual HITL logic)
- Cleaner separation: coordinator decides, framework routes

### Migration Risk Assessment

**Low Risk Areas:**
- Extension method pattern is non-invasive
- HandoffBuilder is well-tested framework code
- Automatic user input pattern simplifies HITL logic

**Medium Risk Areas:**
- Extension accesses HandoffBuilder private attributes (`_executors`, `_aliases`)
- If Agent Framework changes these internals, extension breaks
- Mitigation: Clear warnings in code comments, runtime checks

**High Risk Areas:**
- None identified - this is a straightforward replacement with framework-native patterns

### Performance Considerations

**HandoffBuilder vs SupervisorWorkflowBuilder:**
- HandoffBuilder maintains full conversation in all agents (vs. global + service-managed threads)
- May increase token usage for long conversations
- Mitigation: Use termination conditions to prevent runaway conversations
- Trade-off: Simpler architecture worth slight token cost increase

### Alternative Approaches Considered

1. **Subclass HandoffBuilder**: Rejected - extension method more flexible and less coupling
2. **Wrap HandoffBuilder**: Rejected - unnecessary abstraction layer
3. **Keep both builders**: Rejected - user requested big bang replacement
4. **Reimplement handoff pattern**: Rejected - framework provides proven implementation

## Interfaces and Dependencies

### Module Dependencies

**New module** `src/spec_to_agents/workflow/handoff_extensions.py` depends on:
- `agent_framework`: `BaseChatClient`, `ChatAgent`, `HandoffBuilder`
- `spec_to_agents.prompts.coordinator`: `COORDINATOR_SYSTEM_PROMPT_TEMPLATE`

**New module** `src/spec_to_agents/prompts/coordinator.py`:
- No dependencies (just string template)

**Updated module** `src/spec_to_agents/workflow/core.py` depends on:
- `agent_framework`: `Workflow`, `BaseChatClient`, `HandoffBuilder`
- `spec_to_agents.workflow.handoff_extensions`: `with_auto_coordinator`
- `spec_to_agents.agents.*`: Agent factory functions

### Type Signatures

**with_auto_coordinator:**

```python
def with_auto_coordinator(
    builder: HandoffBuilder,
    *,
    client: BaseChatClient,
    coordinator_name: str | None = None,
    coordinator_instructions_template: str | None = None,
    **agent_kwargs: Any,
) -> HandoffBuilder: ...
```

**build_event_planning_workflow:**

```python
@inject
def build_event_planning_workflow(
    client: BaseChatClient = Provide["client"],
) -> Workflow: ...
```

### Breaking Changes

**Public API Changes:**
- `SupervisorWorkflowBuilder` removed (breaking)
- `SupervisorOrchestratorExecutor` removed (breaking)
- `SupervisorDecision` model removed (breaking)

**Migration Path for External Consumers:**
Replace:
```python
from spec_to_agents.workflow import SupervisorWorkflowBuilder
workflow = SupervisorWorkflowBuilder(...).build()
```

With:
```python
from agent_framework import HandoffBuilder
from spec_to_agents.workflow import with_auto_coordinator

workflow = with_auto_coordinator(
    HandoffBuilder(participants=[...]),
    client=client,
).build()
```

**Note**: This project is early-stage, so no external consumers expected. Breaking changes are acceptable per user decision (big bang replacement).
