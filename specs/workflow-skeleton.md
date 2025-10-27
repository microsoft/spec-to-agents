# Build Multi-Agent Event Planning Workflow Skeleton

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `specs/PLANS.md`.

## Purpose / Big Picture

This specification defines the implementation of a multi-agent workflow skeleton for event planning using the Microsoft Agent Framework. The workflow orchestrates five specialized agents (Event Coordinator, Venue Specialist, Budget Analyst, Catering Coordinator, and Logistics Manager) to collaboratively plan events.

After implementation, users will be able to:
1. Start the DevUI (`uv run devui`) and interact with the event planning workflow
2. Submit an event planning request (e.g., "Plan a corporate holiday party for 50 people with a budget of $5000")
3. Observe the workflow as it coordinates between agents to develop a comprehensive event plan
4. Receive a final, integrated event plan that includes venue recommendations, budget allocation, catering options, and logistics coordination

The workflow follows an orchestrated sequential pattern where the Event Coordinator acts as the primary orchestrator, delegating specialized tasks to other agents and synthesizing their outputs into a coherent plan.

## Progress

- [ ] Design workflow orchestration architecture
- [ ] Define system prompts for all five agents
- [ ] Create workflow builder implementation
- [ ] Update agent module structure to export workflow
- [ ] Create integration tests for workflow
- [ ] Validate workflow in DevUI

## Surprises & Discoveries

(To be populated during implementation)

## Decision Log

(To be populated during implementation)

## Outcomes & Retrospective

(To be populated at completion)

## Context and Orientation

### Current State

The project currently has:
- **Five agent files** under `src/spec2agent/agents/`:
  - `event_coordinator.py`
  - `venue_specialist.py`
  - `budget_analyst.py`
  - `catering_coordinator.py`
  - `logistics_manager.py`
- **Basic agent definitions** that use `get_chat_client().create_agent()`
- **Agent export mechanism** in `src/spec2agent/agents/__init__.py` with `export_entities()` function for DevUI discovery
- **Placeholder system prompts** in `src/spec2agent/prompts/*.py` (all currently "You are a helpful assistant")
- **Shared client code** in `src/spec2agent/clients.py` providing `get_chat_client()` and `get_credential()`
- **Empty workflow module** at `src/spec2agent/workflow/core.py`

### Architecture Overview

Based on the workflow architecture diagram in AGENTS.md, the system follows this pattern:

1. **User Input** → **Event Coordinator** (Orchestrator)
2. **Event Coordinator** → Delegates to specialists:
   - **Venue Specialist**: Researches and recommends venues
   - **Budget Analyst**: Manages costs and financial constraints
   - **Catering Coordinator**: Handles food and beverage planning
   - **Logistics Manager**: Coordinates schedules and resources
3. **Event Coordinator** → Synthesizes outputs → **Final Event Plan**

### Technology Stack

- **Agent Framework Core**: Multi-agent orchestration primitives
- **Agent Framework Azure AI**: `AzureAIAgentClient` for Azure AI Foundry integration
- **Agent Framework DevUI**: Web interface for testing workflows
- **Pydantic**: Data validation and settings management
- **Python 3.11+**: Modern Python features

### Key Framework Concepts

- **ChatAgent**: Individual agent with instructions (system prompt) and optional tools
- **WorkflowBuilder**: Constructs multi-agent workflows by adding agents and defining edges
- **AgentExecutor**: Wraps agents in the workflow execution context
- **Workflow.as_agent()**: Allows workflows to be exposed as single agents for composition

## Plan of Work

### Phase 1: System Prompt Design

Design comprehensive, role-specific system prompts for each of the five agents that enable effective collaboration in an orchestrated workflow.

**Event Coordinator Prompt** (`src/spec2agent/prompts/event_coordinator.py`):
- Define role as the primary orchestrator
- Specify responsibilities: gather requirements, delegate to specialists, synthesize results
- Include guidance on how to structure delegation messages
- Define output format for the final integrated event plan

**Venue Specialist Prompt** (`src/spec2agent/prompts/venue_specialist.py`):
- Define role as venue research and recommendation specialist
- Specify considerations: capacity, location, amenities, accessibility
- Define output format for venue recommendations (structured list with pros/cons)

**Budget Analyst Prompt** (`src/spec2agent/prompts/budget_analyst.py`):
- Define role as financial planning and cost management specialist
- Specify responsibilities: budget allocation, cost estimation, financial constraints
- Define output format for budget breakdowns (categorized allocation)

