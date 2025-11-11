# Implementation Tasks: Entertainment Agent

## Task Organization

Tasks are organized by user story and include:
- **[P]** markers for tasks that can run in parallel
- File paths where implementation should occur
- Clear acceptance criteria for validation
- Dependencies between tasks

## User Story 1: Entertainment Research

### Task 1.1: Create System Prompt
**File**: `src/spec_to_agents/prompts/entertainment_specialist.py`  
**Dependencies**: None  
**Parallel**: Yes [P]

**Description:**
Create the system prompt module defining the Entertainment Specialist's expertise, decision-making process, and interaction modes.

**Implementation Steps:**
1. Create new file `src/spec_to_agents/prompts/entertainment_specialist.py`
2. Add copyright header matching other prompt files
3. Import `Final` from `typing`
4. Define `SYSTEM_PROMPT: Final[str]` constant with:
   - Core responsibilities section
   - Interaction modes (autonomous, collaborative, interactive)
   - Decision-making process (5 steps)
   - Available tools documentation
   - Structured output format with example
5. Follow the pattern from `prompts/logistics_manager.py`

**Acceptance Criteria:**
- [ ] File created with correct copyright header
- [ ] `SYSTEM_PROMPT` constant defined as `Final[str]`
- [ ] Prompt includes all required sections
- [ ] Follows existing prompt file structure

**Example Structure:**
```python
from typing import Final

SYSTEM_PROMPT: Final[str] = """
You are the Entertainment Specialist...

<core_responsibilities>
...
</core_responsibilities>

<interaction_modes>
...
</interaction_modes>
"""
```

---

### Task 1.2: Create Agent Creation Module
**File**: `src/spec_to_agents/agents/entertainment_specialist.py`  
**Dependencies**: Task 1.1 (needs system prompt)  
**Parallel**: No

**Description:**
Create the agent creation function using dependency injection pattern, integrating web search and optional MCP tool.

**Implementation Steps:**
1. Create new file `src/spec_to_agents/agents/entertainment_specialist.py`
2. Add copyright header
3. Import required types:
   ```python
   from typing import Any
   from agent_framework import BaseChatClient, ChatAgent, ToolProtocol
   from dependency_injector.wiring import Provide, inject
   from spec_to_agents.models.messages import SpecialistOutput
   from spec_to_agents.prompts import entertainment_specialist
   from spec_to_agents.tools import web_search
   ```
4. Define `create_agent()` function with `@inject` decorator
5. Use `Provide["client"]`, `Provide["global_tools"]`, `Provide["model_config"]` for DI
6. Add `web_search` to `agent_tools` list
7. Conditionally add MCP `sequential-thinking` tool
8. Return `client.create_agent()` with all parameters
9. Follow the pattern from `agents/venue_specialist.py`

**Acceptance Criteria:**
- [ ] File created with correct imports
- [ ] `@inject` decorator applied to `create_agent()`
- [ ] DI parameters use `Provide[...]` annotations
- [ ] `web_search` tool included in `agent_tools`
- [ ] MCP tool conditionally added with `global_tools.get("sequential-thinking")`
- [ ] Returns `ChatAgent` with correct configuration
- [ ] Docstring includes numpy-style Parameters and Returns sections

---

### Task 1.3: Create Executor Class
**File**: `src/spec_to_agents/workflow/executors.py`  
**Dependencies**: Task 1.2 (needs agent module)  
**Parallel**: No

**Description:**
Add `EntertainmentSpecialist` executor class to handle entertainment requests in the workflow.

**Implementation Steps:**
1. Open `src/spec_to_agents/workflow/executors.py`
2. Add new class `EntertainmentSpecialist(AgentExecutor)` after `LogisticsManager` class
3. Implement `__init__(self, entertainment_agent: ChatAgent)` method:
   - Call `super().__init__(id="entertainment")`
   - Store `self._agent = entertainment_agent`
4. Implement `@handler async def on_request(...)` method:
   - Accept `request: AgentExecutorRequest` and `ctx: WorkflowContext[...]`
   - Run agent: `result = await self._agent.run(request.messages)`
   - Parse output: `output = SpecialistOutput.model_validate_json(result.output)`
   - Log summary with `logger.info()`
   - Route back to coordinator with `ctx.send()`
5. Follow the pattern from `LogisticsManager` class

**Acceptance Criteria:**
- [ ] Class added after `LogisticsManager`
- [ ] Inherits from `AgentExecutor`
- [ ] ID set to "entertainment" in `__init__`
- [ ] `on_request` handler implements agent execution and routing
- [ ] Structured output parsing with `SpecialistOutput.model_validate_json()`
- [ ] Logging includes summary and next_agent info
- [ ] Returns to coordinator via `ctx.send()`

