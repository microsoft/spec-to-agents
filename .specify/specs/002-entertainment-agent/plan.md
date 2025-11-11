# Implementation Plan: Entertainment Agent

## Architecture Overview

### Component Structure
```
src/spec_to_agents/
├── agents/
│   └── entertainment_specialist.py    # NEW: Agent creation module
├── prompts/
│   └── entertainment_specialist.py    # NEW: System prompt and instructions
├── workflow/
│   ├── executors.py                   # MODIFIED: Add EntertainmentSpecialist executor
│   └── builder.py                     # MODIFIED: Add entertainment → coordinator edge
└── tests/
    └── functional/
        └── test_entertainment_agent.py # NEW: Functional test suite
```

### Workflow Integration

**Routing Pattern:**
```
EventCoordinator
    ├─→ VenueSpecialist → BudgetAnalyst → CateringCoordinator → LogisticsManager → EntertainmentSpecialist → EventCoordinator
```

**Structured Output Flow:**
1. Logistics Agent completes, sets `next_agent="entertainment"`
2. Coordinator routes to Entertainment Specialist via `ctx.send()`
3. Entertainment Agent processes, sets `next_agent=None`
4. Coordinator synthesizes final plan (all specialists complete)

## Implementation Details

### 1. Agent Module (`agents/entertainment_specialist.py`)

**Responsibilities:**
- Create Entertainment Specialist agent with web search capability
- Integrate MCP `sequential-thinking` tool conditionally
- Use `SpecialistOutput` response format

**Implementation:**
```python
@inject
def create_agent(
    client: BaseChatClient = Provide["client"],
    global_tools: dict[str, ToolProtocol] = Provide["global_tools"],
    model_config: dict[str, Any] = Provide["model_config"],
) -> ChatAgent:
    """
    Create Entertainment Specialist agent for event planning workflow.
    
    IMPORTANT: Uses dependency injection. ALL parameters injected via DI container.
    DO NOT pass arguments when calling this function.
    """
    agent_tools: list[ToolProtocol] = [web_search]
    
    if global_tools.get("sequential-thinking"):
        agent_tools.append(global_tools["sequential-thinking"])
    
    return client.create_agent(
        name="entertainment_specialist",
        description="Expert in entertainment planning, vendor research, and event programming.",
        instructions=entertainment_specialist.SYSTEM_PROMPT,
        tools=agent_tools,
        response_format=SpecialistOutput,
        **model_config,
    )
```

**Key Patterns:**
- `@inject` decorator for DI
- `Provide["client"]` for auto-injection
- Conditional MCP tool addition
- `SpecialistOutput` for structured responses
- `**model_config` spreads `store=True` and other settings

### 2. System Prompt (`prompts/entertainment_specialist.py`)

**Responsibilities:**
- Define agent's expertise and decision-making process
- Specify interaction modes (autonomous, collaborative, interactive)
- Document structured output format with examples
- Integrate with workflow context (budget, venue, logistics)

**Prompt Structure:**
```python
SYSTEM_PROMPT: Final[str] = """
You are the Entertainment Specialist, an expert in event entertainment planning.

<core_responsibilities>
- Research entertainment options (speakers, performers, activities)
- Match entertainment to event type, audience, and budget
- Validate compatibility with venue capabilities
- Coordinate timing with event schedule
</core_responsibilities>

<interaction_modes>
**Autonomous Mode (default):**
- Make recommendations within budget
- Use venue capabilities from context
- Suggest timing based on logistics schedule

**Collaborative Mode:**
- Present 2-3 options with tradeoffs
- Ask: "Which entertainment style fits your event?"

**Interactive Mode:**
- User requested comparison of options
- Present detailed breakdown with pros/cons
</interaction_modes>

<decision_process>
1. Extract event details from workflow context:
   - Event type (corporate, social, conference)
   - Audience size and demographics
   - Budget allocation (from Budget Agent)
   - Venue capabilities (from Venue Agent)
   - Event timing (from Logistics Agent)
2. Search for entertainment options using web_search tool
3. Filter by budget and venue compatibility
4. Recommend top 3 options with costs and timing
5. Set next_agent=None (return to coordinator)
</decision_process>

<available_tools>
### 1. web_search
Search for entertainment vendors, performers, speakers.
Example: "Seattle corporate event entertainment 50 people"

### 2. sequential-thinking (optional MCP tool)
Use for complex reasoning when comparing options.
</available_tools>

<structured_output_format>
Return SpecialistOutput JSON:
{
  "summary": "Recommended jazz band ($400) for 7-8pm during dinner. Fits $500 budget, venue has stage.",
  "next_agent": null,
  "user_input_needed": false,
  "user_prompt": null
}
</structured_output_format>
"""
```

