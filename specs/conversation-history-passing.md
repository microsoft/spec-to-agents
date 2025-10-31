# ExecPlan: Implement Full Conversation History Passing

**Status**: Draft
**Created**: 2025-10-31
**Priority**: Critical
**Estimated Effort**: Medium (3-4 hours)

## Problem Statement

Agents in the event planning workflow cannot see conversation history from previous agents, causing context loss and confusion. Each `AgentExecutor` maintains an isolated `AgentThread`, so when the coordinator routes between specialists:

- Budget Analyst has no knowledge of the original user request or venue specialist's work
- Catering Coordinator cannot see budget constraints or venue details
- Logistics Manager lacks context about previous decisions

**Current Error**:
```
Budget Analyst asks: "What is the total event budget?"
(even though user specified "$5000" in original request)

Error: Sorry, something went wrong.
```

## Root Cause

`executors.py:_route_to_agent()` sends only a single new message to each agent:

```python
await ctx.send_message(
    AgentExecutorRequest(
        messages=[ChatMessage(Role.USER, text=message)],  # ❌ Only one message!
        should_respond=True,
    ),
    target_id=agent_id,
)
```

The comment claims "Service-managed threads automatically provide full conversation history" but this is **incorrect** - each `AgentExecutor` has an isolated thread.

## Solution: Pass `full_conversation` Between Agents

Implement the standard framework pattern:
1. Extract `full_conversation` from each `AgentExecutorResponse`
2. Append new routing/feedback messages to the conversation
3. Pass the complete conversation to the next agent via `AgentExecutorRequest`

### Reference Patterns

From `azure_chat_agents_function_bridge.py`:
```python
conversation = list(draft.full_conversation or draft.agent_run_response.messages)
conversation.append(ChatMessage(role=Role.USER, text=follow_up))
await ctx.send_message(AgentExecutorRequest(messages=conversation))
```

From `DraftFeedbackCoordinator`:
```python
conversation: list[ChatMessage] = list(request.conversation)
instruction = "Human guidance: ..."
conversation.append(ChatMessage(Role.USER, text=instruction))
await ctx.send_message(AgentExecutorRequest(messages=conversation, should_respond=True))
```

## Implementation Plan

### 1. Update `EventPlanningCoordinator._route_to_agent()`

**Current**:
```python
async def _route_to_agent(
    self, agent_id: str, message: str, ctx: WorkflowContext[AgentExecutorRequest, str]
) -> None:
```

**New**:
```python
async def _route_to_agent(
    self,
    agent_id: str,
    message: str,
    ctx: WorkflowContext[AgentExecutorRequest, str],
    prior_conversation: list[ChatMessage] | None = None,
) -> None:
```

**Logic**:
- If `prior_conversation` is provided, start with that
- Otherwise, start with empty list (for initial routing from `start()` handler)
- Append new routing message
- Send complete conversation to specialist

### 2. Update `start()` Handler

**Current**:
```python
async def start(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
    await self._route_to_agent("venue", prompt, ctx)
```

**New**:
```python
async def start(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
    # Start workflow with user's initial request
    initial_message = ChatMessage(Role.USER, text=prompt)
    await self._route_to_agent("venue", prompt, ctx, prior_conversation=[initial_message])
```

**Why**: Ensure the initial user request is part of the conversation from the start.

### 3. Update `on_specialist_response()` Handler

**Current**:
```python
async def on_specialist_response(
    self,
    response: AgentExecutorResponse,
    ctx: WorkflowContext[AgentExecutorRequest, str],
) -> None:
    specialist_output = self._parse_specialist_output(response)

    if specialist_output.user_input_needed:
        await ctx.request_info(...)
    elif specialist_output.next_agent:
        next_context = f"Previous specialist ({response.executor_id}) completed. Continue with your analysis."
        await self._route_to_agent(specialist_output.next_agent, next_context, ctx)
    else:
        await self._synthesize_plan(ctx)
```

**New**:
```python
async def on_specialist_response(
    self,
    response: AgentExecutorResponse,
    ctx: WorkflowContext[AgentExecutorRequest, str],
) -> None:
    specialist_output = self._parse_specialist_output(response)

    # Extract full conversation from specialist response
    conversation = list(response.full_conversation or response.agent_run_response.messages)

    if specialist_output.user_input_needed:
        # Store conversation in request_data for later retrieval
        await ctx.request_info(
            request_data=HumanFeedbackRequest(
                prompt=specialist_output.user_prompt or "Please provide input",
                context={},
                request_type="clarification",
                requesting_agent=response.executor_id,
                conversation=conversation,  # Add conversation field
            ),
            request_type=HumanFeedbackRequest,
            response_type=str,
        )
    elif specialist_output.next_agent:
        next_context = (
            f"Previous specialist ({response.executor_id}) completed their analysis. "
            f"Please review the conversation history and continue with your specialized analysis."
        )
        await self._route_to_agent(
            specialist_output.next_agent,
            next_context,
            ctx,
            prior_conversation=conversation,
        )
    else:
        # Store conversation for synthesis
        await self._synthesize_plan(ctx, conversation)
```

**Why**: Extract `full_conversation` from each specialist response and pass it along.

### 4. Update `on_human_feedback()` Handler