---

### Task 1.4: Integrate into Workflow Builder
**File**: `src/spec_to_agents/workflow/builder.py`  
**Dependencies**: Task 1.3 (needs executor class)  
**Parallel**: No

**Description:**
Update workflow builder to include Entertainment Specialist in the workflow topology.

**Implementation Steps:**
1. Open `src/spec_to_agents/workflow/builder.py`
2. Add import: `from spec_to_agents.agents import entertainment_specialist`
3. Update import list to include `entertainment_specialist` module
4. Inside `build_event_planning_workflow()` function:
   - Create executor: `entertainment = EntertainmentSpecialist(entertainment_specialist.create_agent())`
   - Add to workflow: `builder.add_executor(entertainment)`
   - Add bidirectional edges:
     ```python
     builder.add_edge(coordinator.id, entertainment.id)
     builder.add_edge(entertainment.id, coordinator.id)
     ```
5. Update docstring to mention 6 executors (was 5)

**Acceptance Criteria:**
- [ ] Import added for `entertainment_specialist`
- [ ] Executor created with `EntertainmentSpecialist(entertainment_specialist.create_agent())`
- [ ] Executor added to workflow with `builder.add_executor(entertainment)`
- [ ] Bidirectional edges added (coordinator ↔ entertainment)
- [ ] Docstring updated to reflect 6 executors

---

## User Story 2: Entertainment Coordination

### Task 2.1: Update Logistics Manager Routing
**File**: `src/spec_to_agents/prompts/logistics_manager.py`  
**Dependencies**: Task 1.4 (workflow integration complete)  
**Parallel**: No

**Description:**
Update Logistics Manager prompt to route to Entertainment Specialist instead of returning to coordinator immediately.

**Implementation Steps:**
1. Open `src/spec_to_agents/prompts/logistics_manager.py`
2. Locate `<routing_rules>` section
3. Update completion routing:
   - Change: `next_agent: null` (returns to coordinator)
   - To: `next_agent: "entertainment"` (routes to entertainment)
4. Add documentation explaining entertainment comes after logistics

**Acceptance Criteria:**
- [ ] Routing rules updated to route to entertainment
- [ ] Documentation explains entertainment is final specialist
- [ ] Example outputs show `next_agent: "entertainment"`

---

### Task 2.2: Update Event Coordinator Synthesis
**File**: `src/spec_to_agents/prompts/event_coordinator.py`  
**Dependencies**: Task 1.4 (workflow integration complete)  
**Parallel**: Yes [P]

**Description:**
Update Event Coordinator prompt to include entertainment section in final synthesis.

**Implementation Steps:**
1. Open `src/spec_to_agents/prompts/event_coordinator.py`
2. Locate `<synthesis_guidelines>` section
3. Add "Entertainment" to the list of sections:
   ```markdown
   - Venue: Selection and key details
   - Budget: Cost allocation and constraints
   - Catering: Menu and service details
   - Logistics: Timeline, weather, calendar
   - Entertainment: Recommendations and timing  # NEW
   - Next Steps: Clear action items for client
   ```
4. Update specialist list to include Entertainment Specialist

**Acceptance Criteria:**
- [ ] Entertainment section added to synthesis guidelines
- [ ] Specialist list includes Entertainment Specialist
- [ ] Documentation explains entertainment integration

---

## User Story 3: Testing & Validation

### Task 3.1: Create Functional Tests
**File**: `tests/functional/test_entertainment_agent.py`  
**Dependencies**: Task 1.2 (needs agent module)  
**Parallel**: Yes [P]

**Description:**
Create comprehensive functional tests for Entertainment Specialist agent.

**Implementation Steps:**
1. Create new file `tests/functional/test_entertainment_agent.py`
2. Import required testing modules:
   ```python
   import pytest
   from agent_framework import AgentExecutorRequest, ChatMessage, Role
   from spec_to_agents.agents import entertainment_specialist
   from spec_to_agents.models.messages import SpecialistOutput
   from spec_to_agents.workflow.executors import EntertainmentSpecialist
   ```
3. Implement test functions:
   - `test_entertainment_agent_creation`: Verify agent config
   - `test_web_search_integration`: Verify tool availability
   - `test_structured_output`: Verify SpecialistOutput format
   - `test_workflow_integration`: Verify executor routing
4. Use `@pytest.mark.asyncio` for async tests
5. Follow patterns from `tests/functional/test_venue_agent.py`

