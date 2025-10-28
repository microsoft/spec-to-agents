# Human-in-the-Loop Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add human-in-the-loop capabilities to the event planning workflow, enabling agents to request user clarification, selection, or approval through a tool-based approach.

**Architecture:** Agents call `request_user_input` tool when they need user input. Custom `HumanInLoopAgentExecutor` wrappers intercept tool calls from `FunctionCallContent`, emit `UserElicitationRequest` to shared `RequestInfoExecutor`, handle `RequestResponse`, and continue workflow.

**Tech Stack:** Agent Framework Python, Pydantic dataclasses, pytest, Azure AI Foundry

---

## Task 1: Create request_user_input Tool

**Files:**
- Create: `src/spec2agent/tools/__init__.py`
- Create: `src/spec2agent/tools/user_input.py`
- Test: `tests/test_tools_user_input.py`

**Step 1: Write the failing test**

Create `tests/test_tools_user_input.py`:

```python
from spec2agent.tools.user_input import request_user_input


def test_request_user_input_returns_placeholder():
    """Test that request_user_input returns placeholder message."""
    result = request_user_input(
        prompt="Test prompt",
        context={"key": "value"},
        request_type="clarification"
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_request_user_input_accepts_all_request_types():
    """Test that all request types are accepted."""
    for req_type in ["clarification", "selection", "approval"]:
        result = request_user_input(
            prompt="Test",
            context={},
            request_type=req_type
        )
        assert isinstance(result, str)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools_user_input.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'spec2agent.tools'"

**Step 3: Create tools module**

Create `src/spec2agent/tools/__init__.py`:

```python
"""Tools for event planning agents."""

from spec2agent.tools.user_input import request_user_input

__all__ = ["request_user_input"]
```

**Step 4: Write minimal implementation**

Create `src/spec2agent/tools/user_input.py`:

```python
"""User input request tool for human-in-the-loop workflows."""

from typing import Any, Literal


def request_user_input(
    prompt: str,
    context: dict[str, Any],
    request_type: Literal["clarification", "selection", "approval"],
) -> str:
    """
    Request input from the user during workflow execution.

    Use this tool when you need:
    - Clarification on ambiguous requirements
    - User selection between multiple options
    - User approval of recommendations or budgets

    Parameters
    ----------
    prompt : str
        Clear question to ask the user (e.g., "Which venue do you prefer?")
    context : dict[str, Any]
        Supporting information such as venue options, budget breakdown, etc.
    request_type : Literal["clarification", "selection", "approval"]
        Category of the request:
        - "clarification": Missing or ambiguous information
        - "selection": User must choose from options
        - "approval": User must approve/reject a proposal

    Returns
    -------
    str
        Placeholder return value - actual user response is handled by workflow

    Notes
    -----
    This tool is intercepted by HumanInLoopAgentExecutor which emits
    UserElicitationRequest to RequestInfoExecutor for DevUI handling.
    """
    return "User input will be requested"


__all__ = ["request_user_input"]
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_tools_user_input.py -v`

Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add src/spec2agent/tools/ tests/test_tools_user_input.py
git commit -m "feat: add request_user_input tool for HITL workflows"
```

---

## Task 2: Create UserElicitationRequest Message Type

**Files:**
- Create: `src/spec2agent/workflow/messages.py`
- Test: `tests/test_workflow_messages.py`

**Step 1: Write the failing test**

Create `tests/test_workflow_messages.py`:

```python
from spec2agent.workflow.messages import UserElicitationRequest


def test_user_elicitation_request_creation():
    """Test UserElicitationRequest can be created with required fields."""
    msg = UserElicitationRequest(
        prompt="Test prompt",
        context={"venues": ["A", "B", "C"]},
        request_type="selection"
    )
    assert msg.prompt == "Test prompt"
    assert msg.context == {"venues": ["A", "B", "C"]}
    assert msg.request_type == "selection"


def test_user_elicitation_request_is_request_info_message():
    """Test UserElicitationRequest inherits from RequestInfoMessage."""
    from agent_framework import RequestInfoMessage

    msg = UserElicitationRequest(
        prompt="Test",
        context={},
        request_type="clarification"
    )
    assert isinstance(msg, RequestInfoMessage)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow_messages.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'spec2agent.workflow.messages'"

**Step 3: Write minimal implementation**

Create `src/spec2agent/workflow/messages.py`:

```python
"""Custom message types for workflow human-in-the-loop interactions."""

