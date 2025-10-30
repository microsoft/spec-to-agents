# Intent-Based Interaction & Enhanced Console Output Design

**Date:** 2025-10-30
**Status:** Design
**Goal:** Create a collaborative yet non-intrusive event planning workflow with clear tool execution visibility

## Overview

This design enhances the event planning workflow to provide a natural, intent-driven interaction model that adapts to user communication style while maintaining efficiency. The system defaults to **autonomous decision-making** and only requests user input when the user's language signals they want collaboration or when critical information is genuinely missing.

**Core Principle:** Handle it for the user unless they explicitly want involvement or something is truly critical.

## Problem Statement

Current state:
- Agent prompts are overly defensive with verbose "DON'T ASK" guidelines
- Console output has basic tool call formatting with truncation
- No clear mechanism for agents to adapt interaction level based on user intent
- Risk of either annoying users with too many questions OR making decisions without desired input

Desired state:
- Natural interaction that adapts to how users communicate
- Clear visibility into tool execution throughout workflow
- Efficient autonomous operation as default
- Graceful collaboration when users signal they want it

## Design Principles

1. **Non-Intrusive by Default:** Autonomous mode is the baseline. Agents make expert decisions.
2. **Intent-Driven Adaptation:** User language signals desired interaction level.
3. **Transparent Execution:** All tool calls and results visible in console output.
4. **Natural Checkpoints:** Collaboration happens at decision points that naturally warrant input (venue selection, budget allocation, date selection).
5. **Clear Rationale:** Every autonomous decision includes explanation so users understand agent reasoning.

## Architecture

### Component 1: Enhanced Console Output

**Location:** `src/spec_to_agents/console.py`

**Current Implementation:**
```python
def format_tool_call(content: FunctionCallContent) -> str:
    args_preview = str(content.arguments)[:100]  # Truncates at 100 chars
    if len(str(content.arguments)) > 100:
        args_preview += "..."
    return f"🔧 Tool Call: {content.name}({args_preview})"

def format_tool_result(content: FunctionResultContent) -> str:
    result_preview = str(content.result)[:150]  # Truncates at 150 chars
    if len(str(content.result)) > 150:
        result_preview += "..."
    return f"   ✓ Result: {result_preview}"
```

**Problems:**
- Arbitrary truncation loses important context
- No executor identification (which agent called the tool?)
- No call_id linking results back to calls
- Doesn't handle structured data (dicts/lists) well
- No deduplication for streaming contexts

**New Implementation:**

Based on microsoft/agent-framework sample pattern from `azure_chat_agents_tool_calls_with_feedback.py`:

```python
def format_tool_call(content: FunctionCallContent, executor_id: str) -> str:
    """
    Format tool call with proper JSON serialization and executor context.

    Parameters
    ----------
    content : FunctionCallContent
        Function call to format
    executor_id : str
        ID of the executor making the call (e.g., "venue", "budget")

    Returns
    -------
    str
        Formatted tool call: "venue [tool-call] web_search({...})"
    """
    args = content.arguments
    if isinstance(args, dict):
        args_str = json.dumps(args, ensure_ascii=False)
    else:
        args_str = (args or "").strip()

    return f"{executor_id} [tool-call] {content.name}({args_str})"

def format_tool_result(content: FunctionResultContent, executor_id: str) -> str:
    """
    Format tool result with call_id linkage and proper serialization.

    Parameters
    ----------
    content : FunctionResultContent
        Function result to format
    executor_id : str
        ID of the executor that made the call

    Returns
    -------
    str
        Formatted tool result: "venue [tool-result] abc123: {...}"
    """
    result = content.result
    if not isinstance(result, str):
        result = json.dumps(result, ensure_ascii=False)

    return f"{executor_id} [tool-result] {content.call_id}: {result}"
```

**Integration into console.py main loop:**

Update the event processing section (lines 176-186) to:

```python
# Track printed tool calls/results to avoid duplication in streaming
printed_tool_calls: set[str] = set()
printed_tool_results: set[str] = set()
last_executor: str | None = None

for event in events:
    if hasattr(event, "agent_run_response_update"):
        update: AgentRunResponseUpdate = event.agent_run_response_update
        executor_id = getattr(event, "executor_id", "workflow")

        # Extract tool calls and results
        function_calls = [c for c in update.contents if isinstance(c, FunctionCallContent)]
        function_results = [c for c in update.contents if isinstance(c, FunctionResultContent)]

        # Show executor transition
        if executor_id != last_executor:
            if last_executor is not None:
                print()
            print(f"{executor_id}:", end=" ", flush=True)
            last_executor = executor_id

        # Print new tool calls
        for call in function_calls:
            if call.call_id in printed_tool_calls:
                continue
            printed_tool_calls.add(call.call_id)
            print(f"\n{format_tool_call(call, executor_id)}", flush=True)
            print(f"{executor_id}:", end=" ", flush=True)

        # Print new tool results
        for result in function_results:
            if result.call_id in printed_tool_results:
                continue
            printed_tool_results.add(result.call_id)
            print(f"\n{format_tool_result(result, executor_id)}", flush=True)
            print(f"{executor_id}:", end=" ", flush=True)
```

**Example Output:**
```
venue: Let me search for suitable corporate event venues in Seattle...
venue [tool-call] web_search({"query": "corporate event venues Seattle 50 people capacity"})
venue [tool-result] abc123: Found 15 venues. Top results: The Foundry (60 capacity, $3k)...
venue: Based on my research, I recommend The Foundry because it offers excellent AV equipment and is centrally located.

budget [tool-call] code_interpreter({"code": "budget=5000\nvenue=3000\nremaining=budget-venue..."})
budget [tool-result] def456: {'venue': 3000, 'catering': 1200, 'logistics': 500, 'contingency': 300}
budget: Here's the budget allocation. Venue takes 60% which is standard for corporate events...
```

**Benefits:**
- Full visibility into tool execution
- Clear attribution (which agent used which tool)
- Proper JSON formatting for structured data
- Call/result linkage via call_id
- No arbitrary truncation

---

### Component 2: Intent Detection System

**Concept:**

Agents analyze the initial user request to detect **intent signals** that indicate desired interaction level. This happens at the start of each specialist's work, not as a separate pre-processing step.

**Intent Signal Categories:**

| Mode | User Language Signals | Agent Behavior |
|------|----------------------|----------------|
| **Autonomous** | Prescriptive constraints: "budget $5k", "50 people", "December 15th"<br>Action-oriented: "Plan a corporate party with..." | Make expert decisions, explain rationale, only ask if critical info missing |
| **Collaborative** | Exploratory: "help me plan", "what do you recommend"<br>Guidance-seeking: "what should I consider", "suggestions for..." | Present 2-3 options at natural decision points, ask for preference |
| **Interactive** | Explicit control: "show me options", "I want to choose", "let me decide" | Present all viable options, wait for user selection |

**Default:** When intent is ambiguous, default to **Autonomous Mode** (non-intrusive).

**Intent Examples:**

**Autonomous:**
- "Plan a corporate holiday party for 50 people in Seattle on December 15th, budget $5000"
- "Need venue for 30-person team lunch, downtown Seattle, budget $1500"

**Collaborative:**
- "Help me plan a corporate holiday party, around 50 people, what venues would work well?"
- "Looking for suggestions on catering for a formal dinner event"

**Interactive:**
- "Show me venue options for my event and let me choose which one"
- "I want to see all the menu options before deciding"

**Critical Rules:**
1. If 80%+ information is present → Autonomous Mode
2. Never ask for minor preferences (appetizer choices, decoration colors)
3. Natural checkpoints for collaboration: venue selection, budget allocation, date selection, dietary restrictions (specialized events only)
4. ONE question maximum per specialist per interaction

---

### Component 3: Agent Prompt Updates

All specialist prompts get the same structure:

1. **Role & Core Responsibilities** (existing, keep concise)
2. **Intent Detection & Interaction Mode** (NEW - insert before behavioral guidelines)
3. **Domain Guidelines** (existing content, streamlined)
4. **Available Tools** (existing, keep)
5. **Structured Output Format** (existing, add mode examples)

**Template for Intent Detection Section:**

