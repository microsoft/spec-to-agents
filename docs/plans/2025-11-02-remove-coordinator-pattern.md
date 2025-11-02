# Remove Old Coordinator Pattern Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove EventPlanningCoordinator, event_coordinator agent, and SpecialistOutput model from codebase, simplifying to supervisor pattern only.

**Architecture:** Delete obsolete coordinator pattern components, update all 4 participant agents to remove SpecialistOutput structured output, keep convert_tool_content_to_text helper function.

**Tech Stack:** Python 3.11+, Agent Framework, Pydantic, pytest

---

## Task 1: Delete event_coordinator Agent Files

**Files:**
- Delete: `src/spec_to_agents/agents/event_coordinator.py`
- Delete: `src/spec_to_agents/prompts/event_coordinator.py`

**Step 1: Delete event_coordinator agent file**

Run: `rm src/spec_to_agents/agents/event_coordinator.py`

**Step 2: Delete event_coordinator prompt file**

Run: `rm src/spec_to_agents/prompts/event_coordinator.py`

**Step 3: Verify files deleted**

Run: `ls src/spec_to_agents/agents/event_coordinator.py 2>&1`
Expected: "No such file or directory"

Run: `ls src/spec_to_agents/prompts/event_coordinator.py 2>&1`
Expected: "No such file or directory"

**Step 4: Commit deletion**

```bash
git add -A
git commit -m "refactor: remove obsolete event_coordinator agent and prompt"
```

---

## Task 2: Remove EventPlanningCoordinator from executors.py

**Files:**
- Modify: `src/spec_to_agents/workflow/executors.py`

**Step 1: Read current executors.py**

Read: `src/spec_to_agents/workflow/executors.py`
Note: Lines 1-87 contain helper function, lines 90-410 contain EventPlanningCoordinator class

**Step 2: Remove SpecialistOutput import and EventPlanningCoordinator class**

Remove lines 23 (SpecialistOutput import) and 90-410 (entire EventPlanningCoordinator class).

Keep:
- Copyright header (lines 1-2)
- Module docstring (line 3) - update to just describe helper function
- All imports except SpecialistOutput (lines 4-21, minus line 23)
- `convert_tool_content_to_text` function (lines 26-87)

New module docstring:
```python
"""Utility functions for event planning workflow."""
```

Remove SpecialistOutput from imports:
```python
# Before (line 23):
from spec_to_agents.models.messages import HumanFeedbackRequest, SpecialistOutput

# After:
from spec_to_agents.models.messages import HumanFeedbackRequest
```

**Step 3: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/workflow/executors.py`
Expected: No output (success)

**Step 4: Run type checking**

Run: `uv run mypy src/spec_to_agents/workflow/executors.py`
Expected: "Success: no issues found"

**Step 5: Commit changes**

```bash
git add src/spec_to_agents/workflow/executors.py
git commit -m "refactor: remove EventPlanningCoordinator class, keep helper function"
```

---

## Task 3: Remove SpecialistOutput Model from messages.py

**Files:**
- Modify: `src/spec_to_agents/models/messages.py`

**Step 1: Read current messages.py**

Read: `src/spec_to_agents/models/messages.py`
Note: Lines 52-83 contain SpecialistOutput class

**Step 2: Remove SpecialistOutput class**

Delete lines 52-83 (entire SpecialistOutput class including docstring and examples).

Keep:
- HumanFeedbackRequest dataclass (lines 12-49)
- SupervisorDecision class (lines 85-123)

**Step 3: Update __all__ export**

Change line 125:
```python
# Before:
__all__ = ["HumanFeedbackRequest", "SpecialistOutput", "SupervisorDecision"]

# After:
__all__ = ["HumanFeedbackRequest", "SupervisorDecision"]
```

**Step 4: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/models/messages.py`
Expected: No output (success)

**Step 5: Run type checking**

Run: `uv run mypy src/spec_to_agents/models/messages.py`
Expected: "Success: no issues found"

**Step 6: Commit changes**

```bash
git add src/spec_to_agents/models/messages.py
git commit -m "refactor: remove SpecialistOutput model"
```

---

## Task 4: Update budget_analyst.py Agent

**Files:**
- Modify: `src/spec_to_agents/agents/budget_analyst.py`

**Step 1: Read current budget_analyst.py**

Read: `src/spec_to_agents/agents/budget_analyst.py`

**Step 2: Remove SpecialistOutput import**

Remove this import (around line 6):
```python
from spec_to_agents.models.messages import SpecialistOutput
```

**Step 3: Remove response_format parameter**

In the `client.create_agent()` call, remove the `response_format=SpecialistOutput,` line.

Before:
```python
return client.create_agent(
    name="BudgetAnalyst",
    instructions=budget_analyst.SYSTEM_PROMPT,
    tools=agent_tools,
    response_format=SpecialistOutput,
    store=True,
)
```

After:
```python
return client.create_agent(
    name="BudgetAnalyst",
    instructions=budget_analyst.SYSTEM_PROMPT,
    tools=agent_tools,
    store=True,
)
```