**Acceptance Criteria:**
- [ ] File created with correct imports
- [ ] At least 4 test functions implemented
- [ ] Tests use `@pytest.mark.asyncio` decorator
- [ ] Tests verify agent creation, tools, structured output, routing
- [ ] All tests pass when executed with `pytest`

**Example Test:**
```python
@pytest.mark.asyncio
async def test_entertainment_agent_creation(container):
    """Verify Entertainment Specialist creates with correct config."""
    agent = entertainment_specialist.create_agent()
    
    assert agent.name == "entertainment_specialist"
    assert "web_search" in [t.name for t in agent.tools]
    assert agent.response_format == SpecialistOutput
```

---

### Task 3.2: Run Functional Tests
**File**: Command-line execution  
**Dependencies**: Task 3.1 (needs test file)  
**Parallel**: No

**Description:**
Execute functional tests to verify Entertainment Agent implementation.

**Implementation Steps:**
1. Run test suite:
   ```bash
   python -m pytest tests/functional/test_entertainment_agent.py -v
   ```
2. Verify all tests pass
3. Check test coverage reports
4. Fix any failing tests

**Acceptance Criteria:**
- [ ] All tests pass (4/4 passing)
- [ ] No errors or warnings in test output
- [ ] Test coverage includes agent creation, tools, output format

---

### Task 3.3: Console Mode Integration Test
**File**: Manual testing via `main.py`  
**Dependencies**: Task 1.4, Task 2.1 (workflow complete)  
**Parallel**: No

**Description:**
Test Entertainment Agent in full workflow via console mode.

**Implementation Steps:**
1. Start console mode:
   ```bash
   uv run python src/spec_to_agents/main.py
   ```
2. Submit test prompt:
   ```
   Plan a corporate party for 50 people in Seattle with a $5,000 budget
   ```
3. Verify workflow execution:
   - Venue Agent runs
   - Budget Agent runs
   - Catering Agent runs
   - Logistics Agent runs
   - **Entertainment Agent runs** (NEW)
   - Event Coordinator synthesizes final plan
4. Check Entertainment Agent output includes:
   - Entertainment recommendations (3-5 options)
   - Cost breakdown
   - Timing suggestions
   - Venue compatibility notes

**Acceptance Criteria:**
- [ ] Workflow executes without errors
- [ ] Entertainment Agent receives request from Logistics Agent
- [ ] Entertainment Agent returns structured output
- [ ] Final synthesis includes entertainment section
- [ ] Console output shows entertainment recommendations

---

### Task 3.4: DevUI Integration Test (Optional)
**File**: Manual testing via DevUI  
**Dependencies**: Task 3.3 (console mode works)  
**Parallel**: No

**Description:**
Verify Entertainment Agent works in DevUI with visual workflow trace.

**Implementation Steps:**
1. Start DevUI:
   ```bash
   uv run python -m spec_to_agents.devui
   ```
2. Open browser to DevUI URL
3. Submit same test prompt:
   ```
   Plan a corporate party for 50 people in Seattle with a $5,000 budget
   ```
4. Verify DevUI displays:
   - Entertainment Specialist in workflow graph
   - Entertainment execution trace
   - Entertainment output in conversation panel

**Acceptance Criteria:**
- [ ] DevUI starts without errors
- [ ] Workflow graph shows Entertainment Specialist node
- [ ] Execution trace includes entertainment steps
- [ ] Output panel displays entertainment recommendations
- [ ] No errors in browser console

---

## Checkpoint: Feature Complete

After completing all tasks, verify:

- ✅ **Code Quality**
  - [ ] All files follow existing code style
  - [ ] Type hints present on all functions
  - [ ] Docstrings use numpy format
  - [ ] No linting errors (`ruff check src/`)

- ✅ **Functionality**
  - [ ] Console mode executes successfully
  - [ ] Entertainment recommendations appear in output
  - [ ] Workflow routes correctly (logistics → entertainment → coordinator)
  - [ ] Structured output parses correctly

- ✅ **Testing**
  - [ ] All functional tests pass
  - [ ] Console mode integration test passes
  - [ ] DevUI integration test passes (if applicable)

- ✅ **Documentation**
  - [ ] Code comments explain non-obvious logic
  - [ ] Docstrings complete for all public functions
  - [ ] README updated if needed

---

## Estimated Time

- **Task 1.1-1.4** (Agent Setup): 15-20 minutes
- **Task 2.1-2.2** (Integration): 5-10 minutes
- **Task 3.1-3.4** (Testing): 15-20 minutes
- **Total**: ~35-50 minutes

---

**Tasks Version**: 1.0  
**Last Updated**: 2025-01-11  
**Ready for `/speckit.implement`**: ✅