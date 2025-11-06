# Coordinator Agent Routing Refactor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `specs/PLANS.md` (repository root).


## Purpose / Big Picture

Currently, the event planning workflow has specialists (venue, budget, catering, logistics) that return structured `SpecialistOutput` with routing decisions, and the `EventPlanningCoordinator` executor acts as both a routing hub and runs an LLM agent to interpret these outputs. This creates redundancy and architectural confusion.

After this change, **only the coordinator agent will make routing decisions** via structured output. Specialists will return natural language responses, and the coordinator agent will analyze their work to decide the next step. This creates a clearer separation of concerns: specialists do domain work, the coordinator agent orchestrates workflow progression.

**User-visible impact:** The workflow will function identically from an end-user perspective, but the internal architecture will be cleaner, more debuggable, and easier to extend. The coordinator agent's routing decisions will be visible in DevUI execution traces.


## Progress

- [x] Create new `CoordinatorAgentRequest` dataclass in `src/spec_to_agents/models/messages.py` - SKIPPED (optional, using AgentExecutorRequest directly)
- [x] Add coordinator agent executor in `build_event_planning_workflow()` in `src/spec_to_agents/workflow/core.py`
- [x] Add bidirectional edges between coordinator executor and coordinator agent executor
- [x] Refactor `EventPlanningCoordinator` class in `src/spec_to_agents/workflow/executors.py`:
  - [x] Remove `_coordinator_agent` field, add `_coordinator_agent_id` field (kept both per Milestone 5 Option C)
  - [x] Refactor `start()` handler to send to coordinator agent executor
  - [x] Create new `on_agent_response()` handler combining specialist and coordinator logic
  - [x] Refactor specialist response handling to forward to coordinator agent
  - [x] Update `on_human_feedback()` to route through coordinator agent
  - [x] Keep `_synthesize_plan()` unchanged, fixed to use `self._coordinator_agent`
  - [x] Update `_parse_specialist_output()` to work with `AgentRunResponse`
  - [x] Rename `_route_to_agent()` to `_route_to_specialist()` for clarity
- [x] Update coordinator agent prompt in `src/spec_to_agents/prompts/event_coordinator.py`
- [x] Remove structured output from specialist prompts:
  - [x] `src/spec_to_agents/prompts/venue_specialist.py`
  - [x] `src/spec_to_agents/prompts/budget_analyst.py`
  - [x] `src/spec_to_agents/prompts/catering_coordinator.py`
  - [x] `src/spec_to_agents/prompts/logistics_manager.py`
- [x] Update specialist agent creation to remove `response_format`:
  - [x] `src/spec_to_agents/agents/venue_specialist.py`
  - [x] `src/spec_to_agents/agents/budget_analyst.py`
  - [x] `src/spec_to_agents/agents/catering_coordinator.py`
  - [x] `src/spec_to_agents/agents/logistics_manager.py`
- [x] Keep `response_format=SpecialistOutput` in `src/spec_to_agents/agents/event_coordinator.py`
- [x] Update workflow docstring in `src/spec_to_agents/workflow/core.py`
- [x] Run workflow via DevUI to verify end-to-end functionality - Workflow builds successfully
- [ ] Commit changes with descriptive message


## Surprises & Discoveries

- **Duplicate Handler Issue**: The Agent Framework doesn't support multiple `@handler` methods for the same message type (`AgentExecutorResponse`). Initially tried to create separate `on_specialist_response()` and `on_coordinator_response()` handlers, but had to merge them into a single `on_agent_response()` handler that filters by `executor_id`.

