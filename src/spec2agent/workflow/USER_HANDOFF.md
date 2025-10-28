# User Handoff Implementation

This document describes the user handoff (human-in-the-loop) implementation for the event planning workflow.

## Overview

The workflow now supports user interaction capabilities, allowing specialist agents to request clarification, approval, or selection from users during event planning. This implementation follows a two-phase approach:

- **Phase 1 (Current)**: Prompt-based user interaction guidance
- **Phase 2 (Future)**: Programmatic user handoff with custom executors

## Phase 1: Prompt-Based Approach

### What Was Implemented

1. **Custom RequestInfoMessage Types** (`src/spec2agent/workflow/messages.py`)
   - `UserElicitationRequest`: General-purpose user input request
   - `VenueSelectionRequest`: Venue selection from options
   - `BudgetApprovalRequest`: Budget allocation approval
   - `CateringApprovalRequest`: Menu and dietary approval

2. **Updated Agent Prompts**
   - Each specialist agent (Venue, Budget, Catering, Logistics) now includes:
     - "User Interaction Guidelines" section
     - Examples of when to request user input
     - Instructions on formulating clear questions
     - Guidance on incorporating user responses

3. **Test Suite** (`tests/test_workflow_user_handoff.py`)
   - Validates workflow builds successfully
   - Tests RequestInfoMessage type definitions
   - Foundation for integration testing

### How It Works

Agents are instructed via system prompts to identify situations where user input would be valuable:

**Venue Specialist** may request input for:
- Selection between multiple viable venue options
- Clarification on location preferences
- Priority decisions when budget constrains choices

**Budget Analyst** may request input for:
- Approval of budget allocation
- Prioritization when budget is tight
- Reallocation between categories

**Catering Coordinator** may request input for:
- Menu theme or cuisine selection
- Service style preferences (buffet vs plated)
- Dietary restriction clarifications

**Logistics Manager** may request input for:
- Event date/time confirmation
- Staffing preferences (professional vs volunteer)
- Timeline adjustments

### Design Principles

1. **Opt-in Interaction**: Agents decide when user input is needed, not hardcoded
2. **Graceful Degradation**: Workflow can complete without user input if context is sufficient
3. **Clear Communication**: User prompts are explicit and provide necessary context
4. **Type Safety**: Pydantic/dataclass for RequestInfoMessage types
5. **Minimal Changes**: Foundation in place without disrupting existing workflow

## Phase 2: Programmatic Handoff (Future Enhancement)

Phase 2 would add custom executors that programmatically detect when user input is needed and route through `RequestInfoExecutor`:

### Planned Enhancements

1. **Custom Executor Wrappers**
   ```python
   class VenueSpecialistWithHandoff(Executor):
       def __init__(self, agent, request_info_id: str):
           self.agent_executor = AgentExecutor(agent=agent)
           self.request_info_id = request_info_id
       
       @handler
       async def process(self, request: AgentExecutorRequest, ctx):
           # Run agent
           response = await self.agent_executor.run(request)
           
           # Check if user input needed (parse agent response)
           if self._needs_user_selection(response):
               await ctx.send_message(
                   VenueSelectionRequest(...),
                   target_id=self.request_info_id
               )
           else:
               await ctx.send_message(response)
   ```

2. **RequestInfoExecutor Integration**
   - Add `RequestInfoExecutor` to workflow
   - Create bidirectional edges between specialists and RequestInfoExecutor
   - Handle `RequestResponse` routing back to specialists

3. **DevUI Integration**
   - DevUI automatically handles `RequestInfoEvent`s
   - Users see prompts and provide responses via UI
   - Workflow pauses/resumes transparently

4. **Checkpoint Support**
   - Enable workflow persistence during user handoff
   - Allow workflows to pause and resume across sessions

## Usage Examples

### Phase 1: Current Behavior

Agents include context in their responses when user input would be valuable:

```
VenueSpecialist: "I've identified 3 excellent venues:
1. Downtown Conference Center - $2000, 50 capacity
2. Garden Event Space - $1500, 40 capacity
3. Rooftop Lounge - $2500, 60 capacity

Based on your budget and attendee count, I recommend Option 2 for best value,
but if ambiance is a priority, Option 3 offers a unique experience. Please let
me know your preference."
```

Users can respond with their choice, and the workflow continues.

### Phase 2: Programmatic Handoff

DevUI would automatically detect and display:

```
🔔 User Input Requested

Venue Specialist needs your decision:

Please select your preferred venue:
○ Downtown Conference Center ($2000, 50 capacity)
● Garden Event Space ($1500, 40 capacity) [Recommended]
○ Rooftop Lounge ($2500, 60 capacity)

[Submit] [Cancel]
```

## Testing

### Run Tests

```bash
# All workflow tests
uv run pytest tests/test_workflow.py -v

# User handoff tests
uv run pytest tests/test_workflow_user_handoff.py -v

# Specific test
uv run pytest tests/test_workflow_user_handoff.py::test_workflow_builds_with_user_handoff -v
```

### Manual Testing with DevUI

```bash
# Start DevUI
uv run devui

# Test scenarios:
# 1. Detailed request (minimal user interaction needed)
"Plan a corporate team building event for 30 people, budget $3000,
location Downtown Seattle, vegetarian and gluten-free options,
3 weeks from now, Friday evening"

# 2. Ambiguous request (may trigger agent requests for clarification)
"Plan an event for 40 people"
```

## Files Modified

- `src/spec2agent/workflow/messages.py` - NEW: RequestInfoMessage types
- `src/spec2agent/workflow/core.py` - Updated docstring
- `src/spec2agent/prompts/venue_specialist.py` - Added user interaction guidelines
- `src/spec2agent/prompts/budget_analyst.py` - Added user interaction guidelines
- `src/spec2agent/prompts/catering_coordinator.py` - Added user interaction guidelines
- `src/spec2agent/prompts/logistics_manager.py` - Added user interaction guidelines
- `tests/test_workflow_user_handoff.py` - NEW: Test suite

## References

- Spec: `specs/workflow-skeleton.md` (Phase 6)
- Agent Framework Samples:
  - `third_party/agent-framework/python/samples/getting_started/workflows/human-in-the-loop/`
  - `third_party/agent-framework/python/samples/getting_started/workflows/agents/workflow_as_agent_human_in_the_loop.py`