**Step 4: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/agents/budget_analyst.py`
Expected: No output (success)

**Step 5: Run type checking**

Run: `uv run mypy src/spec_to_agents/agents/budget_analyst.py`
Expected: "Success: no issues found"

**Step 6: Commit changes**

```bash
git add src/spec_to_agents/agents/budget_analyst.py
git commit -m "refactor: remove SpecialistOutput from budget_analyst agent"
```

---

## Task 5: Update catering_coordinator.py Agent

**Files:**
- Modify: `src/spec_to_agents/agents/catering_coordinator.py`

**Step 1: Read current catering_coordinator.py**

Read: `src/spec_to_agents/agents/catering_coordinator.py`

**Step 2: Remove SpecialistOutput import**

Remove this import:
```python
from spec_to_agents.models.messages import SpecialistOutput
```

**Step 3: Remove response_format parameter**

In the `client.create_agent()` call, remove the `response_format=SpecialistOutput,` line.

Before:
```python
return client.create_agent(
    name="CateringCoordinator",
    instructions=catering_coordinator.SYSTEM_PROMPT,
    tools=agent_tools,
    response_format=SpecialistOutput,
    store=True,
)
```

After:
```python
return client.create_agent(
    name="CateringCoordinator",
    instructions=catering_coordinator.SYSTEM_PROMPT,
    tools=agent_tools,
    store=True,
)
```

**Step 4: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/agents/catering_coordinator.py`
Expected: No output (success)

**Step 5: Run type checking**

Run: `uv run mypy src/spec_to_agents/agents/catering_coordinator.py`
Expected: "Success: no issues found"

**Step 6: Commit changes**

```bash
git add src/spec_to_agents/agents/catering_coordinator.py
git commit -m "refactor: remove SpecialistOutput from catering_coordinator agent"
```

---

## Task 6: Update logistics_manager.py Agent

**Files:**
- Modify: `src/spec_to_agents/agents/logistics_manager.py`

**Step 1: Read current logistics_manager.py**

Read: `src/spec_to_agents/agents/logistics_manager.py`

**Step 2: Remove SpecialistOutput import**

Remove this import:
```python
from spec_to_agents.models.messages import SpecialistOutput
```

**Step 3: Remove response_format parameter**

In the `client.create_agent()` call, remove the `response_format=SpecialistOutput,` line.

Before:
```python
return client.create_agent(
    name="LogisticsManager",
    instructions=logistics_manager.SYSTEM_PROMPT,
    tools=agent_tools,
    response_format=SpecialistOutput,
    store=True,
)
```

After:
```python
return client.create_agent(
    name="LogisticsManager",
    instructions=logistics_manager.SYSTEM_PROMPT,
    tools=agent_tools,
    store=True,
)
```

**Step 4: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/agents/logistics_manager.py`
Expected: No output (success)

**Step 5: Run type checking**

Run: `uv run mypy src/spec_to_agents/agents/logistics_manager.py`
Expected: "Success: no issues found"

**Step 6: Commit changes**

```bash
git add src/spec_to_agents/agents/logistics_manager.py
git commit -m "refactor: remove SpecialistOutput from logistics_manager agent"
```

---

## Task 7: Update venue_specialist.py Agent

**Files:**
- Modify: `src/spec_to_agents/agents/venue_specialist.py`

**Step 1: Read current venue_specialist.py**

Read: `src/spec_to_agents/agents/venue_specialist.py`

**Step 2: Remove SpecialistOutput import**

Remove this import (line 6):
```python
from spec_to_agents.models.messages import SpecialistOutput
```

**Step 3: Remove response_format parameter**

In the `client.create_agent()` call, remove the `response_format=SpecialistOutput,` line.

Before:
```python
return client.create_agent(
    name="VenueSpecialist",
    instructions=venue_specialist.SYSTEM_PROMPT,
    tools=agent_tools,
    response_format=SpecialistOutput,
    store=True,
)
```

After:
```python
return client.create_agent(
    name="VenueSpecialist",
    instructions=venue_specialist.SYSTEM_PROMPT,
    tools=agent_tools,
    store=True,
)
```

**Step 4: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/agents/venue_specialist.py`
Expected: No output (success)

**Step 5: Run type checking**

Run: `uv run mypy src/spec_to_agents/agents/venue_specialist.py`
Expected: "Success: no issues found"

**Step 6: Commit changes**

```bash
git add src/spec_to_agents/agents/venue_specialist.py
git commit -m "refactor: remove SpecialistOutput from venue_specialist agent"
```

---

## Task 8: Update Container Wiring Configuration

**Files:**
- Modify: `src/spec_to_agents/container.py`

**Step 1: Read current container.py**

Read: `src/spec_to_agents/container.py`

**Step 2: Remove event_coordinator from wiring_config**

In the `wiring_config` section, remove the line:
```python
"spec_to_agents.agents.event_coordinator",
```

Before:
```python
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
```

