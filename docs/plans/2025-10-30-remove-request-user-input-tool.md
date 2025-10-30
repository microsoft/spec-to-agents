# Remove request_user_input Tool Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the deprecated `request_user_input` tool from all agents and prompts since SpecialistOutput already handles user input through structured output fields (`user_input_needed` and `user_prompt`).

**Architecture:** The workflow uses SpecialistOutput structured responses with `user_input_needed` and `user_prompt` fields to handle human-in-the-loop interactions. The `request_user_input` tool is no longer needed as this functionality is built into the response format itself. The EventPlanningCoordinator executor detects `user_input_needed=True` and calls `ctx.request_info()` to pause for user feedback.

**Tech Stack:** Python 3.11+, Microsoft Agent Framework, Pydantic, pytest

---

## Task 1: Remove request_user_input from budget_analyst agent

**Files:**
- Modify: `src/spec_to_agents/agents/budget_analyst.py:15-16,26-27,44`
- Test: `tests/test_agents_budget_analyst.py` (if exists, otherwise create)

**Step 1: Write failing test for budget_analyst without request_user_input**

Create `tests/test_agents_budget_analyst.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Tests for budget analyst agent factory."""

from unittest.mock import Mock

from spec_to_agents.agents.budget_analyst import create_agent


def test_create_agent_without_request_user_input():
    """Test that budget analyst agent is created without request_user_input tool."""
    # Arrange
    mock_client = Mock()
    mock_code_interpreter = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = create_agent(mock_client, mock_code_interpreter)

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["tools"] == [mock_code_interpreter]
    assert "request_user_input" not in str(call_kwargs)


def test_create_agent_signature_has_no_request_user_input_parameter():
    """Test that create_agent function signature doesn't include request_user_input."""
    import inspect

    sig = inspect.signature(create_agent)
    params = list(sig.parameters.keys())

    assert "client" in params
    assert "code_interpreter" in params
    assert "request_user_input" not in params
    assert len(params) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agents_budget_analyst.py -v`
Expected: FAIL with "TypeError: create_agent() missing 1 required positional argument: 'request_user_input'" or similar

**Step 3: Remove request_user_input from budget_analyst.py**

Modify `src/spec_to_agents/agents/budget_analyst.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, HostedCodeInterpreterTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import budget_analyst
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(
    client: AzureAIAgentClient,
    code_interpreter: HostedCodeInterpreterTool,
) -> ChatAgent:
    """
    Create Budget Analyst agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    code_interpreter : HostedCodeInterpreterTool
        Python code execution tool for financial calculations

    Returns
    -------
    ChatAgent
        Configured budget analyst agent with code interpreter capabilities

    Notes
    -----
    MCP sequential-thinking tool was removed because it interferes with
    structured output generation (SpecialistOutput). The agent would complete
    its thinking process but fail to return a final structured response,
    causing ValueError in the workflow.

    User input is handled through SpecialistOutput.user_input_needed field,
    not through a separate tool.
    """
    return client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=[code_interpreter],
        response_format=SpecialistOutput,
        store=True,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agents_budget_analyst.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add tests/test_agents_budget_analyst.py src/spec_to_agents/agents/budget_analyst.py
git commit -m "refactor: remove request_user_input from budget_analyst agent"
```

---

## Task 2: Remove request_user_input from venue_specialist agent

**Files:**
- Modify: `src/spec_to_agents/agents/venue_specialist.py` (similar to budget_analyst)
- Test: `tests/test_agents_venue_specialist.py`

**Step 1: Write failing test for venue_specialist without request_user_input**