**Catering Coordinator Prompt** (`src/spec2agent/prompts/catering_coordinator.py`):
- Define role as food and beverage planning specialist
- Specify considerations: dietary restrictions, cuisine types, service style
- Define output format for catering recommendations

**Logistics Manager Prompt** (`src/spec2agent/prompts/logistics_manager.py`):
- Define role as scheduling and resource coordination specialist
- Specify responsibilities: timeline creation, vendor coordination, equipment needs
- Define output format for logistics plans

### Phase 2: Workflow Architecture Design

Design the workflow structure that implements the orchestration pattern shown in the architecture diagram.

**Workflow Pattern Decision**:
Based on Agent Framework patterns, choose between:
1. **Sequential with Coordinator**: Event Coordinator delegates to each specialist sequentially, gathering outputs
2. **Magentic-style Orchestration**: Event Coordinator uses dynamic delegation based on task progress
3. **Fan-out/Fan-in**: Event Coordinator fans out to all specialists in parallel, then aggregates

**Recommended Approach**: Sequential with Coordinator (most aligned with diagram and simplest to implement)

**Workflow Structure** (`src/spec2agent/workflow/core.py`):
- Create `build_event_planning_workflow()` function
- Initialize all five agents using their respective system prompts
- Use `WorkflowBuilder` to construct the workflow:
  - Set Event Coordinator as start executor
  - Add edges: Event Coordinator → Venue Specialist → Budget Analyst → Catering Coordinator → Logistics Manager → Event Coordinator (synthesis)
  - Configure Event Coordinator with `output_response=True` for final output
- Return `Workflow` instance

### Phase 3: Module Structure Updates

Update the agent module structure to align with DevUI discovery requirements.

**Agent Export Pattern** (per AGENTS.md):
The `src/spec2agent/agents/__init__.py` module uses an `export_entities()` function that returns a list of all agents/workflows for DevUI discovery.

**Workflow Integration**:
- Create a workflow variable in `src/spec2agent/workflow/core.py` that builds the complete event planning workflow
- Import and add the workflow to the `export_entities()` list in `src/spec2agent/agents/__init__.py`
- This makes the workflow discoverable alongside individual agents in DevUI

**Individual Agent Files**:
- Keep existing agent files (`event_coordinator.py`, `venue_specialist.py`, etc.)
- These remain available for standalone testing and as building blocks for the workflow
- Already exported via `export_entities()` for individual DevUI testing

### Phase 4: Shared State and Context

Design how agents share context and information during workflow execution.

**Context Passing Approach**:
- Use conversation history as implicit context (messages accumulate)
- Event Coordinator provides context in delegation messages
- Each specialist receives full conversation history
- Specialists can reference previous outputs in their responses

**Alternative (if needed)**:
- Use `SharedState` for explicit data passing
- Define Pydantic models in `src/spec2agent/models/` for structured data
- Examples: `VenueRecommendation`, `BudgetAllocation`, `CateringPlan`, `LogisticsPlan`

### Phase 5: Integration and Testing

Create tests and validation for the workflow.

**Unit Tests** (`tests/test_workflow.py`):
- Test workflow construction (no errors during build)
- Mock agent responses to test flow
- Validate that all agents are included in the workflow
- Test edge definitions

**Integration Tests** (`tests/test_workflow_integration.py`):
- Test full workflow execution with real AI Foundry calls (requires .env)
- Provide sample event planning requests
- Validate that final output includes contributions from all specialists
- Test error handling and edge cases

**DevUI Validation**:
- Start DevUI: `uv run devui`
- Navigate to Event Coordinator workflow
- Submit test requests
- Validate agent interactions and final outputs

## Concrete Steps

### Step 1: Design and Implement System Prompts

Navigate to the project root and update each system prompt file:

    cd c:\Users\alexlavaee\source\repos\spec-to-agents

Update `src/spec2agent/prompts/event_coordinator.py`:
- Define Event Coordinator as orchestrator role
- Include delegation strategy
- Specify synthesis approach for final plan

Update `src/spec2agent/prompts/venue_specialist.py`:
- Define Venue Specialist role and expertise
- Specify venue evaluation criteria
- Define recommendation format

Update `src/spec2agent/prompts/budget_analyst.py`:
- Define Budget Analyst role and expertise
- Specify budget breakdown categories
- Define allocation format

Update `src/spec2agent/prompts/catering_coordinator.py`:
- Define Catering Coordinator role and expertise
- Specify catering considerations
- Define recommendation format

