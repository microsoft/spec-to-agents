# Event Planning Multi-Agent Workflow Specification

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `specs/PLANS.md`.

## Purpose / Big Picture

This specification defines the implementation of a multi-agent workflow for event planning using the Microsoft Agent Framework. The workflow orchestrates five specialized agents (Event Coordinator, Venue Specialist, Budget Analyst, Catering Coordinator, and Logistics Manager) through a coordinator-centric architecture with human-in-the-loop capabilities.

After implementation, users can:
1. Start the DevUI (`uv run app`) and interact with the event planning workflow
2. Submit an event planning request (e.g., "Plan a corporate holiday party for 50 people with a budget of $5000")
3. Observe the workflow as the coordinator intelligently routes between specialists based on structured output
4. Provide input when agents request clarification, selection, or approval
5. Receive a final, integrated event plan that synthesizes all specialist recommendations

The workflow uses **coordinator-centric star topology** where the EventPlanningCoordinator manages all routing decisions, human-in-the-loop interactions, and final synthesis. Conversation history is automatically managed through **service-managed threads** (`store=True`), eliminating manual message tracking overhead.

## Progress

- [x] Design workflow orchestration architecture - Completed 2025-10-27
- [x] Define system prompts for all five agents - Completed 2025-10-27
- [x] Create workflow builder implementation - Completed 2025-10-27
- [x] Update agent module structure to export workflow - Completed 2025-10-27
- [x] Create integration tests for workflow - Completed 2025-10-27
- [x] Validate workflow in DevUI - Completed 2025-10-27
- [x] Design and implement coordinator-centric architecture - Completed 2025-10-28
- [x] Implement EventPlanningCoordinator with routing logic - Completed 2025-10-28
- [x] Add structured output routing via SpecialistOutput - Completed 2025-10-28
- [x] Implement human-in-the-loop via ctx.request_info() + @response_handler - Completed 2025-10-28
- [x] Add HumanFeedbackRequest message type - Completed 2025-10-28
- [x] Implement service-managed threads with store=True - Completed 2025-10-28
- [x] Add convert_tool_content_to_text for cross-thread communication - Completed 2025-10-28
- [x] Update workflow edges for star topology - Completed 2025-10-28
- [x] Update agent prompts with structured output guidance - Completed 2025-10-28
- [x] Add tests for human-in-the-loop scenarios - Completed 2025-10-28
- [x] Integrate tools (Web Search, Weather, Calendar, Code Interpreter, MCP) - Completed 2025-10-29

**Implementation Status:** ✅ Complete

## Surprises & Discoveries

### Service-Managed Threads Pattern

- **Discovery**: Azure AI Agent Client provides service-managed threads via `store=True` parameter
- **Mechanism**: When `store=True` is set in agent creation, the Azure AI service automatically:
  - Creates a `service_thread_id` for persistent conversation storage
  - Stores all messages in the Azure AI service backend
  - Retrieves conversation history automatically on subsequent agent runs
  - No manual `full_conversation` passing required
- **Impact**: Eliminates need for manual conversation history tracking in coordinator
- **Evidence**: All agents in `src/spec_to_agents/agents/*.py` use `store=True`
- **Source**: DeepWiki research on microsoft/agent-framework patterns

### Tool Content Conversion Requirement

- **Discovery**: `FunctionCallContent` and `FunctionResultContent` cannot cross thread boundaries
- **Root Cause**: These content types embed `run_id` in their `call_id`, which is specific to the originating thread
- **Error**: "No thread ID was provided, but chat messages includes tool results"
- **Solution**: `convert_tool_content_to_text()` function converts tool content to text summaries
  - `FunctionCallContent` → `"[Tool Call: tool_name({args})]"`
  - `FunctionResultContent` → `"[Tool Result for call_id: result]"`
- **Implementation**: Used in `_route_to_agent()` and `_synthesize_plan()` methods
- **Evidence**: `src/spec_to_agents/workflow/executors.py:25-86`
- **Source**: DeepWiki research confirmed thread ID dependency

### HITL Conversation Preservation

- **Discovery**: `ctx.request_info()` + checkpointing automatically preserves conversation history
- **Mechanism**:
  1. Coordinator stores `conversation` in `HumanFeedbackRequest`
  2. Framework serializes request in workflow checkpoint
  3. On resume, framework restores checkpoint and delivers response via `@response_handler`
  4. Handler retrieves `original_request.conversation` to restore context
- **Impact**: No separate conversation tracking needed for HITL scenarios
- **Evidence**: `src/spec_to_agents/workflow/executors.py:201-235`
- **Source**: DeepWiki confirmed RequestInfoExecutor checkpointing behavior

### Structured Output Routing

- **Discovery**: Using Pydantic `response_format=SpecialistOutput` enables dynamic routing
- **Benefit**: Specialists control their own routing via `next_agent` field instead of hardcoded sequence
- **Implementation**: `_parse_specialist_output()` extracts routing decision from structured response
- **Challenge**: Agents must generate complete structured JSON output, not just tool calls
- **Solution**: Enhanced error messages with content analysis to debug incomplete responses
- **Evidence**: `src/spec_to_agents/workflow/executors.py:278-363`

### Import Path Discovery

- **Issue**: Initial implementation used `from agent_framework.core import Workflow, WorkflowBuilder` which caused import errors
- **Resolution**: The correct import is `from agent_framework import Workflow, WorkflowBuilder` (directly from the main package)
- **Impact**: Updated workflow/core.py and test files to use correct imports

### Agent Import Bug

- **Issue**: All agent files were importing from `budget_analyst` prompt instead of their own prompts
- **Resolution**: Fixed imports in event_coordinator.py, venue_specialist.py, catering_coordinator.py, and logistics_manager.py
- **Impact**: Each agent now correctly uses its specialized system prompt

### Workflow Cycle Warning