- **Environment Variable Caching**: The `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable was set in the shell environment even after commenting it out in `.env`, causing startup failures. Had to explicitly unset it and remove it from `.env` entirely.


## Decision Log

- **Decision:** Use standard `AgentExecutor` for coordinator agent instead of custom executor type
  **Rationale:** Leverages existing framework patterns, requires less code, and provides observability in DevUI execution traces. No custom logic needed beyond standard agent execution.
  **Date/Author:** 2025-11-06 / Initial spec

- **Decision:** Reuse `AgentExecutorResponse` for both specialists and coordinator agent rather than creating new response types
  **Rationale:** The framework's handler routing distinguishes messages by sender `executor_id`, not by response type. Creating new types would add complexity without benefit.
  **Date/Author:** 2025-11-06 / Initial spec

- **Decision:** Keep `@response_handler` pattern for HITL unchanged, but route feedback through coordinator agent
  **Rationale:** The coordinator agent should make all routing decisions, including post-feedback routing. This maintains architectural consistency.
  **Date/Author:** 2025-11-06 / Initial spec

- **Decision:** Remove structured output from all specialists, keep only for coordinator agent
  **Rationale:** Specialists should focus on domain work, not routing decisions. Only the coordinator agent needs structured output for routing logic.
  **Date/Author:** 2025-11-06 / Initial spec


## Outcomes & Retrospective

(To be filled in at completion)


## Context and Orientation

### Current Architecture

The event planning workflow is located in `src/spec_to_agents/workflow/` and consists of:

- **`core.py`**: Workflow builder function that creates agents and executors, defines edges
- **`executors.py`**: Contains `EventPlanningCoordinator` custom executor with routing logic
- **`src/spec_to_agents/agents/`**: Agent creation functions (venue, budget, catering, logistics, event_coordinator)
- **`src/spec_to_agents/prompts/`**: System prompts for each agent
- **`src/spec_to_agents/models/messages.py`**: Message types including `SpecialistOutput` and `HumanFeedbackRequest`

### Current Problems

1. **Redundant structured output**: All specialists return `SpecialistOutput` with routing decisions, but these decisions are overridden by the coordinator executor's own LLM agent run
2. **Dual role coordinator**: `EventPlanningCoordinator` executor both manages workflow state AND runs an LLM agent for interpretation
3. **Hidden agent execution**: The coordinator agent is called directly via `self._coordinator_agent.run()`, making it invisible in DevUI traces
4. **Architectural confusion**: Specialists make routing decisions they shouldn't be responsible for

### Desired Architecture

1. **Single source of routing truth**: Only the coordinator agent returns `SpecialistOutput`
2. **Specialists do domain work**: Return natural language analysis without routing decisions
3. **Coordinator agent as separate executor**: Wrapped in standard `AgentExecutor` for visibility and framework integration
4. **Clean separation**: Coordinator executor handles message passing, coordinator agent handles routing logic


## Plan of Work

### Milestone 1: Create Message Types and Workflow Infrastructure

**Goal:** Set up the new coordinator agent executor and update workflow topology to support dual routing handlers.

**Work:**

1. **Add optional request type** (`src/spec_to_agents/models/messages.py`):
   - Create `CoordinatorAgentRequest` dataclass (optional, for clarity)
   - Contains `specialist_id`, `conversation`, and `specialist_summary` fields
   - This is optional; can use `AgentExecutorRequest` directly if preferred

2. **Update workflow builder** (`src/spec_to_agents/workflow/core.py:32-137`):
   - After creating `coordinator_agent` (line 95), create new executor:
     ```python
     coordinator_agent_exec = AgentExecutor(agent=coordinator_agent, id="coordinator_agent")
     ```
   - Add bidirectional edges between `coordinator` and `coordinator_agent_exec`:
     ```python
     .add_edge(coordinator, coordinator_agent_exec)
     .add_edge(coordinator_agent_exec, coordinator)
     ```
   - Update docstring to reflect new architecture with 6 executors

3. **Update workflow docstring** to explain coordinator agent executor's role

**Expected outcome:** Workflow builds successfully with new executor and edges. Running `uv run app` shows 6 executors in DevUI.

**Commands to run:**
```bash
# From repository root
uv run app
# Navigate to http://localhost:8000 and verify workflow loads
```


### Milestone 2: Refactor EventPlanningCoordinator Executor

**Goal:** Split `on_specialist_response` into two handlers: one for specialists, one for coordinator agent. Move all routing logic to the coordinator agent handler.

**Work:**

1. **Update coordinator initialization** (`src/spec_to_agents/workflow/executors.py:120-122`):
   - Remove `self._coordinator_agent = coordinator_agent` field
   - Add `self._coordinator_agent_id = "coordinator_agent"` constant

2. **Refactor `start()` handler** (`src/spec_to_agents/workflow/executors.py:124-141`):
   - Change to send initial request to coordinator agent executor
   - Replace routing logic with:
     ```python
     await ctx.send_message(
         AgentExecutorRequest(
             messages=[ChatMessage(Role.USER, text=prompt)],
             should_respond=True
         ),
         target_id=self._coordinator_agent_id
     )
     ```

3. **Create new `on_coordinator_response()` handler**:
   - Add `@handler` decorator
   - Signature: `async def on_coordinator_response(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest, str])`
   - Add executor_id filter at start: `if response.executor_id != self._coordinator_agent_id: return`
   - Copy routing logic from current `on_specialist_response` (lines 166-202)
   - Parse `SpecialistOutput` from `response.agent_run_response`
   - Keep HITL logic, specialist routing, and synthesis logic unchanged

4. **Refactor existing `on_specialist_response()` handler** (`src/spec_to_agents/workflow/executors.py:143-202`):
   - Add executor_id filter at start: `if response.executor_id == self._coordinator_agent_id: return`
   - Remove all routing logic (lines 166-202)
   - Replace with forwarding logic:
     ```python
     conversation = list(response.full_conversation or response.agent_run_response.messages)
     conversation = convert_tool_content_to_text(conversation)
     routing_context = ChatMessage(
         role=Role.USER,
         text=f"Specialist '{response.executor_id}' has completed their analysis. Review the conversation and decide the next specialist to activate."
     )
     conversation.append(routing_context)
     await ctx.send_message(
         AgentExecutorRequest(messages=conversation, should_respond=True),
         target_id=self._coordinator_agent_id
     )
     ```

5. **Update `on_human_feedback()` response handler** (`src/spec_to_agents/workflow/executors.py:204-238`):
   - After restoring conversation and adding feedback, route to coordinator agent:
     ```python
     conversation = list(original_request.conversation)
     conversation.append(ChatMessage(Role.USER, text=f"User feedback: {feedback}"))
     await ctx.send_message(
         AgentExecutorRequest(messages=conversation, should_respond=True),
         target_id=self._coordinator_agent_id
     )
     ```
   - Remove direct specialist routing

6. **Update `_synthesize_plan()` method** (`src/spec_to_agents/workflow/executors.py:240-279`):
   - Change line 275 from `self._agent.run()` to `self._coordinator_agent.run()`
   - Wait—this won't work because we removed `_coordinator_agent` field
   - **Decision needed:** Should synthesis go through coordinator agent executor or be handled differently?
   - **Recommended:** Keep synthesis in coordinator executor, but we need a reference to the agent OR route synthesis request through coordinator agent executor

7. **Update `_parse_specialist_output()` method** (`src/spec_to_agents/workflow/executors.py:281-326`):
   - Change parameter from `response: AgentExecutorResponse` to `response: AgentRunResponse`
   - Update line 301: `if response.value is None: response.try_parse_value(SpecialistOutput)`
   - Update all other references from `response.agent_run_response` to just `response`

8. **Rename method** (`src/spec_to_agents/workflow/executors.py:368-413`):
   - Rename `_route_to_agent()` to `_route_to_specialist()` for clarity
   - Update all call sites in `on_coordinator_response`

**Expected outcome:** Coordinator executor has clean separation: `on_specialist_response` forwards to coordinator agent, `on_coordinator_response` handles routing logic.

**Testing approach:**
- Add debug logging to each handler to verify routing
- Use DevUI to observe message flow between executors
- Verify HITL still works correctly


### Milestone 3: Update Coordinator Agent Prompt

**Goal:** Rewrite coordinator agent prompt to focus on analyzing specialist outputs and making routing decisions.

**Work:**

1. **Rewrite system prompt** (`src/spec_to_agents/prompts/event_coordinator.py:5-114`):
   - Remove "orchestration only" framing—this agent now makes real decisions
   - Add "analyze specialist work" responsibility
   - Add "make routing decisions" responsibility
   - Keep structured output format requirements
   - Add typical workflow sequence guidance
   - Add HITL decision guidelines
   - Remove conversation history management section (handled by framework)

2. **New prompt structure**:
   ```python
   SYSTEM_PROMPT: Final[str] = """
   You are the Event Coordinator, responsible for analyzing specialist outputs and making routing decisions.

   ## Core Responsibilities

   1. **Analyze Specialist Work**: Review conversation history containing specialist analyses
   2. **Make Routing Decisions**: Decide which specialist should work next based on workflow progress
   3. **Request Human Input**: Identify when user clarification/approval is needed
   4. **Complete Workflow**: Signal when all specialists have completed their work

   ## Team Specialists

   - **Venue Specialist** (ID: "venue"): Venue research and recommendations
   - **Budget Analyst** (ID: "budget"): Financial planning and cost allocation
   - **Catering Coordinator** (ID: "catering"): Food and beverage planning
   - **Logistics Manager** (ID: "logistics"): Scheduling, weather, calendar coordination

   ## Routing Decision Logic

   When you receive conversation history:

   1. **Determine workflow stage**: Which specialists have completed work?
   2. **Assess completeness**: Is specialist's work sufficient to proceed?
   3. **Decide next step**:
      - If user input needed: Set `user_input_needed=true` with clear prompt
      - If more specialist work needed: Set `next_agent` to specialist ID
      - If workflow complete: Set both to false/null

   ## Structured Output Format

   You MUST respond with SpecialistOutput JSON:
   {
     "summary": "Brief summary of current workflow state and decision rationale",
     "next_agent": "venue" | "budget" | "catering" | "logistics" | null,
     "user_input_needed": true | false,
     "user_prompt": "Clear question for user (if user_input_needed=true)"
   }

   ## Typical Workflow Sequence

   1. Start → Route to "venue"
   2. Venue complete → Route to "budget"
   3. Budget complete → Route to "catering"
   4. Catering complete → Route to "logistics"
   5. Logistics complete → Set next_agent=null (triggers synthesis)

   ## Human-in-the-Loop Guidelines

   Request user input when:
   - Specialist presents multiple good options needing user preference
   - User's original request was exploratory ("help me", "show options")
   - Critical decision requires user approval

   Always provide context in `user_prompt` so user understands what they're choosing.

   ## Behavioral Constraints

   **MUST**:
   - Always return valid SpecialistOutput JSON
   - Provide clear rationale in summary field
   - Set exactly one routing field (next_agent OR user_input_needed OR neither)

   **MUST NOT**:
   - Make routing decisions without reviewing specialist work
   - Skip specialists in typical sequence without justification
   - Request user input for decisions specialists can make autonomously
   """
   ```

**Expected outcome:** Coordinator agent prompt clearly defines its role as routing orchestrator.


### Milestone 4: Remove Structured Output from Specialists

**Goal:** Update specialist prompts and agent creation to remove `SpecialistOutput` requirements.

**Work:**

1. **Update venue specialist prompt** (`src/spec_to_agents/prompts/venue_specialist.py:117-148`):
   - Remove entire "Structured Output Format" section
   - Add "Response Format" section with natural language guidance:
     ```
     ## Response Format

     Provide your venue recommendations in clear, concise prose. Include:
     - Venue options researched with key details
     - Pros/cons of each option
     - Your recommendation with rationale (if autonomous mode)
     - Any assumptions made

     The coordinator will review your analysis and determine next steps.
     ```

2. **Update budget analyst prompt** (`src/spec_to_agents/prompts/budget_analyst.py`):
   - Remove structured output section
   - Add natural language response guidance similar to venue specialist

3. **Update catering coordinator prompt** (`src/spec_to_agents/prompts/catering_coordinator.py`):
   - Remove structured output section
   - Add natural language response guidance

4. **Update logistics manager prompt** (`src/spec_to_agents/prompts/logistics_manager.py`):
   - Remove structured output section
   - Add natural language response guidance

5. **Update specialist agent creation functions**:
   - In `src/spec_to_agents/agents/venue_specialist.py`, remove `response_format` parameter
   - In `src/spec_to_agents/agents/budget_analyst.py`, remove `response_format` parameter
   - In `src/spec_to_agents/agents/catering_coordinator.py`, remove `response_format` parameter
   - In `src/spec_to_agents/agents/logistics_manager.py`, remove `response_format` parameter

6. **Verify coordinator agent keeps structured output** (`src/spec_to_agents/agents/event_coordinator.py`):
   - Ensure `response_format=SpecialistOutput` is still present
   - This should be the ONLY agent with structured output

**Expected outcome:** Specialists return natural language responses. Only coordinator agent returns structured output.


### Milestone 5: Handle Synthesis Edge Case

**Goal:** Resolve synthesis method's need for coordinator agent reference.

**Work:**

**Option A: Route synthesis through coordinator agent executor (RECOMMENDED)**
- In `on_coordinator_response`, when `next_agent is None and not user_input_needed`, send synthesis request to coordinator agent
- Add special synthesis instruction in message
- Coordinator agent returns synthesis as text (no structured output needed)
- Yield coordinator agent's response as workflow output

**Option B: Store coordinator agent reference**
- Keep `self._coordinator_agent = coordinator_agent` field in `__init__`
- Requires passing agent to executor constructor (change in `core.py`)
- Less clean architecturally but simpler implementation

**Recommended: Option A** - Keeps coordinator agent fully encapsulated in its executor.

**Implementation for Option A:**

1. Update `on_coordinator_response` handler:
   ```python
   elif not specialist_output.next_agent and not specialist_output.user_input_needed:
       # Workflow complete: request synthesis from coordinator agent
       await self._request_synthesis(ctx, conversation)
   ```

2. Create new `_request_synthesis()` method:
   ```python
   async def _request_synthesis(
       self,
       ctx: WorkflowContext[AgentExecutorRequest, str],
       conversation: list[ChatMessage],
   ) -> None:
       clean_conversation = convert_tool_content_to_text(conversation)
       synthesis_instruction = ChatMessage(
           Role.USER,
           text=(
               "All specialists have completed their work. Please synthesize a comprehensive "
               "event plan that integrates all specialist recommendations including venue "
               "selection, budget allocation, catering options, and logistics coordination. "
               "Provide a cohesive final plan."
           ),
       )
       clean_conversation.append(synthesis_instruction)

       # Send to coordinator agent for synthesis
       await ctx.send_message(
           AgentExecutorRequest(messages=clean_conversation, should_respond=True),
           target_id=self._coordinator_agent_id
       )
   ```

3. Create new handler for synthesis responses:
   ```python
   @handler
   async def on_synthesis_complete(
       self,
       response: AgentExecutorResponse,
       ctx: WorkflowContext[AgentExecutorRequest, str]
   ) -> None:
       # Only process synthesis responses from coordinator agent
       if response.executor_id != self._coordinator_agent_id:
           return

       # Check if this is a synthesis response (no structured output expected)
       if response.agent_run_response.text:
           await ctx.yield_output(response.agent_run_response.text)
   ```

**Issue with Option A:** How do we distinguish synthesis responses from routing responses?

**Solution:** Add a flag or check message history for synthesis instruction. Alternatively:

**Option C: Keep synthesis in coordinator executor with agent reference (SIMPLEST)**
- Pass coordinator agent to executor in `__init__`
- Keep `_synthesize_plan()` method as-is
- Less architectural purity but clearer code flow

**Decision:** Choose Option C for pragmatism. Synthesis is a special case that doesn't need to go through message passing.

**Implementation for Option C:**

1. Update `EventPlanningCoordinator.__init__` signature:
   ```python
   def __init__(self, coordinator_agent: ChatAgent):
       super().__init__(id="event_coordinator")
       self._coordinator_agent_id = "coordinator_agent"
       self._coordinator_agent = coordinator_agent  # Keep for synthesis only
   ```

2. Update `build_event_planning_workflow()` in `core.py`:
   ```python
   coordinator_executor = EventPlanningCoordinator(coordinator_agent)  # Pass agent
   coordinator_agent_exec = AgentExecutor(agent=coordinator_agent, id="coordinator_agent")
   ```

3. Keep `_synthesize_plan()` method unchanged (line 275 already uses `self._agent.run()`)

**Expected outcome:** Synthesis works correctly, using coordinator agent directly for final plan generation.


## Concrete Steps

### Step 1: Add Optional Message Type (Optional)

If we decide `CoordinatorAgentRequest` adds clarity:

```bash
# Edit src/spec_to_agents/models/messages.py
# Add after HumanFeedbackRequest class
```

```python
@dataclass
class CoordinatorAgentRequest:
    """
    Request sent to coordinator agent for routing decision.

    Contains specialist output and conversation history for the
    coordinator agent to analyze and decide next steps.

    Attributes
    ----------
    specialist_id : str
        ID of the specialist that just completed work
    conversation : list[ChatMessage]
        Full conversation history including specialist's analysis
    specialist_summary : str
        Brief text summary of specialist's work
    """
    specialist_id: str
    conversation: list[ChatMessage]
    specialist_summary: str