```markdown
## Intent Detection & Interaction Mode

Analyze the user's request to determine the appropriate interaction style:

**Autonomous Mode (DEFAULT)**:
- User provided specific constraints (budget, location, dates, attendee count)
- Language is prescriptive: "Plan a [specific event] with [constraints]"
- **Behavior:** Make expert decisions based on available context, explain rationale clearly, proceed to next agent
- **Only ask if:** Critical information is completely missing and cannot be reasonably inferred

**Collaborative Mode**:
- User language is exploratory: "help", "recommend", "suggest", "what should", "looking for ideas"
- User provides partial context and seeks guidance on remaining aspects
- **Behavior:** Present 2-3 options at natural decision points, explain tradeoffs, ask for preference
- **Ask when:** Multiple good options exist and user language signals they want involvement

**Interactive Mode**:
- User explicitly requests options: "show me options", "I want to choose", "let me decide"
- **Behavior:** Present all viable options with full details, wait for user selection before proceeding
- **Ask when:** User has explicitly indicated they want to make the decision

**Default Rule:** When intent is ambiguous or 80%+ of information is present, use Autonomous Mode.
```

---

#### Venue Specialist Specific Updates

**New Interaction Guidelines (replaces verbose lines 44-91):**

```markdown
## Interaction Guidelines by Mode

**Autonomous Mode:**
- Research and select the best venue matching user requirements
- Provide clear rationale: "I recommend [Venue] because [reasoning]"
- Proceed directly to next agent with venue selection
- Only ask if location or attendee count is completely missing

**Collaborative Mode:**
- Present 2-3 venue options with pros/cons comparison
- Set `user_input_needed=true` with prompt: "I found these venues: [brief comparison]. Which appeals to you?"
- After user selection, acknowledge and proceed to budget agent

**Interactive Mode:**
- Present all viable venues (3-5) with full details
- Set `user_input_needed=true` with comprehensive options
- Wait for explicit user selection

**Examples:**

Autonomous:
Request: "Plan corporate party for 50 people, Seattle, budget $5k"
Response: Research venues → Select best match → Explain: "I recommend The Foundry ($3k, 60 capacity, excellent AV) because it's centrally located and within budget" → Route to budget

Collaborative:
Request: "Help me find a venue for a corporate party, around 50 people in Seattle"
Response: Research venues → Present top 3 with tradeoffs → Ask: "I found The Foundry ($3k, downtown, modern), Pioneer Square Hall ($2.5k, historic, charm), or Fremont Studios ($3.5k, creative space). Which style appeals to you?"

Interactive:
Request: "Show me venue options for 50 people in Seattle, I want to choose"
Response: Research venues → Present 4-5 options with full details → Ask: "Here are the top venues with capacity, pricing, and amenities. Which would you like?"
```

---

#### Budget Analyst Specific Updates

**New Interaction Guidelines:**

```markdown
## Interaction Guidelines by Mode

**Autonomous Mode:**
- Allocate budget across categories using industry standards
- Explain allocation: "Venue $3k (60%) is standard for corporate events of this size..."
- Proceed directly to catering agent
- Only ask if total budget is completely unspecified AND cannot be inferred from event type

**Collaborative Mode:**
- Present allocation with alternative: "Standard allocation is X, but we could shift Y to Z if [tradeoff]"
- Ask: "Does this budget allocation align with your priorities, or would you like adjustments?"

**Interactive Mode:**
- Present 2-3 allocation strategies with clear tradeoffs
- Wait for user to choose or provide specific allocation preferences

**Budget Inference Rules:**
- Corporate events: $50-100 per person
- Casual events: $20-40 per person
- Formal events: $100-200 per person
- If user says "reasonable budget" → Use midpoint of range

**Examples:**

Autonomous:
Request: "Corporate party, 50 people, $5k budget" → Allocate: Venue 60%, Catering 24%, Logistics 10%, Contingency 6% → Explain rationale → Route to catering

Collaborative:
Request: "Help plan party for 50 people, not sure about budget" → Infer $50/person = $2500 total → Present: "For 50 people, $2500 is reasonable. I suggest Venue $1200 (48%), Catering $900 (36%), Logistics $250 (10%), Contingency $150 (6%). Does this work?"
```

---

#### Catering Coordinator Specific Updates

**New Interaction Guidelines:**

