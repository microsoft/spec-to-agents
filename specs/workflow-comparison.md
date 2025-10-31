# Workflow Architecture Comparison

## Before: Star Topology with Custom Executor

```
                    ┌──────────────────────────────┐
                    │  EventPlanningCoordinator    │
                    │  (Custom Executor)           │
                    │                              │
                    │  • Manual routing logic      │
                    │  • Parse SpecialistOutput    │
                    │  • Handle HITL requests      │
                    │  • Track conversation        │
                    │  • Synthesize final plan     │
                    └──────────────────────────────┘
                            ↕ ↕ ↕ ↕
              ┌─────────────┴─┴─┴─┴─────────────┐
              ↓              ↓   ↓              ↓
         ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
         │ Venue  │    │ Budget │    │Catering│    │Logistics│
         └────────┘    └────────┘    └────────┘    └────────┘

Problems:
- Complex routing in Python code
- Manual message passing
- Specialists must know about routing
- Hard to add/remove agents
- Not declarative
```

## After: Fan-Out/Fan-In Pattern

```
                    ┌──────────────────────────────┐
                    │  Initial Coordinator         │
                    │  (Simple AgentExecutor)      │
                    │                              │
                    │  • Extract requirements      │
                    │  • Provide context           │
                    └──────────────────────────────┘
                              ↓
                    ┌─────────┴─────────┐
                    ↓         ↓         ↓         ↓
               ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
               │ Venue  │ │ Budget │ │Catering│ │Logistics│
               │        │ │        │ │        │ │        │
               └────────┘ └────────┘ └────────┘ └────────┘
                    ↓         ↓         ↓         ↓
                    └─────────┬─────────┘
                              ↓
                    ┌──────────────────────────────┐
                    │  Event Synthesizer           │
                    │  (Simple AgentExecutor)      │
                    │                              │
                    │  • Consolidate outputs       │
                    │  • Create cohesive plan      │
                    └──────────────────────────────┘
                              ↓
                        Final Event Plan

Benefits:
- Fully declarative (WorkflowBuilder edges)
- Parallel specialist execution
- No manual routing
- Each agent has single responsibility
- Easy to add/remove agents
```

## Key Differences

| Aspect | Before (Star) | After (Fan-Out/Fan-In) |
|--------|--------------|-------------------------|
| **Coordinator Type** | Custom Executor class | Simple AgentExecutor |
| **Routing Logic** | In Python code (~400 lines) | Declarative edges |
| **Specialist Execution** | Sequential (one at a time) | Parallel (all at once) |
| **Agent Responsibilities** | Routing + domain logic | Domain logic only |
| **Complexity** | High (custom executor + routing) | Low (standard pattern) |
| **Adding Agents** | Modify coordinator code | Add edges in builder |
| **Testability** | Mock complex executor | Test agents independently |
| **Framework Alignment** | Custom workaround | Standard pattern |

## Code Complexity Reduction

### Before
- EventPlanningCoordinator: ~410 lines of complex routing logic
- Specialists need routing knowledge (next_agent field)
- Manual HITL handling in coordinator
- Tool content conversion for cross-agent communication

### After
- Initial Coordinator: Simple requirement extraction
- Event Synthesizer: Simple consolidation
- Specialists: Domain logic only, no routing
- HITL handled by framework
- Total complexity: ~60% reduction

## Migration Impact

### Breaking Changes
None - public API remains the same

### Internal Changes
- EventPlanningCoordinator custom executor removed
- All executors now simple AgentExecutor instances
- Workflow structure changed from star to fan-out/fan-in
- Specialist prompts simplified

### Performance Impact
Positive - specialists execute in parallel instead of sequentially