Create `tests/test_agents_venue_specialist.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Tests for venue specialist agent factory."""

from unittest.mock import Mock

from spec_to_agents.agents.venue_specialist import create_agent


def test_create_agent_without_request_user_input():
    """Test that venue specialist agent is created without request_user_input tool."""
    # Arrange
    mock_client = Mock()
    mock_bing_search = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = create_agent(mock_client, mock_bing_search)

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["tools"] == [mock_bing_search]
    assert "request_user_input" not in str(call_kwargs)


def test_create_agent_signature_has_no_request_user_input_parameter():
    """Test that create_agent function signature doesn't include request_user_input."""
    import inspect

    sig = inspect.signature(create_agent)
    params = list(sig.parameters.keys())

    assert "client" in params
    assert "bing_search" in params
    assert "request_user_input" not in params
    assert len(params) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agents_venue_specialist.py -v`
Expected: FAIL with missing argument error

**Step 3: Remove request_user_input from venue_specialist.py**

Modify `src/spec_to_agents/agents/venue_specialist.py` to remove the `request_user_input` parameter and tool, similar to budget_analyst changes. Update function signature, docstring, and tools list.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agents_venue_specialist.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add tests/test_agents_venue_specialist.py src/spec_to_agents/agents/venue_specialist.py
git commit -m "refactor: remove request_user_input from venue_specialist agent"
```

---

## Task 3: Remove request_user_input from catering_coordinator agent

**Files:**
- Modify: `src/spec_to_agents/agents/catering_coordinator.py`
- Test: `tests/test_agents_catering_coordinator.py`

**Step 1: Write failing test for catering_coordinator without request_user_input**

Create `tests/test_agents_catering_coordinator.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Tests for catering coordinator agent factory."""

from unittest.mock import Mock

from spec_to_agents.agents.catering_coordinator import create_agent


def test_create_agent_without_request_user_input():
    """Test that catering coordinator agent is created without request_user_input tool."""
    # Arrange
    mock_client = Mock()
    mock_bing_search = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = create_agent(mock_client, mock_bing_search)

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    assert call_kwargs["tools"] == [mock_bing_search]
    assert "request_user_input" not in str(call_kwargs)


def test_create_agent_signature_has_no_request_user_input_parameter():
    """Test that create_agent function signature doesn't include request_user_input."""
    import inspect

    sig = inspect.signature(create_agent)
    params = list(sig.parameters.keys())

    assert "client" in params
    assert "bing_search" in params
    assert "request_user_input" not in params
    assert len(params) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agents_catering_coordinator.py -v`
Expected: FAIL with missing argument error

**Step 3: Remove request_user_input from catering_coordinator.py**

Modify `src/spec_to_agents/agents/catering_coordinator.py` to remove the `request_user_input` parameter and tool, similar to budget_analyst changes.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agents_catering_coordinator.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add tests/test_agents_catering_coordinator.py src/spec_to_agents/agents/catering_coordinator.py
git commit -m "refactor: remove request_user_input from catering_coordinator agent"
```

---

## Task 4: Remove request_user_input from logistics_manager agent

**Files:**
- Modify: `src/spec_to_agents/agents/logistics_manager.py`
- Test: `tests/test_agents_logistics_manager.py`

**Step 1: Write failing test for logistics_manager without request_user_input**

Create `tests/test_agents_logistics_manager.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Tests for logistics manager agent factory."""

from unittest.mock import Mock

from spec_to_agents.agents.logistics_manager import create_agent


def test_create_agent_without_request_user_input():
    """Test that logistics manager agent is created without request_user_input tool."""
    # Arrange
    mock_client = Mock()
    mock_weather = Mock()
    mock_create_cal = Mock()
    mock_list_cal = Mock()
    mock_delete_cal = Mock()
    mock_agent = Mock()
    mock_client.create_agent.return_value = mock_agent

    # Act
    agent = create_agent(
        mock_client,
        mock_weather,
        mock_create_cal,
        mock_list_cal,
        mock_delete_cal,
    )

    # Assert
    assert agent == mock_agent
    mock_client.create_agent.assert_called_once()
    call_kwargs = mock_client.create_agent.call_args.kwargs
    expected_tools = [mock_weather, mock_create_cal, mock_list_cal, mock_delete_cal]
    assert call_kwargs["tools"] == expected_tools
    assert "request_user_input" not in str(call_kwargs)


def test_create_agent_signature_has_no_request_user_input_parameter():
    """Test that create_agent function signature doesn't include request_user_input."""
    import inspect

    sig = inspect.signature(create_agent)
    params = list(sig.parameters.keys())

    assert "client" in params
    assert "get_weather_forecast" in params
    assert "create_calendar_event" in params
    assert "list_calendar_events" in params
    assert "delete_calendar_event" in params
    assert "request_user_input" not in params
    assert len(params) == 5
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agents_logistics_manager.py -v`
Expected: FAIL with missing argument error

