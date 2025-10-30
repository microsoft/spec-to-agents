# Agent Factory Function Refactoring Design

**Date**: 2025-01-30
**Status**: Approved

## Purpose

Refactor `event_planning_workflow.py` to import agents from individual agent files in `src/spec_to_agents/agents/` instead of defining all agent creation inline. This improves modularity, reusability, and maintainability.

## Current State

All agent creation happens in `build_event_planning_workflow()`:
- 5 specialist agents created inline (lines 118-155)
- Agent configuration mixed with workflow orchestration logic
- No reusable agent factories for testing or alternative workflows

## Design Decision

**Pattern**: Factory functions in individual agent files

Each agent file exports an async `create_agent()` function that:
- Takes client and required tools as parameters
- Returns a fully configured `ChatAgent` instance
- Encapsulates all agent-specific configuration (name, prompt, tools, response format)

## Architecture

### File Structure
```
src/spec_to_agents/agents/
├── budget_analyst.py          # Adds: create_agent(client, code_interpreter, mcp_tool, request_user_input)
├── catering_coordinator.py    # Adds: create_agent(client, bing_search, mcp_tool, request_user_input)
├── event_coordinator.py       # Adds: create_agent(client, mcp_tool)
├── logistics_manager.py       # Adds: create_agent(client, weather, calendar_tools, mcp_tool, request_user_input)
└── venue_specialist.py        # Adds: create_agent(client, bing_search, mcp_tool, request_user_input)
```

### Factory Function Signature Pattern

**For Specialists (with structured output):**
```python
async def create_agent(
    client: AzureAIAgentClient,
    <domain_specific_tool>,  # e.g., bing_search, code_interpreter
    mcp_tool,
    request_user_input,
) -> ChatAgent:
    """Create <Agent Name> for event planning workflow."""
    return client.create_agent(
        name="<AgentName>",
        instructions=<agent_prompt>.SYSTEM_PROMPT,
        tools=[<domain_tool>, mcp_tool, request_user_input],
        response_format=SpecialistOutput,
        store=True,
    )
```

**For Coordinator (no structured output):**
```python
async def create_agent(
    client: AzureAIAgentClient,
    mcp_tool,
) -> ChatAgent:
    """Create Event Coordinator for workflow orchestration."""
    return client.create_agent(
        name="EventCoordinator",
        instructions=event_coordinator.SYSTEM_PROMPT,
        tools=[mcp_tool],
        store=True,
    )
```

### Workflow Builder Changes

Before:
```python
async def build_event_planning_workflow() -> Workflow:
    client = get_chat_client()
    mcp_tool = await get_sequential_thinking_tool()

    # 50+ lines of inline agent creation
    venue_agent = client.create_agent(
        name="VenueSpecialist",
        instructions=venue_specialist.SYSTEM_PROMPT,
        tools=[bing_search, mcp_tool, request_user_input],
        response_format=SpecialistOutput,
        store=True,
    )
    # ... repeated for all 5 agents
```

After:
```python
async def build_event_planning_workflow() -> Workflow:
    client = get_chat_client()
    mcp_tool = await get_sequential_thinking_tool()
    bing_search = HostedWebSearchTool(...)
    code_interpreter = HostedCodeInterpreterTool(...)

    # Clean delegation to factory functions
    coordinator_agent = await event_coordinator.create_agent(client, mcp_tool)
    venue_agent = await venue_specialist.create_agent(
        client, bing_search, mcp_tool, request_user_input
    )
    budget_agent = await budget_analyst.create_agent(
        client, code_interpreter, mcp_tool, request_user_input
    )
    # ... etc
```

## Agent-Specific Configurations

| Agent | Domain Tool | Shared Tools | Response Format |
|-------|-------------|--------------|-----------------|
| Event Coordinator | None | mcp_tool | None (free-form) |
| Venue Specialist | bing_search | mcp_tool, request_user_input | SpecialistOutput |
| Budget Analyst | code_interpreter | mcp_tool, request_user_input | SpecialistOutput |
| Catering Coordinator | bing_search | mcp_tool, request_user_input | SpecialistOutput |
| Logistics Manager | weather, calendar_tools | mcp_tool, request_user_input | SpecialistOutput |

## Implementation Tasks

1. **Add factory functions to each agent file** (5 files)
   - Import required types and message formats
   - Add `create_agent()` function with docstring
   - Export function in `__all__`

2. **Refactor workflow builder** (1 file)
   - Import agent modules
   - Replace inline agent creation with factory calls
   - Keep tool creation and workflow orchestration unchanged

3. **Update tests** (as needed)
   - Verify factory functions can be tested independently
   - Ensure workflow tests still pass

## Benefits

1. **Modularity**: Agent configuration co-located with agent definitions
2. **Reusability**: Factory functions available for tests and alternative workflows
3. **Maintainability**: Single source of truth for each agent's configuration
4. **Clarity**: Workflow file focuses on orchestration, not agent details
5. **Testability**: Can unit test agent creation independently

## Non-Goals

- Not changing agent behavior or prompts
- Not modifying workflow orchestration logic
- Not changing tool implementations
- Not adding new agents or features

## Validation

**Success criteria:**
- All agent files export `create_agent()` function
- Workflow file imports and uses factory functions
- All existing tests pass
- DevUI workflow still loads and executes correctly
- No behavior changes to end-user functionality

**Test plan:**
1. Run unit tests: `uv run pytest tests/`
2. Run workflow integration tests
3. Start DevUI: `uv run app`
4. Execute sample event planning request
5. Verify agents behave identically to before refactor
