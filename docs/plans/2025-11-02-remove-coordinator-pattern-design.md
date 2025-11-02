# Remove Old Coordinator Pattern and SpecialistOutput Design

**Date:** 2025-11-02
**Status:** Approved
**Author:** Claude Code

## Overview

Remove the obsolete EventPlanningCoordinator pattern and SpecialistOutput model from the codebase now that the supervisor pattern has been fully implemented. This cleanup eliminates ~320 lines of dead code and simplifies the participant agent interface.

## Problem Statement

The codebase currently contains two workflow orchestration patterns:

1. **Old Pattern (EventPlanningCoordinator)**: Coordinator-centric with hardcoded routing logic
   - Specialists return `SpecialistOutput` with `next_agent` field for routing
   - Coordinator has explicit routing methods and state management
   - Used previously by `build_event_planning_workflow()`

2. **New Pattern (SupervisorOrchestratorExecutor)**: Supervisor agent makes routing decisions
   - Supervisor agent uses `SupervisorDecision` structured output
   - Participants use natural language responses (no routing logic)
   - Currently used by `build_event_planning_workflow()`

**Issues with keeping both:**
- Dead code confusion about which pattern to use
- Maintenance burden of keeping unused components
- Participants unnecessarily constrained by `SpecialistOutput` structured output
- Tests covering obsolete behavior

## Design Goals

1. Remove all EventPlanningCoordinator pattern artifacts
2. Remove SpecialistOutput model entirely
3. Simplify participant agents to use natural text responses
4. Update tests to only cover supervisor pattern
5. Keep useful utilities (convert_tool_content_to_text)

## Architecture

### Components to Remove

#### 1. EventPlanningCoordinator Class
**Location:** `src/spec_to_agents/workflow/executors.py` (lines 90-410)

**Removal rationale:**
- Replaced by `SupervisorOrchestratorExecutor` in `workflow/supervisor.py`
- Contains ~320 lines of hardcoded routing logic
- Not referenced by current `build_event_planning_workflow()`
- Three handler methods (`start`, `on_specialist_response`, `on_human_feedback`) now handled by supervisor

**Dependencies:**
- Used `SpecialistOutput` model (also being removed)
- Used `convert_tool_content_to_text()` helper (keeping this - still needed by supervisor)

#### 2. event_coordinator Agent

**Files to delete:**
- `src/spec_to_agents/agents/event_coordinator.py`
- `src/spec_to_agents/prompts/event_coordinator.py`

**Removal rationale:**
- Only used by EventPlanningCoordinator for synthesis
- Supervisor agent now handles both routing and synthesis
- Not included in current workflow builder's participant list

#### 3. SpecialistOutput Model
**Location:** `src/spec_to_agents/models/messages.py` (lines 52-83)

**Removal rationale:**
- Forced participants to manage workflow routing logic
- Supervisor pattern centralizes routing in supervisor agent
- Participants should focus on domain expertise, not orchestration
- No longer used by any participant agents after this refactor

**Model structure (for reference):**
```python
class SpecialistOutput(BaseModel):
    summary: str
    next_agent: str | None
    user_input_needed: bool
    user_prompt: str | None
```

### Components to Modify

#### 1. Participant Agents (4 files)

All participant agents require identical changes:

**Files:**
- `src/spec_to_agents/agents/budget_analyst.py`
- `src/spec_to_agents/agents/catering_coordinator.py`
- `src/spec_to_agents/agents/logistics_manager.py`
- `src/spec_to_agents/agents/venue_specialist.py`

**Changes per file:**
1. Remove import: `from spec_to_agents.models.messages import SpecialistOutput`
2. Remove parameter: `response_format=SpecialistOutput` from `client.create_agent()` call

**Example change (venue_specialist.py):**

Before:
```python
from spec_to_agents.models.messages import SpecialistOutput

return client.create_agent(
    name="VenueSpecialist",
    instructions=venue_specialist.SYSTEM_PROMPT,
    tools=agent_tools,
    response_format=SpecialistOutput,  # ← Remove this
    store=True,
)
```

After:
```python
# SpecialistOutput import removed

return client.create_agent(
    name="VenueSpecialist",
    instructions=venue_specialist.SYSTEM_PROMPT,
    tools=agent_tools,
    store=True,  # response_format removed - use natural text
)
```

**Effect:**
- Agents return plain text responses focused on their domain
- No need to populate routing fields (next_agent, user_input_needed)
- Simpler agent prompts can be written without routing instructions

#### 2. Module Exports

**File:** `src/spec_to_agents/models/messages.py`

Update `__all__` to remove SpecialistOutput:

```python
# Before:
__all__ = ["HumanFeedbackRequest", "SpecialistOutput", "SupervisorDecision"]

# After:
__all__ = ["HumanFeedbackRequest", "SupervisorDecision"]
```

#### 3. executors.py Module

**File:** `src/spec_to_agents/workflow/executors.py`

**Keep:**
- Module docstring
- `convert_tool_content_to_text()` function (lines 26-87)
- Import statements needed for that function