**Step 3: Remove request_user_input from logistics_manager.py**

Modify `src/spec_to_agents/agents/logistics_manager.py` to remove the `request_user_input` parameter and tool. Update function signature, docstring, and tools list.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agents_logistics_manager.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add tests/test_agents_logistics_manager.py src/spec_to_agents/agents/logistics_manager.py
git commit -m "refactor: remove request_user_input from logistics_manager agent"
```

---

## Task 5: Update workflow builder to remove request_user_input

**Files:**
- Modify: `src/spec_to_agents/workflow/event_planning_workflow.py:20-28,108-109,114-115,120-121,129-130`
- Test: `tests/test_workflow_event_planning.py`

**Step 1: Write failing test for workflow without request_user_input**

Create `tests/test_workflow_event_planning.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Tests for event planning workflow builder."""

from unittest.mock import Mock, patch

from spec_to_agents.workflow.event_planning_workflow import build_event_planning_workflow


@patch("spec_to_agents.workflow.event_planning_workflow.get_chat_client")
@patch("spec_to_agents.workflow.event_planning_workflow.get_sequential_thinking_tool")
@patch("spec_to_agents.workflow.event_planning_workflow.event_coordinator")
@patch("spec_to_agents.workflow.event_planning_workflow.venue_specialist")
@patch("spec_to_agents.workflow.event_planning_workflow.budget_analyst")
@patch("spec_to_agents.workflow.event_planning_workflow.catering_coordinator")
@patch("spec_to_agents.workflow.event_planning_workflow.logistics_manager")
def test_workflow_agents_created_without_request_user_input(
    mock_logistics,
    mock_catering,
    mock_budget,
    mock_venue,
    mock_coordinator,
    mock_mcp_tool,
    mock_client,
):
    """Test that workflow agents are created without request_user_input tool."""
    # Arrange
    mock_client.return_value = Mock()
    mock_mcp_tool.return_value = Mock()

    # Create mock agents
    mock_coordinator.create_agent.return_value = Mock()
    mock_venue.create_agent.return_value = Mock()
    mock_budget.create_agent.return_value = Mock()
    mock_catering.create_agent.return_value = Mock()
    mock_logistics.create_agent.return_value = Mock()

    # Act
    workflow = build_event_planning_workflow()

    # Assert - verify no agent received request_user_input
    for create_call in [
        mock_venue.create_agent.call_args,
        mock_budget.create_agent.call_args,
        mock_catering.create_agent.call_args,
        mock_logistics.create_agent.call_args,
    ]:
        args = create_call.args if create_call else ()
        # Check that request_user_input is not in args
        assert not any("request_user_input" in str(arg) for arg in args)


def test_workflow_imports_no_request_user_input():
    """Test that workflow module doesn't import request_user_input."""
    import spec_to_agents.workflow.event_planning_workflow as workflow_module

    # Check module doesn't have request_user_input in its namespace
    assert not hasattr(workflow_module, "request_user_input")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow_event_planning.py -v`
Expected: FAIL - test will fail because workflow still imports and uses request_user_input

**Step 3: Update event_planning_workflow.py to remove request_user_input**

Modify `src/spec_to_agents/workflow/event_planning_workflow.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Event planning multi-agent workflow definition."""

from agent_framework import (
    AgentExecutor,
    HostedCodeInterpreterTool,
    HostedWebSearchTool,
    Workflow,
    WorkflowBuilder,
)

from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec_to_agents.clients import get_chat_client
from spec_to_agents.tools import (
    create_calendar_event,
    delete_calendar_event,
    get_sequential_thinking_tool,
    get_weather_forecast,
    list_calendar_events,
)
from spec_to_agents.workflow.executors import EventPlanningCoordinator


def build_event_planning_workflow() -> Workflow:
    """
    Build the multi-agent event planning workflow with human-in-the-loop capabilities.

    Architecture
    ------------
    Uses coordinator-centric star topology with 5 executors:
    - EventPlanningCoordinator: Manages routing and human-in-the-loop using service-managed threads
    - VenueSpecialist: Venue research via Bing Search
    - BudgetAnalyst: Financial planning via Code Interpreter
    - CateringCoordinator: Food planning via Bing Search
    - LogisticsManager: Scheduling, weather, calendar management

    Conversation history is managed automatically by service-managed threads (store=True).
    No manual message tracking or summarization overhead.

    Workflow Pattern
    ----------------
    Star topology with bidirectional edges:
    - Coordinator ←→ Venue Specialist
    - Coordinator ←→ Budget Analyst
    - Coordinator ←→ Catering Coordinator
    - Coordinator ←→ Logistics Manager

    Human-in-the-Loop
    ------------------
    Specialists indicate user input needs via SpecialistOutput.user_input_needed field.
    The coordinator detects this and uses ctx.request_info() + @response_handler to
    pause the workflow, emit RequestInfoEvent, and resume with user responses via DevUI.

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution via DevUI
        or programmatic invocation.

    Notes
    -----
    The workflow uses sequential orchestration managed by the coordinator.
    Human-in-the-loop is optional: the workflow can complete autonomously
    if agents have sufficient context and choose not to request user input.

    Requires Azure AI Foundry credentials configured via environment variables
    or Azure CLI authentication.
    """
    client = get_chat_client()

    # Get MCP tool for coordinator only (removed from specialists - see note below)
    mcp_tool = get_sequential_thinking_tool()

    # Create hosted tools
    bing_search = HostedWebSearchTool(
        description="Search the web for current information using Bing with grounding (source citations)",
    )

    code_interpreter = HostedCodeInterpreterTool(
        description=(
            "Execute Python code for complex financial calculations, budget analysis, "
            "cost projections, and data visualization. Creates a scratchpad for "
            "intermediate calculations and maintains calculation history."
        ),
    )

    # Create coordinator agent with MCP tool for advanced reasoning
    coordinator_agent = event_coordinator.create_agent(
        client,
        mcp_tool,
    )

    # Create specialist agents with domain-specific tools
    # NOTE: MCP tool removed from specialists - it interferes with structured output (SpecialistOutput)
    # The thinking process doesn't return a final structured response, causing ValueError
    # NOTE: request_user_input tool removed - user input is handled via SpecialistOutput fields
    venue_agent = venue_specialist.create_agent(
        client,
        bing_search,
    )

    budget_agent = budget_analyst.create_agent(
        client,
        code_interpreter,
    )

    catering_agent = catering_coordinator.create_agent(
        client,
        bing_search,
    )

    logistics_agent = logistics_manager.create_agent(
        client,
        get_weather_forecast,  # type: ignore
        create_calendar_event,  # type: ignore
        list_calendar_events,  # type: ignore
        delete_calendar_event,  # type: ignore
    )

    # Create coordinator executor with routing logic
    coordinator = EventPlanningCoordinator(coordinator_agent)

    # Create specialist executors
    venue_exec = AgentExecutor(agent=venue_agent, id="venue")
    budget_exec = AgentExecutor(agent=budget_agent, id="budget")
    catering_exec = AgentExecutor(agent=catering_agent, id="catering")
    logistics_exec = AgentExecutor(agent=logistics_agent, id="logistics")

    # Build workflow with bidirectional star topology
    workflow = (
        WorkflowBuilder(
            name="Event Planning Workflow",
            description=(
                "Multi-agent event planning workflow with venue selection, budgeting, "
                "catering, and logistics coordination. Supports human-in-the-loop for "
                "clarification and approval."
            ),
        )
        # Set coordinator as start executor
        .set_start_executor(coordinator)
        # Bidirectional edges: Coordinator ←→ Each Specialist
        .add_edge(coordinator, venue_exec)
        .add_edge(venue_exec, coordinator)
        .add_edge(coordinator, budget_exec)
        .add_edge(budget_exec, coordinator)
        .add_edge(coordinator, catering_exec)
        .add_edge(catering_exec, coordinator)
        .add_edge(coordinator, logistics_exec)
        .add_edge(logistics_exec, coordinator)
        .build()
    )

    # Set stable ID to prevent URL issues on restart
    workflow.id = "event-planning-workflow"
    return workflow


__all__ = ["build_event_planning_workflow"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow_event_planning.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add tests/test_workflow_event_planning.py src/spec_to_agents/workflow/event_planning_workflow.py
git commit -m "refactor: remove request_user_input from workflow builder"
```

---

## Task 6: Update prompts to remove request_user_input tool documentation

**Files:**
- Modify: `src/spec_to_agents/prompts/budget_analyst.py:113-146`
- Modify: `src/spec_to_agents/prompts/venue_specialist.py` (similar sections)
- Modify: `src/spec_to_agents/prompts/catering_coordinator.py` (similar sections)
- Modify: `src/spec_to_agents/prompts/logistics_manager.py` (similar sections)
- Test: `tests/test_prompts_no_request_user_input.py`

**Step 1: Write test to verify prompts don't mention request_user_input**

Create `tests/test_prompts_no_request_user_input.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Tests to ensure prompts don't reference deprecated request_user_input tool."""