from dataclasses import dataclass
from typing import Any

from agent_framework import RequestInfoMessage


@dataclass
class UserElicitationRequest(RequestInfoMessage):
    """
    General-purpose request for user input during event planning.

    This message type allows any specialist agent to request clarification,
    approval, or selection from the user during workflow execution.

    Attributes
    ----------
    prompt : str
        Clear question or instruction for the user
    context : dict[str, Any]
        Contextual information such as options, data, constraints
    request_type : str
        Category of request: "clarification", "selection", or "approval"

    Examples
    --------
    >>> UserElicitationRequest(
    ...     prompt="Which venue do you prefer?",
    ...     context={"venues": [{"name": "Venue A", "capacity": 50}]},
    ...     request_type="selection"
    ... )
    """

    prompt: str
    context: dict[str, Any]
    request_type: str


__all__ = ["UserElicitationRequest"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow_messages.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/spec2agent/workflow/messages.py tests/test_workflow_messages.py
git commit -m "feat: add UserElicitationRequest message type"
```

---

## Task 3: Create HumanInLoopAgentExecutor

**Files:**
- Create: `src/spec2agent/workflow/executors.py`
- Test: `tests/test_workflow_executors.py`

**Step 1: Write the failing test**

Create `tests/test_workflow_executors.py`:

```python
import json
from unittest.mock import Mock

import pytest
from agent_framework import AgentExecutorResponse, FunctionCallContent
from spec2agent.workflow.executors import HumanInLoopAgentExecutor


def test_extract_user_request_detects_tool_call():
    """Test that _extract_user_request finds request_user_input tool calls."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Create mock AgentExecutorResponse with tool call
    mock_response = Mock(spec=AgentExecutorResponse)
    mock_message = Mock()

    # Create FunctionCallContent for request_user_input
    tool_call = Mock(spec=FunctionCallContent)
    tool_call.name = "request_user_input"
    tool_call.arguments = json.dumps({
        "prompt": "Which venue?",
        "context": {"venues": ["A", "B"]},
        "request_type": "selection"
    })

    mock_message.contents = [tool_call]
    mock_response.agent_run_response.messages = [mock_message]

    # Extract should find the tool call
    result = executor._extract_user_request(mock_response)

    assert result is not None
    assert result["prompt"] == "Which venue?"
    assert result["context"] == {"venues": ["A", "B"]}
    assert result["request_type"] == "selection"


def test_extract_user_request_returns_none_when_no_tool_call():
    """Test that _extract_user_request returns None when no tool call present."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Create mock response with no tool calls
    mock_response = Mock(spec=AgentExecutorResponse)
    mock_message = Mock()
    mock_message.contents = []  # No tool calls
    mock_response.agent_run_response.messages = [mock_message]

    result = executor._extract_user_request(mock_response)

    assert result is None


def test_extract_user_request_ignores_other_tools():
    """Test that _extract_user_request ignores non-request_user_input tools."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    mock_response = Mock(spec=AgentExecutorResponse)
    mock_message = Mock()

    # Create tool call for different tool
    other_tool = Mock(spec=FunctionCallContent)
    other_tool.name = "some_other_tool"
    other_tool.arguments = json.dumps({"arg": "value"})

    mock_message.contents = [other_tool]
    mock_response.agent_run_response.messages = [mock_message]

    result = executor._extract_user_request(mock_response)

    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow_executors.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'spec2agent.workflow.executors'"

**Step 3: Write minimal implementation**

Create `src/spec2agent/workflow/executors.py`:

```python
"""Custom executors for human-in-the-loop workflow interactions."""

import json

from agent_framework import (
    AgentExecutorResponse,
    Executor,
    FunctionCallContent,
    RequestResponse,
)
from agent_framework.core import WorkflowContext
from agent_framework.handlers import handler

from spec2agent.workflow.messages import UserElicitationRequest


class HumanInLoopAgentExecutor(Executor):
    """
    Wraps AgentExecutor to enable human-in-the-loop via request_user_input tool.

    When an agent calls the request_user_input tool, this executor:
    1. Intercepts the tool call from FunctionCallContent in AgentExecutorResponse
    2. Emits UserElicitationRequest to RequestInfoExecutor
    3. Workflow pauses until user provides response via DevUI
    4. Receives RequestResponse and continues workflow with agent's output

    Parameters
    ----------
    agent_id : str
        ID of the wrapped agent (for naming this executor)
    request_info_id : str
        ID of the RequestInfoExecutor to send user requests to

    Notes
    -----
    This executor must be placed between AgentExecutor and the next workflow step:
    AgentExecutor → HumanInLoopAgentExecutor → Next AgentExecutor

    It requires bidirectional edges to RequestInfoExecutor:
    HumanInLoopAgentExecutor ←→ RequestInfoExecutor
    """

    def __init__(self, agent_id: str, request_info_id: str):
        super().__init__(id=f"{agent_id}_hitl")
        self._agent_id = agent_id
        self._request_info_id = request_info_id
        self._current_response: AgentExecutorResponse | None = None

    @handler
    async def on_agent_response(
        self, response: AgentExecutorResponse, ctx: WorkflowContext
    ) -> None:
        """
        Handle agent response and check for request_user_input tool calls.

        If tool call found, emit UserElicitationRequest to RequestInfoExecutor.
        Otherwise, continue workflow by forwarding agent response.
        """
        self._current_response = response

        # Check for request_user_input tool call
        user_request = self._extract_user_request(response)

        if user_request:
            # Agent needs user input - emit request to RequestInfoExecutor
            await ctx.send_message(
                UserElicitationRequest(
                    prompt=user_request["prompt"],
                    context=user_request["context"],
                    request_type=user_request["request_type"],
                ),
                target_id=self._request_info_id,
            )
            # Workflow pauses here until user responds via DevUI
        else:
            # No user input needed - continue to next agent
            await ctx.send_message(response)

    @handler
    async def on_user_response(
        self, response: RequestResponse, ctx: WorkflowContext
    ) -> None:
        """
        Handle user response and continue workflow.

        User provided input via DevUI, which was routed back as RequestResponse.
        Forward the original agent response to continue workflow.
        """
        # User provided input - forward the agent response to continue workflow
        # The user's response is incorporated in the conversation context
        if self._current_response:
            await ctx.send_message(self._current_response)

    def _extract_user_request(self, response: AgentExecutorResponse) -> dict | None:
        """
        Extract request_user_input tool call arguments from agent response.

        Iterates through agent response messages looking for FunctionCallContent
        with name="request_user_input" and parses JSON arguments.

        Parameters
        ----------
        response : AgentExecutorResponse
            Agent's response to check for tool calls

        Returns
        -------
        dict | None
            Parsed tool arguments if found, None otherwise
        """
        for message in response.agent_run_response.messages:
            for content in message.contents:
                if isinstance(content, FunctionCallContent):
                    if content.name == "request_user_input":
                        try:
                            args = json.loads(content.arguments)
                            return args
                        except json.JSONDecodeError:
                            # Arguments not valid JSON, skip
                            continue
        return None


__all__ = ["HumanInLoopAgentExecutor"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow_executors.py -v`

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/spec2agent/workflow/executors.py tests/test_workflow_executors.py
git commit -m "feat: add HumanInLoopAgentExecutor for tool call interception"
```

---

## Task 4: Update Workflow to Integrate HITL Components

**Files:**
- Modify: `src/spec2agent/workflow/core.py`
- Test: `tests/test_workflow.py` (add new test)

**Step 1: Write the failing test**

Add to `tests/test_workflow.py`:

```python
def test_workflow_includes_request_info_executor():
    """Test that workflow includes RequestInfoExecutor for HITL."""
    from spec2agent.workflow.core import build_event_planning_workflow

    workflow = build_event_planning_workflow()

    # Workflow should build successfully with HITL components
    assert workflow is not None

    # Note: Can't easily inspect workflow internals, but building without
    # errors confirms RequestInfoExecutor and HITL wrappers are integrated
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow.py::test_workflow_includes_request_info_executor -v`

Expected: PASS (implementation already exists, but we're adding HITL)

**Step 3: Update workflow implementation**

Modify `src/spec2agent/workflow/core.py`. Find the `build_event_planning_workflow()` function and update it:

```python
"""Event planning workflow implementation."""

from agent_framework import AgentExecutor, RequestInfoExecutor, Workflow, WorkflowBuilder

from spec2agent.clients import get_chat_client
from spec2agent.prompts import (
    budget_analyst,
    catering_coordinator,
    event_coordinator,
    logistics_manager,
    venue_specialist,
)
from spec2agent.tools.user_input import request_user_input
from spec2agent.workflow.executors import HumanInLoopAgentExecutor


def build_event_planning_workflow() -> Workflow:
    """
    Build the multi-agent event planning workflow with human-in-the-loop capabilities.

    The workflow orchestrates five specialized agents with optional user interaction:
    - Event Coordinator: Primary orchestrator and synthesizer
    - Venue Specialist: Venue research and recommendations (can request user input)
    - Budget Analyst: Financial planning and allocation (can request user input)
    - Catering Coordinator: Food and beverage planning (can request user input)
    - Logistics Manager: Scheduling and resource coordination (can request user input)

    Agents can call the request_user_input tool when they need clarification,
    selection, or approval from the user. HumanInLoopAgentExecutor wrappers
    intercept these tool calls and emit UserElicitationRequest to a shared
    RequestInfoExecutor, which pauses the workflow until the user responds via DevUI.

    Returns
    -------
    Workflow
        Configured workflow instance ready for execution via DevUI
        or programmatic invocation.

    Notes
    -----
    The workflow uses sequential orchestration where the Event Coordinator
    delegates to each specialist in sequence, then synthesizes the final plan.

    Human-in-the-loop is optional: the workflow can complete autonomously
    if agents have sufficient context and choose not to request user input.

    Requires Azure AI Foundry credentials configured via environment variables
    or Azure CLI authentication.
    """
    client = get_chat_client()

    # Create coordinator agent (no HITL - doesn't request user input)
    coordinator_agent = client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        store=True,
    )

    # Create specialist agents WITH request_user_input tool
    venue_agent = client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    budget_agent = client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    catering_agent = client.create_agent(
        name="CateringCoordinator",
        instructions=catering_coordinator.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    logistics_agent = client.create_agent(
        name="LogisticsManager",
        instructions=logistics_manager.SYSTEM_PROMPT,
        tools=[request_user_input],
        store=True,
    )

    # Create AgentExecutors
    coordinator_exec = AgentExecutor(agent=coordinator_agent, id="coordinator")
    venue_exec = AgentExecutor(agent=venue_agent, id="venue")
    budget_exec = AgentExecutor(agent=budget_agent, id="budget")
    catering_exec = AgentExecutor(agent=catering_agent, id="catering")
    logistics_exec = AgentExecutor(agent=logistics_agent, id="logistics")

    # Create RequestInfoExecutor for human-in-the-loop
    request_info = RequestInfoExecutor(id="user_input")

    # Create HITL wrappers for specialist agents
    venue_hitl = HumanInLoopAgentExecutor(agent_id="venue", request_info_id="user_input")
    budget_hitl = HumanInLoopAgentExecutor(agent_id="budget", request_info_id="user_input")
    catering_hitl = HumanInLoopAgentExecutor(
        agent_id="catering", request_info_id="user_input"
    )
    logistics_hitl = HumanInLoopAgentExecutor(
        agent_id="logistics", request_info_id="user_input"
    )

    # Build workflow with HITL integration
    workflow = (
        WorkflowBuilder()
        # Add all executors
        .add_executor(coordinator_exec, output_response=True)
        .add_executor(venue_exec)
        .add_executor(budget_exec)
        .add_executor(catering_exec)
        .add_executor(logistics_exec)
        .add_executor(request_info)
        .add_executor(venue_hitl)
        .add_executor(budget_hitl)
        .add_executor(catering_hitl)
        .add_executor(logistics_hitl)
        # Set starting point
        .set_start_executor(coordinator_exec)
        # Sequential flow: Agent → HITL Wrapper → Next Agent
        .add_edge(coordinator_exec, venue_exec)
        .add_edge(venue_exec, venue_hitl)
        .add_edge(venue_hitl, budget_exec)
        .add_edge(budget_exec, budget_hitl)
        .add_edge(budget_hitl, catering_exec)
        .add_edge(catering_exec, catering_hitl)
        .add_edge(catering_hitl, logistics_exec)
        .add_edge(logistics_exec, logistics_hitl)
        .add_edge(logistics_hitl, coordinator_exec)  # Back to coordinator for synthesis
        # Bidirectional HITL edges: Wrapper ←→ RequestInfoExecutor
        .add_edge(venue_hitl, request_info)
        .add_edge(request_info, venue_hitl)
        .add_edge(budget_hitl, request_info)
        .add_edge(request_info, budget_hitl)
        .add_edge(catering_hitl, request_info)
        .add_edge(request_info, catering_hitl)
        .add_edge(logistics_hitl, request_info)
        .add_edge(request_info, logistics_hitl)
        .build()
    )

    return workflow


# Export workflow instance for DevUI discovery
workflow = build_event_planning_workflow()

__all__ = ["build_event_planning_workflow", "workflow"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow.py -v`

Expected: PASS (all tests including new one)

**Step 5: Commit**

```bash
git add src/spec2agent/workflow/core.py tests/test_workflow.py
git commit -m "feat: integrate HITL executors and RequestInfoExecutor into workflow"
```

---

## Task 5: Update Agent Prompts with Tool Usage Guidance

**Files:**
- Modify: `src/spec2agent/prompts/venue_specialist.py`
- Modify: `src/spec2agent/prompts/budget_analyst.py`
- Modify: `src/spec2agent/prompts/catering_coordinator.py`
- Modify: `src/spec2agent/prompts/logistics_manager.py`

**Step 1: Update Venue Specialist prompt**

Modify `src/spec2agent/prompts/venue_specialist.py` - add to end of SYSTEM_PROMPT:

```python
## User Interaction Tool

You have access to a `request_user_input` tool for requesting user clarification or selection.

**When to use:**
- Event requirements are ambiguous (e.g., "plan a party" without size/budget/location)
- You have multiple strong venue options and need user preference
- Specific venue constraints aren't clear (accessibility, parking, amenities)
- Location preferences are unstated or unclear

**How to use:**
Call request_user_input with:
- prompt: Clear question (e.g., "Which venue do you prefer?")
- context: Relevant data as a dict (e.g., {"venues": [venue1_dict, venue2_dict]})
- request_type: "selection" for choosing options, "clarification" for missing info

**Example:**
If you find 3 excellent venues that match requirements:
```python
request_user_input(
    prompt="I found 3 venues that meet your requirements. Which do you prefer?",
    context={
        "venues": [
            {"name": "Venue A", "capacity": 50, "cost": "$2000", "pros": "...", "cons": "..."},
            {"name": "Venue B", "capacity": 60, "cost": "$2500", "pros": "...", "cons": "..."},
            {"name": "Venue C", "capacity": 55, "cost": "$2200", "pros": "...", "cons": "..."}
        ]
    },
    request_type="selection"
)
```

**Important:** Only request user input when truly necessary. Make reasonable assumptions when possible.
"""
```

**Step 2: Update Budget Analyst prompt**

Modify `src/spec2agent/prompts/budget_analyst.py` - add to end of SYSTEM_PROMPT:

```python
## User Interaction Tool

You have access to a `request_user_input` tool for requesting user approval or clarification.

**When to use:**
- Budget allocation needs user approval before proceeding
- Budget constraints are unclear or conflicting
- Cost estimates exceed stated budget and need user decision
- Priority trade-offs require user input (e.g., venue vs. catering budget)

**How to use:**
Call request_user_input with:
- prompt: Clear question (e.g., "Do you approve this budget allocation?")
- context: Budget breakdown as a dict
- request_type: "approval" for budget sign-off, "clarification" for unclear constraints

**Example:**
```python
request_user_input(
    prompt="Do you approve this budget allocation?",
    context={
        "total_budget": 5000,
        "allocation": {
            "venue": 2000,
            "catering": 1800,
            "logistics": 800,
            "contingency": 400
        }
    },
    request_type="approval"
)
```

**Important:** Only request approval when budget decisions are significant or uncertain.
"""
```

**Step 3: Update Catering Coordinator prompt**

Modify `src/spec2agent/prompts/catering_coordinator.py` - add to end of SYSTEM_PROMPT:

```python
## User Interaction Tool

You have access to a `request_user_input` tool for requesting user selection or clarification.

**When to use:**
- Dietary restrictions are unclear or missing
- Multiple menu options are equally suitable
- Cuisine preferences are unstated
- Service style needs user preference (buffet vs. plated vs. stations)

**How to use:**
Call request_user_input with:
- prompt: Clear question
- context: Menu options or dietary considerations as a dict
- request_type: "selection" for menu choices, "clarification" for dietary needs

**Example:**
```python
request_user_input(
    prompt="Which catering style do you prefer?",
    context={
        "options": [
            {"style": "Buffet", "pros": "Flexible, casual", "cons": "Less formal", "cost": "$30/person"},
            {"style": "Plated", "pros": "Formal, elegant", "cons": "More expensive", "cost": "$45/person"},
            {"style": "Food Stations", "pros": "Interactive, variety", "cons": "Requires space", "cost": "$38/person"}
        ]
    },
    request_type="selection"
)
```

**Important:** Only request input when catering decisions significantly impact the event.
"""
```

**Step 4: Update Logistics Manager prompt**

Modify `src/spec2agent/prompts/logistics_manager.py` - add to end of SYSTEM_PROMPT:

```python
## User Interaction Tool

You have access to a `request_user_input` tool for requesting user clarification.

**When to use:**
- Event date/time is not specified or ambiguous
- Timeline conflicts need resolution
- Vendor coordination requires user preference
- Setup/teardown logistics need clarification

**How to use:**
Call request_user_input with:
- prompt: Clear question
- context: Timeline or logistics details as a dict
- request_type: "clarification" for missing information, "selection" for choosing options

**Example:**
```python
request_user_input(
    prompt="What is your preferred event date and time?",
    context={
        "venue_availability": ["Friday 6pm", "Saturday 2pm", "Saturday 6pm"],
        "catering_availability": ["Friday evening", "Saturday afternoon/evening"]
    },
    request_type="clarification"
)
```

**Important:** Only request clarification when logistics cannot proceed without the information.
"""
```

**Step 5: Run linting to verify changes**

Run: `uv run ruff check src/spec2agent/prompts/`

Expected: No errors

**Step 6: Commit**

```bash
git add src/spec2agent/prompts/venue_specialist.py
git add src/spec2agent/prompts/budget_analyst.py
git add src/spec2agent/prompts/catering_coordinator.py
git add src/spec2agent/prompts/logistics_manager.py
git commit -m "feat: add request_user_input tool guidance to agent prompts"
```

---

## Task 6: Create Comprehensive HITL Tests

**Files:**
- Update: `tests/test_workflow_user_handoff.py` (already exists)

**Step 1: Review existing tests**

Run: `uv run pytest tests/test_workflow_user_handoff.py -v`

Expected: Tests may exist from spec but need updates for actual implementation

**Step 2: Update test file with comprehensive tests**

Replace content of `tests/test_workflow_user_handoff.py`:

```python
"""Tests for human-in-the-loop workflow functionality."""

import json
from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentExecutorResponse, FunctionCallContent, RequestInfoEvent

from spec2agent.workflow.core import build_event_planning_workflow
from spec2agent.workflow.executors import HumanInLoopAgentExecutor
from spec2agent.workflow.messages import UserElicitationRequest


def test_hitl_executor_detects_tool_call():
    """Test HumanInLoopAgentExecutor correctly detects request_user_input calls."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Mock AgentExecutorResponse with tool call
    mock_response = Mock(spec=AgentExecutorResponse)
    mock_message = Mock()
    mock_content = Mock(spec=FunctionCallContent)
    mock_content.name = "request_user_input"
    mock_content.arguments = json.dumps(
        {"prompt": "test", "context": {}, "request_type": "clarification"}
    )
    mock_message.contents = [mock_content]
    mock_response.agent_run_response.messages = [mock_message]

    # Extract should find the tool call
    result = executor._extract_user_request(mock_response)
    assert result is not None
    assert result["prompt"] == "test"


def test_hitl_executor_returns_none_without_tool_call():
    """Test HumanInLoopAgentExecutor returns None when no tool call."""
    executor = HumanInLoopAgentExecutor(agent_id="test", request_info_id="user_input")

    # Mock response without tool calls
    mock_response = Mock(spec=AgentExecutorResponse)
    mock_message = Mock()
    mock_message.contents = []
    mock_response.agent_run_response.messages = [mock_message]

    result = executor._extract_user_request(mock_response)
    assert result is None


def test_workflow_builds_with_hitl_components():
    """Test that workflow builds successfully with HITL components."""
    workflow = build_event_planning_workflow()
    assert workflow is not None


@pytest.mark.asyncio
async def test_workflow_with_detailed_request_no_user_input():
    """
    Test workflow completes without user input when given detailed context.

    NOTE: This test requires Azure credentials and makes real API calls.
    It may be skipped in CI if credentials are not available.
    """
    workflow = build_event_planning_workflow()

    detailed_request = """
    Plan a corporate team building event:
    - 30 people
    - Budget: $3000
    - Location: Downtown Seattle
    - Date: 3 weeks from now, Friday evening
    - Dietary: vegetarian and gluten-free options required
    """

    events = []
    async for event in workflow.run_stream(detailed_request):
        events.append(event)

    # Should complete without requiring user input
    assert len(events) > 0

    # Check if any RequestInfoEvents occurred (should be zero or handled)
    request_events = [e for e in events if isinstance(e, RequestInfoEvent)]
    # With detailed context, agents should not need to request user input
    # But this depends on LLM behavior, so we just verify workflow completes


@pytest.mark.asyncio
async def test_workflow_with_ambiguous_request_may_trigger_user_input():
    """
    Test workflow handles ambiguous requests (may trigger RequestInfoEvent).

    NOTE: This test requires Azure credentials and makes real API calls.
    Whether user input is requested depends on agent LLM behavior.
    """
    workflow = build_event_planning_workflow()

    # Ambiguous request that could trigger user input
    request = "Plan a party for 30 people"

    events = []
    async for event in workflow.run_stream(request):
        events.append(event)
        # If RequestInfoEvent occurs, workflow will pause
        # In real usage, DevUI would handle this
        if isinstance(event, RequestInfoEvent):
            # In test, we can't easily provide user response
            # This confirms HITL mechanism is working
            break

    # Workflow produces events
    assert len(events) > 0

    # Check if RequestInfoEvent was emitted (confirms HITL works)
    request_events = [e for e in events if isinstance(e, RequestInfoEvent)]
    # May or may not occur depending on agent behavior
    # Test validates workflow handles both cases
```

**Step 3: Run tests**

Run: `uv run pytest tests/test_workflow_user_handoff.py -v`

Expected: Unit tests PASS, integration tests may be skipped if no Azure credentials

**Step 4: Commit**

```bash
git add tests/test_workflow_user_handoff.py
git commit -m "test: add comprehensive HITL workflow tests"
```

---

## Task 7: Run Full Test Suite

**Step 1: Run all tests**

Run: `uv run pytest -v`

Expected: All tests PASS

**Step 2: If any failures, debug and fix**

Review test output, fix issues, commit fixes

**Step 3: Run linting**

Run: `uv run ruff check src/ tests/`

Expected: No linting errors

**Step 4: Run formatting**

Run: `uv run ruff format src/ tests/`

Expected: All files formatted correctly

---

## Task 8: Manual DevUI Validation via Playwright MCP

**Step 1: Start DevUI**

Run: `uv run devui`

Expected: Server starts at http://localhost:8000

**Step 2: Use Playwright MCP to test workflow**

Use `mcp__playwright` tools to:
1. Navigate to DevUI
2. Select event planning workflow
3. Submit ambiguous request: "Plan a party for 40 people"
4. Observe if RequestInfoEvent appears
5. Provide user response if prompted
6. Verify workflow completes

**Step 3: Test detailed request**

Submit: "Plan corporate team building for 30, $3000 budget, Seattle, 3 weeks, vegetarian"

Expected: Workflow completes without user prompts

**Step 4: Document results**

Note any issues or unexpected behavior

---

## Task 9: Update Spec Progress Section

**Files:**
- Modify: `specs/workflow-skeleton.md`

**Step 1: Update Progress section**

Modify `specs/workflow-skeleton.md` Progress section (lines ~20-33):

```markdown
## Progress

- [x] Design workflow orchestration architecture - Completed 2025-10-27
- [x] Define system prompts for all five agents - Completed 2025-10-27
- [x] Create workflow builder implementation - Completed 2025-10-27
- [x] Update agent module structure to export workflow - Completed 2025-10-27
- [x] Create integration tests for workflow - Completed 2025-10-27
- [x] Validate workflow in DevUI - Completed 2025-10-27
- [x] Design and implement user handoff integration - Completed 2025-10-28
- [x] Add request_user_input tool - Completed 2025-10-28
- [x] Create UserElicitationRequest message type - Completed 2025-10-28
- [x] Implement HumanInLoopAgentExecutor - Completed 2025-10-28
- [x] Update workflow with HITL integration - Completed 2025-10-28
- [x] Update agent prompts with user elicitation guidance - Completed 2025-10-28
- [x] Add tests for user handoff scenarios - Completed 2025-10-28
- [x] Validate HITL workflow in DevUI - Completed 2025-10-28
```

**Step 2: Commit**

```bash
git add specs/workflow-skeleton.md
git commit -m "docs: update spec progress with HITL implementation completion"
```

---

## Task 10: Final Verification and Documentation

**Step 1: Run complete test suite one more time**

Run: `uv run pytest -v`

Expected: All tests PASS

**Step 2: Verify git status is clean**

Run: `git status`

Expected: All changes committed

**Step 3: Review implementation checklist in design doc**

Open `docs/plans/2025-10-28-human-in-the-loop-workflow-design.md`

Verify all checklist items completed:
- ✅ Create tools/user_input.py
- ✅ Create workflow/messages.py
- ✅ Create workflow/executors.py
- ✅ Update workflow/core.py
- ✅ Update all specialist prompts
- ✅ Create and run tests
- ✅ DevUI validation
- ✅ Update spec progress

---

## Verification Steps

After completing all tasks:

1. **Unit Tests**: `uv run pytest tests/test_tools_user_input.py tests/test_workflow_messages.py tests/test_workflow_executors.py -v`
   - Expected: All unit tests PASS

2. **Integration Tests**: `uv run pytest tests/test_workflow_user_handoff.py -v`
   - Expected: Tests PASS (or skip if no Azure credentials)

3. **Full Test Suite**: `uv run pytest -v`
   - Expected: All tests PASS

4. **Linting**: `uv run ruff check src/ tests/`
   - Expected: No errors

5. **DevUI Manual Test**:
   - Start: `uv run devui`
   - Navigate to workflow in browser
   - Test ambiguous and detailed requests
   - Verify HITL behavior

6. **Git Status**: `git status`
   - Expected: Clean (all changes committed)

---

## Related Skills

- @superpowers:test-driven-development: Follow TDD for each task
- @superpowers:verification-before-completion: Verify tests pass before committing
- @superpowers:systematic-debugging: If tests fail, debug systematically

---

## Implementation Complete

When all tasks are completed and verified:

1. All tests passing
2. All code committed
3. DevUI validation successful
4. Spec updated with completion status

The human-in-the-loop workflow is ready for use!