```markdown
## Interaction Guidelines by Mode

**Autonomous Mode:**
- Design appropriate menu with standard dietary accommodations (vegetarian/vegan for groups >20)
- Explain choices: "Buffet style at $30/person allows flexibility and accommodates dietary needs..."
- Proceed directly to logistics agent
- Only ask about dietary restrictions for specialized events (medical conference, religious event)

**Collaborative Mode:**
- Ask about service style preference if event formality is ambiguous
- "Would you prefer buffet ($30/person, flexible, casual) or plated ($40/person, formal, structured)?"
- OR ask about cuisine preference if event type doesn't indicate: "What cuisine style appeals to you?"

**Interactive Mode:**
- Present multiple menu packages with pricing tiers
- Show different service style options
- Wait for user selection or modification requests

**Default Behavior:**
- ALWAYS include vegetarian/vegan options for groups >20 (don't ask)
- Use event type to infer service style (corporate lunch = buffet, formal dinner = plated)
- Calculate per-person cost from budget allocation

**Examples:**

Autonomous:
Request: "Corporate party, 50 people, $1200 catering budget" → Calculate $24/person → Design buffet menu with veg options → Explain: "Buffet style with 3 entrees (1 vegetarian), sides, dessert. Allows flexible timing and dietary variety" → Route to logistics

Collaborative:
Request: "Help with catering for formal dinner, 50 people" → Present: "For a formal dinner, would you prefer plated service ($40/person, elegant) or upscale buffet ($32/person, variety)?"
```

---

#### Logistics Manager Specific Updates

**New Interaction Guidelines:**

```markdown
## Interaction Guidelines by Mode

**Autonomous Mode:**
- Create timeline using industry standards (corporate dinner: 6-10pm, lunch: 11am-2pm)
- Check weather forecast if date provided
- Create calendar entries automatically
- Explain logistics: "Setup at 5pm allows 1hr buffer before 6pm doors..."
- Only ask for date if completely unspecified AND cannot be inferred

**Collaborative Mode:**
- Ask for date preference: "When would you like to hold this event? I can check weather and availability."
- OR ask about timing if ambiguous: "Would you prefer a morning, afternoon, or evening event?"

**Interactive Mode:**
- Present suggested timeline with alternatives
- Show weather forecast with date options
- Ask for approval or modifications

**Special Case:**
Logistics is the ONE specialist where asking for a date is acceptable if truly missing. A date is critical for weather checks, calendar management, and vendor coordination.

**Examples:**

Autonomous:
Request: "Corporate party December 15th, 6-10pm" → Create timeline → Check weather → Create calendar event → Explain: "Setup 5pm, doors 6pm, dinner 7pm, activities 8:30pm, end 10pm. Weather forecast: 45°F, clear." → Route to coordinator (workflow complete)

Collaborative:
Request: "Corporate party sometime in December" → Ask: "What date in December works best? I'll check weather forecasts and availability."
```

---

#### Event Coordinator Updates

Coordinator already handles routing well. Add awareness note:

```markdown
## Intent Awareness

Specialists will adapt their interaction style based on user intent signals in the request. Trust specialist judgment on when to request user input:

- `user_input_needed=true` signals specialist needs user decision
- Present `user_prompt` to user via DevUI
- Route user response back to requesting specialist
- Specialist proceeds with updated context

No changes needed to coordinator routing logic. The intent detection happens within each specialist.
```

---

## Implementation Impact

### Files Modified

1. **`src/spec_to_agents/console.py`**
   - Update `format_tool_call()` function
   - Update `format_tool_result()` function
   - Update main event loop to track printed calls/results
   - Add executor_id display logic

2. **`src/spec_to_agents/prompts/venue_specialist.py`**
   - Add Intent Detection section
   - Simplify/replace interaction guidelines with mode-based approach
   - Add mode-specific examples

3. **`src/spec_to_agents/prompts/budget_analyst.py`**
   - Add Intent Detection section
   - Add budget inference rules
   - Replace defensive guidelines with mode-based approach
   - Add mode-specific examples

4. **`src/spec_to_agents/prompts/catering_coordinator.py`**
   - Add Intent Detection section
   - Clarify default accommodations (no need to ask)
   - Add mode-specific examples

5. **`src/spec_to_agents/prompts/logistics_manager.py`**
   - Add Intent Detection section
   - Clarify date is acceptable question point
   - Add mode-specific examples

6. **`src/spec_to_agents/prompts/event_coordinator.py`**
   - Add brief intent awareness note
   - No routing logic changes

### Files NOT Modified

- **`src/spec_to_agents/workflow/event_planning_workflow.py`** - No changes, routing stays the same
- **`src/spec_to_agents/workflow/executors.py`** - No changes, coordinator logic stays the same
- **`src/spec_to_agents/workflow/messages.py`** - No changes, SpecialistOutput format stays the same
- Agent factory functions - No changes to signatures or tools

