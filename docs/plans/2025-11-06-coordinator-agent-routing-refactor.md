# Coordinator Agent Routing Refactor

**Date:** 2025-11-06
**Status:** Approved
**Author:** Claude + alexlavaee

## Overview

Refactor the `EventPlanningCoordinator` to use explicit message-passing for specialist routing instead of direct helper method calls. This change improves separation of concerns, testability, and adherence to Agent Framework patterns.

## Context

The coordinator was recently refactored from a single `on_agent_response` handler into two specialized handlers:
- `on_coordinator_response`: Handles coordinator agent responses and routing decisions
- `on_specialist_response`: Handles specialist agent responses and forwards to coordinator

However, `_route_to_specialist` remains a private helper method that directly calls `ctx.send_message()`, mixing routing logic with coordinator logic. This violates the framework's message-passing paradigm where handlers communicate via typed messages, not direct calls.

## Problem Statement

**Current Flow:**
```
on_coordinator_response
    → _route_to_specialist (helper method)
    → ctx.send_message(AgentExecutorRequest, target_id=specialist_id)
```

**Issues:**
1. Routing logic embedded in coordinator handler
2. Difficult to test routing independently
3. Violates framework pattern: handlers should communicate via messages
4. Mixed concerns: coordinator both decides *what* to route and *how* to route

## Design Decision

Introduce `SpecialistRequest` as a formal message type that flows through the workflow, following the `AgentExecutorRequest` pattern.

### SpecialistRequest Structure

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
    """
    specialist_id: str
    message: str
    prior_conversation: list[ChatMessage] | None = None
```

**Design Rationale:**
- **Dataclass over Pydantic**: Matches `AgentExecutorRequest` pattern, minimal overhead
- **Location**: `src/spec_to_agents/models/messages.py` alongside `HumanFeedbackRequest` and `SpecialistOutput`
- **Fields mirror `_route_to_specialist` parameters**: Direct replacement with type safety

### Message Flow

**New Flow:**
```
on_coordinator_response (parses SpecialistOutput)
    ↓ creates SpecialistRequest
    ↓ ctx.send_message(specialist_request, target_id=self.id)
on_specialist_request (receives SpecialistRequest) ← NEW HANDLER
    ↓ converts tool content via convert_tool_content_to_text()
    ↓ builds conversation with prior_conversation + new message
    ↓ ctx.send_message(AgentExecutorRequest, target_id=specialist_id)
specialist agent executor (processes request)
    ↓ AgentExecutorResponse
on_specialist_response (forwards to coordinator)
```

### Handler Responsibilities

**on_coordinator_response** (lines 150-199):
- Parse `SpecialistOutput` from coordinator agent
- Determine routing action (HITL, specialist, or synthesis)
- Create and send `SpecialistRequest` for specialist routing
- Maintain ownership of routing *decisions*

**on_specialist_request** (NEW):
- Receive `SpecialistRequest` message
- Convert tool content to text summaries
- Build complete conversation history
- Send `AgentExecutorRequest` to target specialist
- Handle routing *execution*

## Implementation Plan

### 1. Add SpecialistRequest to messages.py

```python
@dataclass
class SpecialistRequest:
    """Request to route conversation to a specialist agent."""
    specialist_id: str
    message: str
    prior_conversation: list[ChatMessage] | None = None
```

Update `__all__` export list.

### 2. Update on_coordinator_response

Replace direct `_route_to_specialist()` call with message creation:

```python
elif specialist_output.next_agent:
    # Create routing request instead of calling helper
    specialist_request = SpecialistRequest(
        specialist_id=specialist_output.next_agent,
        message="Please analyze the event planning requirements and provide your recommendations.",
        prior_conversation=conversation,
    )
    await ctx.send_message(specialist_request, target_id=self.id)
```

### 3. Add on_specialist_request Handler

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

### 4. Remove _route_to_specialist

Delete the private helper method (lines 388-432) as it's no longer needed.

### 5. Update WorkflowContext Type Hints

Update all `WorkflowContext` type hints to include `SpecialistRequest`:

```python
WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str]
```

Or create a type alias for clarity:

```python
CoordinatorMessage = AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest
WorkflowContext[CoordinatorMessage, str]
```

## Benefits

1. **Separation of Concerns**: Coordinator decides routing, handler executes it
2. **Message-Passing Purity**: All handler communication via typed messages
3. **Testability**: Can mock and test `on_specialist_request` independently
4. **Extensibility**: Could add validation, logging, or middleware between decision and execution
5. **Consistency**: Matches Agent Framework patterns (`AgentExecutorRequest` dataclass)
6. **Type Safety**: Explicit types for all workflow messages

## Testing Considerations

- Unit test `on_specialist_request` with mock `SpecialistRequest` objects
- Verify tool content conversion happens correctly
- Ensure conversation history preserved across routing
- Test edge cases: empty prior_conversation, missing specialist_id

## Migration Notes

- This is a **refactoring**, not a feature change
- External behavior remains identical
- No changes to specialist agents or workflow builder
- Diagnostic errors on line 204 will be resolved

## References

- Agent Framework `AgentExecutorRequest`: `@dataclass` with `messages` and `should_respond`
- DeepWiki: "Handlers communicate via `ctx.send_message()`, not direct calls or return values"
- Existing patterns: `HumanFeedbackRequest` (dataclass in messages.py)