Update `src/spec2agent/prompts/logistics_manager.py`:
- Define Logistics Manager role and expertise
- Specify coordination responsibilities
- Define logistics plan format

### Step 2: Implement Workflow Builder

Create the workflow builder in `src/spec2agent/workflow/core.py`:

Expected structure:

    from agent_framework.core import WorkflowBuilder
    from spec2agent.clients import get_chat_client
    from spec2agent.prompts import (
        event_coordinator,
        venue_specialist,
        budget_analyst,
        catering_coordinator,
        logistics_manager,
    )

    def build_event_planning_workflow():
        """Build the event planning multi-agent workflow."""
        client = get_chat_client()
        
        # Create agents
        coordinator = client.create_agent(
            name="EventCoordinator",
            instructions=event_coordinator.SYSTEM_PROMPT,
            store=True
        )
        
        # ... create other agents ...
        
        # Build workflow
        workflow = (
            WorkflowBuilder()
            .add_agent(coordinator, id="coordinator", output_response=True)
            .add_agent(venue_agent, id="venue")
            .add_agent(budget_agent, id="budget")
            .add_agent(catering_agent, id="catering")
            .add_agent(logistics_agent, id="logistics")
            .set_start_executor(coordinator)
            .add_edge(coordinator, venue_agent)
            .add_edge(venue_agent, budget_agent)
            .add_edge(budget_agent, catering_agent)
            .add_edge(catering_agent, logistics_agent)
            .add_edge(logistics_agent, coordinator)
            .build()
        )
        
        return workflow

### Step 3: Update Agent Module Exports

Update `src/spec2agent/workflow/core.py` to export the workflow as a module-level variable:

    from agent_framework.core import WorkflowBuilder, Workflow
    from spec2agent.clients import get_chat_client
    from spec2agent.prompts import (
        event_coordinator,
        venue_specialist,
        budget_analyst,
        catering_coordinator,
        logistics_manager,
    )

    def build_event_planning_workflow() -> Workflow:
        """Build the event planning multi-agent workflow."""
        # ... implementation ...
        return workflow

    # Export workflow instance for DevUI discovery
    workflow = build_event_planning_workflow()

Update `src/spec2agent/agents/__init__.py` to include the workflow in exports:

    from agent_framework import ChatAgent, Workflow

    from spec2agent.agents.budget_analyst import agent as budget_analyst_agent
    from spec2agent.agents.catering_coordinator import agent as catering_coordinator_agent
    from spec2agent.agents.event_coordinator import agent as event_coordinator_agent
    from spec2agent.agents.logistics_manager import agent as logistics_manager_agent
    from spec2agent.agents.venue_specialist import agent as venue_specialist_agent
    from spec2agent.workflow.core import workflow as event_planning_workflow

    def export_entities() -> list[Workflow | ChatAgent]:
        """Export all agents/workflows for registration in DevUI."""
        return [
            budget_analyst_agent,
            catering_coordinator_agent,
            event_coordinator_agent,
            logistics_manager_agent,
            venue_specialist_agent,
            event_planning_workflow,  # Add workflow to exports
        ]

This makes the workflow discoverable by DevUI alongside individual agents.

### Step 4: Create Tests

Create `tests/test_workflow.py`:

    import pytest
    from spec2agent.workflow.core import build_event_planning_workflow

    def test_workflow_builds_successfully():
        """Test that the workflow can be constructed without errors."""
        workflow = build_event_planning_workflow()
        assert workflow is not None

    def test_workflow_has_all_agents():
        """Test that all five agents are included in the workflow."""
        workflow = build_event_planning_workflow()
        # Add assertions to check agent presence

Create `tests/test_workflow_integration.py`:

    import pytest
    from spec2agent.workflow.core import build_event_planning_workflow

    @pytest.mark.asyncio
    async def test_workflow_execution():
        """Test full workflow execution with sample request."""
        workflow = build_event_planning_workflow()
        
        # Submit test request
        request = "Plan a corporate holiday party for 50 people with a $5000 budget"
        
        # Execute workflow
        result = await workflow.run(request)
        
        # Validate result contains expected sections
        assert "venue" in result.lower()
        assert "budget" in result.lower()
        assert "catering" in result.lower()
        assert "logistics" in result.lower()

Run tests:

    uv run pytest tests/test_workflow.py
    uv run pytest tests/test_workflow_integration.py

Expected output: All tests pass, confirming workflow construction and execution.

### Step 5: Validate in DevUI

Start the DevUI:

    uv run devui