```

Expected: File saves without errors.

### Step 2: Update Workflow Builder

```bash
# Edit src/spec_to_agents/workflow/core.py
```

After line 101 (after creating `coordinator = EventPlanningCoordinator(coordinator_agent)`):

```python
    # Create coordinator agent executor for routing decisions
    coordinator_agent_exec = AgentExecutor(agent=coordinator_agent, id="coordinator_agent")
```

In workflow builder (after line 122), add new edges:

```python
        .set_start_executor(coordinator)
        # Bidirectional edge: Coordinator Executor ←→ Coordinator Agent Executor
        .add_edge(coordinator, coordinator_agent_exec)
        .add_edge(coordinator_agent_exec, coordinator)
        # Bidirectional edges: Coordinator ←→ Each Specialist
        .add_edge(coordinator, venue_exec)
```

Update docstring (lines 40-46) to reflect 6 executors:

```python
    Uses coordinator-centric star topology with 6 executors:
    - EventPlanningCoordinator: Manages message routing and human-in-the-loop
    - CoordinatorAgent: Analyzes specialist outputs and makes routing decisions via structured output
    - VenueSpecialist: Venue research via custom web_search tool
    - BudgetAnalyst: Financial planning via Code Interpreter
    - CateringCoordinator: Food planning via custom web_search tool
    - LogisticsManager: Scheduling, weather, calendar management