from spec_to_agents.prompts import (
    budget_analyst,
    catering_coordinator,
    logistics_manager,
    venue_specialist,
)


def test_budget_analyst_prompt_no_request_user_input():
    """Test that budget analyst prompt doesn't mention request_user_input."""
    prompt = budget_analyst.SYSTEM_PROMPT
    assert "request_user_input" not in prompt.lower()
    assert "SpecialistOutput" in prompt  # Should use structured output


def test_venue_specialist_prompt_no_request_user_input():
    """Test that venue specialist prompt doesn't mention request_user_input."""
    prompt = venue_specialist.SYSTEM_PROMPT
    assert "request_user_input" not in prompt.lower()
    assert "SpecialistOutput" in prompt


def test_catering_coordinator_prompt_no_request_user_input():
    """Test that catering coordinator prompt doesn't mention request_user_input."""
    prompt = catering_coordinator.SYSTEM_PROMPT
    assert "request_user_input" not in prompt.lower()
    assert "SpecialistOutput" in prompt


def test_logistics_manager_prompt_no_request_user_input():
    """Test that logistics manager prompt doesn't mention request_user_input."""
    prompt = logistics_manager.SYSTEM_PROMPT
    assert "request_user_input" not in prompt.lower()
    assert "SpecialistOutput" in prompt