**Current**:
```python
async def on_human_feedback(
    self,
    original_request: HumanFeedbackRequest,
    feedback: str,
    ctx: WorkflowContext[AgentExecutorRequest, str],
) -> None:
    feedback_context = f"User provided: {feedback}. Please continue with your analysis."
    await self._route_to_agent(original_request.requesting_agent, feedback_context, ctx)
```

**New**:
```python
async def on_human_feedback(
    self,
    original_request: HumanFeedbackRequest,
    feedback: str,
    ctx: WorkflowContext[AgentExecutorRequest, str],
) -> None:
    # Retrieve conversation from original request
    conversation = list(original_request.conversation)

    feedback_context = (
        f"User provided the following input: {feedback}\n"
        f"Please continue with your analysis based on this feedback."
    )
    await self._route_to_agent(
        original_request.requesting_agent,
        feedback_context,
        ctx,
        prior_conversation=conversation,
    )
```

**Why**: Restore conversation history when routing back to the specialist after human feedback.

### 5. Update `_synthesize_plan()` Method

**Current**:
```python
async def _synthesize_plan(self, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
    synthesis_msg = ChatMessage(
        Role.USER,
        text=(
            "Please synthesize a comprehensive event plan that integrates "
            "all specialist recommendations..."
        ),
    )
    synthesis_result = await self._agent.run(messages=[synthesis_msg])
    if synthesis_result.text:
        await ctx.yield_output(synthesis_result.text)
```

**New**:
```python
async def _synthesize_plan(
    self,
    ctx: WorkflowContext[AgentExecutorRequest, str],
    conversation: list[ChatMessage],
) -> None:
    # Add synthesis instruction to full conversation
    synthesis_instruction = ChatMessage(
        Role.USER,
        text=(
            "All specialists have completed their work. Please synthesize a comprehensive "
            "event plan that integrates all specialist recommendations including venue "
            "selection, budget allocation, catering options, and logistics coordination. "
            "Provide a cohesive final plan."
        ),
    )
    conversation.append(synthesis_instruction)

    # Run coordinator agent with full conversation context
    synthesis_result = await self._agent.run(messages=conversation)

    if synthesis_result.text:
        await ctx.yield_output(synthesis_result.text)
```

**Why**: The coordinator agent needs to see all specialist conversations to synthesize properly.

### 6. Update `HumanFeedbackRequest` Message Class

**File**: `src/spec_to_agents/workflow/messages.py`

**Current**:
```python
@dataclass
class HumanFeedbackRequest(RequestInfoMessage):
    """Request for human input during workflow execution."""

    prompt: str
    context: dict[str, Any]
    request_type: str  # "clarification", "selection", "approval"
    requesting_agent: str  # ID of the agent that needs input
```

**New**:
```python
@dataclass
class HumanFeedbackRequest(RequestInfoMessage):
    """Request for human input during workflow execution."""

    prompt: str
    context: dict[str, Any]
    request_type: str  # "clarification", "selection", "approval"
    requesting_agent: str  # ID of the agent that needs input
    conversation: list[ChatMessage] = field(default_factory=list)  # Full conversation history
```

**Why**: Store conversation history in the request so it can be retrieved when resuming.

## Testing Strategy

### Unit Tests

1. **Test conversation building in `_route_to_agent()`**:
   - Verify that `prior_conversation` is preserved
   - Verify new message is appended
   - Verify complete conversation is sent

2. **Test conversation extraction in `on_specialist_response()`**:
   - Verify `full_conversation` is extracted correctly
   - Verify fallback to `agent_run_response.messages` works
   - Verify conversation is passed to next agent

3. **Test conversation restoration in `on_human_feedback()`**:
   - Verify conversation is retrieved from `HumanFeedbackRequest`
   - Verify feedback message is appended
   - Verify complete conversation is sent back to specialist

### Integration Tests

1. **Test full workflow with conversation tracking**:
   - Start with user request
   - Verify venue specialist sees original request
   - Verify budget analyst sees venue + original request
   - Verify final synthesis includes all context

2. **Test human-in-the-loop with conversation**:
   - Trigger user input request from specialist
   - Verify conversation is preserved during pause
   - Verify specialist sees full context after feedback

### Manual Testing via DevUI

1. Run: `uv run app`
2. Input: "Plan a corporate holiday party for 50 people, budget $5000"
3. Provide location: "Seattle, WA"
4. Verify each agent's prompts show awareness of previous context
5. Verify no "What is the budget?" questions from agents

## Success Criteria

- ✅ All agents see the complete conversation history up to their execution point
- ✅ Budget Analyst knows the budget without asking
- ✅ Catering Coordinator sees venue and budget constraints
- ✅ Logistics Manager has full context for scheduling
- ✅ No context-loss errors or redundant clarification questions
- ✅ Final synthesis includes all specialist recommendations

## Rollback Plan

If issues arise:
1. Revert changes to `executors.py`
2. Revert changes to `messages.py`
3. Document issues for alternative approach (shared thread)

## Dependencies

- No new external dependencies required
- Uses existing `AgentExecutorResponse.full_conversation` API
- Compatible with current Azure AI Foundry setup

## Estimated Timeline

- Implementation: 2 hours
- Testing: 1.5 hours
- Documentation: 0.5 hours
- **Total**: 4 hours

## References

- DeepWiki: `azure_chat_agents_function_bridge.py` sample
- DeepWiki: `DraftFeedbackCoordinator` pattern
- Agent Framework docs: `AgentExecutorResponse.full_conversation`