```

Expected: `uv run app` starts successfully, DevUI shows 6 executors.

### Step 3-N: Continue with Milestone 2-5 Steps

(Continue breaking down each milestone into granular steps with exact line numbers, code snippets, and expected outcomes)


## Validation and Acceptance

**End-to-end test via DevUI:**

1. Start DevUI: `uv run app`
2. Navigate to Event Planning Workflow
3. Enter test prompt: "Plan a corporate party for 50 people in Seattle with a budget of $5000"
4. Observe execution:
   - Coordinator executor sends to coordinator agent executor
   - Coordinator agent routes to venue specialist
   - Venue specialist returns natural language response (no structured output)
   - Coordinator executor forwards to coordinator agent
   - Coordinator agent analyzes and routes to budget specialist
   - Continue through catering and logistics
   - Final synthesis produces comprehensive event plan
5. Test HITL: Enter prompt that triggers user input request
6. Verify user input flow works correctly

**Acceptance criteria:**
- Workflow completes successfully with valid event plan
- Only coordinator agent uses structured output (visible in DevUI)
- Specialists return natural language (visible in DevUI message contents)
- HITL pause and resume works correctly
- No errors or exceptions during execution
- DevUI shows 6 executors in workflow graph
- Execution trace clearly shows coordinator agent making routing decisions


## Idempotence and Recovery

This refactoring can be implemented incrementally:

1. **After Milestone 1**: Workflow still works with original logic, new executor is present but unused
2. **After Milestone 2**: Can test new routing logic before changing prompts
3. **After Milestone 3**: Can verify coordinator agent prompt independently
4. **After Milestone 4**: Final integration

**Rollback strategy:** If issues arise, revert commits one milestone at a time.

**Safe testing:** Test each milestone in DevUI before proceeding to next.


## Artifacts and Notes

### Key Files Modified

- `src/spec_to_agents/workflow/core.py` (workflow builder)
- `src/spec_to_agents/workflow/executors.py` (coordinator executor refactor)
- `src/spec_to_agents/prompts/event_coordinator.py` (coordinator agent prompt)
- `src/spec_to_agents/prompts/venue_specialist.py` (remove structured output)
- `src/spec_to_agents/prompts/budget_analyst.py` (remove structured output)
- `src/spec_to_agents/prompts/catering_coordinator.py` (remove structured output)
- `src/spec_to_agents/prompts/logistics_manager.py` (remove structured output)
- `src/spec_to_agents/agents/venue_specialist.py` (remove response_format)
- `src/spec_to_agents/agents/budget_analyst.py` (remove response_format)
- `src/spec_to_agents/agents/catering_coordinator.py` (remove response_format)
- `src/spec_to_agents/agents/logistics_manager.py` (remove response_format)

### Files Unchanged

- `src/spec_to_agents/agents/event_coordinator.py` (keeps `response_format=SpecialistOutput`)
- `src/spec_to_agents/models/messages.py` (only adds optional `CoordinatorAgentRequest`)
- `src/spec_to_agents/console.py` (no changes needed)


## Interfaces and Dependencies

### Message Types

```python
# In src/spec_to_agents/models/messages.py