def test_all_prompts_mention_structured_output_for_user_input():
    """Test that all prompts explain using SpecialistOutput for user input needs."""
    prompts = [
        budget_analyst.SYSTEM_PROMPT,
        venue_specialist.SYSTEM_PROMPT,
        catering_coordinator.SYSTEM_PROMPT,
        logistics_manager.SYSTEM_PROMPT,
    ]

    for prompt in prompts:
        # Each prompt should explain structured output format
        assert "user_input_needed" in prompt
        assert "user_prompt" in prompt
        assert "SpecialistOutput" in prompt
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_prompts_no_request_user_input.py -v`
Expected: FAIL - prompts still reference request_user_input tool

**Step 3: Update budget_analyst.py prompt**

Modify `src/spec_to_agents/prompts/budget_analyst.py` to remove lines 113-146 (the entire "### 3. User Interaction Tool" section) and replace with:

```python
## Available Tools

You have access to the following tools:

### 1. Code Interpreter Tool
- **Tool:** Code Interpreter (Python code execution in sandboxed environment)
- **Purpose:** Execute Python code for complex financial calculations, budget analysis, and data visualization
- **When to use:**
  - Performing detailed cost calculations
  - Creating budget projections and scenarios
  - Analyzing spending patterns
  - Generating financial reports
  - Calculating ROI and cost-benefit analyses
  - Running "what-if" scenarios for budget allocation