**Remove:**
- `EventPlanningCoordinator` class (lines 90-410)
- Import of `SpecialistOutput` from messages

**Result:** Module becomes a simple utility module with just the helper function.

#### 4. Container Wiring Configuration

**File:** `src/spec_to_agents/container.py`

Remove `event_coordinator` from wiring_config modules list:

```python
wiring_config = containers.WiringConfiguration(
    modules=[
        "spec_to_agents.agents.budget_analyst",
        "spec_to_agents.agents.catering_coordinator",
        "spec_to_agents.agents.event_coordinator",  # ← Remove this line
        "spec_to_agents.agents.logistics_manager",
        "spec_to_agents.agents.venue_specialist",
        "spec_to_agents.agents.supervisor",
        "spec_to_agents.workflow.core",
    ]
)
```

### Test Updates

#### Tests to Remove/Update

**Search patterns:**
- Files importing `EventPlanningCoordinator`
- Files importing `SpecialistOutput`
- Tests creating `event_coordinator` agent
- Tests validating specialist routing logic

**Expected test files to modify:**
- `tests/test_workflow_executors.py` - May test EventPlanningCoordinator
- `tests/test_workflow.py` - Integration tests (should still work)
- `tests/test_agents_module.py` - May import event_coordinator
- Any tests verifying SpecialistOutput structure

**Strategy:**
1. Remove unit tests specific to EventPlanningCoordinator
2. Remove unit tests specific to SpecialistOutput validation
3. Keep integration tests using `build_event_planning_workflow()` (uses supervisor)
4. Add new tests if supervisor pattern lacks coverage

## Implementation Steps

### Phase 1: Remove Files
1. Delete `src/spec_to_agents/agents/event_coordinator.py`
2. Delete `src/spec_to_agents/prompts/event_coordinator.py`

### Phase 2: Update executors.py
1. Remove `SpecialistOutput` import
2. Remove `EventPlanningCoordinator` class (keep helper function)
3. Verify `convert_tool_content_to_text()` remains intact

### Phase 3: Remove SpecialistOutput Model
1. Delete `SpecialistOutput` class from `messages.py`
2. Update `__all__` export list

### Phase 4: Update Participant Agents
1. Update `budget_analyst.py` - remove SpecialistOutput
2. Update `catering_coordinator.py` - remove SpecialistOutput
3. Update `logistics_manager.py` - remove SpecialistOutput
4. Update `venue_specialist.py` - remove SpecialistOutput

### Phase 5: Update Container Configuration
1. Remove `event_coordinator` from wiring_config in `container.py`

### Phase 6: Update Tests
1. Find tests importing removed components
2. Remove obsolete test cases
3. Verify integration tests still pass
4. Run full test suite

### Phase 7: Verification
1. Run type checking: `uv run mypy .`
2. Run linting: `uv run ruff .`
3. Run full test suite: `uv run pytest tests/ -v`
4. Manual smoke test via console: `uv run app`

## Verification Commands

```bash
# Check for remaining references to removed components
grep -r "EventPlanningCoordinator" src/ tests/
grep -r "SpecialistOutput" src/ tests/
grep -r "event_coordinator" src/ tests/

# Run validation suite
uv run mypy .
uv run ruff .
uv run pytest tests/ -v
```

Expected: No references found, all checks pass.

## Risk Mitigation

**Risk:** Breaking tests that depend on removed components
**Mitigation:** Run tests after each phase; integration tests should continue working since they use `build_event_planning_workflow()` which already uses supervisor pattern

**Risk:** Hidden dependencies on SpecialistOutput in external code
**Mitigation:** This is internal project code only; grep confirms all usage is in this repo

**Risk:** Participants don't respond correctly without structured output
**Mitigation:** Supervisor pattern is already working in current implementation; agents naturally provide domain responses

## Success Criteria

1. ✅ EventPlanningCoordinator class removed from executors.py
2. ✅ event_coordinator agent and prompt files deleted
3. ✅ SpecialistOutput model removed from messages.py
4. ✅ All 4 participant agents updated to remove SpecialistOutput
5. ✅ Container wiring config updated
6. ✅ All tests pass: `uv run pytest tests/`
7. ✅ Type checking passes: `uv run mypy .`
8. ✅ Linting passes: `uv run ruff .`
9. ✅ No grep results for removed component names
10. ✅ Console.py workflow executes successfully

## Benefits

**Code reduction:**
- ~320 lines removed from executors.py
- ~40 lines removed from event_coordinator agent
- ~30 lines removed from SpecialistOutput model
- ~20 lines removed from participant agents (4 files × 5 lines)
- **Total: ~410 lines of code removed**

**Simplification:**
- Single workflow pattern (supervisor) instead of two
- Participants focus on domain, not routing
- Clearer separation of concerns
- Easier onboarding (one pattern to learn)

**Maintainability:**
- No dead code to maintain
- No confusion about which pattern to use
- Reduced test surface area
- Cleaner import graph