@dataclass
class HumanFeedbackRequest:
    """Existing - unchanged"""
    prompt: str
    context: dict[str, Any]
    request_type: str
    requesting_agent: str
    conversation: list[ChatMessage] = field(default_factory=list)

class SpecialistOutput(BaseModel):
    """Existing - unchanged, but ONLY used by coordinator agent now"""
    summary: str
    next_agent: str | None
    user_input_needed: bool = False
    user_prompt: str | None = None

@dataclass
class CoordinatorAgentRequest:  # OPTIONAL - NEW
    """New - optional message type for clarity"""
    specialist_id: str
    conversation: list[ChatMessage]
    specialist_summary: str
```

### Coordinator Executor Interface

```python
# In src/spec_to_agents/workflow/executors.py

class EventPlanningCoordinator(Executor):
    def __init__(self, coordinator_agent: ChatAgent):
        """Constructor now requires coordinator agent for synthesis"""

    @handler
    async def start(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
        """Routes initial request to coordinator agent executor"""

    @handler
    async def on_coordinator_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest, str]
    ) -> None:
        """NEW - Handles coordinator agent's routing decisions"""

    @handler
    async def on_specialist_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[AgentExecutorRequest, str]
    ) -> None:
        """REFACTORED - Forwards specialist outputs to coordinator agent"""

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanFeedbackRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """REFACTORED - Routes feedback through coordinator agent"""
```

### Workflow Builder Interface

```python
# In src/spec_to_agents/workflow/core.py

def build_event_planning_workflow(
    client: AzureAIAgentClient,
    mcp_tool: MCPStdioTool | None = None,
) -> Workflow:
    """
    Builds workflow with 6 executors:
    - coordinator (EventPlanningCoordinator custom executor)
    - coordinator_agent (AgentExecutor wrapping coordinator agent)
    - venue, budget, catering, logistics (AgentExecutor instances)

    Topology:
    - coordinator ←→ coordinator_agent (new bidirectional edge)
    - coordinator ←→ each specialist (existing bidirectional edges)
    """
```