Expected output:

    Starting Agent Framework DevUI...
    Server running at http://localhost:8000
    Open your browser to interact with agents

Navigate to `http://localhost:8000` in browser.

Expected behavior:
- DevUI loads successfully
- Event Coordinator workflow appears in the workflow list
- Can select workflow and submit test requests
- Workflow executes and shows agent interactions
- Final response includes integrated event plan

Test with sample request:

    Input: "Plan a team building event for 30 people in Seattle with a budget of $3000"
    
    Expected flow:
    1. Event Coordinator receives request
    2. Venue Specialist provides Seattle venue options
    3. Budget Analyst allocates $3000 across categories
    4. Catering Coordinator suggests food options
    5. Logistics Manager creates timeline
    6. Event Coordinator synthesizes final plan

## Validation and Acceptance

### Acceptance Criteria

The workflow skeleton implementation is complete when:

1. **System Prompts**: All five system prompts are comprehensive, role-specific, and enable effective collaboration
2. **Workflow Builder**: `build_event_planning_workflow()` successfully constructs a workflow with all five agents
3. **Module Structure**: Event Coordinator module exports `workflow` variable discoverable by DevUI
4. **Unit Tests**: `test_workflow.py` passes, confirming workflow construction
5. **Integration Tests**: `test_workflow_integration.py` passes, confirming end-to-end execution
6. **DevUI Validation**: Workflow appears in DevUI, accepts requests, orchestrates agents, and produces integrated output

### Observable Behaviors

**Unit Test Output**:

    $ uv run pytest tests/test_workflow.py -v
    
    tests/test_workflow.py::test_workflow_builds_successfully PASSED
    tests/test_workflow.py::test_workflow_has_all_agents PASSED
    
    ========== 2 passed in 1.23s ==========

**Integration Test Output**:

    $ uv run pytest tests/test_workflow_integration.py -v
    
    tests/test_workflow_integration.py::test_workflow_execution PASSED
    
    ========== 1 passed in 5.67s ==========

**DevUI Interaction**:

User submits: "Plan a corporate holiday party for 50 people with a budget of $5000"

Expected final response structure:

    # Corporate Holiday Party Plan

    ## Venue Recommendation
    [Venue Specialist output: venue options with capacity, location, cost]

    ## Budget Allocation
    [Budget Analyst output: categorized budget breakdown totaling $5000]

    ## Catering Plan
    [Catering Coordinator output: menu options, service style, dietary accommodations]

    ## Logistics & Timeline
    [Logistics Manager output: event timeline, vendor coordination, equipment needs]

    ## Summary
    [Event Coordinator synthesis: integrated recommendations and next steps]

## Idempotence and Recovery

### Safe Execution

- Workflow construction is stateless and can be called multiple times
- Agent creation uses consistent names and instructions
- Tests can be run repeatedly without side effects
- DevUI can be restarted without data loss (agents recreated on demand)

### Error Recovery

**If workflow construction fails**:
- Check agent client initialization in `clients.py`
- Validate Azure credentials: `az login` or check Managed Identity
- Verify environment variables in `.env` (if needed)
- Check Agent Framework package versions: `uv run pip list | grep agent-framework`

**If tests fail**:
- Ensure `.env` file exists with correct Azure AI Foundry configuration
- Validate network connectivity to Azure AI services
- Check test assertions match actual workflow structure
- Run tests with increased verbosity: `uv run pytest -vv`

**If DevUI doesn't show workflow**:
- Verify `src/spec2agent/agents/event_coordinator/__init__.py` exports `workflow`
- Check for Python syntax errors: `uv run ruff check src/`
- Restart DevUI: `uv run devui`
- Check DevUI console for discovery errors

### Rollback Strategy

To revert changes:
- System prompts: Restore placeholder prompts if needed
- Workflow code: Remove `workflow/core.py` implementation
- Module exports: Remove workflow export from `__init__.py`
- Tests: Delete or skip new test files

## Artifacts and Notes

### Key Design Decisions

**Sequential vs. Parallel Orchestration**:
- **Decision**: Use sequential orchestration with Event Coordinator as primary orchestrator
- **Rationale**: Matches architecture diagram, simpler to implement and debug, allows each agent to build on previous outputs
- **Alternative**: Fan-out/fan-in for parallel specialist execution (could be future enhancement)

**Workflow Location**:
- **Decision**: Export workflow instance from `workflow/core.py` and include in `agents/__init__.py` `export_entities()` list
- **Rationale**: Centralizes workflow definition in dedicated module while using standard DevUI discovery pattern
- **Alternative**: Export only from `workflow/` module (would require DevUI to scan multiple directories)

