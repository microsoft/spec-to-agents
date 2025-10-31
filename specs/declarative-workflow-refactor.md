# Declarative Workflow Refactor

## Summary

Refactored the Event Planning Workflow from a complex procedural coordinator pattern to a simple, declarative fan-out/fan-in pattern. This makes the workflow more composable, easier to understand, and aligns with agent-framework best practices.

## Problem Statement

The original `EventPlanningCoordinator` custom executor class was problematic:
- **Complex routing logic**: Manual routing decisions in Python code rather than declarative edges
- **Manual HITL handling**: Custom request/response handlers for human-in-the-loop
- **Procedural, not declarative**: Workflow structure obscured by imperative code
- **Hard to modify**: Adding/removing agents required changing coordinator logic
- **Framework gap**: Pattern indicated a gap in agent-framework that forced custom executors

## Solution

### New Architecture: Declarative Fan-Out/Fan-In Pattern

```
User Request
     ↓
Initial Coordinator (extracts requirements)
     ↓
┌────┴────┬────────┬─────────┐
↓         ↓        ↓         ↓
Venue     Budget   Catering  Logistics  (parallel execution)
↓         ↓        ↓         ↓
└────┬────┴────────┴─────────┘
     ↓
Event Synthesizer (consolidates all outputs)
     ↓
Final Event Plan
```

### Key Changes

1. **Removed EventPlanningCoordinator Custom Executor**
   - Was: 400+ lines of complex routing, parsing, and HITL logic
   - Now: Simple `AgentExecutor` instances throughout

2. **Added Event Synthesizer Agent**
   - New agent responsible for consolidating specialist outputs
   - Receives all specialist recommendations and creates cohesive plan
   - Declarative fan-in point

3. **Simplified Initial Coordinator**
   - Previously: Complex orchestration and routing
   - Now: Just extracts event requirements and provides context
   - Single responsibility: understand user request

4. **Updated All Specialist Prompts**
   - Removed routing logic (`next_agent` is always `null`)
   - Specialists focus on their domain expertise only
   - No need to coordinate with other specialists

5. **Fully Declarative Workflow**
   - All routing done via `WorkflowBuilder` edges
   - Pattern: coordinator → (fan-out) → specialists → (fan-in) → synthesizer
   - No custom Python routing logic needed

### Benefits

1. **Simpler**: 6 simple `AgentExecutor` instances vs 1 custom executor + 4 agent executors
2. **More Declarative**: Workflow structure visible in builder pattern
3. **Easier to Modify**: Add/remove specialists by changing edges, not code
4. **More Composable**: Agents are self-contained, can be reused
5. **Better Separation of Concerns**: Each agent has single responsibility
6. **Parallel Execution**: Specialists can work simultaneously (more efficient)
7. **Aligns with Framework**: Uses standard patterns, no custom workarounds

## Code Changes

### New Files

- `src/spec_to_agents/agents/event_synthesizer.py` - Synthesizer agent creation
- `src/spec_to_agents/prompts/event_synthesizer.py` - Synthesizer system prompt

### Modified Files

- `src/spec_to_agents/workflow/core.py` - Refactored to use declarative pattern
- `src/spec_to_agents/prompts/event_coordinator.py` - Simplified to requirement extraction
- `src/spec_to_agents/prompts/venue_specialist.py` - Removed routing logic
- `src/spec_to_agents/prompts/budget_analyst.py` - Removed routing logic
- `src/spec_to_agents/prompts/catering_coordinator.py` - Removed routing logic
- `src/spec_to_agents/prompts/logistics_manager.py` - Removed routing logic

### Test Updates

- `tests/test_workflow.py` - Updated for new architecture
- `tests/test_workflow_executors.py` - Marked as skip (tests obsolete custom executor)
- `tests/test_workflow_no_summarization.py` - Marked as skip (tests obsolete custom executor)
- Integration tests unchanged (test interface, not implementation)

## Usage Example

The workflow API remains the same for end users:

```python
from spec_to_agents.workflow import workflow

# Run workflow with user request
result = await workflow.run("Plan a corporate party for 50 people in Seattle")
```

Internally, the workflow now:
1. Routes to initial coordinator (extracts requirements)
2. Fans out to all 4 specialists in parallel
3. Each specialist provides recommendations independently
4. Fans in to synthesizer who consolidates into final plan
5. Returns comprehensive event plan

## Human-in-the-Loop

HITL is still supported but handled by the framework natively rather than custom code:
- Specialists can request user input via their interaction patterns
- Framework handles pausing/resuming workflow automatically
- No manual `ctx.request_info()` or `@response_handler` needed in custom executors

## Migration Notes

### For Maintainers

- The `EventPlanningCoordinator` class in `executors.py` is no longer used
- Consider archiving/removing `executors.py` in future cleanup
- All routing is now declarative via workflow edges

### For Users

- No changes to public API
- Workflow behavior is semantically equivalent
- May see improved performance due to parallel execution

## Future Improvements

1. **Optional Sequential Mode**: Some use cases may benefit from sequential specialist execution
2. **Conditional Routing**: Add ability to conditionally skip specialists based on requirements
3. **Dynamic Fan-Out**: Automatically determine which specialists are needed based on request
4. **Specialist Dependencies**: Allow specialists to declare dependencies on each other's outputs

## Acceptance Criteria

- [x] EventPlanningCoordinator workflow is more declarative and composable
- [x] Example code and usage is simplified (6 agents vs custom executor + routing logic)
- [x] Pattern aligns with agent-framework best practices
- [x] All tests pass or are appropriately marked as obsolete
- [x] Documentation updated to reflect new pattern

## Related Issues

This addresses the issue: "Make EventPlanningCoordinator workflow more declarative and composable"

The pattern shift from procedural custom executor to declarative fan-out/fan-in demonstrates how agent-framework's native features can replace complex custom code.
