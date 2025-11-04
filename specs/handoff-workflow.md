# Handoff Workflow Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `specs/PLANS.md` (from repository root).

## Purpose / Big Picture

Replace the custom SupervisorWorkflowBuilder implementation with an **AutoHandoffBuilder** subclass of Microsoft Agent Framework's HandoffBuilder. The AutoHandoffBuilder extends HandoffBuilder to automatically create a coordinator agent from participant descriptions when `.set_coordinator()` is not called, preserving the valuable auto-configuration logic from SupervisorWorkflowBuilder.

After implementation, the event planning workflow will use HandoffBuilder's proven handoff mechanism (tool-based routing with middleware interception) with automatic coordinator creation, eliminating boilerplate coordinator setup code.

## Progress

- [ ] Create AutoHandoffBuilder subclass with auto-coordinator logic
- [ ] Create coordinator prompt template module
- [ ] Refactor build_event_planning_workflow to use AutoHandoffBuilder
- [ ] Remove SupervisorWorkflowBuilder and SupervisorOrchestratorExecutor
- [ ] Remove SupervisorDecision model (no longer needed)
- [ ] Update tests to use AutoHandoffBuilder pattern
- [ ] Update CLAUDE.md documentation
- [ ] Validate workflow E2E via DevUI and console.py

## Surprises & Discoveries

(To be filled during implementation)

## Decision Log

- **Decision**: Use HandoffBuilder instead of SupervisorWorkflowBuilder
  **Rationale**: HandoffBuilder is built-in to Agent Framework with proven handoff tool synthesis, middleware interception, and conversation management. Reduces custom code maintenance burden.
  **Date/Author**: 2025-01-04 / User requirement

- **Decision**: Create AutoHandoffBuilder subclass that auto-creates coordinator if `.set_coordinator()` not called
  **Rationale**: Stay true to HandoffBuilder conventions while adding auto-coordinator feature. Subclass is cleaner than monkey patching and easier to maintain than wrapper pattern. Coordinator is NOT included in participants list when auto-created.
  **Date/Author**: 2025-01-04 / User requirement

- **Decision**: Adopt HandoffBuilder's automatic user input pattern
  **Rationale**: Framework's built-in pattern (request input after every specialist) is battle-tested and eliminates need for custom human-in-the-loop logic in coordinator.
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

Microsoft Agent Framework provides **HandoffBuilder** (built-in, located at `.venv/lib/python3.13/site-packages/agent_framework/_workflows/_handoff.py`) which:
- Uses handoff tools (e.g., `handoff_to_refund_agent`) for routing
- Automatically synthesizes handoff tools and intercepts them via middleware
- Maintains full conversation history via `_HandoffCoordinator`
- Requests user input automatically after each specialist response
- Supports termination conditions

The migration will create **AutoHandoffBuilder** (subclass of HandoffBuilder) that automatically creates coordinator when `.set_coordinator()` is not called.

## Plan of Work

### 1. Create AutoHandoffBuilder Subclass

**File**: `src/spec_to_agents/workflow/auto_handoff.py` (new file)

Create AutoHandoffBuilder subclass that auto-creates coordinator from participant descriptions:

```python
"""AutoHandoffBuilder - HandoffBuilder with automatic coordinator creation."""

from typing import Any

from agent_framework import BaseChatClient, ChatAgent, Workflow
from agent_framework._workflows._handoff import HandoffBuilder


class AutoHandoffBuilder(HandoffBuilder):
    """
    Extended HandoffBuilder that automatically creates a coordinator agent if not explicitly set.

    This builder extends HandoffBuilder to eliminate boilerplate coordinator setup by:
    1. Accepting a `client` parameter for creating the coordinator agent
    2. Auto-generating a coordinator from participant descriptions if `.set_coordinator()` not called
    3. Maintaining HandoffBuilder's fluent API and conventions

    Key Differences from HandoffBuilder:
    - Accepts `client` parameter in __init__ for auto-coordinator creation
    - If `.set_coordinator()` is NOT called before `.build()`, automatically creates coordinator
    - Auto-created coordinator is NOT included in participants list
    - Coordinator gets handoff tools for all participants
    - Coordinator instructions generated from participant descriptions

    Usage Patterns:

    **Auto-Coordinator (Recommended):**

    >>> workflow = AutoHandoffBuilder(
    ...     name="Event Planning",
    ...     participants=[venue, budget, catering, logistics],  # No coordinator!
    ...     client=client,  # Required for auto-creation
    ... ).build()  # Coordinator created automatically as "Event Planning Coordinator"

    **Manual Coordinator (Same as HandoffBuilder):**

    >>> coordinator = client.create_agent(name="coordinator", ...)
    >>> workflow = AutoHandoffBuilder(
    ...     participants=[coordinator, venue, budget, catering],
    ...     # No client needed when using explicit coordinator
    ... ).set_coordinator("coordinator").build()  # Explicit coordinator

    **With Custom Coordinator Name:**

    >>> workflow = AutoHandoffBuilder(
    ...     name="Support",
    ...     participants=[tier1, tier2, escalation],
    ...     client=client,
    ...     coordinator_name="Support Triage Agent",  # Custom name
    ... ).build()

    Parameters
    ----------
    client : BaseChatClient, optional
        Chat client for creating coordinator agent. Required ONLY if you want auto-coordinator
        feature (i.e., not calling .set_coordinator()). If you call .set_coordinator()
        manually, client is not needed. Defaults to None.
    coordinator_name : str, optional
        Name for auto-created coordinator. Defaults to "{name} Coordinator".
        Only used if .set_coordinator() not called.
    coordinator_instructions_template : str, optional
        Custom prompt template for coordinator. Must include {coordinator_name} and
        {participants_description} placeholders. If not provided, uses default template.
    **kwargs : Any
        All other HandoffBuilder parameters (name, participants, description)

    Raises
    ------
    ValueError
        If .set_coordinator() not called AND client not provided in __init__
    """

    def __init__(
        self,
        *,
        client: BaseChatClient | None = None,
        coordinator_name: str | None = None,
        coordinator_instructions_template: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize AutoHandoffBuilder with optional client for auto-coordinator."""
        super().__init__(**kwargs)
        self._client = client
        self._coordinator_name_override = coordinator_name
        self._coordinator_instructions_template = coordinator_instructions_template

    def build(self) -> Workflow:
        """
        Build workflow, auto-creating coordinator if not explicitly set.

        Returns
        -------
        Workflow
            Configured workflow ready for execution

        Raises
        ------
        ValueError
            If coordinator not set AND client not provided
        """
        # Check if coordinator was explicitly set
        if self._starting_agent_id is None:
            # No coordinator set - create automatically
            if self._client is None:
                raise ValueError(
                    "AutoHandoffBuilder requires 'client' parameter in __init__ to auto-create coordinator. "
                    "Either provide client=... or call .set_coordinator() manually."
                )

            # Auto-create coordinator from participants
            self._auto_create_coordinator()

        # Call parent build() method
        return super().build()

    def _auto_create_coordinator(self) -> None:
        """Create coordinator agent from participant descriptions and configure builder."""
        if not self._executors:
            raise ValueError(
                "Cannot auto-create coordinator with no participants. "
                "Call .participants([...]) before .build()."
            )

        # Extract participant descriptions for coordinator instructions
        participant_descriptions = []
        for exec_id, executor in self._executors.items():
            # Get agent from executor
            agent = getattr(executor, '_agent', None)
            if agent:
                name = getattr(agent, 'name', exec_id)
                description = getattr(agent, 'description', None)
                if description is None:
                    # Fallback: use first line of instructions
                    instructions = getattr(getattr(agent, 'chat_options', None), 'instructions', None)
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
        coordinator_name = self._coordinator_name_override
        if coordinator_name is None:
            if self._name:
                coordinator_name = f"{self._name} Coordinator"
            else:
                coordinator_name = "Coordinator"

        # Build coordinator instructions
        if self._coordinator_instructions_template:
            instructions = self._coordinator_instructions_template.format(
                coordinator_name=coordinator_name,
                participants_description=participants_description,
            )
        else:
            # Use default template
            from spec_to_agents.prompts.coordinator import COORDINATOR_SYSTEM_PROMPT_TEMPLATE
            instructions = COORDINATOR_SYSTEM_PROMPT_TEMPLATE.format(
                coordinator_name=coordinator_name,
                participants_description=participants_description,
            )

        # Create coordinator agent
        coordinator = self._client.create_agent(  # type: ignore[union-attr]
            name=coordinator_name.lower().replace(' ', '_'),
            description=coordinator_name,
            instructions=instructions,
            store=True,  # Use service-managed threads
        )

        # Register coordinator and set as starting agent
        # Note: coordinator is NOT in original participants list
        current_participants = list(self._executors.values())
        all_participants = [coordinator] + current_participants
        self.participants(all_participants)
        self.set_coordinator(coordinator)


__all__ = ["AutoHandoffBuilder"]
```