### 3. Executor Module (`workflow/executors.py`)

**Modifications:**
- Add `EntertainmentSpecialist` executor class
- Follow existing executor pattern (VenueSpecialist, BudgetAnalyst, etc.)

**Implementation:**
```python
class EntertainmentSpecialist(AgentExecutor):
    """
    Entertainment Specialist executor for workflow integration.
    
    Handles entertainment research and recommendations, integrating with
    budget allocations, venue capabilities, and event timing.
    """
    
    def __init__(self, entertainment_agent: ChatAgent):
        super().__init__(id="entertainment")
        self._agent = entertainment_agent
    
    @handler
    async def on_request(
        self,
        request: AgentExecutorRequest,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """
        Handle entertainment request from logistics agent.
        
        Processes entertainment research, validates against budget and venue,
        returns to coordinator with structured output.
        """
        # Run agent with conversation context
        result = await self._agent.run(request.messages)
        
        # Parse structured output
        output = SpecialistOutput.model_validate_json(result.output)
        
        logger.info(
            f"Entertainment recommendations: {output.summary[:100]}... "
            f"Next: {output.next_agent or 'coordinator'}"
        )
        
        # Route based on structured output
        if output.user_input_needed:
            # Request user input via coordinator
            await ctx.send(
                AgentExecutorResponse(
                    output=output.model_dump_json(),
                    messages=result.messages,
                ),
                recipient=ctx.workflow_id,  # Coordinator handles HITL
            )
        else:
            # Return to coordinator (next_agent=None)
            await ctx.send(
                AgentExecutorResponse(
                    output=output.model_dump_json(),
                    messages=result.messages,
                ),
                recipient=ctx.workflow_id,
            )
```

### 4. Workflow Builder (`workflow/builder.py`)

**Modifications:**
- Import `entertainment_specialist` module
- Create Entertainment Specialist executor
- Add bidirectional edge: coordinator ↔ entertainment

**Implementation:**
```python
from spec_to_agents.agents import (
    budget_analyst,
    catering_coordinator,
    entertainment_specialist,  # NEW
    event_coordinator,
    logistics_manager,
    venue_specialist,
)

# Inside build_event_planning_workflow():
coordinator = EventPlanningCoordinator(event_coordinator.create_agent())
venue = VenueSpecialist(venue_specialist.create_agent())
budget = BudgetAnalyst(budget_analyst.create_agent())
catering = CateringCoordinator(catering_coordinator.create_agent())
logistics = LogisticsManager(logistics_manager.create_agent())
entertainment = EntertainmentSpecialist(entertainment_specialist.create_agent())  # NEW

# Build workflow with updated topology
builder = WorkflowBuilder()
builder.add_executor(coordinator)
builder.add_executor(venue)
builder.add_executor(budget)
builder.add_executor(catering)
builder.add_executor(logistics)
builder.add_executor(entertainment)  # NEW

# Add bidirectional edges
builder.add_edge(coordinator.id, venue.id)
builder.add_edge(venue.id, coordinator.id)
builder.add_edge(coordinator.id, budget.id)
builder.add_edge(budget.id, coordinator.id)
builder.add_edge(coordinator.id, catering.id)
builder.add_edge(catering.id, coordinator.id)
builder.add_edge(coordinator.id, logistics.id)
builder.add_edge(logistics.id, coordinator.id)
builder.add_edge(coordinator.id, entertainment.id)  # NEW
builder.add_edge(entertainment.id, coordinator.id)  # NEW

return builder.build()
```