**Context Passing**:
- **Decision**: Use conversation history for context
- **Rationale**: Simplest approach, leverages Agent Framework's built-in message passing
- **Alternative**: SharedState with Pydantic models (could be added later if needed)

**Agent Names**:
- **Decision**: Use descriptive names: "EventCoordinator", "VenueSpecialist", etc.
- **Rationale**: Clear role identification in conversation history and DevUI
- **Format**: PascalCase for consistency

### System Prompt Design Principles

Each system prompt should include:

1. **Role Definition**: Clear statement of the agent's expertise and responsibilities
2. **Collaboration Context**: Awareness that the agent is part of a multi-agent workflow
3. **Input Expectations**: What information the agent should expect to receive
4. **Output Format**: Structured format for responses (bullet points, sections, etc.)
5. **Constraints**: What the agent should NOT do or assume
6. **Handoff Guidance**: How to conclude and hand back to coordinator

Example template structure:

    SYSTEM_PROMPT: Final[str] = """
    You are [Role Name], an expert in [domain].
    
    Your responsibilities:
    - [Responsibility 1]
    - [Responsibility 2]
    - [Responsibility 3]
    
    You are part of an event planning team. When you receive a request:
    1. [Step 1]
    2. [Step 2]
    3. [Step 3]
    
    Format your response as:
    [Expected format description]
    
    Constraints:
    - [Constraint 1]
    - [Constraint 2]
    
    Once you complete your analysis, provide your recommendations and indicate you are ready for the next step.
    """

### Workflow Architecture Notes

The workflow implements this pattern:

    User Request
        ↓
    Event Coordinator (initial processing)
        ↓
    Venue Specialist (venue recommendations)
        ↓
    Budget Analyst (budget allocation)
        ↓
    Catering Coordinator (catering plan)
        ↓
    Logistics Manager (logistics & timeline)
        ↓
    Event Coordinator (final synthesis)
        ↓
    Integrated Event Plan

Each arrow represents a workflow edge where:
- Previous agent's output is in conversation history
- Next agent receives full context
- Agents build incrementally on previous work

### Testing Strategy

**Unit Tests** focus on:
- Workflow construction without errors
- Agent presence validation
- Edge definition validation
- No actual AI calls (fast, deterministic)

**Integration Tests** focus on:
- Full workflow execution with AI Foundry
- Real agent interactions
- Output validation
- End-to-end behavior
- Requires valid Azure credentials

**DevUI Validation** focuses on:
- User experience
- Visual workflow representation
- Real-time interaction
- Agent conversation flow
- Final output quality

### Future Enhancements (Out of Scope)

These are NOT part of this specification but could be future work:

1. **Tool Integration**: Add tools for each specialist (venue search APIs, budget calculators, etc.)
2. **Shared State Models**: Pydantic models for structured data passing
3. **Parallel Execution**: Fan-out specialists for faster execution
4. **Human-in-the-Loop**: Add approval gates for budget or venue selection
5. **Memory Integration**: Use Mem0 for learning from past events
6. **Dynamic Routing**: Magentic-style orchestration based on task complexity
7. **Sub-workflows**: Make each specialist a mini-workflow
8. **Error Handling**: Retry logic, fallback strategies

## Interfaces and Dependencies

### Required Imports

In `src/spec2agent/workflow/core.py`:

    from agent_framework.core import WorkflowBuilder, Workflow
    from spec2agent.clients import get_chat_client
    from spec2agent.prompts import (
        event_coordinator,
        venue_specialist,
        budget_analyst,
        catering_coordinator,
        logistics_manager,
    )

### Function Signature

    def build_event_planning_workflow() -> Workflow:
        """
        Build the multi-agent event planning workflow.
        
        The workflow orchestrates five specialized agents:
        - Event Coordinator: Primary orchestrator and synthesizer
        - Venue Specialist: Venue research and recommendations
        - Budget Analyst: Financial planning and allocation
        - Catering Coordinator: Food and beverage planning
        - Logistics Manager: Scheduling and resource coordination
        
        Returns
        -------
        Workflow
            Configured workflow instance ready for execution via DevUI
            or programmatic invocation.
        
        Notes
        -----
        The workflow uses sequential orchestration where the Event Coordinator
        delegates to each specialist in sequence, then synthesizes the final plan.
        
        Requires Azure AI Foundry credentials configured via environment variables
        or Azure CLI authentication.
        """
        ...