**Key Design Decisions**:
- Subclass pattern (clean inheritance, no monkey patching)
- Client passed in `__init__` for auto-coordinator creation
- Auto-coordinator only created if `.set_coordinator()` NOT called
- Coordinator NOT included in original participants list
- Falls back to manual coordinator if `.set_coordinator()` called explicitly

### 2. Create Coordinator Prompt Template

**File**: `src/spec_to_agents/prompts/coordinator.py` (new file)

Create prompt template for auto-generated coordinator agents:

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

Replace SupervisorWorkflowBuilder usage with AutoHandoffBuilder:

```python
"""Event planning multi-agent workflow definition."""

from agent_framework import Workflow, BaseChatClient
from dependency_injector.wiring import inject, Provide

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

    Architecture:
    - Coordinator agent routes to specialists via handoff tools (auto-created from descriptions)
    - HandoffBuilder automatically synthesizes handoff tools and intercepts invocations
    - Full conversation history maintained by _HandoffCoordinator
    - User input automatically requested after each specialist response
    - Termination condition: stops after 10 user messages (default, customizable)

    Handoff Flow:
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
    workflow = AutoHandoffBuilder(
        name="Event Planning Workflow",
        participants=[venue_agent, budget_agent, catering_agent, logistics_agent],
        description="Multi-agent event planning with coordinator orchestration",
        client=client,  # Required for auto-coordinator creation
        coordinator_name="Event Planning Coordinator",  # Optional: customize name
    ).build()

    return workflow
```

**Key Changes**:
- Replaced `SupervisorWorkflowBuilder` with `AutoHandoffBuilder`
- Pass `client` parameter for auto-coordinator creation
- No coordinator in participants list
- No `.set_coordinator()` call (happens automatically)
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

Keep `HumanFeedbackRequest` and `SpecialistOutput` (may be used for future enhancements).

**File**: `src/spec_to_agents/agents/supervisor.py`

**Action**: Delete entire file (no longer needed, coordinator created automatically)

**File**: `src/spec_to_agents/prompts/supervisor.py`

**Action**: Delete entire file (replaced by coordinator.py)

### 5. Update Module Exports

**File**: `src/spec_to_agents/workflow/__init__.py`

Update exports to include AutoHandoffBuilder:

```python
from spec_to_agents.workflow.core import build_event_planning_workflow, workflow
from spec_to_agents.workflow.auto_handoff import AutoHandoffBuilder

__all__ = [
    "build_event_planning_workflow",
    "workflow",
    "AutoHandoffBuilder",
]
```

### 6. Update Tests

**File**: `tests/workflow/test_auto_handoff.py` (new file, replaces supervisor tests)

Create tests for AutoHandoffBuilder:

```python
"""Tests for AutoHandoffBuilder with automatic coordinator creation."""

import pytest
from unittest.mock import MagicMock

from agent_framework import RequestInfoEvent, WorkflowOutputEvent
from spec_to_agents.workflow.auto_handoff import AutoHandoffBuilder


class TestAutoHandoffBuilder:
    """Test AutoHandoffBuilder auto-coordinator feature."""

    def test_auto_creates_coordinator_when_not_set(self):
        """Test that AutoHandoffBuilder auto-creates coordinator if not explicitly set."""
        # Mock client
        mock_client = MagicMock()
        mock_coordinator = MagicMock()
        mock_coordinator.name = "event_planning_coordinator"
        mock_client.create_agent.return_value = mock_coordinator

        # Mock participant agents
        venue_agent = MagicMock()
        venue_agent.name = "venue"
        venue_agent.description = "Finds event venues"

        budget_agent = MagicMock()
        budget_agent.name = "budget"
        budget_agent.description = "Analyzes budgets"

        # Build workflow without calling .set_coordinator()
        builder = AutoHandoffBuilder(
            name="Event Planning",
            participants=[venue_agent, budget_agent],
            client=mock_client,
        )

        # Should not raise - coordinator created automatically
        workflow = builder.build()

        # Verify coordinator agent was created
        mock_client.create_agent.assert_called_once()
        call_kwargs = mock_client.create_agent.call_args[1]

        # Check instructions contain participant descriptions
        assert "venue" in call_kwargs["instructions"]
        assert "budget" in call_kwargs["instructions"]
        assert "Finds event venues" in call_kwargs["instructions"]
        assert "Analyzes budgets" in call_kwargs["instructions"]

    def test_requires_client_for_auto_coordinator(self):
        """Test that AutoHandoffBuilder requires client if coordinator not set."""
        venue_agent = MagicMock()
        venue_agent.name = "venue"

        builder = AutoHandoffBuilder(
            name="Test",
            participants=[venue_agent],
            # No client provided
        )

        with pytest.raises(ValueError, match="requires 'client' parameter"):
            builder.build()

    def test_manual_coordinator_still_works(self):
        """Test that explicit .set_coordinator() still works (HandoffBuilder behavior)."""
        coordinator = MagicMock()
        coordinator.name = "coordinator"

        venue_agent = MagicMock()
        venue_agent.name = "venue"

        # Explicitly set coordinator (should NOT auto-create)
        # No client needed when using explicit coordinator
        builder = AutoHandoffBuilder(
            participants=[coordinator, venue_agent],
        ).set_coordinator("coordinator")

        workflow = builder.build()

        # Should build successfully without client

    def test_custom_coordinator_name(self):
        """Test custom coordinator_name parameter."""
        mock_client = MagicMock()
        mock_coordinator = MagicMock()
        mock_coordinator.name = "custom_coordinator"
        mock_client.create_agent.return_value = mock_coordinator

        venue_agent = MagicMock()
        venue_agent.name = "venue"

        builder = AutoHandoffBuilder(
            participants=[venue_agent],
            client=mock_client,
            coordinator_name="Custom Coordinator",
        )

        workflow = builder.build()

        # Verify custom name used
        call_kwargs = mock_client.create_agent.call_args[1]
        assert "Custom Coordinator" in call_kwargs["instructions"]
```

**File**: `tests/workflow/test_supervisor_unit.py`

**Action**: Delete file (replaced by test_auto_handoff.py)

**File**: `tests/workflow/test_supervisor_integration.py`

**Action**: Delete file (E2E tests via DevUI and console.py)

### 7. Update Documentation

**File**: `CLAUDE.md`

Update the Architecture section to reflect AutoHandoffBuilder usage:

Replace the entire "Workflow Architecture" section with:

```markdown
## Workflow Architecture

**Handoff Pattern with Auto-Coordinator:**
```
User Request
    ↓
Event Planning Coordinator (auto-created from descriptions)
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

1. **AutoHandoffBuilder**: Extends HandoffBuilder to automatically create coordinator from specialist descriptions
2. **Handoff Tool Routing**: Coordinator invokes handoff tools (e.g., `handoff_to_venue`) to transfer control
3. **Full Conversation History**: All agents receive complete conversation via `_HandoffCoordinator`
4. **Automatic User Input**: Framework requests user input after each specialist responds (cyclical flow)
5. **Termination Condition**: Workflow stops after 10 user messages (default, customizable)
```

Update the "Key Implementation Patterns" section:

```markdown
## Key Implementation Patterns

### 1. AutoHandoffBuilder with Auto-Coordinator

The workflow uses AutoHandoffBuilder for automatic coordinator creation:

```python
workflow = AutoHandoffBuilder(
    name="Event Planning Workflow",
    participants=[venue, budget, catering, logistics],  # No coordinator!
    client=client,  # Required for auto-creation
).build()  # Coordinator automatically created
```

**Benefits:**
- No manual coordinator agent creation
- Coordinator instructions generated from participant descriptions
- Clean fluent API
- Falls back to manual coordinator if `.set_coordinator()` called

**Code Location:** `src/spec_to_agents/workflow/auto_handoff.py:19-205`
```

Remove all references to:
- `SupervisorWorkflowBuilder`
- `SupervisorOrchestratorExecutor`
- `SupervisorDecision`
- Supervisor pattern

## Validation and Acceptance

### Acceptance Criteria

The implementation is complete when:

1. **AutoHandoffBuilder exists** at `src/spec_to_agents/workflow/auto_handoff.py`
2. **Coordinator prompt template exists** at `src/spec_to_agents/prompts/coordinator.py`
3. **Event planning workflow refactored** in `src/spec_to_agents/workflow/core.py` to use AutoHandoffBuilder
4. **Obsolete code removed**:
   - `src/spec_to_agents/workflow/supervisor.py` deleted
   - `src/spec_to_agents/agents/supervisor.py` deleted
   - `src/spec_to_agents/prompts/supervisor.py` deleted
   - `SupervisorDecision` model removed from `models/messages.py`
5. **Tests updated**: New tests for AutoHandoffBuilder pattern, old supervisor tests removed
6. **All tests pass**: `uv run pytest tests/` completes without errors
7. **Type checking passes**: `uv run mypy .` reports no errors
8. **Linting passes**: `uv run ruff .` reports no issues
9. **DevUI integration works**: Workflow executes end-to-end with visible coordinator handoff routing
10. **Documentation updated**: `CLAUDE.md` reflects AutoHandoffBuilder architecture

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
workflow = AutoHandoffBuilder(
    name="My Workflow",
    participants=[agent1, agent2, agent3],
    client=client,
).build()
```

