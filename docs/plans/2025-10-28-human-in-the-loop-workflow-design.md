# Human-in-the-Loop Workflow Design

**Date**: 2025-10-28
**Status**: Design Finalized
**Related Spec**: `specs/workflow-skeleton.md` (Phase 6)

## Overview

This document describes the design for adding human-in-the-loop capabilities to the multi-agent event planning workflow. The design enables specialist agents to request user clarification, selection, or approval during workflow execution through a tool-based approach.

## Problem Statement

The current event planning workflow executes fully autonomously. When users provide ambiguous requirements (e.g., "plan a party for 30 people"), agents make assumptions rather than asking clarifying questions. This can lead to:

- Venue recommendations that don't match unstated preferences
- Budget allocations without user approval
- Catering selections that miss dietary requirements
- Reduced alignment with user expectations

**Goal**: Enable agents to request user input when needed while maintaining workflow autonomy when sufficient context is provided.

## Design Constraints

1. **Framework Limitation**: ChatAgents cannot directly emit `RequestInfoMessage` - custom executors are required
2. **DevUI Integration**: Solution must work with existing DevUI without custom UI
3. **Minimal Disruption**: Preserve existing sequential workflow structure
4. **Optional Interaction**: Workflow should complete without user input when context is sufficient
5. **Agent Autonomy**: Agents decide when user input is needed, not hardcoded gates

## Architecture

### High-Level Flow

```
User Request
    ↓
EventCoordinator
    ↓
VenueAgent → VenueHITL Wrapper ←→ RequestInfoExecutor ←→ DevUI/User
    ↓
BudgetAgent → BudgetHITL Wrapper ←→ RequestInfoExecutor ←→ DevUI/User
    ↓
CateringAgent → CateringHITL Wrapper ←→ RequestInfoExecutor ←→ DevUI/User
    ↓
LogisticsAgent → LogisticsHITL Wrapper ←→ RequestInfoExecutor ←→ DevUI/User
    ↓
EventCoordinator (synthesis)
    ↓
Final Plan
```

### Components

#### 1. Tool Definition: `request_user_input`

**File**: `src/spec2agent/tools/user_input.py`

Agents call this tool when they need user input:

```python
def request_user_input(
    prompt: str,
    context: dict[str, Any],
    request_type: Literal["clarification", "selection", "approval"]
) -> str:
    """Request input from the user during workflow execution."""
```

**Parameters**:
- `prompt`: Clear question for the user (e.g., "Which venue do you prefer?")
- `context`: Supporting data (e.g., `{"venues": [venue1, venue2, venue3]}`)
- `request_type`: Category of request for potential filtering/handling

#### 2. Message Type: `UserElicitationRequest`

**File**: `src/spec2agent/workflow/messages.py`

Single general-purpose message type for all user requests:

```python
@dataclass
class UserElicitationRequest(RequestInfoMessage):
    """General-purpose request for user input during event planning."""
    prompt: str
    context: dict[str, Any]
    request_type: str
```

**Design Decision**: Use single message type for simplicity. Specialized types (VenueSelectionRequest, BudgetApprovalRequest) can be added later if needed.

#### 3. Custom Executor: `HumanInLoopAgentExecutor`

**File**: `src/spec2agent/workflow/executors.py`

Wraps `AgentExecutor` to intercept tool calls and emit `UserElicitationRequest`:

```python
class HumanInLoopAgentExecutor(Executor):
    """
    Intercepts request_user_input tool calls and emits UserElicitationRequest.

    Flow:
    1. Receives AgentExecutorResponse from wrapped agent
    2. Checks for request_user_input in FunctionCallContent
    3. If found: emit UserElicitationRequest to RequestInfoExecutor (workflow pauses)
    4. If not found: continue to next agent
    5. On RequestResponse: forward agent response to continue workflow
    """
```

**Key Methods**:
- `on_agent_response(AgentExecutorResponse)`: Intercept agent output, check for tool calls
- `on_user_response(RequestResponse)`: Handle user response and continue workflow
- `_extract_user_request(AgentExecutorResponse)`: Parse `FunctionCallContent` for tool arguments

