# Coordinator Agent Routing Refactor - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor `EventPlanningCoordinator` to use explicit `SpecialistRequest` message type for routing instead of direct helper method calls.

**Architecture:** Replace `_route_to_specialist()` helper with a new `SpecialistRequest` dataclass that flows through the workflow as a message. Add `on_specialist_request()` handler to receive and execute routing requests.

**Tech Stack:** Python 3.11+, Agent Framework, dataclasses, pytest

---

## Task 1: Add SpecialistRequest Dataclass to messages.py

**Files:**
- Modify: `src/spec_to_agents/models/messages.py:1-86`

**Step 1: Add SpecialistRequest dataclass**

Add the following after `HumanFeedbackRequest` (after line 49, before `SpecialistOutput`):

```python
@dataclass
class SpecialistRequest:
    """
    Request to route conversation to a specialist agent.

    This message type separates routing decisions (made by coordinator)
    from routing execution (handled by on_specialist_request handler).

    Attributes
    ----------
    specialist_id : str
        ID of specialist to route to ("venue", "budget", "catering", "logistics")
    message : str
        New message/context to send to specialist
    prior_conversation : list[ChatMessage] | None
        Previous conversation history to preserve. Tool calls/results will be
        converted to text summaries when routing to avoid thread ID conflicts.

    Examples
    --------
    >>> SpecialistRequest(
    ...     specialist_id="venue",
    ...     message="Please analyze venue options",
    ...     prior_conversation=[ChatMessage(Role.USER, text="Plan a party")],
    ... )
    """

    specialist_id: str
    message: str
    prior_conversation: list[ChatMessage] | None = None
```

**Step 2: Update __all__ export list**

Change line 85 from:

```python
__all__ = ["HumanFeedbackRequest", "SpecialistOutput"]
```

To:

```python
__all__ = ["HumanFeedbackRequest", "SpecialistOutput", "SpecialistRequest"]
```

**Step 3: Run linter to verify syntax**

Run: `uv run ruff check src/spec_to_agents/models/messages.py`
Expected: No errors

**Step 4: Commit**

```bash
git add src/spec_to_agents/models/messages.py
git commit -m "feat: add SpecialistRequest dataclass for routing

Introduces SpecialistRequest message type to separate routing
decisions from routing execution in coordinator workflow.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Add on_specialist_request Handler to EventPlanningCoordinator

**Files:**
- Modify: `src/spec_to_agents/workflow/executors.py:1-433`

**Step 1: Import SpecialistRequest**

Update line 23 from:

```python
from spec_to_agents.models.messages import HumanFeedbackRequest, SpecialistOutput
```

To:

```python
from spec_to_agents.models.messages import HumanFeedbackRequest, SpecialistOutput, SpecialistRequest
```

**Step 2: Add on_specialist_request handler**

Add the following after `on_specialist_response()` handler (after line 224, before `on_human_feedback()`):

```python
    @handler
    async def on_specialist_request(
        self,
        request: SpecialistRequest,
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
    ) -> None:
        """
        Handle routing requests to specialist agents.

        Converts tool content, builds conversation history, and sends
        AgentExecutorRequest to the target specialist.

        Parameters
        ----------
        request : SpecialistRequest
            Routing request containing specialist_id, message, and conversation history
        ctx : WorkflowContext
            Workflow context for sending messages to specialists
        """
        # Convert prior conversation to remove tool-specific content
        conversation = (
            convert_tool_content_to_text(request.prior_conversation)
            if request.prior_conversation
            else []
        )

        # Add new routing message
        conversation.append(ChatMessage(Role.USER, text=request.message))

        await ctx.send_message(
            AgentExecutorRequest(
                messages=conversation,
                should_respond=True,
            ),
            target_id=request.specialist_id,
        )
```

**Step 3: Run linter to verify syntax**

Run: `uv run ruff check src/spec_to_agents/workflow/executors.py`
Expected: May show errors about unused `_route_to_specialist` or incomplete refactor (will fix in next tasks)

**Step 4: Commit**

```bash
git add src/spec_to_agents/workflow/executors.py
git commit -m "feat: add on_specialist_request handler

Adds new handler to receive SpecialistRequest messages and
execute routing to specialist agents with tool content conversion.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Update on_coordinator_response to Send SpecialistRequest

**Files:**
- Modify: `src/spec_to_agents/workflow/executors.py:149-199`

**Step 1: Replace _route_to_specialist call with SpecialistRequest**

Update lines 189-196 (the `elif specialist_output.next_agent:` block) from:

```python
        elif specialist_output.next_agent:
            # Route to next specialist
            await self._route_to_specialist(
                specialist_output.next_agent,
                "Please analyze the event planning requirements and provide your recommendations.",
                ctx,
                prior_conversation=conversation,
            )
```

To:

```python
        elif specialist_output.next_agent:
            # Create routing request and send to self for on_specialist_request handler
            specialist_request = SpecialistRequest(
                specialist_id=specialist_output.next_agent,
                message="Please analyze the event planning requirements and provide your recommendations.",
                prior_conversation=conversation,
            )
            await ctx.send_message(specialist_request, target_id=self.id)
```

**Step 2: Update WorkflowContext type hint**

Update line 153 from:

```python
        ctx: WorkflowContext[AgentExecutorRequest, str],
```

To:

```python
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
```

**Step 3: Run linter**

Run: `uv run ruff check src/spec_to_agents/workflow/executors.py`
Expected: May show unused `_route_to_specialist` warning (will fix next)

**Step 4: Commit**

```bash
git add src/spec_to_agents/workflow/executors.py
git commit -m "refactor: use SpecialistRequest in on_coordinator_response

Replaces direct _route_to_specialist call with SpecialistRequest
message creation and sending to coordinator for handler processing.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Remove _route_to_specialist Helper Method

**Files:**
- Modify: `src/spec_to_agents/workflow/executors.py:388-432`

**Step 1: Delete _route_to_specialist method**

Delete lines 388-432 (entire `_route_to_specialist` method including docstring).

**Step 2: Run linter to verify no unused code**

Run: `uv run ruff check src/spec_to_agents/workflow/executors.py`
Expected: No errors or warnings

**Step 3: Run type checker**

Run: `uv run mypy src/spec_to_agents/workflow/executors.py`
Expected: No type errors

**Step 4: Commit**

```bash
git add src/spec_to_agents/workflow/executors.py
git commit -m "refactor: remove _route_to_specialist helper method

Removes obsolete helper method now that routing is handled
via SpecialistRequest messages and on_specialist_request handler.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Update Remaining WorkflowContext Type Hints

**Files:**
- Modify: `src/spec_to_agents/workflow/executors.py:126-258`

**Step 1: Update start handler type hint**

Update line 126 from:

```python
    async def start(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
```

To:

```python
    async def start(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str]) -> None:
```

**Step 2: Update on_specialist_response type hint**

Update line 205 from:

```python
        ctx: WorkflowContext[AgentExecutorRequest, str],
```

To:

```python
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
```

**Step 3: Update on_human_feedback type hint**

Update line 231 from:

```python
        ctx: WorkflowContext[AgentExecutorRequest, str],
```

To:

```python
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
```

**Step 4: Update _synthesize_plan type hint**

Update line 262 from:

```python
        ctx: WorkflowContext[AgentExecutorRequest, str],
```

To:

```python
        ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
```

**Step 5: Run type checker**

Run: `uv run mypy src/spec_to_agents/workflow/executors.py`
Expected: No type errors

**Step 6: Run linter**

Run: `uv run ruff check src/spec_to_agents/workflow/executors.py && uv run ruff format src/spec_to_agents/workflow/executors.py`
Expected: No errors, file formatted

**Step 7: Commit**

```bash
git add src/spec_to_agents/workflow/executors.py
git commit -m "refactor: update WorkflowContext type hints

Updates all WorkflowContext type hints to include SpecialistRequest
in the message union type for consistency and type safety.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Write Unit Tests for on_specialist_request Handler

**Files:**
- Modify: `tests/test_workflow_executors.py:1-end`

**Step 1: Add test for on_specialist_request with conversation history**

Add the following at the end of the file:

```python
@pytest.mark.asyncio
async def test_on_specialist_request_with_conversation_history():
    """Test on_specialist_request routes to specialist with converted conversation."""
    from agent_framework import AgentExecutorRequest, FunctionCallContent, WorkflowContext

    from spec_to_agents.models.messages import SpecialistRequest
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create specialist request with conversation including tool calls
    prior_conversation = [
        ChatMessage(Role.USER, text="Plan a corporate event"),
        ChatMessage(
            Role.ASSISTANT,
            contents=[
                TextContent(text="Searching for venues..."),
                FunctionCallContent(
                    id="call_123",
                    name="web_search",
                    arguments={"query": "corporate event venues Seattle"},
                ),
            ],
        ),
        ChatMessage(
            Role.USER,
            contents=[
                FunctionResultContent(
                    call_id="call_123",
                    result='[{"name": "Convention Center", "capacity": 500}]',
                )
            ],
        ),
    ]

    request = SpecialistRequest(
        specialist_id="budget",
        message="Please analyze budget options",
        prior_conversation=prior_conversation,
    )

    # Create coordinator and mock context
    coordinator = EventPlanningCoordinator(Mock())
    mock_ctx = AsyncMock(spec=WorkflowContext)

    # Execute handler
    await coordinator.on_specialist_request(request, mock_ctx)

    # Verify ctx.send_message was called once
    assert mock_ctx.send_message.call_count == 1

    # Extract the sent message
    sent_message = mock_ctx.send_message.call_args[0][0]
    target_id = mock_ctx.send_message.call_args[1]["target_id"]

    # Verify target is correct specialist
    assert target_id == "budget"

    # Verify sent message is AgentExecutorRequest
    assert isinstance(sent_message, AgentExecutorRequest)
    assert sent_message.should_respond is True

    # Verify conversation was converted (tool calls become text)
    messages = sent_message.messages
    assert len(messages) == 4  # 3 converted + 1 new message

    # Verify tool call was converted to text
    assert any(
        isinstance(content, TextContent) and "[Tool Call:" in content.text
        for msg in messages
        for content in msg.contents
    )

    # Verify tool result was converted to text
    assert any(
        isinstance(content, TextContent) and "[Tool Result" in content.text
        for msg in messages
        for content in msg.contents
    )

    # Verify new message was added
    last_message = messages[-1]
    assert last_message.role == Role.USER
    assert "Please analyze budget options" in last_message.text