### Testing Strategy

**Unit Tests:**
- Console formatting functions with various input types
- Verify JSON serialization for structured data
- Verify call_id preservation in results

**Integration Tests:**
- Test Autonomous Mode flow (full details provided)
- Test Collaborative Mode flow (exploratory language)
- Test Interactive Mode flow (explicit choice request)
- Test mode transitions (user changes mind mid-workflow)

**Manual Testing via DevUI:**
1. Autonomous: "Plan corporate party Dec 15, 50 people, Seattle, $5k budget"
   - Expect: Minimal questions, autonomous decisions, clear rationale
2. Collaborative: "Help me plan a corporate party, around 50 people"
   - Expect: Venue options presented, budget guidance, natural checkpoints
3. Interactive: "Show me venue options for 50 people, I want to choose"
   - Expect: Multiple options, wait for selection

**Console Output Verification:**
- Verify tool calls display with full context
- Verify results link to calls via call_id
- Verify executor_id shows which agent is acting
- Verify no duplication in streaming scenarios

---

## Success Metrics

1. **User Experience:**
   - Users with full details experience <1 question per workflow (autonomous efficiency)
   - Users with exploratory language get natural guidance (collaborative feel)
   - Users always understand what agents are doing (transparent execution)

2. **Code Quality:**
   - No changes to workflow architecture or routing logic
   - Prompt token count stays within reasonable bounds (avoid excessive verbosity)
   - Clear separation between mode logic and domain logic

3. **Maintainability:**
   - Intent detection pattern is consistent across all specialists
   - Examples clearly demonstrate mode behaviors
   - Easy to add new specialists following the pattern

---

## Rollout Plan

**Phase 1: Console Output Enhancement**
- Update console.py formatting functions
- Test with existing prompts to verify display quality
- Commit: "feat: enhance console tool call/result display"

**Phase 2: Prompt Updates (Agent by Agent)**
- Update venue_specialist.py with intent detection
- Test autonomous and collaborative flows
- Commit: "feat: add intent-based interaction to venue specialist"
- Repeat for budget, catering, logistics (separate commits)

**Phase 3: Coordinator Update**
- Add intent awareness note to coordinator
- Commit: "feat: add intent awareness to event coordinator"

**Phase 4: Integration Testing**
- Test full workflows in all three modes
- Verify console output quality
- Fix any issues discovered
- Commit: "fix: address intent detection edge cases"

**Phase 5: Documentation**
- Update CLAUDE.md if needed
- Update workflow-skeleton.md to mention intent detection
- Commit: "docs: document intent-based interaction system"

---

## Future Enhancements

**Possible Extensions (Out of Scope for This Design):**

1. **Explicit Preference Setting:**
   - Allow users to set interaction mode at workflow start: "Interaction preference: Autonomous/Collaborative/Interactive"
   - Pass as context to all agents
   - More predictable than intent detection, but less natural

2. **Mid-Workflow Corrections:**
   - Support interruptions: "Actually, show me all venue options"
   - Requires response_handler for out-of-turn user input
   - More complex to implement

3. **Persistent User Preferences:**
   - Learn user's preferred interaction style across sessions
   - Store in user profile
   - Apply as default for future workflows

4. **Rich Console Output:**
   - Markdown formatting for structured data
   - Color coding for different agent actions
   - Progress indicators for long-running tools

---

## Summary

This design creates a **collaborative yet non-intrusive** event planning workflow by:

1. **Enhanced Tool Visibility:** Console output follows agent-framework best practices with full tool call/result display, executor identification, and proper JSON formatting

2. **Intent-Based Interaction:** Agents detect user intent signals and adapt between Autonomous (default), Collaborative, and Interactive modes

3. **Non-Intrusive Defaults:** 80% information present = autonomous mode. Agents make expert decisions with clear rationale. Questions only when truly needed.

4. **Natural Checkpoints:** Collaboration happens at decision points that naturally warrant input (venue selection, budget allocation, date selection)

5. **Consistent Pattern:** All specialists follow the same intent detection structure, making the system predictable and maintainable

The result is a workflow that feels smart and respectful: it handles planning efficiently when users provide details, and collaborates naturally when users signal they want guidance.