The builder automatically:
- Extracts agent descriptions
- Creates coordinator agent with appropriate instructions
- Registers handoff tools for all specialists
- Configures coordinator as starting agent

2. **Or use manual coordinator (HandoffBuilder behavior):**

```python
coordinator = client.create_agent(name="coordinator", ...)
workflow = AutoHandoffBuilder(
    participants=[coordinator, agent1, agent2],
    # No client needed when using explicit coordinator
).set_coordinator("coordinator").build()
```

3. **See coordinator making routing decisions** via handoff tool invocations in DevUI

4. **Experience automatic user input pattern** - workflow requests user input after each specialist

5. **Customize termination conditions** via `.with_termination_condition()`

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
workflow = SupervisorWorkflowBuilder(
    name="Event Planning Workflow",
    client=client,
).participants(
    venue=venue, budget=budget, catering=catering, logistics=logistics
).build()
```

**After (AutoHandoffBuilder):**
```python
workflow = AutoHandoffBuilder(
    name="Event Planning Workflow",
    participants=[venue, budget, catering, logistics],
    client=client,
).build()
```

**Benefits:**
- Leverage framework-native HandoffBuilder patterns
- Automatic handoff tool synthesis and middleware interception
- Proven conversation management via `_HandoffCoordinator`
- Automatic user input pattern (no manual human-in-the-loop logic)
- Cleaner API (coordinator NOT in participants list)

### Migration Risk Assessment

**Low Risk Areas:**
- Subclass pattern is clean and maintainable
- HandoffBuilder is well-tested framework code
- Automatic user input pattern simplifies human-in-the-loop logic

**Medium Risk Areas:**
- AutoHandoffBuilder accesses HandoffBuilder private attributes (`_executors`, `_starting_agent_id`)
- If Agent Framework changes these internals, AutoHandoffBuilder may break
- Mitigation: Clear warnings in code comments, runtime checks, tests

**High Risk Areas:**
- None identified - this is a straightforward subclass with framework-native patterns

### Alternative Approaches Considered

1. **Monkey patch HandoffBuilder**: Rejected - fragile, breaks on package updates
2. **Wrapper pattern**: Rejected - unnecessary abstraction layer
3. **Keep both builders**: Rejected - user requested big bang replacement
4. **Extension function**: Rejected - subclass is cleaner and more pythonic

## Interfaces and Dependencies

### Module Dependencies

**New module** `src/spec_to_agents/workflow/auto_handoff.py` depends on:
- `agent_framework`: `BaseChatClient`, `ChatAgent`, `Workflow`, `HandoffBuilder`
- `spec_to_agents.prompts.coordinator`: `COORDINATOR_SYSTEM_PROMPT_TEMPLATE`

**New module** `src/spec_to_agents/prompts/coordinator.py`:
- No dependencies (just string template)

**Updated module** `src/spec_to_agents/workflow/core.py` depends on:
- `agent_framework`: `Workflow`, `BaseChatClient`
- `spec_to_agents.workflow.auto_handoff`: `AutoHandoffBuilder`
- `spec_to_agents.agents.*`: Agent factory functions

### Type Signatures

**AutoHandoffBuilder:**

```python
class AutoHandoffBuilder(HandoffBuilder):
    def __init__(
        self,
        *,
        client: BaseChatClient | None = None,
        coordinator_name: str | None = None,
        coordinator_instructions_template: str | None = None,
        **kwargs: Any,
    ) -> None: ...

    def build(self) -> Workflow: ...
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
workflow = SupervisorWorkflowBuilder(client=client, ...).participants(...).build()
```

With:
```python
from spec_to_agents.workflow import AutoHandoffBuilder
workflow = AutoHandoffBuilder(client=client, participants=[...]).build()
```

**Note**: This project is early-stage, so no external consumers expected. Breaking changes are acceptable per user decision (big bang replacement).