### 5. Functional Tests (`tests/functional/test_entertainment_agent.py`)

**Test Cases:**
1. **test_entertainment_agent_creation**: Verify agent creates with correct config
2. **test_web_search_integration**: Verify `web_search` tool available
3. **test_structured_output**: Verify `SpecialistOutput` response format
4. **test_workflow_integration**: Verify entertainment routes to coordinator
5. **test_budget_awareness**: Verify entertainment respects budget from context

**Implementation:**
```python
import pytest
from agent_framework import AgentExecutorRequest, ChatMessage, Role

from spec_to_agents.agents import entertainment_specialist
from spec_to_agents.models.messages import SpecialistOutput
from spec_to_agents.workflow.executors import EntertainmentSpecialist

@pytest.mark.asyncio
async def test_entertainment_agent_creation(container):
    """Verify Entertainment Specialist agent creates with correct configuration."""
    agent = entertainment_specialist.create_agent()
    
    assert agent.name == "entertainment_specialist"
    assert "web_search" in [t.name for t in agent.tools]
    assert agent.response_format == SpecialistOutput

@pytest.mark.asyncio
async def test_structured_output(container):
    """Verify Entertainment Specialist returns valid SpecialistOutput."""
    agent = entertainment_specialist.create_agent()
    
    messages = [
        ChatMessage(
            Role.USER,
            "Recommend entertainment for corporate party, 50 people, $500 budget"
        )
    ]
    
    result = await agent.run(messages)
    output = SpecialistOutput.model_validate_json(result.output)
    
    assert output.summary
    assert output.next_agent is None  # Returns to coordinator
    assert isinstance(output.user_input_needed, bool)
```

## Integration Checklist

- [ ] Create `agents/entertainment_specialist.py` with agent creation function
- [ ] Create `prompts/entertainment_specialist.py` with system prompt
- [ ] Add `EntertainmentSpecialist` executor to `workflow/executors.py`
- [ ] Update `workflow/builder.py` to include entertainment in workflow topology
- [ ] Create `tests/functional/test_entertainment_agent.py` with test suite
- [ ] Update `prompts/logistics_manager.py` to route to entertainment (`next_agent="entertainment"`)
- [ ] Update `prompts/event_coordinator.py` synthesis to include entertainment section
- [ ] Verify DevUI displays entertainment recommendations correctly

## Testing Strategy

### Console Mode Testing
```bash
# Test entertainment agent in isolation
python -m pytest tests/functional/test_entertainment_agent.py -v

# Test full workflow with entertainment
uv run python src/spec_to_agents/main.py
> "Plan corporate party for 50 people in Seattle, $5k budget"
```

### DevUI Testing
```bash
# Start DevUI and test workflow
uv run python -m spec_to_agents.devui
# Submit: "Plan corporate party for 50 people in Seattle, $5k budget"
# Verify: Entertainment recommendations appear in workflow trace
```

## Risk Mitigation

### Risk 1: Web Search Failures
**Mitigation:** Fallback to generic entertainment suggestions if search returns no results
```python
if not search_results:
    return "Generic options: DJ ($300-500), Live band ($400-800), Trivia host ($200-400)"
```

### Risk 2: Budget Not Allocated
**Mitigation:** Use default 8-12% of total budget if Budget Agent doesn't specify
```python
entertainment_budget = context.get("entertainment_budget") or (total_budget * 0.10)
```

### Risk 3: Timing Conflicts
**Mitigation:** Default to "after dinner" if Logistics Agent doesn't specify schedule
```python
event_timing = context.get("event_schedule") or "7-10pm (entertainment 8:30-9:30pm)"
```

## Success Criteria

- ✅ Agent integrates into workflow with correct routing (logistics → entertainment → coordinator)
- ✅ `web_search` tool successfully finds entertainment vendors
- ✅ Recommendations respect budget allocation from Budget Agent
- ✅ Structured output parses correctly in coordinator synthesis
- ✅ All functional tests pass
- ✅ Console mode execution completes without errors
- ✅ DevUI displays entertainment in workflow trace

---

**Plan Version**: 1.0  
**Last Updated**: 2025-01-11  
**Ready for Implementation**: ✅