#### 4. Workflow Integration

**File**: `src/spec2agent/workflow/core.py` (modifications)

```python
def build_event_planning_workflow():
    # Create agents with request_user_input tool
    venue_agent = client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True
    )

    # Create AgentExecutors
    venue_exec = AgentExecutor(agent=venue_agent, id="venue")

    # Create RequestInfoExecutor
    request_info = RequestInfoExecutor(id="user_input")

    # Create HITL wrappers
    venue_hitl = HumanInLoopAgentExecutor(agent_id="venue", request_info_id="user_input")

    # Build workflow
    workflow = (
        WorkflowBuilder()
        .add_executor(venue_exec)
        .add_executor(request_info)
        .add_executor(venue_hitl)
        # Sequential flow: Agent → HITL Wrapper → Next Agent
        .add_edge(coordinator_exec, venue_exec)
        .add_edge(venue_exec, venue_hitl)
        .add_edge(venue_hitl, budget_exec)
        # Bidirectional HITL edges: Wrapper ←→ RequestInfoExecutor
        .add_edge(venue_hitl, request_info)
        .add_edge(request_info, venue_hitl)
        .build()
    )
```

**Edge Pattern**:
- **Sequential**: `AgentExecutor` → `HumanInLoopAgentExecutor` → `Next AgentExecutor`
- **Bidirectional**: `HumanInLoopAgentExecutor` ←→ `RequestInfoExecutor`

## Agent Prompt Updates

Each specialist agent prompt receives guidance on using `request_user_input`:

**Example (Venue Specialist)**:
```
## User Interaction Tool

You have access to a `request_user_input` tool for requesting user input.

**When to use:**
- Event requirements are ambiguous
- Multiple strong venue options require user preference
- Specific constraints aren't clear

**How to use:**
request_user_input(
    prompt="Which venue do you prefer?",
    context={"venues": [...]},
    request_type="selection"
)

**Important:** Only request input when truly necessary.
```

Similar guidance added to: `budget_analyst.py`, `catering_coordinator.py`, `logistics_manager.py`

## Execution Flow Examples

### Scenario 1: Ambiguous Request with User Input

**User**: "Plan a party for 30 people"

1. EventCoordinator analyzes → delegates to VenueSpecialist
2. VenueSpecialist researches venues → finds 3 options
3. VenueSpecialist calls `request_user_input`:
   ```python
   request_user_input(
       prompt="I found 3 venues. Which do you prefer?",
       context={"venues": [venue_a, venue_b, venue_c]},
       request_type="selection"
   )
   ```
4. VenueHITL wrapper intercepts tool call → emits `UserElicitationRequest`
5. RequestInfoExecutor emits `RequestInfoEvent` → workflow pauses
6. DevUI displays prompt to user
7. User selects "Venue B"
8. RequestInfoExecutor sends `RequestResponse` to VenueHITL
9. VenueHITL continues workflow with user's choice
10. BudgetAnalyst receives context with selected venue
11. Workflow continues...

### Scenario 2: Detailed Request without User Input

**User**: "Plan a corporate team building event for 30 people, budget $3000, downtown Seattle, Friday evening in 3 weeks, vegetarian and gluten-free options required"

1. EventCoordinator delegates to specialists
2. VenueSpecialist has all context → recommends venue without calling tool
3. BudgetAnalyst has budget → allocates without calling tool
4. CateringCoordinator has dietary requirements → plans menu without calling tool
5. LogisticsManager has date/time → creates timeline without calling tool
6. Workflow completes without user interaction

## Testing Strategy

### Unit Tests (`tests/test_workflow_user_handoff.py`)

1. **Tool Call Detection**: Verify `HumanInLoopAgentExecutor._extract_user_request()` correctly parses `FunctionCallContent`
2. **Message Emission**: Test executor emits `UserElicitationRequest` when tool call detected
3. **Workflow Construction**: Verify workflow builds with HITL wrappers and edges

### Integration Tests