- **Features:**
  - Automatic scratchpad creation for intermediate calculations
  - Maintains calculation history
  - Supports data visualization (charts, graphs)
  - Can handle complex mathematical operations
- **Best practices:**
  - Show your calculations and explain reasoning
  - Use the scratchpad for intermediate values
  - Create visualizations when helpful for understanding budget distribution
  - Document all assumptions in calculations

Once you provide your budget allocation, indicate you're ready for the next step in planning.

## Structured Output Format

Your response MUST be structured JSON with these fields:
- summary: Your budget allocation in maximum 200 words
- next_agent: Which specialist should work next ("venue", "catering", "logistics") or null
- user_input_needed: true if you need user approval/clarification before proceeding
- user_prompt: Question for user (if user_input_needed is true)

**Using user_input_needed for Human-in-the-Loop:**
When you need user input (budget approval, constraint clarification, etc.):
1. Set user_input_needed = true
2. Set user_prompt to your clear, specific question
3. Set next_agent = null (workflow pauses for user)
4. After user responds, you'll receive their input and can continue

Routing guidance:
- Typical flow: budget → "catering" (after allocating budget)
- If budget constraints require venue change: route to "venue"
- If user needs to approve budget: set user_input_needed=true, user_prompt="Do you approve this budget allocation?"

Example (requesting user input):
{
  "summary": "Budget allocation: Venue $3k (60%), Catering $1.2k (24%), Logistics $0.5k (10%), Contingency $0.3k (6%). Total: $5k.",
  "next_agent": null,
  "user_input_needed": true,
  "user_prompt": "Do you approve this budget allocation?"
}

Example (routing to next agent):
{
  "summary": "Budget allocation: Venue $3k (60%), Catering $1.2k (24%), Logistics $0.5k (10%), Contingency $0.3k (6%). Total: $5k.",
  "next_agent": "catering",
  "user_input_needed": false,
  "user_prompt": null
}
```

**Step 4: Update other prompts similarly**

Update `src/spec_to_agents/prompts/venue_specialist.py`, `catering_coordinator.py`, and `logistics_manager.py` to remove request_user_input tool documentation and replace with SpecialistOutput guidance.

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_prompts_no_request_user_input.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
git add src/spec_to_agents/prompts/*.py tests/test_prompts_no_request_user_input.py
git commit -m "refactor: remove request_user_input tool from all prompts"
```

---

## Task 7: Remove request_user_input tool file and update tools __init__

**Files:**
- Delete: `src/spec_to_agents/tools/user_input.py`
- Modify: `src/spec_to_agents/tools/__init__.py` (remove request_user_input export)
- Delete: `tests/test_tools_user_input.py` (if exists)
- Test: `tests/test_tools_init.py`

**Step 1: Write test to verify request_user_input is not exported**

Create `tests/test_tools_init.py`:

```python
# Copyright (c) Microsoft. All rights reserved.

"""Tests for tools module exports."""


def test_request_user_input_not_exported():
    """Test that request_user_input is not exported from tools module."""
    from spec_to_agents import tools

    assert not hasattr(tools, "request_user_input")
    assert "request_user_input" not in dir(tools)


def test_tools_module_exports_expected_tools():
    """Test that tools module exports expected tools (not request_user_input)."""
    from spec_to_agents import tools

    # These should still be exported
    assert hasattr(tools, "get_weather_forecast")
    assert hasattr(tools, "create_calendar_event")
    assert hasattr(tools, "list_calendar_events")
    assert hasattr(tools, "delete_calendar_event")
    assert hasattr(tools, "get_sequential_thinking_tool")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools_init.py -v`
