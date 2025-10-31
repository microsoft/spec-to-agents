# Project Overview

This is a Python project that uses **Microsoft Agent Framework**--the new unified orchestration framework that combines the best of:

- **Semantic Kernel**: Enterprise-ready AI orchestration
- **AutoGen**: Multi-agent conversation patterns

To build a multi-agent event planning workflow.

# ExecPlans

When writing complex features or significant refactors, use an ExecPlan (as described in `specs/PLANS.md`) from design to implementation. If the user request requires multiple specs, create multiple specification files in the `specs/` directory. After creating the specs, create a master ExecPlan that links to each individual spec ExecPlan. Update the `specs/README.md` to include links to the new specs.

ALWAYS start an ExecPlan creation by consulting the DeepWiki tool for best practices on design patterns, architecture, and implementation strategies. Ask it questions about the system design and constructs in the library that will help you achieve your goals.

Skip using an ExecPlan for straightforward tasks (roughly the easiest 25%).

# Architecture

This project follows a **coordinator-centric star topology** multi-agent workflow architecture.

## Workflow Architecture

**Star Topology with Coordinator Hub:**
```
User Request
    ↓
EventPlanningCoordinator (Routing Hub)
    ↓ ↑ (bidirectional edges)
    ├── Venue Specialist (Web Search)
    ├── Budget Analyst (Code Interpreter)
    ├── Catering Coordinator (Web Search)
    └── Logistics Manager (Weather, Calendar)
    ↓
EventPlanningCoordinator (Synthesis)
    ↓
Final Event Plan
```

**Key Architectural Patterns:**

1. **Coordinator-Centric Routing**: `EventPlanningCoordinator` manages all routing decisions based on structured output from specialists
2. **Service-Managed Threads**: All agents use `store=True` for automatic conversation history management via Azure AI service
3. **Structured Output Routing**: Specialists return `SpecialistOutput` Pydantic model with `next_agent` field for dynamic routing
4. **Human-in-the-Loop**: Framework-native `ctx.request_info()` + `@response_handler` for user interaction
5. **Tool Content Conversion**: Cross-thread message passing requires converting tool calls/results to text summaries

![Workflow Architecture](assets/workflow_architecture.png)

## Agents and Tools

Each specialist agent has access to domain-specific tools:

![Agents and Tools](assets/agent_tools.png)

**Tool Integration:**
- **Custom Web Search**: Replaces Bing Search, used by Venue Specialist and Catering Coordinator
- **Weather Tool**: Open-Meteo API (free, no key required), used by Logistics Manager
- **Calendar Tools**: iCalendar (.ics) management with create/list/delete operations, used by Logistics Manager
- **Code Interpreter**: Python REPL with scratchpad for financial calculations, used by Budget Analyst
- **MCP Tool Orchestration**: sequential-thinking-tools for complex reasoning (optional, all agents)

## Directory Structure

IMPORTANT: For your agents to be discovered by the DevUI, they must be organized in a directory structure like below. Each agent/workflow must have an `__init__.py` that exports the required variable (`agent` or `workflow`).

**Note**: `.env` is a shared env file, it contains the Azure OpenAI config, if this doesn't exist refer to `.env.example` and ask user for values and create `.env`

```
spec-to-agents/
├── src/
│   └── spec_to_agents/
│       ├── __init__.py
│       ├── clients.py # contains shared client code for AI Foundry
│       ├── agents/ # contains core agent/workflow definitions
│       │   ├── __init__.py
│       │   ├── budget_analyst.py
│       │   ├── catering_coordinator.py
│       │   ├── event_coordinator.py
│       │   ├── logistics_manager.py
│       │   └── venue_specialist.py
│       ├── prompts/ # contains system prompts for each agent
│       │   ├── __init__.py
│       │   ├── budget_analyst.py
│       │   ├── catering_coordinator.py
│       │   ├── event_coordinator.py
│       │   ├── logistics_manager.py
│       │   └── venue_specialist.py
│       └── tools/ # contains reusable tool definitions for agents
│           └── __init__.py
├── tests/ # contains units tests for agents and tools
├── .env  
└── pyproject.toml
```