1. **With User Input**: Test workflow handles `RequestInfoEvent` and completes after user response
2. **Without User Input**: Test workflow completes when agents don't call tool
3. **Multiple Requests**: Test multiple agents requesting input sequentially

### DevUI Validation (Manual via Playwright MCP)

1. Start DevUI: `uv run devui`
2. Submit ambiguous request: "Plan a party for 40 people"
3. Verify `RequestInfoEvent` appears in DevUI
4. Provide user response via DevUI form
5. Verify workflow resumes and completes
6. Submit detailed request with all context
7. Verify workflow completes without user prompts

## Implementation Checklist

- [ ] Create `src/spec2agent/tools/user_input.py` with `request_user_input` function
- [ ] Create `src/spec2agent/workflow/messages.py` with `UserElicitationRequest` dataclass
- [ ] Create `src/spec2agent/workflow/executors.py` with `HumanInLoopAgentExecutor` class
- [ ] Update `src/spec2agent/workflow/core.py` to integrate HITL wrappers and edges
- [ ] Update `src/spec2agent/prompts/venue_specialist.py` with tool usage guidance
- [ ] Update `src/spec2agent/prompts/budget_analyst.py` with tool usage guidance
- [ ] Update `src/spec2agent/prompts/catering_coordinator.py` with tool usage guidance
- [ ] Update `src/spec2agent/prompts/logistics_manager.py` with tool usage guidance
- [ ] Create `tests/test_workflow_user_handoff.py` with unit tests
- [ ] Run unit tests: `uv run pytest tests/test_workflow_user_handoff.py`
- [ ] Run integration tests: `uv run pytest tests/test_workflow_integration.py`
- [ ] Validate in DevUI using Playwright MCP
- [ ] Update `specs/workflow-skeleton.md` Progress section with completion status

## Alternative Approaches Considered

### 1. Marker-Based Detection (Rejected)
- Agents output text markers like `REQUEST_USER_INPUT: venue_selection`
- Executors parse text responses
- **Rejected**: Unreliable, requires complex regex, easy to miss markers

### 2. Structured Output Parsing (Rejected)
- Agents output JSON blocks for user requests
- Executors parse JSON
- **Rejected**: Requires agents to produce valid JSON, error-prone, complex

### 3. Prompt-Only Approach (Rejected)
- Update prompts to guide agents on requesting input
- No custom executors
- **Rejected**: Agents cannot directly emit `RequestInfoMessage` per framework design

### 4. Tool-Based Approach (✅ SELECTED)
- Agents call `request_user_input` tool
- Custom executors intercept tool calls via `FunctionCallContent`
- **Selected**: Most reliable, clear agent interface, programmatic detection

## Future Enhancements

1. **Specialized Message Types**: Add `VenueSelectionRequest`, `BudgetApprovalRequest` for stronger typing
2. **Conditional HITL**: Add configuration to enable/disable user handoff per agent
3. **Timeout Handling**: Auto-continue workflow if user doesn't respond within timeout
4. **Response Validation**: Validate user responses match expected format (e.g., venue selection from list)
5. **Multi-Turn Clarification**: Allow agents to ask follow-up questions if initial response insufficient
6. **Checkpoint Integration**: Save/restore workflow state during user handoff for resilience

## References

### Agent Framework Documentation
- DeepWiki: RequestInfoExecutor and RequestInfoMessage
- DeepWiki: FunctionCallContent structure and tool call detection
- DeepWiki: Workflows and Orchestration patterns

### Sample Code
- `third_party/agent-framework/python/samples/getting_started/workflows/human-in-the-loop/guessing_game_with_human_input.py`
- `third_party/agent-framework/python/samples/getting_started/workflows/agents/workflow_as_agent_human_in_the_loop.py`
- `azure_chat_agents_tool_calls_with_feedback.py` (DraftFeedbackCoordinator pattern)

### Related Specifications
- `specs/workflow-skeleton.md` (Phase 6: Human-in-the-Loop User Handoff)
- `specs/PLANS.md` (ExecPlan documentation standards)