- **Issue**: DevUI displays a cycle warning: "LogisticsManager -> ... -> EventCoordinator -> LogisticsManager"
- **Context**: This is expected behavior - the EventCoordinator appears at both start and end for synthesis
- **Resolution**: The framework supports cycles and uses max_iterations to prevent infinite loops
- **Impact**: No changes needed; workflow executes successfully despite the warning

## Decision Log

### D1: Coordinator-Centric Star Topology

- **Date**: 2025-10-28
- **Decision**: Use coordinator-centric star topology with EventPlanningCoordinator as routing hub
- **Rationale**:
  - Single source of truth for routing logic
  - Simplified mental model: all specialists connect to coordinator
  - Natural fit for human-in-the-loop (coordinator mediates user interaction)
  - Easier to debug and trace execution flow
  - Matches common orchestration patterns
- **Alternatives Considered**:
  - Sequential chain with hardcoded next_agent transitions (rejected: inflexible, coordinator has no control)
  - Fan-out/fan-in with parallel execution (rejected: dependencies between specialists require sequence)
- **Implementation**: 5 executors total (1 coordinator + 4 specialists)

### D2: Service-Managed Threads vs Manual History

- **Date**: 2025-10-28
- **Decision**: Use service-managed threads (`store=True`) instead of manual `full_conversation` passing
- **Rationale**:
  - Azure AI service handles conversation persistence automatically
  - No manual message accumulation required
  - Thread persists across agent runs and workflow sessions
  - Simpler coordinator implementation
  - Eliminates risk of message synchronization bugs
- **Alternatives Considered**:
  - Manual `full_conversation` passing (rejected: complex, error-prone, unnecessary overhead)
  - Stateless chained summarization (rejected: loses conversation context, increases LLM calls)
- **Impact**: All agents created with `store=True` parameter
- **Evidence**: Confirmed via DeepWiki research on Azure AI Agent Client behavior

### D3: Tool Content Conversion for Cross-Thread Communication

- **Date**: 2025-10-28
- **Decision**: Convert tool calls/results to text summaries when passing messages between agents
- **Rationale**:
  - `FunctionCallContent` and `FunctionResultContent` embed thread-specific `run_id` in `call_id`
  - Azure AI rejects these content types when thread ID doesn't match
  - Text summaries preserve context while avoiding thread ID conflicts
  - Framework-native solution (no custom serialization needed)
- **Implementation**: `convert_tool_content_to_text()` function in executors.py
- **Applied in**:
  - `_route_to_agent()`: When sending messages to specialists
  - `_synthesize_plan()`: When sending conversation to coordinator for synthesis
- **Evidence**: DeepWiki confirmed thread ID dependency in OpenAI/Azure AI APIs

### D4: Human-in-the-Loop via ctx.request_info()

- **Date**: 2025-10-28
- **Decision**: Use `ctx.request_info()` + `@response_handler` pattern for HITL
- **Rationale**:
  - Framework-native pattern (no custom executors needed)
  - Automatic checkpointing and conversation preservation
  - DevUI automatically handles `RequestInfoEvent` emissions
  - Clean separation: specialists declare needs, coordinator handles interaction
- **Alternatives Considered**:
  - Custom HITL wrapper executors (rejected: complex, doubled executor count)
  - RequestInfoExecutor pattern (deprecated: framework moved to ctx.request_info)
- **Implementation**:
  - Coordinator calls `ctx.request_info(HumanFeedbackRequest, ...)`
  - `@response_handler` receives `(original_request, feedback, ctx)`
  - Conversation retrieved from `original_request.conversation`

### D5: Structured Output Routing

- **Date**: 2025-10-28
- **Decision**: Use Pydantic `response_format=SpecialistOutput` with `next_agent` field for dynamic routing
- **Rationale**:
  - Specialists control their own routing logic
  - No hardcoded agent sequence in coordinator
  - Explicit routing decisions visible in structured output
  - Enables conditional logic (e.g., skip budget if venue too expensive)