# Development Guidelines

## General

- Before implementing a large refactor or new feature explain your plan and get approval.
- Human-in-the-loop: If you're unsure about a design decision or implementation detail, ask for clarification before proceeding. Feel free to ask clarifying questions as you are working.
- Avoid re-inventing the wheel: Use existing libraries and tools where appropriate.

## Python

`uv` is the command-line tool used to manage the development environment and dependencies in Python projects. This project uses the workspace feature of `uv` to manage multiple packages within the `packages` directory. Below are the common commands you'll use:

- `uv sync --dev` - Install / sync regular + dev dependencies
- `uv add <package>` - Add a dependency
- `uv lock` - Lock dependencies / regenerate lockfile
- `uv run` - You NEVER need to activate a virtual environment manually; just prefix commands with `uv run`
  - `uv run <script>.py` - Run a Python script
  - `uv run -m <module>` - Run a Python module
- `uv run pytest` - Run tests
- `uv run ruff .` - Run linting / formatting
- `uv run mypy .` - Run type checking

**Project-specific Commands:**
- `uv run app` - Start the Agent Framework DevUI for testing and debugging agents/workflows

### Technology Stack Focus
- **Python 3.11+**: Latest stable version with modern features
- **Pydantic**: Data validation and settings management
- **Agent Framework**: Building and orchestrating agents
- **Agent Framework DevUI**: Workflow/agent frontend
- **Infrastructure**: AI Foundry, Azure Container Apps, AZD template, Managed Identity (No API Key Authentication)

### Code Organization and Modularity

**Prefer highly modular code** that separates concerns into distinct modules. This improves:
- **Testability**: Each module can be tested in isolation
- **Reusability**: Modules can be used independently
- **Maintainability**: Changes are localized to specific modules
- **Readability**: Clear separation of concerns makes code easier to understand

**Guidelines**:
- Keep modules focused on a single responsibility
- Use clear module boundaries and minimal public APIs
- Prefer composition over large monolithic modules
- Extract shared functionality into dedicated modules as the codebase grows

### Code Organization and Modularity

**Prefer highly modular code** that separates concerns into distinct modules. This improves:
- **Testability**: Each module can be tested in isolation
- **Reusability**: Modules can be used independently
- **Maintainability**: Changes are localized to specific modules
- **Readability**: Clear separation of concerns makes code easier to understand

**Guidelines**:
- Keep modules focused on a single responsibility
- Use clear module boundaries and minimal public APIs
- Prefer composition over large monolithic modules
- Extract shared functionality into dedicated modules as the codebase grows

## Conversation History Management

The workflow uses **service-managed threads** for automatic conversation history management, eliminating manual message tracking.

### Service-Managed Threads Pattern

**How It Works:**
When agents are created with `store=True`, the Azure AI Agent Client leverages service-managed threads:

1. **Thread Creation**: Client creates `service_thread_id` in Azure AI service backend
2. **Message Storage**: All messages automatically stored in service backend
3. **Automatic Retrieval**: On subsequent `agent.run()` calls, conversation history retrieved automatically
4. **No Manual Tracking**: No need for `full_conversation` passing or manual message arrays

**Implementation:**
```python
agent = client.create_agent(
    name="Agent Name",
    instructions=PROMPT,
    tools=[...],
    store=True,  # Enable service-managed threads
)
```

**Benefits:**
- Eliminates manual conversation tracking in coordinator
- Conversation persists across workflow sessions
- Simplifies coordinator logic significantly
- Reduces risk of message synchronization bugs

**Code Location:** All agents in `src/spec_to_agents/agents/*.py` use `store=True`

### Tool Content Conversion Pattern