Expected: FAIL - request_user_input still exported

**Step 3: Update tools/__init__.py to remove request_user_input**

Modify `src/spec_to_agents/tools/__init__.py` to remove the import and export of `request_user_input`. Only keep the remaining tools.

**Step 4: Delete user_input.py and its test**

```bash
# Will be done in commit step
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_tools_init.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git rm src/spec_to_agents/tools/user_input.py
git rm tests/test_tools_user_input.py
git add src/spec_to_agents/tools/__init__.py tests/test_tools_init.py
git commit -m "refactor: remove request_user_input tool file and exports"
```

---

## Task 8: Run full test suite and verify workflow

**Files:**
- Test: All tests in `tests/`

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

**Step 2: Run type checking**

Run: `uv run mypy src/`
Expected: No type errors

**Step 3: Run linting**

Run: `uv run ruff check src/ tests/`
Expected: No linting errors

**Step 4: Manual verification with DevUI**

Run: `uv run app`

Then test the workflow:
1. Start a new event planning request
2. Verify that specialists can request user input via SpecialistOutput fields
3. Verify that workflow pauses and resumes correctly with user feedback
4. Verify no errors about missing request_user_input tool

**Step 5: Commit if any fixes needed**

If step 4 revealed issues, fix them and commit:
```bash
git add [files]
git commit -m "fix: address issues found in manual testing"
```

---

## Task 9: Update documentation and specs

**Files:**
- Modify: `specs/workflow-skeleton.md` (remove request_user_input references)
- Modify: `specs/agent-tools.md` (remove request_user_input references)

**Step 1: Update workflow-skeleton.md**

Remove any references to `request_user_input` tool and update to explain that user input is handled via SpecialistOutput structured output fields.

**Step 2: Update agent-tools.md**

Remove `request_user_input` from tool descriptions and add explanation of how SpecialistOutput handles user interaction.

**Step 3: Verify no other docs reference request_user_input**

Run: `grep -r "request_user_input" specs/ docs/`
Expected: No matches (or only historical references in old plans)

**Step 4: Commit**

```bash
git add specs/workflow-skeleton.md specs/agent-tools.md
git commit -m "docs: remove request_user_input tool from specifications"
```

---

## Task 10: Final verification and cleanup

**Files:**
- All repository files

**Step 1: Search for any remaining references**

Run: `grep -r "request_user_input" src/ tests/ --exclude-dir=__pycache__`
Expected: No matches

**Step 2: Verify git status is clean**

Run: `git status`
Expected: Clean working tree or only untracked files that should remain

**Step 3: Review all commits**

Run: `git log --oneline -10`
Expected: See all 9+ commits from this refactor with clear messages

**Step 4: Run final full test suite**

Run: `uv run pytest tests/ -v && uv run mypy src/ && uv run ruff check src/ tests/`
Expected: All checks pass

**Step 5: Create summary of changes**

Document in final commit message or PR description:
- Removed request_user_input tool (user_input.py and test)
- Updated all 4 agent factories (budget, venue, catering, logistics)
- Updated workflow builder
- Updated all 4 prompts to use SpecialistOutput fields
- Removed tool from __init__ exports
- Updated specs documentation
- Added comprehensive tests

---

## Summary

This plan removes the deprecated `request_user_input` tool from the entire codebase and ensures that all human-in-the-loop functionality is handled through SpecialistOutput structured output fields (`user_input_needed` and `user_prompt`). The refactor:

1. Updates 4 agent factory functions to remove the tool parameter
2. Updates the workflow builder to stop passing the tool
3. Updates 4 agent prompts to document SpecialistOutput instead of the tool
4. Removes the tool file and its test
5. Adds comprehensive test coverage for the changes
6. Updates documentation to reflect the new approach

The architecture remains the same - EventPlanningCoordinator detects `user_input_needed=True` in SpecialistOutput and calls `ctx.request_info()` to pause the workflow for user feedback.