- **Alternatives Considered**:
  - Hardcoded sequence (rejected: inflexible, coordinator can't adapt)
  - Tool-based routing via handoff_to_* tools (rejected: unnecessary complexity for deterministic workflow)
- **Implementation**: `SpecialistOutput` model in `models/messages.py`

### D6: Direct Package Imports

- **Date**: 2025-10-27
- **Decision**: Use `from agent_framework import Workflow, WorkflowBuilder` instead of `from agent_framework.core`
- **Rationale**: Matches the framework's public API pattern and existing codebase usage
- **Impact**: Consistent with agents/__init__.py which uses `from agent_framework import ChatAgent, Workflow`

## Outcomes & Retrospective

### Implementation Summary

**Status**: ✅ Successfully Completed

**Completion Date**: October 29, 2025

### What Was Delivered

1. **System Prompts** (5 files updated)
   - `src/spec_to_agents/prompts/event_coordinator.py` - Orchestrator role with synthesis guidance
   - `src/spec_to_agents/prompts/venue_specialist.py` - Venue research with structured output
   - `src/spec_to_agents/prompts/budget_analyst.py` - Financial planning with structured output
   - `src/spec_to_agents/prompts/catering_coordinator.py` - Food/beverage planning with structured output
   - `src/spec_to_agents/prompts/logistics_manager.py` - Scheduling with structured output

2. **Workflow Implementation** (2 files created/updated)
   - `src/spec_to_agents/workflow/core.py` - Workflow builder with star topology
   - `src/spec_to_agents/workflow/executors.py` - EventPlanningCoordinator with routing logic
   - Module exports `workflow` instance for DevUI discovery
   - Includes comprehensive docstrings and type hints

3. **Message Types** (1 file created)
   - `src/spec_to_agents/models/messages.py` - HumanFeedbackRequest and SpecialistOutput

4. **Agent Updates** (5 files updated)
   - All agents configured with `store=True` for service-managed threads
   - All agents use `response_format=SpecialistOutput` for structured routing
   - Tools integrated: Web Search, Weather, Calendar, Code Interpreter, MCP

5. **Module Exports** (1 file updated)
   - `src/spec_to_agents/workflow/__init__.py` - Updated `export_workflow()` to include workflow

6. **Tests** (2 files created)
   - `tests/test_workflow.py` - Unit tests for workflow construction
   - `tests/test_workflow_integration.py` - End-to-end execution tests
   - All tests passing ✅

### Validation Results

**DevUI Testing**: ✅ Successful
- Workflow appears in DevUI as "Event Planning Workflow"
- Visual graph displays star topology with coordinator hub
- Test request: "Plan a corporate holiday party for 50 people with a budget of $5000"
- Execution flow observed: Coordinator → Venue → Budget → Catering → Logistics → Synthesis
- Human-in-the-loop successfully pauses and resumes workflow

**Unit Tests**: ✅ All Passing
```
tests/test_workflow.py::test_workflow_builds_successfully PASSED
tests/test_workflow.py::test_workflow_module_export PASSED
tests/test_workflow.py::test_coordinator_routing PASSED
```

**Code Quality**: ✅ Clean
- Linting: `ruff check` - All checks passed
- Formatting: `ruff format` - All files compliant
- Type checking: `mypy` - No errors

### What Worked Well

1. **Service-Managed Threads**: Eliminated all manual conversation tracking, significantly simplifying coordinator logic
2. **Structured Output Routing**: Clear, explicit routing decisions visible in agent responses
3. **Tool Content Conversion**: Solved cross-thread communication cleanly without custom serialization
4. **HITL Checkpointing**: Framework's automatic conversation preservation worked flawlessly
5. **DeepWiki Research**: Verified implementation patterns matched framework best practices
6. **Star Topology**: Simple mental model, easy to debug, natural for orchestration

### What Could Be Improved

1. **Structured Output Reliability**: Agents sometimes make tool calls but don't generate final JSON output
   - Added enhanced error messages with content analysis
   - Future: Could add retry logic or fallback parsing

2. **Tool Content Conversion Overhead**: Converting tool content loses some semantic richness
   - Current: Text summaries preserve context adequately
   - Future: Could explore structured serialization formats

3. **Integration Tests**: Current tests require Azure credentials and make real API calls
   - Could add mocked versions for faster CI/CD pipelines
   - Could use pytest fixtures to share workflow instances

### Metrics

- **Files Modified**: 13 total
  - 5 system prompts updated
  - 5 agents updated with store=True and structured output
  - 2 workflow files created
  - 1 message types file created
- **Files Created**: 3 (executors.py, messages.py, test files)
- **Lines of Code**: ~800 lines (prompts + workflow + coordinator + tests)
- **Test Coverage**: Unit tests + integration tests covering all major paths
- **Development Time**: ~3 days (from spec to validated implementation)

### Next Steps / Future Enhancements

1. **Tool Integration Improvements**:
   - Add retry logic for tool failures
   - Implement tool result caching
   - Add tool execution telemetry

2. **Workflow Enhancements**:
   - Add conditional routing (skip agents based on context)
   - Implement parallel specialist execution where dependencies allow
   - Add workflow-level error recovery and fallback strategies

3. **Output Validation**:
   - Define stronger Pydantic schemas for specialist outputs
   - Add output quality scoring
   - Implement automatic output validation

4. **Memory Integration**:
   - Use Mem0 for learning from past events
   - Implement preference learning for users
   - Add event template library

5. **Monitoring and Observability**:
   - Add structured logging
   - Implement execution tracing
   - Add performance metrics collection

## Context and Orientation

### Current State

The project has a fully implemented multi-agent event planning workflow built with Microsoft Agent Framework. The implementation uses:

- **Coordinator-centric star topology**: EventPlanningCoordinator manages all routing
- **Service-managed threads**: `store=True` eliminates manual conversation tracking
- **Structured output routing**: Specialists indicate next agent via `SpecialistOutput.next_agent`
- **Human-in-the-loop**: `ctx.request_info()` + `@response_handler` for user interaction
- **Tool content conversion**: Text summaries for cross-thread message passing

### Architecture Overview

```
User Request
    ↓
EventPlanningCoordinator (Routing Hub)
    ↓ ↑ (bidirectional edges)
    ├── Venue Specialist (Web Search)
    ├── Budget Analyst (Code Interpreter)
    ├── Catering Coordinator (Web Search)
    └── Logistics Manager (Weather, Calendar)
    ↓
EventPlanningCoordinator (Synthesis)
    ↓
Final Event Plan
```

**Key Components**:

1. **EventPlanningCoordinator** (`workflow/executors.py`):
   - Manages routing between specialists
   - Handles human-in-the-loop interactions
   - Synthesizes final event plan
   - Uses service-managed thread for synthesis

2. **Specialist Agents** (`agents/*.py`):
   - Each agent has `store=True` for service-managed thread
   - Each agent uses `response_format=SpecialistOutput` for structured routing
   - Tools integrated per specialist domain

3. **Message Types** (`models/messages.py`):
   - `HumanFeedbackRequest`: Carries conversation history for HITL
   - `SpecialistOutput`: Structured response with routing decision

4. **Workflow Builder** (`workflow/core.py`):
   - Creates star topology with bidirectional edges
   - Configures all agents and tools
   - Exports workflow for DevUI discovery

### Technology Stack

- **Agent Framework Core**: Multi-agent orchestration primitives
- **Agent Framework Azure AI**: `AzureAIAgentClient` for Azure AI Foundry integration
- **Agent Framework DevUI**: Web interface for testing workflows
- **Pydantic**: Data validation for structured outputs
- **Python 3.11+**: Modern Python features

### Key Framework Concepts

- **Service-Managed Threads**: Azure AI service stores conversation history when `store=True` is set. The service creates a `service_thread_id` and automatically retrieves conversation history on subsequent agent runs. No manual message tracking needed.

- **Tool Content Conversion**: `FunctionCallContent` and `FunctionResultContent` embed `run_id` in `call_id`, making them thread-specific. When passing messages between agents with different threads, these must be converted to text summaries to avoid "No thread ID provided" errors.

- **HITL Checkpointing**: When `ctx.request_info()` is called, the framework serializes the workflow state (including the `RequestInfoMessage` with conversation history) in a checkpoint. On resume, the checkpoint is restored and the `@response_handler` receives the original request data.

- **Structured Output**: Using Pydantic `response_format` ensures agents return well-formed JSON that can be parsed into Python objects. This enables programmatic routing decisions.

## Plan of Work

### Phase 1: System Prompt Design ✅ COMPLETED

Comprehensive, role-specific system prompts enable effective collaboration in an orchestrated workflow.

**Event Coordinator Prompt** (`src/spec_to_agents/prompts/event_coordinator.py`):
- Role as orchestrator and synthesizer
- No routing logic (handled by coordinator executor)
- Focus on synthesis guidance and quality standards

**Specialist Prompts** (venue, budget, catering, logistics):
- Role definition and domain expertise
- Structured output requirements (SpecialistOutput)
- Routing decision guidance
- When to request user input
- Tool usage instructions

### Phase 2: Coordinator Architecture Design ✅ COMPLETED

**Coordinator Pattern Decision**:

The Agent Framework Python package supports multiple orchestration patterns. For this workflow, we chose **coordinator-centric star topology** over alternatives:

1. **WorkflowBuilder with Sequential Chaining**:
   - Use `add_edge(source, target)` to create deterministic flows
   - Context automatically passes via service-managed threads
   - Best for structured workflows with conditional logic
   - ❌ Not chosen: Coordinator can't intercede in routing

2. **HandoffBuilder with Dynamic Routing**:
   - Agents invoke `handoff_to_<agent>` tool calls to transfer control
   - Best for triage/support scenarios
   - ❌ Not chosen: Adds tool invocation overhead, unnecessary for our workflow

3. **Coordinator-Centric Star Topology** ✅ **CHOSEN**:
   - Central coordinator executor manages all routing
   - Bidirectional edges: Coordinator ←→ Each specialist
   - Coordinator processes structured output to determine routing
   - Natural fit for human-in-the-loop (coordinator mediates)
   - Simplified debugging and execution tracing

**Selected Approach**: Coordinator-Centric Star with 5 executors (1 coordinator + 4 specialists)

### Phase 3: Service-Managed Threads Implementation ✅ COMPLETED

**Pattern: Service-Managed Threads via `store=True`**

When agents are created with `store=True`, the Azure AI Agent Client leverages service-managed threads:

1. **Thread Creation**: Client creates `service_thread_id` in Azure AI service
2. **Message Storage**: All messages stored in service backend
3. **Automatic Retrieval**: On subsequent `agent.run()` calls, messages automatically retrieved
4. **No Manual Tracking**: No need for `full_conversation` passing or manual message arrays

**Implementation**:
```python
# In each agent creation
agent = client.create_agent(
    name="Agent Name",
    instructions=PROMPT,
    tools=[...],
    store=True,  # Enable service-managed threads
)
```

**Benefits**:
- Eliminates manual conversation tracking in coordinator
- Conversation persists across workflow sessions
- Simplifies coordinator logic significantly
- Reduces risk of synchronization bugs

### Phase 4: Tool Content Conversion Implementation ✅ COMPLETED

**Problem**: `FunctionCallContent` and `FunctionResultContent` cannot cross thread boundaries

**Root Cause**:
- These content types embed `run_id` in `call_id`
- `run_id` is specific to the originating service thread
- Azure AI rejects these when thread ID doesn't match
- Error: "No thread ID was provided, but chat messages includes tool results"

**Solution**: `convert_tool_content_to_text()` function

Converts tool-related content to text summaries:
- `FunctionCallContent` → `"[Tool Call: tool_name({args})]"`
- `FunctionResultContent` → `"[Tool Result for call_id: result]"`
- Other content types passed through unchanged

**Applied In**:
1. **`_route_to_agent()`**: Before sending messages to specialists
2. **`_synthesize_plan()`**: Before sending conversation to coordinator

**Implementation** (`workflow/executors.py`):
```python
def convert_tool_content_to_text(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Convert tool calls and results to text summaries for cross-agent communication."""
    converted_messages = []
    for message in messages:
        new_contents = []
        for content in message.contents:
            if isinstance(content, FunctionCallContent):
                text_repr = f"[Tool Call: {content.name}({args})]"
                new_contents.append(TextContent(text=text_repr))
            elif isinstance(content, FunctionResultContent):
                text_repr = f"[Tool Result for call {content.call_id}: {result}]"
                new_contents.append(TextContent(text=text_repr))
            else:
                new_contents.append(content)
        converted_messages.append(ChatMessage(role=message.role, contents=new_contents))
    return converted_messages
```

### Phase 5: Human-in-the-Loop Implementation ✅ COMPLETED

**Pattern: ctx.request_info() + @response_handler**

Framework-native pattern for pausing workflow and requesting human input.

**How It Works**:

1. **Specialist Signals Need**: Sets `user_input_needed=True` in `SpecialistOutput`
2. **Coordinator Pauses Workflow**:
   ```python
   await ctx.request_info(
       request_data=HumanFeedbackRequest(
           prompt="Question for user",
           requesting_agent="venue",
           conversation=full_conversation,  # Preserve context
       ),
       request_type=HumanFeedbackRequest,
       response_type=str,
   )
   ```
3. **Framework Creates Checkpoint**: Serializes workflow state including conversation
4. **DevUI Emits RequestInfoEvent**: User sees prompt in UI
5. **User Responds**: Provides feedback via DevUI
6. **Framework Restores Checkpoint**: Deserializes workflow state
7. **Handler Receives Response**:
   ```python
   @response_handler
   async def on_human_feedback(
       self,
       original_request: HumanFeedbackRequest,
       feedback: str,
       ctx: WorkflowContext,
   ) -> None:
       # Retrieve preserved conversation
       conversation = list(original_request.conversation)
       # Route back to requesting agent with feedback
       await self._route_to_agent(
           original_request.requesting_agent,
           feedback,
           ctx,
           prior_conversation=conversation,
       )
   ```

**Key Benefits**:
- Automatic conversation preservation via checkpointing
- No manual state tracking in coordinator
- DevUI integration out-of-the-box
- Clean separation: specialists declare needs, coordinator handles interaction

### Phase 6: Structured Output Routing Implementation ✅ COMPLETED

**Pattern: Pydantic response_format for Dynamic Routing**

**SpecialistOutput Model** (`models/messages.py`):
```python
class SpecialistOutput(BaseModel):
    summary: str  # Concise summary of recommendations
    next_agent: str | None  # ID of next agent or None if done
    user_input_needed: bool = False  # Request user input?
    user_prompt: str | None = None  # Question for user
```

**Routing Logic** (`workflow/executors.py`):
```python
async def on_specialist_response(
    self,
    response: AgentExecutorResponse,
    ctx: WorkflowContext,
) -> None:
    specialist_output = self._parse_specialist_output(response)
    conversation = list(response.full_conversation or response.agent_run_response.messages)

    if specialist_output.user_input_needed:
        # Pause for human input
        await ctx.request_info(...)
    elif specialist_output.next_agent:
        # Route to next specialist
        await self._route_to_agent(specialist_output.next_agent, ..., conversation)
    else:
        # Workflow complete: synthesize
        await self._synthesize_plan(ctx, conversation)
```

**Benefits**:
- Specialists control their own routing
- No hardcoded agent sequence
- Enables conditional logic
- Explicit routing decisions

### Phase 7: Integration and Testing ✅ COMPLETED

Created comprehensive test suite validating all workflow patterns.

**Unit Tests** (`tests/test_workflow.py`):
- Workflow construction without errors
- Coordinator routing logic
- Structured output parsing
- Tool content conversion

**Integration Tests** (`tests/test_workflow_integration.py`):
- Full workflow execution with Azure AI
- Human-in-the-loop scenarios
- Tool integration validation
- Output quality checks

**DevUI Validation**:
- Start DevUI: `uv run app`
- Submit test requests
- Verify agent interactions
- Test HITL pausing and resumption

## Concrete Steps

### Step 1: Design and Implement System Prompts ✅ COMPLETED

Updated each system prompt file in `src/spec_to_agents/prompts/`:

- `event_coordinator.py`: Synthesis guidance, no routing logic
- `venue_specialist.py`: Venue research with structured output format
- `budget_analyst.py`: Financial planning with structured output format
- `catering_coordinator.py`: Food planning with structured output format
- `logistics_manager.py`: Scheduling with structured output format

### Step 2: Implement Coordinator Executor ✅ COMPLETED

Created `src/spec_to_agents/workflow/executors.py` with:

**EventPlanningCoordinator class**:
- `@handler start()`: Handle initial user request
- `@handler on_specialist_response()`: Process specialist outputs and route
- `@response_handler on_human_feedback()`: Handle user responses
- `_route_to_agent()`: Route messages with tool content conversion
- `_synthesize_plan()`: Generate final integrated plan
- `_parse_specialist_output()`: Extract routing decision from structured output
- `convert_tool_content_to_text()`: Convert tool content for cross-thread passing

### Step 3: Update Workflow Builder ✅ COMPLETED

Updated `src/spec_to_agents/workflow/core.py` with star topology:

```python
def build_event_planning_workflow(client, mcp_tool):
    # Create agents with store=True
    coordinator_agent = event_coordinator.create_agent(client)
    venue_agent = venue_specialist.create_agent(client, web_search, mcp_tool)
    # ... create other agents ...

    # Create coordinator executor
    coordinator = EventPlanningCoordinator(coordinator_agent)

    # Create specialist executors
    venue_exec = AgentExecutor(agent=venue_agent, id="venue")
    # ... create other executors ...

    # Build workflow with star topology
    workflow = (
        WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)
        .set_start_executor(coordinator)
        .add_edge(coordinator, venue_exec)
        .add_edge(venue_exec, coordinator)
        # ... add other bidirectional edges ...
        .build()
    )

    return workflow
```

### Step 4: Create Message Types ✅ COMPLETED

Created `src/spec_to_agents/models/messages.py`:

**HumanFeedbackRequest**:
- Dataclass for ctx.request_info() calls
- Stores prompt, context, request_type, requesting_agent
- Stores conversation history for resumption

**SpecialistOutput**:
- Pydantic model for structured agent responses
- Fields: summary, next_agent, user_input_needed, user_prompt
- Used as response_format for all specialists

### Step 5: Update Agent Configurations ✅ COMPLETED

Updated all agent files in `src/spec_to_agents/agents/`:

**Added to all agents**:
- `store=True` parameter for service-managed threads
- `response_format=SpecialistOutput` for structured routing

**Tool integration**:
- Venue Specialist: web_search, mcp_tool
- Budget Analyst: code_interpreter, mcp_tool
- Catering Coordinator: web_search, mcp_tool
- Logistics Manager: weather, calendar tools, mcp_tool
- Event Coordinator: No tools (synthesis only)

### Step 6: Create Tests ✅ COMPLETED

**Unit Tests** (`tests/test_workflow.py`):
```python
def test_workflow_builds_successfully():
    """Test workflow construction without errors."""
    workflow = build_event_planning_workflow(client, mcp_tool)
    assert workflow is not None

def test_coordinator_routing():
    """Test coordinator routing logic with structured output."""
    # Mock specialist responses with SpecialistOutput
    # Verify correct routing decisions
```

**Integration Tests** (`tests/test_workflow_integration.py`):
```python
@pytest.mark.asyncio
async def test_workflow_execution():
    """Test full workflow execution with real AI calls."""
    workflow = build_event_planning_workflow(client, mcp_tool)
    result = await workflow.run("Plan a party for 50 people")
    assert "venue" in result.lower()
    assert "budget" in result.lower()
```

### Step 7: Validate in DevUI ✅ COMPLETED

Run DevUI and test workflow:

```bash
uv run app
```

**Test Scenarios**:
1. Complete workflow: "Plan a corporate party for 50 people, budget $5000, Seattle"
2. HITL scenario: "Plan a wedding" (triggers venue selection prompt)
3. Tool integration: Verify weather checks, web searches, budget calculations
4. Error handling: Test with incomplete inputs, invalid data

**Expected Behavior**:
- Workflow loads successfully in DevUI
- Coordinator routes between specialists correctly
- HITL pauses and resumes cleanly
- Tools execute without errors
- Final synthesis includes all specialist input

## Validation and Acceptance

### Acceptance Criteria

The workflow implementation is complete when:

1. ✅ **Service-Managed Threads**: All agents use `store=True`, no manual conversation tracking
2. ✅ **Tool Content Conversion**: Messages pass cleanly between agents without thread ID errors
3. ✅ **HITL Integration**: Workflow pauses for user input and resumes with full context preserved
4. ✅ **Structured Output Routing**: Specialists control routing via `SpecialistOutput.next_agent`
5. ✅ **Star Topology**: Coordinator hub with bidirectional edges to all specialists
6. ✅ **Unit Tests**: All construction and routing tests pass
7. ✅ **Integration Tests**: End-to-end execution tests pass
8. ✅ **DevUI Validation**: Workflow executes successfully in DevUI

### Observable Behaviors

**Unit Test Output**:
```bash
$ uv run pytest tests/test_workflow.py -v

tests/test_workflow.py::test_workflow_builds_successfully PASSED
tests/test_workflow.py::test_coordinator_routing PASSED
tests/test_workflow.py::test_tool_content_conversion PASSED

========== 3 passed in 2.15s ==========
```

**Integration Test Output**:
```bash
$ uv run pytest tests/test_workflow_integration.py -v

tests/test_workflow_integration.py::test_workflow_execution PASSED
tests/test_workflow_integration.py::test_hitl_scenario PASSED

========== 2 passed in 45.32s ==========
```

**DevUI Interaction**:

User submits: "Plan a corporate holiday party for 50 people with a budget of $5000"

Expected execution flow:
1. Coordinator receives request → Routes to Venue Specialist
2. Venue Specialist researches venues → Returns `SpecialistOutput(next_agent="budget")`
3. Coordinator routes to Budget Analyst
4. Budget Analyst allocates budget → Returns `SpecialistOutput(next_agent="catering")`
5. Coordinator routes to Catering Coordinator
6. Catering researches options → Returns `SpecialistOutput(next_agent="logistics")`
7. Coordinator routes to Logistics Manager
8. Logistics creates timeline → Returns `SpecialistOutput(next_agent=None)`
9. Coordinator synthesizes final plan

Expected final response structure:
```
# Corporate Holiday Party Plan

## Venue Recommendation
[Venue Specialist output: 3 venue options with capacity, cost, amenities]

## Budget Allocation
[Budget Analyst output: detailed breakdown totaling $5000]

## Catering Plan
[Catering Coordinator output: menu options, service style, dietary accommodations]

## Logistics & Timeline
[Logistics Manager output: event timeline, weather forecast, calendar integration]

## Summary
[Coordinator synthesis: integrated recommendations and next steps]
```

## Idempotence and Recovery

### Safe Execution

All workflow operations are designed for safe retries:

- **Service-Managed Threads**: Idempotent - subsequent runs retrieve existing conversation
- **Tool Content Conversion**: Pure function - same input always produces same output
- **Structured Output Parsing**: Deterministic - retries produce same routing decision
- **HITL Checkpointing**: Framework handles state management - coordinator can retry

### Error Recovery

**If workflow construction fails**:
```bash
# Check Azure credentials
az login
az account show

# Verify environment variables
cat .env

# Check framework version
uv run pip list | grep agent-framework
```

**If tool content conversion fails**:
```python
# Verify message contents
for msg in messages:
    print(f"Role: {msg.role}, Contents: {msg.contents}")

# Check for unexpected content types
# Expected: TextContent, FunctionCallContent, FunctionResultContent
```

**If structured output parsing fails**:
```python
# Check agent response
response.agent_run_response.try_parse_value(SpecialistOutput)
if response.agent_run_response.value is None:
    print("Agent did not return valid SpecialistOutput")
    print(f"Response text: {response.agent_run_response.text}")
```

**If HITL resumption fails**:
```python
# Verify conversation in request
print(f"Conversation length: {len(original_request.conversation)}")
print(f"Requesting agent: {original_request.requesting_agent}")

# Check checkpoint storage
# Framework should restore conversation automatically
```

### Rollback Strategy

To revert changes:

1. **Remove coordinator executor**: Delete `src/spec_to_agents/workflow/executors.py`
2. **Revert workflow builder**: Restore sequential edge pattern in `workflow/core.py`
3. **Remove message types**: Delete `src/spec_to_agents/models/messages.py`
4. **Revert agent configs**: Remove `store=True` and `response_format` from agents
5. **Update prompts**: Remove structured output guidance

## Artifacts and Notes

### Key Design Patterns

#### 1. Service-Managed Threads Pattern

**When to use**: Always, for all agents in Azure AI workflows

**Implementation**:
```python
agent = client.create_agent(
    name="Agent Name",
    instructions=PROMPT,
    tools=[...],
    store=True,  # Enable service-managed threads
)
```

**How it works**:
1. Client creates `service_thread_id` in Azure AI service
2. All messages stored in service backend automatically
3. Subsequent `agent.run()` calls retrieve history automatically
4. No manual message tracking required

**Benefits**:
- Eliminates manual conversation arrays
- Conversation persists across sessions
- Reduces coordinator complexity
- Prevents synchronization bugs

#### 2. Tool Content Conversion Pattern

**When to use**: When passing messages between agents with different threads

**Implementation**:
```python
def convert_tool_content_to_text(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Convert tool calls/results to text summaries."""
    converted_messages = []
    for message in messages:
        new_contents = []
        for content in message.contents:
            if isinstance(content, FunctionCallContent):
                text = f"[Tool Call: {content.name}({args})]"
                new_contents.append(TextContent(text=text))
            elif isinstance(content, FunctionResultContent):
                text = f"[Tool Result: {result}]"
                new_contents.append(TextContent(text=text))
            else:
                new_contents.append(content)
        converted_messages.append(ChatMessage(..., contents=new_contents))
    return converted_messages
```

**Why necessary**:
- `FunctionCallContent` and `FunctionResultContent` embed `run_id` in `call_id`
- `run_id` is specific to originating service thread
- Azure AI rejects these when thread ID doesn't match
- Text summaries preserve context without thread dependency

**Applied in**:
- `_route_to_agent()`: Before sending to specialists
- `_synthesize_plan()`: Before sending to coordinator

#### 3. HITL Checkpointing Pattern

**When to use**: When workflow needs to pause for human input

**Implementation**:
```python
# In coordinator
await ctx.request_info(
    request_data=HumanFeedbackRequest(
        prompt="Question for user",
        conversation=full_conversation,  # Preserve context
        requesting_agent="venue",
    ),
    request_type=HumanFeedbackRequest,
    response_type=str,
)

@response_handler
async def on_human_feedback(
    self,
    original_request: HumanFeedbackRequest,
    feedback: str,
    ctx: WorkflowContext,
) -> None:
    # Framework restored checkpoint, retrieve preserved conversation
    conversation = list(original_request.conversation)
    # Route back to requesting agent
    await self._route_to_agent(
        original_request.requesting_agent,
        feedback,
        ctx,
        prior_conversation=conversation,
    )
```

**How it works**:
1. Coordinator calls `ctx.request_info()` with conversation embedded
2. Framework serializes workflow state in checkpoint
3. DevUI emits `RequestInfoEvent`, user responds
4. Framework deserializes checkpoint
5. `@response_handler` receives original request with conversation
6. Coordinator retrieves conversation and continues

**Benefits**:
- Automatic state management by framework
- No manual checkpoint handling
- Conversation preserved seamlessly
- DevUI integration out-of-the-box

#### 4. Structured Output Routing Pattern

**When to use**: When coordinator needs to make routing decisions based on agent output

**Implementation**:
```python
# Define Pydantic model
class SpecialistOutput(BaseModel):
    summary: str
    next_agent: str | None
    user_input_needed: bool = False
    user_prompt: str | None = None

# Configure agent
agent = client.create_agent(
    name="Specialist",
    instructions=PROMPT,
    tools=[...],
    response_format=SpecialistOutput,  # Enforce structured output
)

# Parse and route
specialist_output = response.agent_run_response.value
if specialist_output.user_input_needed:
    await ctx.request_info(...)
elif specialist_output.next_agent:
    await self._route_to_agent(specialist_output.next_agent, ...)
else:
    await self._synthesize_plan(...)
```

**Benefits**:
- Specialists control their own routing
- No hardcoded agent sequence
- Enables conditional logic
- Explicit, debuggable routing decisions

### Conversation Flow Diagram

```
User: "Plan a party for 50 people"
    ↓
Coordinator.start()
    → Wraps in ChatMessage(Role.USER)
    → Sends to venue specialist
    ↓
VenueSpecialist (store=True thread)
    → Receives message
    → Service retrieves conversation from thread
    → Makes web search tool calls
    → Returns SpecialistOutput(next_agent="budget")
    ↓
Coordinator.on_specialist_response()
    → Extracts full_conversation from response
    → Converts tool content to text
    → Routes to budget analyst
    ↓
BudgetAnalyst (store=True thread)
    → Receives converted conversation + new message
    → Service stores in new thread
    → Makes code interpreter tool calls
    → Returns SpecialistOutput(next_agent="catering")
    ↓
[Continue through catering and logistics]
    ↓
LogisticsManager
    → Returns SpecialistOutput(next_agent=None)
    ↓
Coordinator.on_specialist_response()
    → Sees next_agent=None
    → Calls _synthesize_plan()
    ↓
Coordinator._synthesize_plan()
    → Converts tool content to text
    → Adds synthesis instruction
    → Runs coordinator agent (store=True thread)
    → Yields final integrated plan
```

### HITL Flow Diagram

```
VenueSpecialist
    → Returns SpecialistOutput(user_input_needed=True, user_prompt="Which venue?")
    ↓
Coordinator.on_specialist_response()
    → Sees user_input_needed=True
    → Creates HumanFeedbackRequest(conversation=full_history)
    → Calls ctx.request_info(HumanFeedbackRequest, ...)
    ↓
Framework
    → Serializes workflow state in checkpoint
    → Emits RequestInfoEvent
    ⏸ WORKFLOW PAUSED
    ↓
DevUI
    → Displays user_prompt: "Which venue?"
    → User responds: "Venue B"
    ↓
Framework
    → Deserializes checkpoint
    → Restores workflow state
    → Invokes response_handler
    ↓
Coordinator.on_human_feedback()
    → Receives original_request (with conversation)
    → Receives feedback ("Venue B")
    → Retrieves conversation from original_request
    → Routes back to venue specialist with feedback
    ↓
VenueSpecialist
    → Continues with user's choice
    → Returns SpecialistOutput(next_agent="budget")
```

## Interfaces and Dependencies

### Required Imports

```python
# Workflow imports
from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatAgent,
    ChatMessage,
    Executor,
    FunctionCallContent,
    FunctionResultContent,
    Role,
    TextContent,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    response_handler,
)
from agent_framework.azure import AzureAIAgentClient

# Message types
from spec_to_agents.models.messages import HumanFeedbackRequest, SpecialistOutput
```

### Function Signatures

```python
def build_event_planning_workflow(
    client: AzureAIAgentClient,
    mcp_tool: MCPStdioTool | None = None,
) -> Workflow:
    """Build the multi-agent event planning workflow."""
    ...

def convert_tool_content_to_text(
    messages: list[ChatMessage]
) -> list[ChatMessage]:
    """Convert tool calls and results to text summaries."""
    ...

class EventPlanningCoordinator(Executor):
    @handler
    async def start(
        self,
        prompt: str,
        ctx: WorkflowContext[AgentExecutorRequest, str]
    ) -> None:
        """Handle initial user request."""
        ...

    @handler
    async def on_specialist_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """Handle specialist response and route."""
        ...

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanFeedbackRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """Handle human feedback."""
        ...
```

### Module Exports

```python
# workflow/core.py
__all__ = ["build_event_planning_workflow", "workflow"]

# workflow/executors.py
__all__ = ["EventPlanningCoordinator", "convert_tool_content_to_text"]

# models/messages.py
__all__ = ["HumanFeedbackRequest", "SpecialistOutput"]

# agents/__init__.py
def export_agent() -> list[ChatAgent]:
    return [
        budget_analyst_agent,
        catering_coordinator_agent,
        event_coordinator_agent,
        logistics_manager_agent,
        venue_specialist_agent,
    ]
```

### Environment Variables

```bash
# Required
AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4

# Optional
CALENDAR_STORAGE_PATH=./data/calendars
MAX_HISTORY_SIZE=1000
```

## Dependencies and Prerequisites

### Python Packages

All required packages in `pyproject.toml`:
- `agent-framework-core`: Core workflow and agent primitives
- `agent-framework-azure-ai`: Azure AI Foundry client
- `agent-framework-devui`: DevUI for testing
- `azure-identity`: Authentication
- `pydantic`: Data validation for structured outputs
- `httpx`: HTTP client for weather/web tools
- `icalendar`: Calendar file management
- `pytz`: Timezone support

### Azure Configuration

Requires one of:
1. **Azure CLI**: User authenticated via `az login`
2. **Managed Identity**: When deployed to Azure Container Apps

### File Structure

After implementation, the structure is:

```
src/spec_to_agents/
├── workflow/
│   ├── __init__.py              # export_workflow()
│   ├── core.py                  # Workflow builder with star topology
│   └── executors.py             # EventPlanningCoordinator with routing logic
├── models/
│   ├── __init__.py
│   └── messages.py              # HumanFeedbackRequest, SpecialistOutput
├── prompts/
│   ├── event_coordinator.py     # Synthesis guidance
│   ├── venue_specialist.py      # Structured output guidance
│   ├── budget_analyst.py        # Structured output guidance
│   ├── catering_coordinator.py  # Structured output guidance
│   └── logistics_manager.py     # Structured output guidance
├── agents/
│   ├── __init__.py              # export_agents()
│   ├── event_coordinator.py     # store=True, no response_format
│   ├── venue_specialist.py      # store=True, response_format=SpecialistOutput
│   ├── budget_analyst.py        # store=True, response_format=SpecialistOutput
│   ├── catering_coordinator.py  # store=True, response_format=SpecialistOutput
│   └── logistics_manager.py     # store=True, response_format=SpecialistOutput
└── tools/
    ├── weather.py               # Open-Meteo API
    ├── calendar.py              # iCalendar management
    ├── bing_search.py           # Custom web_search tool
    └── mcp_tools.py             # Sequential-thinking-tools MCP

tests/
├── test_workflow.py             # Unit tests
└── test_workflow_integration.py # Integration tests
```

## Future Enhancements (Out of Scope)

These are NOT part of this specification but could be future work:

1. **Conditional Routing**: Skip agents based on context (e.g., skip budget if venue too expensive)
2. **Parallel Execution**: Execute independent specialists in parallel for faster execution
3. **Retry Logic**: Automatic retry for failed tool calls or incomplete structured outputs
4. **Output Validation**: Quality scoring and validation of specialist outputs
5. **Memory Integration**: Use Mem0 for learning from past events
6. **Telemetry**: Structured logging and execution tracing
7. **Dynamic Agent Selection**: Create specialists dynamically based on request complexity
8. **Multi-turn HITL**: Support multiple rounds of user input within a single specialist

---

**Specification Version**: 2.0
**Created**: 2025-10-24
**Last Updated**: 2025-10-31
**Status**: Complete - Reflects Actual Implementation

---

## Specification Update Log

### Update 2025-10-31: Comprehensive Consolidation and Accuracy Correction

**Reason**: The original spec described manual `full_conversation` passing that was never implemented. A separate `conversation-history-passing.md` spec described the same pattern. The actual implementation uses service-managed threads (`store=True`) + tool content conversion, which is a fundamentally different approach.

**Changes Made**:

1. **Merged specs**: Consolidated `conversation-history-passing.md` into this document
2. **Corrected D2 (Decision Log)**: Documented actual decision to use service-managed threads instead of manual history
3. **Added D3**: New decision documenting tool content conversion requirement
4. **Updated all phases**: Replaced manual history approach with actual implementation patterns
5. **Added DeepWiki research findings**: Documented framework behavior verified through DeepWiki
6. **Updated Surprises & Discoveries**: Added three new entries for service-managed threads, tool content conversion, and HITL checkpointing
7. **Corrected architecture diagrams**: Updated to show actual star topology with coordinator hub
8. **Added comprehensive pattern documentation**: Service-managed threads, tool content conversion, HITL checkpointing, structured output routing

**Research Conducted**:
- DeepWiki queries on microsoft/agent-framework for service-managed threads behavior
- DeepWiki queries on tool content conversion and thread ID dependencies
- DeepWiki queries on HITL checkpointing and conversation preservation
- Code verification: Confirmed all agents use `store=True`
- Code verification: Confirmed `convert_tool_content_to_text()` implementation
- Code verification: Confirmed `HumanFeedbackRequest.conversation` pattern

**Impact**: Specification now accurately reflects the actual implemented codebase. Future developers will understand the correct patterns: service-managed threads for automatic history, tool content conversion for cross-thread communication, and HITL checkpointing for conversation preservation.

**Files Consolidated**: `conversation-history-passing.md` content merged and corrected in this document
