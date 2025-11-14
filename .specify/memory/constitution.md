# Project Constitution: Spec-to-Agents Event Planning System

## Core Principles

### 1. Framework-Native Patterns First
- **Use built-in abstractions**: Leverage service-managed threads (`store=True`), structured outputs, and dependency injection
- **Avoid reinventing**: Don't manually track conversation history or implement custom routing when framework provides solutions
- **Follow established patterns**: Match existing agent creation, tool integration, and executor patterns in codebase

### 2. Minimal, Focused Implementations
- **Single responsibility per agent**: Each agent has one clear domain (venue, budget, catering, logistics, entertainment)
- **Avoid over-engineering**: Don't add databases, complex state management, or unnecessary abstractions
- **Keep tools simple**: Use `@ai_function` decorators with clear docstrings; avoid heavyweight SDKs when simple API calls suffice

### 3. Consistent Code Style
- **Match existing conventions**: Follow the patterns in `agents/*.py`, `tools/*.py`, `workflow/executors.py`
- **Type annotations everywhere**: Use `typing` module for all function signatures
- **Docstrings with numpy format**: Include Parameters, Returns, Notes sections
- **Dependency injection**: Use `@inject` decorator and `Provide[...]` annotations

### 4. Testing Before Features
- **Functional tests required**: Every new agent/tool must have test coverage in `tests/functional/`
- **Unit tests for utilities**: Test helper functions in `tests/unit/`
- **Console mode first**: Ensure basic functionality works via `main.py` before adding DevUI complexity

### 5. Educational Value
- **Clear comments for learners**: Add `# IMPORTANT:` and `# NOTE:` comments explaining non-obvious patterns
- **Follow tutorial structure**: New features should align with existing lab exercise progression
- **Demonstrate best practices**: Code should serve as reference implementation for agent-framework patterns

## Development Standards

### Agent Creation
```python
@inject
def create_agent(
    client: BaseChatClient = Provide["client"],
    global_tools: dict[str, ToolProtocol] = Provide["global_tools"],
    model_config: dict[str, Any] = Provide["model_config"],
) -> ChatAgent:
    """Docstring with numpy format."""
    agent_tools: list[ToolProtocol] = [tool1, tool2]
    
    if global_tools.get("sequential-thinking"):
        agent_tools.append(global_tools["sequential-thinking"])
    
    return client.create_agent(
        name="agent_name",
        description="Human-readable description",
        instructions=prompts.SYSTEM_PROMPT,
        tools=agent_tools,
        response_format=SpecialistOutput,
        **model_config,
    )
```

### Tool Creation
```python
@ai_function
async def tool_name(param: str) -> str:
    """
    Brief description.
    
    Parameters
    ----------
    param : str
        Parameter description
    
    Returns
    -------
    str
        Return value description
    """
    # Implementation
```

### Executor Pattern
```python
class SpecialistExecutor(AgentExecutor):
    def __init__(self, agent: ChatAgent):
        super().__init__(id="agent_id")
        self._agent = agent
    
    @handler
    async def on_request(
        self,
        request: AgentExecutorRequest,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """Handle incoming request."""
        result = await self._agent.run(request.messages)
        # Parse SpecialistOutput, route accordingly
```

## Technical Constraints

### Required Technologies
- **Python 3.11+**: For advanced type hints and async features
- **Microsoft Foundry**: All agents use Azure-hosted models (no local LLMs)
- **Dependency Injection**: `dependency-injector` library for IoC pattern
- **Pydantic V2**: For structured outputs and validation

### Prohibited Patterns
- ❌ Manual message tracking (use service-managed threads)
- ❌ String-based routing (use structured outputs with `next_agent` field)
- ❌ Custom state management (leverage workflow context and thread storage)
- ❌ Hardcoded tool calls (use agent autonomy and structured outputs)

### Code Quality Requirements
- **Type hints**: 100% coverage on function signatures
- **Error handling**: Graceful degradation with informative messages
- **Logging**: Use `logger.info()` for key workflow events
- **Documentation**: Every module has file-level docstring explaining purpose

## Governance

### Decision-Making
1. **Architectural changes**: Must align with Microsoft Agent Framework idioms
2. **New dependencies**: Require justification (prefer built-in or existing dependencies)
3. **Breaking changes**: Must update lab instructions and README

### Review Criteria
- ✅ Follows existing code patterns
- ✅ Includes functional tests
- ✅ Updates relevant documentation
- ✅ Works in both console and DevUI modes
- ✅ Demonstrates educational best practices

---

**Last Updated**: 2025-01-11  
**Applies To**: All feature development in spec-to-agents project