### Module Exports

In `src/spec2agent/workflow/core.py`:

    # Export workflow instance for DevUI discovery
    workflow = build_event_planning_workflow()
    
    __all__ = ["build_event_planning_workflow", "workflow"]

In `src/spec2agent/agents/__init__.py`:

    from spec2agent.workflow.core import workflow as event_planning_workflow
    
    def export_entities() -> list[Workflow | ChatAgent]:
        """Export all agents/workflows for registration in DevUI."""
        return [
            budget_analyst_agent,
            catering_coordinator_agent,
            event_coordinator_agent,
            logistics_manager_agent,
            venue_specialist_agent,
            event_planning_workflow,
        ]

### System Prompt Variables

Each prompt file in `src/spec2agent/prompts/` must export:

    from typing import Final
    
    SYSTEM_PROMPT: Final[str] = """
    [Comprehensive system prompt content]
    """
    
    __all__ = ["SYSTEM_PROMPT"]

### Test Fixtures

In `tests/conftest.py` (if needed):

    import pytest
    from spec2agent.workflow.core import build_event_planning_workflow

    @pytest.fixture
    def event_workflow():
        """Fixture providing the event planning workflow."""
        return build_event_planning_workflow()

## Dependencies and Prerequisites

### Python Packages

All required packages are already in `pyproject.toml`:
- `agent-framework-core`: Core workflow and agent primitives
- `agent-framework-azure-ai`: Azure AI Foundry client
- `agent-framework-devui`: DevUI for testing
- `azure-identity`: Authentication
- `python-dotenv`: Environment configuration (if needed)

### Azure Configuration

Requires one of:
1. **Azure CLI**: User authenticated via `az login`
2. **Managed Identity**: When deployed to Azure Container Apps
3. **Environment Variables**: (if using API keys, though project prefers managed identity)

### File Structure

After implementation, the structure should be:

    src/spec2agent/
    ├── clients.py                    (existing, no changes)
    ├── workflow/
    │   ├── __init__.py              (existing, no changes)
    │   └── core.py                  (implement workflow builder + export workflow instance)
    ├── prompts/
    │   ├── event_coordinator.py     (update SYSTEM_PROMPT)
    │   ├── venue_specialist.py      (update SYSTEM_PROMPT)
    │   ├── budget_analyst.py        (update SYSTEM_PROMPT)
    │   ├── catering_coordinator.py  (update SYSTEM_PROMPT)
    │   └── logistics_manager.py     (update SYSTEM_PROMPT)
    └── agents/
        ├── __init__.py              (update export_entities() to include workflow)
        ├── event_coordinator.py     (existing, no changes)
        ├── venue_specialist.py      (existing, no changes)
        ├── budget_analyst.py        (existing, no changes)
        ├── catering_coordinator.py  (existing, no changes)
        └── logistics_manager.py     (existing, no changes)

    tests/
    ├── test_workflow.py             (create unit tests)
    └── test_workflow_integration.py (create integration tests)

---

## Implementation Checklist

Before starting implementation, review:
- [x] Agent Framework documentation on workflows (via DeepWiki)
- [x] Current project structure and existing code
- [x] AGENTS.md architecture diagrams
- [ ] System prompt design principles
- [ ] Testing strategy

During implementation:
- [ ] Update all five system prompts with comprehensive, role-specific content
- [ ] Implement `build_event_planning_workflow()` in `workflow/core.py`
- [ ] Export workflow instance as module-level variable in `workflow/core.py`
- [ ] Update `agents/__init__.py` to include workflow in `export_entities()`
- [ ] Create unit tests in `test_workflow.py`
- [ ] Create integration tests in `test_workflow_integration.py`
- [ ] Run all tests and ensure they pass
- [ ] Start DevUI and validate workflow discovery
- [ ] Submit test requests and validate workflow orchestration
- [ ] Document any discoveries in "Surprises & Discoveries"
- [ ] Record design decisions in "Decision Log"

After implementation:
- [ ] Run full test suite: `uv run pytest`
- [ ] Run linting: `uv run ruff check src/ tests/`
- [ ] Run formatting: `uv run ruff format src/ tests/`
- [ ] Validate DevUI end-to-end with multiple test cases
- [ ] Update Progress section with completion timestamps
- [ ] Write Outcomes & Retrospective summary
- [ ] Update `specs/README.md` to link to this specification

---

**Specification Version**: 1.0  
**Created**: 2025-10-24  
**Status**: Draft - Ready for Review and Implementation