**Problem:** `FunctionCallContent` and `FunctionResultContent` cannot cross thread boundaries because they embed thread-specific `run_id` in their `call_id`.

**Error:** "No thread ID was provided, but chat messages includes tool results"

**Solution:** The `convert_tool_content_to_text()` function converts tool-related content to text summaries:
- `FunctionCallContent` → `"[Tool Call: tool_name({args})]"`
- `FunctionResultContent` → `"[Tool Result for call_id: result]"`
- Other content types passed through unchanged

**When To Use:**
- When passing messages between agents with different service thread IDs
- In `_route_to_agent()`: Before sending messages to specialists
- In `_synthesize_plan()`: Before sending conversation to coordinator

**Code Location:** `src/spec_to_agents/workflow/executors.py:25-86`

## Human-in-the-Loop (HITL)

The workflow supports pausing for user input using framework-native patterns.

### HITL Pattern: ctx.request_info() + @response_handler

**How It Works:**

1. **Specialist Signals Need**: Specialist sets `user_input_needed=True` in `SpecialistOutput`
2. **Coordinator Pauses Workflow**: Calls `ctx.request_info(HumanFeedbackRequest, ...)`
3. **Framework Creates Checkpoint**: Serializes workflow state including conversation history
4. **DevUI Emits RequestInfoEvent**: User sees prompt in UI
5. **User Responds**: Provides feedback via DevUI
6. **Framework Restores Checkpoint**: Deserializes workflow state automatically
7. **Handler Receives Response**: `@response_handler` gets original request + user feedback
8. **Coordinator Continues**: Routes back to requesting specialist with feedback

**Implementation:**
```python
# In coordinator
await ctx.request_info(
    request_data=HumanFeedbackRequest(
        prompt="Which venue do you prefer?",
        conversation=full_conversation,  # Preserved in checkpoint
        requesting_agent="venue",
    ),
    request_type=HumanFeedbackRequest,
    response_type=str,
)

@response_handler
async def on_human_feedback(
    self,
    original_request: HumanFeedbackRequest,
    feedback: str,
    ctx: WorkflowContext,
) -> None:
    # Framework automatically restored conversation
    conversation = list(original_request.conversation)
    await self._route_to_agent(
        original_request.requesting_agent,
        feedback,
        ctx,
        prior_conversation=conversation,
    )
```

**Key Benefits:**
- Automatic conversation preservation via checkpointing
- No manual state tracking required
- DevUI integration out-of-the-box
- Clean separation: specialists declare needs, coordinator handles interaction

**Code Location:** `src/spec_to_agents/workflow/executors.py:201-235`

## Key Implementation Patterns

### 1. Coordinator-Centric Routing

The `EventPlanningCoordinator` custom executor manages all routing decisions:

- **Receives initial requests** via `@handler start(prompt: str)`
- **Processes specialist responses** via `@handler on_specialist_response(AgentExecutorResponse)`
- **Handles human feedback** via `@response_handler on_human_feedback(HumanFeedbackRequest, str)`
- **Synthesizes final plan** via `_synthesize_plan(conversation)`

**Code Location:** `src/spec_to_agents/workflow/executors.py:89-277`

### 2. Structured Output Routing

Specialists return Pydantic `SpecialistOutput` model with explicit routing decisions:

```python
class SpecialistOutput(BaseModel):
    summary: str  # Concise summary of recommendations
    next_agent: str | None  # ID of next agent ("venue", "budget", "catering", "logistics") or None
    user_input_needed: bool = False  # Whether user input is required
    user_prompt: str | None = None  # Question to ask user if input needed
```

**Routing Logic:**
```python
if specialist_output.user_input_needed:
    await ctx.request_info(...)  # Pause for human input
elif specialist_output.next_agent:
    await self._route_to_agent(specialist_output.next_agent, ...)  # Route to next specialist
else:
    await self._synthesize_plan(...)  # Workflow complete, synthesize
```