@pytest.mark.asyncio
async def test_on_specialist_request_without_conversation_history():
    """Test on_specialist_request routes to specialist without prior conversation."""
    from agent_framework import AgentExecutorRequest, WorkflowContext

    from spec_to_agents.models.messages import SpecialistRequest
    from spec_to_agents.workflow.executors import EventPlanningCoordinator

    # Create specialist request without prior conversation
    request = SpecialistRequest(
        specialist_id="venue",
        message="Please find venue options",
        prior_conversation=None,
    )

    # Create coordinator and mock context
    coordinator = EventPlanningCoordinator(Mock())
    mock_ctx = AsyncMock(spec=WorkflowContext)

    # Execute handler
    await coordinator.on_specialist_request(request, mock_ctx)

    # Verify ctx.send_message was called once
    assert mock_ctx.send_message.call_count == 1

    # Extract the sent message
    sent_message = mock_ctx.send_message.call_args[0][0]
    target_id = mock_ctx.send_message.call_args[1]["target_id"]

    # Verify target is correct specialist
    assert target_id == "venue"

    # Verify sent message is AgentExecutorRequest
    assert isinstance(sent_message, AgentExecutorRequest)
    assert sent_message.should_respond is True

    # Verify only one message (the new one)
    messages = sent_message.messages
    assert len(messages) == 1
    assert messages[0].role == Role.USER
    assert "Please find venue options" in messages[0].text
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_workflow_executors.py::test_on_specialist_request_with_conversation_history -v`
Expected: PASS

Run: `uv run pytest tests/test_workflow_executors.py::test_on_specialist_request_without_conversation_history -v`
Expected: PASS

**Step 3: Run all executor tests to verify no regressions**

Run: `uv run pytest tests/test_workflow_executors.py -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_workflow_executors.py
git commit -m "test: add unit tests for on_specialist_request handler

Tests verify handler correctly converts tool content, builds
conversation history, and routes to correct specialist agent.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Run Full Test Suite and Verify

**Files:**
- N/A (verification only)

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

**Step 2: Run linter on entire project**

Run: `uv run ruff check src/spec_to_agents/`
Expected: No errors

**Step 3: Run type checker on entire project**

Run: `uv run mypy src/spec_to_agents/`
Expected: No type errors

**Step 4: Run formatter on entire project**

Run: `uv run ruff format src/spec_to_agents/`
Expected: All files formatted

**Step 5: Verify git status is clean (except unstaged changes if any)**

Run: `git status`
Expected: All refactoring changes committed, working tree clean or only known unstaged files

**Step 6: Final commit if any formatting changes**

```bash
git add -u
git commit -m "style: apply formatter to refactored code

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `SpecialistRequest` dataclass added to `messages.py` with proper docstring
- [ ] `SpecialistRequest` exported in `__all__` list
- [ ] `on_specialist_request()` handler added to `EventPlanningCoordinator`
- [ ] `on_coordinator_response()` sends `SpecialistRequest` instead of calling helper
- [ ] `_route_to_specialist()` helper method removed
- [ ] All `WorkflowContext` type hints updated with union type
- [ ] Unit tests for `on_specialist_request()` pass (with and without conversation)
- [ ] Full test suite passes
- [ ] No linter errors or warnings
- [ ] No type errors
- [ ] All changes committed with descriptive messages

## Success Criteria

1. All tests pass (`uv run pytest tests/ -v`)
2. No linter errors (`uv run ruff check src/`)
3. No type errors (`uv run mypy src/`)
4. Diagnostic errors on line 204 resolved
5. External behavior identical (refactoring only)
6. Clean git history with 7 atomic commits

## Rollback Plan

If issues arise:
1. Revert commits in reverse order
2. Each commit is atomic and can be reverted independently
3. Tests verify functionality at each step