After:
```python
wiring_config = containers.WiringConfiguration(
    modules=[
        "spec_to_agents.agents.budget_analyst",
        "spec_to_agents.agents.catering_coordinator",
        "spec_to_agents.agents.logistics_manager",
        "spec_to_agents.agents.venue_specialist",
        "spec_to_agents.agents.supervisor",
        "spec_to_agents.workflow.core",
    ]
)
```

**Step 3: Verify syntax**

Run: `uv run python -m py_compile src/spec_to_agents/container.py`
Expected: No output (success)

**Step 4: Run type checking**

Run: `uv run mypy src/spec_to_agents/container.py`
Expected: "Success: no issues found"

**Step 5: Commit changes**

```bash
git add src/spec_to_agents/container.py
git commit -m "refactor: remove event_coordinator from DI wiring config"
```

---

## Task 9: Check for Remaining References

**Files:**
- Check: All source and test files

**Step 1: Search for EventPlanningCoordinator references**

Run: `grep -r "EventPlanningCoordinator" src/ tests/ 2>/dev/null || echo "No references found"`
Expected: "No references found"

If references found: Note files for manual review/update

**Step 2: Search for SpecialistOutput references**

Run: `grep -r "SpecialistOutput" src/ tests/ 2>/dev/null || echo "No references found"`
Expected: "No references found"

If references found: Note files for manual review/update

**Step 3: Search for event_coordinator references**

Run: `grep -r "event_coordinator" src/ tests/ --include="*.py" 2>/dev/null || echo "No references found"`
Expected: "No references found"

If references found: Note files for manual review/update

**Step 4: Document findings**

If any references remain, create list of files that need manual updates.

---

## Task 10: Update Tests

**Files:**
- Modify/Remove: Test files with references to removed components

**Step 1: Find test files with references**

Run: `grep -l "EventPlanningCoordinator\|SpecialistOutput\|event_coordinator" tests/*.py 2>/dev/null`

Expected files to check:
- `tests/test_workflow_executors.py`
- `tests/test_agents_module.py`

**Step 2: Update test_workflow_executors.py (if exists)**

If file tests EventPlanningCoordinator:
- Remove all tests for EventPlanningCoordinator class
- Keep tests for `convert_tool_content_to_text` helper function

**Step 3: Update test_agents_module.py (if exists)**

If file imports event_coordinator:
- Remove event_coordinator imports
- Remove tests that create event_coordinator agent

**Step 4: Run updated tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass (some may be removed, remaining should pass)

**Step 5: Commit test updates**

```bash
git add tests/
git commit -m "test: remove tests for obsolete coordinator pattern"
```

---

## Task 11: Full Validation Suite

**Files:**
- All modified files

**Step 1: Run full type checking**

Run: `uv run mypy .`
Expected: "Success: no issues found"

**Step 2: Run linting**

Run: `uv run ruff check .`
Expected: No errors

Run: `uv run ruff format .`
Expected: Files reformatted (if needed)

**Step 3: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 4: Verify no remaining references**

Run:
```bash
grep -r "EventPlanningCoordinator" src/ tests/ 2>/dev/null && echo "FOUND REFERENCES" || echo "Clean"
grep -r "SpecialistOutput" src/ tests/ 2>/dev/null && echo "FOUND REFERENCES" || echo "Clean"
grep -r "event_coordinator" src/ tests/ --include="*.py" 2>/dev/null && echo "FOUND REFERENCES" || echo "Clean"
```

Expected: "Clean" for all three

**Step 5: Manual smoke test**

Run: `uv run app`
Navigate to event planning workflow in DevUI
Submit test prompt: "Plan a corporate party for 50 people"
Expected: Workflow executes successfully with supervisor routing

---

## Task 12: Final Commit and Summary

**Files:**
- All files

**Step 1: Review git status**

Run: `git status`
Expected: No uncommitted changes (all committed in individual tasks)

**Step 2: Review commit history**

Run: `git log --oneline -15`
Expected: See all commits from this refactor

**Step 3: Create summary of changes**

Document:
- Files deleted: 2 (event_coordinator agent and prompt)
- Files modified: 7 (executors.py, messages.py, 4 agents, container.py)
- Lines removed: ~410 total
- Tests updated: As needed
- All validation passing

**Step 4: Verify branch is ready**

Branch `alexlavaee/feature/supervisor-workflow` is ready for PR review.

---

## Validation Checklist

- [ ] EventPlanningCoordinator class removed
- [ ] event_coordinator agent files deleted
- [ ] SpecialistOutput model removed
- [ ] All 4 participant agents updated
- [ ] Container wiring config updated
- [ ] No grep results for removed components
- [ ] `uv run mypy .` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run pytest tests/ -v` passes
- [ ] Manual DevUI test successful

---

## Success Criteria

✅ ~410 lines of obsolete code removed
✅ Single workflow pattern (supervisor only)
✅ All type checking passes
✅ All linting passes
✅ All tests pass
✅ Workflow executes correctly in console/DevUI
