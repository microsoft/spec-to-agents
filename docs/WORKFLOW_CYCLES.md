# Workflow Cycle Detection and Termination Guarantees

## Overview

The event planning workflow uses a **coordinator-centric star topology** with **bidirectional edges**. This architecture creates cycles in the workflow graph, which may trigger a validation warning from the Agent Framework:

```
[WARNING] Cycle detected in the workflow graph involving: logistics -> catering -> budget -> venue -> event_coordinator -> logistics. Ensure termination or iteration limits exist.
```

**This warning is expected and safe.** The cycles are intentional and necessary for the coordinator pattern, and termination is guaranteed through multiple mechanisms.

## Why Bidirectional Edges?

The workflow uses bidirectional edges to enable flexible routing:

```
User Request
    ↓
EventPlanningCoordinator (Routing Hub)
    ↓ ↑ (bidirectional edges)
    ├── Venue Specialist ←→ Coordinator
    ├── Budget Analyst ←→ Coordinator
    ├── Catering Coordinator ←→ Coordinator
    └── Logistics Manager ←→ Coordinator
    ↓
EventPlanningCoordinator (Synthesis)
    ↓
Final Event Plan
```

This architecture allows:
- **Dynamic routing**: Coordinator can route to any specialist based on specialist responses
- **Iterative refinement**: Budget analyst can send back to venue specialist if cheaper option needed
- **Human-in-the-loop**: User feedback can be routed back to the requesting specialist
- **Flexible workflow**: No rigid sequential order enforced by workflow edges

## Termination Guarantees

Despite the cycles, the workflow **cannot run indefinitely**. Termination is guaranteed through:

### 1. Max Iterations Limit (Framework-Level)

The workflow is configured with `max_iterations=30`:

```python
workflow = (
    WorkflowBuilder(
        name="Event Planning Workflow",
        max_iterations=30,  # Enforce iteration limit
    )
    # ...
    .build()
)
```

If 30 iterations are reached (extremely unlikely in normal operation), the framework automatically terminates the workflow. This is a hard limit enforced by the Agent Framework.

### 2. Structured Output Routing (Coordinator-Level)

Each specialist agent returns `SpecialistOutput` with a `next_agent` field:

```python
class SpecialistOutput(BaseModel):
    summary: str
    next_agent: str | None  # "venue", "budget", "catering", "logistics", or None
    user_input_needed: bool
    user_prompt: str | None
```

The coordinator routes based on this structured output:
- **`next_agent="venue"|"budget"|"catering"|"logistics"`**: Route to that specialist
- **`next_agent=None` and `user_input_needed=False`**: Workflow complete, synthesize final plan
- **`user_input_needed=True`**: Pause for human input

This means **specialists explicitly signal completion** by returning `next_agent=None`.

### 3. Explicit Termination via Output Yielding (Handler-Level)

When workflow is complete, the coordinator calls `_synthesize_plan()`, which yields the final output:

```python
async def _synthesize_plan(self, ctx, conversation):
    """
    WORKFLOW TERMINATION: This method terminates the workflow by calling
    ctx.yield_output(), which signals to the framework that the workflow
    has completed successfully.
    """
    synthesis_result = await self._agent.run(messages=clean_conversation)
    
    # Yield final plan as workflow output - this terminates the workflow
    if synthesis_result.text:
        await ctx.yield_output(synthesis_result.text)
```

After `ctx.yield_output()` is called, the framework recognizes the workflow as complete and stops executing handlers.

## Why the Warning Appears

The Agent Framework's cycle detection algorithm identifies cycles by analyzing the graph structure (edges between executors). It sees:

```
coordinator → venue → coordinator → budget → coordinator → catering → coordinator → logistics → coordinator
```

This forms a cycle. The framework warns about this because **in general**, cycles can lead to infinite loops if not properly managed.

## Why the Warning is Safe to Ignore

For this workflow, the warning can be safely acknowledged because:

1. **Routing is not edge-based**: Despite having bidirectional edges, actual routing is controlled by the coordinator's logic, not by following edges arbitrarily.

2. **Explicit termination signals**: Specialists use structured output to signal completion (`next_agent=None`), which the coordinator recognizes and acts upon.

3. **Multiple safety nets**: Even if the coordinator logic had a bug, the framework's `max_iterations` limit would prevent runaway execution.

4. **Proven pattern**: This coordinator-centric star topology is a standard pattern in multi-agent systems and is recommended by the Agent Framework documentation.

## Best Practices

When building workflows with cycles:

1. **Always set `max_iterations`**: Provides a hard limit as a safety net
2. **Use structured output for routing**: Make termination conditions explicit and machine-readable
3. **Document termination logic**: Explain in code comments and docstrings how the workflow terminates
4. **Test edge cases**: Verify that the workflow terminates correctly under various scenarios

## References

- [Agent Framework Workflow Documentation](https://github.com/microsoft/agent-framework)
- [Coordinator Pattern Best Practices](https://github.com/microsoft/agent-framework/blob/main/docs/patterns.md)
- Project: `src/spec_to_agents/workflow/core.py` - Workflow builder with termination documentation
- Project: `src/spec_to_agents/workflow/executors.py` - Coordinator implementation with termination logic