**Benefits:**
- Specialists control their own routing
- No hardcoded agent sequence
- Enables conditional logic (e.g., skip agents based on context)
- Explicit, debuggable routing decisions

**Code Location:** `src/spec_to_agents/models/messages.py:52-83`

### 3. Star Topology Workflow Builder

The workflow uses bidirectional edges connecting coordinator to each specialist:

```python
workflow = (
    WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)
    .set_start_executor(coordinator)
    # Bidirectional edges: Coordinator ←→ Each Specialist
    .add_edge(coordinator, venue_exec)
    .add_edge(venue_exec, coordinator)
    .add_edge(coordinator, budget_exec)
    .add_edge(budget_exec, coordinator)
    # ... other specialists ...
    .build()
)
```

**Benefits:**
- Simple mental model: all routing through coordinator hub
- Easy to debug and trace execution
- Natural fit for human-in-the-loop mediation
- Coordinator has complete control over execution flow

**Code Location:** `src/spec_to_agents/workflow/core.py:148-170`

# Code Style

## Documentation

**IMPORTANT: Documentation means docstrings and type hints in the code, NOT separate documentation files.**

- You should NOT create any separate documentation pages (README files, markdown docs, etc.)
- The code itself should contain proficient documentation in the form of docstrings and type hints (for Python)
- For Python: Add comprehensive numpy-style docstrings to all functions, classes, and modules

**Avoid Over-Documenting:**
- Do NOT document obvious behavior (e.g., a function named `get_name` that returns a name doesn't need extensive documentation)
- Focus documentation on WHY and HOW, not WHAT (the code itself shows what it does)
- Document edge cases, non-obvious behavior, and important constraints
- Skip docstrings for trivial functions where the name and type hints are self-explanatory
- Prioritize documenting public APIs, complex logic, and non-intuitive design decisions

## Python

### Documentation and Comments

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
  - Use `numpy` style for docstrings. Example:

  ```python
  def calculate_area(radius: float) -> float:
      """
      Calculate the area of a circle given the radius.

      Parameters
      ----------
      radius : float
          The radius of the circle.

      Returns
      -------
      float
          The area of the circle, calculated as π * radius^2.
      """
      import math
      return math.pi * radius ** 2
  ```
- Use proper built-in type annotations (e.g. `dict[..., ...]`, `list[...]`, `tuple[...]`) and only using `typing` module when needed.
- Prefer to use `|` for union types instead of `Union[...]`, `type | None` instead of `Optional[...]`, etc.
- Break down complex functions into smaller, more manageable functions.

# Test-Driven Development (TDD)

- Never create throwaway test scripts or ad hoc verification files
- If you need to test functionality, write a proper test in the test suite

## Python

- Write tests for all new features in the `tests/` directory
- Use `pytest` as the testing framework
- Use `pytest-mock` for mocking dependencies
- Aim for high test coverage, especially for critical components
- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

# Tools

You have a collection of tools available to assist with development and debugging. These tools can be invoked as needed.

- `sequential-thinking-tools`
  - **When to use:** For complex reasoning tasks that require step-by-step analysis. A good rule of thumb is if the task requires more than 25% effort.
- `deepwiki`
  - **When to use:** Consult for external knowledge or documentation that is not part of the immediate codebase. Can be helpful for system design questions or understanding third-party libraries.
- `context7`
  - **When to use:** For retrieving immediate documentation on the latest version of a library or framework. Useful for quick lookups to double-check syntax, parameters, or usage examples.
- `playwright`
  - **When to use:** Interact with DevUI for testing the workflow end-to-end from prompt to final result. Prefer using this as your default snapshot testing tool. You also have the ability to use `playwright` for viewing the browser console logs and network requests to help debug issues that may arise.

# Updates to This Document
- Update this document as needed to reflect changes in development practices or project structure
  - Updates usually come in the form of the package structure changing
- Do NOT contradict existing guidelines in the document
- This document should be an executive summary of the development practices for this project
  - Keep low-level implementation details out of this document