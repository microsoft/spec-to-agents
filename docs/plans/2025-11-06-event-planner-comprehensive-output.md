# Event Planner Comprehensive Output Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform event planning workflow to produce comprehensive event itineraries with calendar integration, removing structured output from specialist agents while keeping coordinator-based routing.

**Architecture:** Remove SpecialistOutput from all specialist agents (venue, budget, catering, logistics), keeping only in coordinator for routing decisions. Update coordinator synthesis to create full event itinerary with calendar event creation. Specialists return natural text responses; coordinator parses and routes based on SpecialistOutput.

**Tech Stack:** Microsoft Agent Framework, Azure AI Agent Client, Pydantic for coordinator routing, Python 3.11+

---

## Current System Analysis

### What Works Well
- **Service-managed threads** automatically handle conversation history
- **Star topology** provides clear routing through coordinator hub
- **Tool content conversion** prevents cross-thread contamination
- **Human-in-the-loop** framework integration works smoothly
- **Calendar tools** are already implemented and available

### Key Issues
1. **All specialists use SpecialistOutput** but should only use natural text
2. **Final synthesis** produces text plan but doesn't create calendar event
3. **Incomplete itinerary** lacks detailed timeline and scheduling
4. **Prompts reference structured output** that shouldn't exist for specialists

### Design Decision: Coordinator-Only Structured Output

**Pattern:**
- Specialists → Natural text responses with domain expertise
- Coordinator → Reads specialist text, makes routing decision via SpecialistOutput
- Only coordinator agent uses `response_format=SpecialistOutput`

**Benefits:**
- Specialists freed from routing logic complexity
- Natural conversation flow for domain experts
- Coordinator maintains full routing control
- Simpler specialist prompts focused on domain work

---

## Task 1: Remove StructuredOutput from Venue Specialist

**Files:**
- Modify: `src/spec_to_agents/agents/venue_specialist.py:43-49`
- Modify: `src/spec_to_agents/prompts/venue_specialist.py:116-148`
- Test: `tests/agents/test_venue_specialist.py`

**Step 1: Update venue specialist agent creation**

In `src/spec_to_agents/agents/venue_specialist.py`, remove `response_format` parameter:

```python
return client.create_agent(
    name="VenueSpecialist",
    instructions=venue_specialist.SYSTEM_PROMPT,
    tools=tools,
    # Remove: response_format=SpecialistOutput,
    store=True,
)
```

**Step 2: Update venue specialist prompt**

Remove the "Structured Output Format" section (lines 116-148) and replace with natural output guidance:

```python
## Output Format

Your response should be natural, conversational text that:
- Clearly states your venue recommendations
- Provides specific details (capacity, pricing, amenities, location)
- Explains your reasoning based on the requirements
- Indicates if you need user input with a clear question
- Signals readiness for next step (budget planning)

**Example Autonomous Response:**
"I recommend The Foundry in downtown Seattle ($3,000 rental). It has 60-person capacity (comfortable for 50),
excellent AV equipment, on-site catering facilities, and accessible parking. The industrial-modern aesthetic
works well for corporate events. Ready for budget planning."

**Example Requesting User Input:**
"I found three excellent venues: The Foundry (downtown, $3k, modern), Pioneer Square Hall (historic, $2.5k,
charming), and Fremont Studios (creative space, $3.5k, industrial). Which style appeals to you?"
```

**Step 3: Write failing test**

Create test that verifies agent returns text (not SpecialistOutput):

```python
def test_venue_specialist_returns_text_not_structured_output():
    """Venue specialist should return natural text, not SpecialistOutput."""
    # Setup
    client = create_test_client()
    agent = create_agent(client, mcp_tool=None)

    # Execute
    result = agent.run(messages=[ChatMessage(Role.USER, text="Find venue for 50 people in Seattle")])

    # Assert: result.value should be None (no structured output)
    # Assert: result.text should contain natural recommendation
    assert result.value is None
    assert result.text is not None
    assert "venue" in result.text.lower()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/agents/test_venue_specialist.py::test_venue_specialist_returns_text_not_structured_output -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/spec_to_agents/agents/venue_specialist.py src/spec_to_agents/prompts/venue_specialist.py tests/agents/test_venue_specialist.py
git commit -m "refactor: remove SpecialistOutput from venue specialist

Venue specialist now returns natural text responses instead of
structured output. Coordinator will parse text and make routing
decisions independently.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Remove StructuredOutput from Budget Analyst

**Files:**
- Modify: `src/spec_to_agents/agents/budget_analyst.py:50-56`
- Modify: `src/spec_to_agents/prompts/budget_analyst.py:132-153`
- Test: `tests/agents/test_budget_analyst.py`

**Step 1: Update budget analyst agent creation**

In `src/spec_to_agents/agents/budget_analyst.py`, remove `response_format` parameter:

```python
return client.create_agent(
    name="BudgetAnalyst",
    instructions=budget_analyst.SYSTEM_PROMPT,
    tools=tools,
    # Remove: response_format=SpecialistOutput,
    store=True,
)
```

**Step 2: Update budget analyst prompt**

Remove "Structured Output Format" section (lines 132-153) and replace:

```python
## Output Format

Your response should be natural text that:
- Presents clear budget allocation across categories
- Shows calculations and percentages
- Explains rationale for allocation decisions
- Indicates if user approval is needed
- Signals readiness for next step (catering planning)

**Example Response:**
"Budget allocation for $5,000 event:
- Venue: $3,000 (60%) - standard for corporate events this size
- Catering: $1,200 (24%) - $24/person for 50 attendees
- Logistics: $500 (10%) - coordination, equipment, weather planning
- Contingency: $300 (6%) - buffer for unexpected costs

This follows industry standards for corporate events. Ready for catering coordination."
```

**Step 3: Write failing test**

```python
def test_budget_analyst_returns_text_not_structured_output():
    """Budget analyst should return natural text with calculations."""
    client = create_test_client()
    agent = create_agent(client, mcp_tool=None)

    result = agent.run(messages=[
        ChatMessage(Role.USER, text="Allocate budget for 50-person corporate event, $5k total")
    ])

    assert result.value is None
    assert result.text is not None
    assert "budget" in result.text.lower() or "allocation" in result.text.lower()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/agents/test_budget_analyst.py::test_budget_analyst_returns_text_not_structured_output -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/spec_to_agents/agents/budget_analyst.py src/spec_to_agents/prompts/budget_analyst.py tests/agents/test_budget_analyst.py
git commit -m "refactor: remove SpecialistOutput from budget analyst

Budget analyst now returns natural text with calculations instead
of structured output. Enables clearer financial explanations.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Remove StructuredOutput from Catering Coordinator

**Files:**
- Modify: `src/spec_to_agents/agents/catering_coordinator.py:43-49`
- Modify: `src/spec_to_agents/prompts/catering_coordinator.py:130-151`
- Test: `tests/agents/test_catering_coordinator.py`

**Step 1: Update catering coordinator agent creation**

In `src/spec_to_agents/agents/catering_coordinator.py`, remove `response_format`:

```python
return client.create_agent(
    name="CateringCoordinator",
    instructions=catering_coordinator.SYSTEM_PROMPT,
    tools=tools,
    # Remove: response_format=SpecialistOutput,
    store=True,
)
```

**Step 2: Update catering coordinator prompt**

Remove "Structured Output Format" section and replace:

```python
## Output Format

Your response should be natural text that:
- Describes the menu and service style
- Itemizes costs and shows budget fit
- Lists dietary accommodations included
- Indicates if clarification is needed
- Signals readiness for logistics planning

**Example Response:**
"Catering plan for 50 people, $1,200 budget ($24/person):

**Service:** Buffet style for flexibility
**Menu:**
- Appetizers: Mixed greens salad, artisan breads ($300)
- Entrees: Herb chicken, vegetarian pasta primavera, roasted vegetables ($600)
- Desserts: Assorted mini pastries ($200)
- Beverages: Coffee, tea, soft drinks, water ($100)

**Dietary:** Includes vegetarian, can accommodate gluten-free with advance notice

Within budget, ready for logistics coordination."
```

**Step 3: Write failing test**

```python
def test_catering_coordinator_returns_text_not_structured_output():
    """Catering coordinator should return natural text menu descriptions."""
    client = create_test_client()
    agent = create_agent(client, mcp_tool=None)

    result = agent.run(messages=[
        ChatMessage(Role.USER, text="Plan catering for 50 people, $1200 budget")
    ])

    assert result.value is None
    assert result.text is not None
    assert "catering" in result.text.lower() or "menu" in result.text.lower()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/agents/test_catering_coordinator.py::test_catering_coordinator_returns_text_not_structured_output -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/spec_to_agents/agents/catering_coordinator.py src/spec_to_agents/prompts/catering_coordinator.py tests/agents/test_catering_coordinator.py
git commit -m "refactor: remove SpecialistOutput from catering coordinator

Catering coordinator now returns natural menu descriptions instead
of structured output. Provides clearer food and service details.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Remove StructuredOutput from Logistics Manager

**Files:**
- Modify: `src/spec_to_agents/agents/logistics_manager.py:53-59`
- Modify: `src/spec_to_agents/prompts/logistics_manager.py:149-170`
- Test: `tests/agents/test_logistics_manager.py`

**Step 1: Update logistics manager agent creation**

In `src/spec_to_agents/agents/logistics_manager.py`, remove `response_format`:

```python
return client.create_agent(
    name="LogisticsManager",
    instructions=logistics_manager.SYSTEM_PROMPT,
    tools=tools,
    # Remove: response_format=SpecialistOutput,
    store=True,
)
```

**Step 2: Update logistics manager prompt**

Remove "Structured Output Format" section and replace with comprehensive output guidance:

```python
## Output Format

Your response should be natural text that:
- Provides detailed event timeline with specific times
- Lists weather forecast results
- Confirms calendar event creation with event details
- Identifies logistics needs (staff, equipment, setup)
- Signals workflow completion

**Example Response:**
"Logistics plan for December 15, 2025:

**Timeline:**
- 5:00 PM: Venue setup begins (tables, AV equipment, decorations)
- 6:00 PM: Catering arrives, food station setup
- 6:30 PM: Doors open, reception begins
- 7:00 PM: Dinner service starts
- 8:30 PM: Program/activities
- 10:00 PM: Event ends
- 10:30 PM: Venue clear, cleanup complete

**Weather Forecast (Dec 15):** 45°F, partly cloudy, 10% chance precipitation. Indoor venue recommended.

**Calendar Event Created:** 'Corporate Holiday Party' on 2025-12-15 from 18:00-22:00 at The Foundry, Seattle.
Includes venue address, catering details, and setup timeline.

**Logistics Needs:**
- AV technician for setup (included in venue)
- 2 catering staff (included in catering package)
- 1 event coordinator for day-of management

All specialists have completed their work. Ready for final synthesis."
```

**Step 3: Write failing test**

```python
def test_logistics_manager_returns_text_not_structured_output():
    """Logistics manager should return natural text with timeline details."""
    client = create_test_client()
    agent = create_agent(client, mcp_tool=None)

    result = agent.run(messages=[
        ChatMessage(Role.USER, text="Create logistics plan for Dec 15, 2025, corporate party")
    ])

    assert result.value is None
    assert result.text is not None
    assert "timeline" in result.text.lower() or "logistics" in result.text.lower()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/agents/test_logistics_manager.py::test_logistics_manager_returns_text_not_structured_output -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/spec_to_agents/agents/logistics_manager.py src/spec_to_agents/prompts/logistics_manager.py tests/agents/test_logistics_manager.py
git commit -m "refactor: remove SpecialistOutput from logistics manager

Logistics manager now returns comprehensive natural text with timeline,
weather, and calendar details. Signals workflow completion clearly.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Update Coordinator Routing Logic

**Files:**
- Modify: `src/spec_to_agents/workflow/executors.py:153-203`
- Test: `tests/workflow/test_executors.py`

**Step 1: Create new coordinator routing method**

Add new method to parse specialist text and determine routing:

```python
def _analyze_specialist_response_for_routing(
    self, specialist_text: str, specialist_id: str
) -> SpecialistOutput:
    """
    Analyze specialist text response to determine routing decision.

    This method uses the coordinator agent (with SpecialistOutput format)
    to read specialist responses and make routing decisions.

    Parameters
    ----------
    specialist_text : str
        Natural text response from specialist agent
    specialist_id : str
        ID of the specialist that produced the response

    Returns
    -------
    SpecialistOutput
        Structured routing decision with next_agent, user_input_needed, etc.
    """
    routing_prompt = f"""You are analyzing the response from the {specialist_id} specialist.

Specialist response:
{specialist_text}

Based on this response, determine the next routing action:
1. If the specialist is asking the user a question or presenting options for selection, set user_input_needed=true
2. If the specialist has completed their work and signals readiness for the next step, set next_agent to the appropriate specialist:
   - After venue → "budget"
   - After budget → "catering"
   - After catering → "logistics"
   - After logistics → null (workflow complete)
3. If the specialist indicates workflow is complete or all planning is done, set next_agent=null

Provide a brief summary of what the specialist accomplished."""

    routing_result = self._coordinator_agent.run(messages=[
        ChatMessage(Role.USER, text=routing_prompt)
    ])

    # Parse structured output
    if routing_result.value and isinstance(routing_result.value, SpecialistOutput):
        return routing_result.value

    # Fallback if parsing fails
    return SpecialistOutput(
        summary=f"Routing analysis failed for {specialist_id}",
        next_agent=None,
        user_input_needed=False,
    )
```

**Step 2: Update on_specialist_response handler**

Modify the handler to use new routing method:

```python
@handler
async def on_specialist_response(
    self,
    response: AgentExecutorResponse,
    ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
) -> None:
    """
    Handle responses from specialist agents.

    Specialists now return natural text. Coordinator analyzes the text
    to determine routing decisions using SpecialistOutput format.
    """
    # Extract conversation and specialist text
    conversation = list(response.full_conversation or response.agent_run_response.messages)
    specialist_text = response.agent_run_response.text or ""
    specialist_id = response.executor_id

    # Analyze specialist response for routing decision
    specialist_output = self._analyze_specialist_response_for_routing(
        specialist_text, specialist_id
    )

    # Route based on analysis
    if specialist_output.user_input_needed:
        await ctx.request_info(
            request_data=HumanFeedbackRequest(
                prompt=specialist_output.user_prompt or "Please provide input",
                context={},
                request_type="clarification",
                requesting_agent="coordinator",
                conversation=conversation,
            ),
            response_type=str,
        )
    elif specialist_output.next_agent:
        target_id = specialist_output.next_agent
        specialist_request = SpecialistRequest(
            specialist_id=target_id,
            message="Please analyze the event planning requirements and provide your recommendations.",
            conversation=conversation,
        )
        await ctx.send_message(specialist_request, target_id=target_id)
    else:
        # Workflow complete
        await self._synthesize_plan(ctx, conversation)
```

**Step 3: Write failing test**

```python
def test_coordinator_routes_based_on_specialist_text():
    """Coordinator should analyze specialist text and route appropriately."""
    # Setup
    coordinator_agent = create_coordinator_agent()
    executor = EventPlanningCoordinator(coordinator_agent)

    # Create mock specialist response with text (not SpecialistOutput)
    specialist_response = AgentExecutorResponse(
        executor_id="venue",
        agent_run_response=AgentRunResponse(
            text="I recommend The Foundry. Ready for budget planning.",
            messages=[],
        ),
        full_conversation=[],
    )

    # Execute
    routing_decision = executor._analyze_specialist_response_for_routing(
        specialist_response.agent_run_response.text,
        "venue"
    )

    # Assert: should route to budget
    assert routing_decision.next_agent == "budget"
    assert not routing_decision.user_input_needed
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/workflow/test_executors.py::test_coordinator_routes_based_on_specialist_text -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/spec_to_agents/workflow/executors.py tests/workflow/test_executors.py
git commit -m "feat: coordinator analyzes specialist text for routing

Coordinator now reads natural text from specialists and uses its own
SpecialistOutput capability to make routing decisions. Separates domain
expertise (specialists) from workflow orchestration (coordinator).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Enhance Coordinator Synthesis for Full Itinerary

**Files:**
- Modify: `src/spec_to_agents/workflow/executors.py:272-311`
- Modify: `src/spec_to_agents/prompts/event_coordinator.py:62-76`
- Test: `tests/workflow/test_synthesis.py`

**Step 1: Update synthesis guidelines in prompt**

In `src/spec_to_agents/prompts/event_coordinator.py`, update synthesis section:

```python
## Synthesis Guidelines

When synthesizing final event plan (all specialists complete):

1. Review all specialist outputs from conversation history
2. Extract key details:
   - Venue name, location, capacity, cost
   - Budget allocation across categories
   - Menu, service style, dietary accommodations
   - Event date, timeline, weather forecast
   - Calendar event details

3. Create comprehensive event itinerary with:
   **Executive Summary** (2-3 sentences): Event overview with key decisions

   **Venue Details:**
   - Name and location with full address
   - Capacity and room configuration
   - Amenities and accessibility features
   - Rental cost and what's included

   **Budget Breakdown:**
   - Total budget with allocation percentages
   - Category-by-category costs (venue, catering, logistics, contingency)
   - Cost per person calculation
   - Payment schedule if applicable

   **Catering Plan:**
   - Service style and timing
   - Complete menu with appetizers, entrees, sides, desserts
   - Beverage program (alcoholic and non-alcoholic)
   - Dietary accommodations
   - Total catering cost

   **Event Timeline:**
   - Setup time and requirements
   - Guest arrival and registration
   - Event activities with specific times
   - Meal service schedule
   - Program/entertainment timing
   - Event conclusion and cleanup

   **Logistics & Coordination:**
   - Weather forecast for event date
   - Staffing requirements (catering, AV, event coordinator)
   - Equipment needs and who provides
   - Parking and transportation notes
   - Backup plans for weather/issues

   **Calendar Confirmation:**
   - Confirm logistics manager created calendar event
   - Repeat event name, date, time, location
   - Note that event is now scheduled

   **Next Steps:**
   - Action items for client (deposits, confirmations, final headcount)
   - Timeline for next decisions
   - Key contact information

4. Format with markdown: Use headings (##), bullet points, bold for emphasis
5. Highlight integration points where specialist recommendations align
6. Note any tradeoffs or key decisions made during planning
```

**Step 2: Update _synthesize_plan method**

Enhance synthesis method to create richer output:

```python
async def _synthesize_plan(
    self,
    ctx: WorkflowContext[AgentExecutorRequest | SpecialistRequest | HumanFeedbackRequest, str],
    conversation: list[ChatMessage],
) -> None:
    """
    Synthesize comprehensive event itinerary from all specialist recommendations.

    Creates detailed event plan integrating venue, budget, catering, and logistics.
    Includes full timeline, costs, menu, weather, and confirms calendar event creation.

    Parameters
    ----------
    ctx : WorkflowContext
        Workflow context for yielding final output
    conversation : list[ChatMessage]
        Complete conversation history including all specialist interactions
    """
    # Convert tool content to text for coordinator's thread
    clean_conversation = convert_tool_content_to_text(conversation)

    # Add detailed synthesis instruction
    synthesis_instruction = ChatMessage(
        Role.USER,
        text=(
            "All specialists have completed their work. Please synthesize a COMPREHENSIVE "
            "event itinerary that integrates ALL specialist recommendations.\n\n"
            "Your synthesis must include:\n"
            "1. Executive Summary (2-3 sentences)\n"
            "2. Venue Details (name, location, capacity, cost, amenities)\n"
            "3. Budget Breakdown (total, allocations, per-person cost)\n"
            "4. Catering Plan (service style, complete menu, dietary options, cost)\n"
            "5. Event Timeline (specific times for setup, arrival, activities, meals, conclusion)\n"
            "6. Logistics & Coordination (weather forecast, staffing, equipment, parking)\n"
            "7. Calendar Confirmation (verify event was added to calendar with details)\n"
            "8. Next Steps (action items for client)\n\n"
            "Provide a COMPLETE, DETAILED event itinerary that the client can use to execute this event. "
            "This should be the definitive planning document."
        ),
    )
    clean_conversation.append(synthesis_instruction)

    # Run coordinator agent with full context
    synthesis_result = await self._coordinator_agent.run(messages=clean_conversation)

    # Yield comprehensive event itinerary
    if synthesis_result.text:
        await ctx.yield_output(synthesis_result.text)
    else:
        # Fallback if synthesis fails
        await ctx.yield_output(
            "Event planning workflow completed. Please review specialist recommendations above."
        )
```

**Step 3: Write failing test**

```python
def test_synthesis_creates_comprehensive_itinerary():
    """Final synthesis should create detailed event itinerary."""
    # Setup conversation with all specialist responses
    conversation = [
        ChatMessage(Role.USER, text="Plan corporate party for 50 people"),
        ChatMessage(Role.ASSISTANT, text="Venue: The Foundry, Seattle, $3k, 60 capacity"),
        ChatMessage(Role.ASSISTANT, text="Budget: Venue $3k (60%), Catering $1.2k (24%), Logistics $500 (10%), Contingency $300 (6%)"),
        ChatMessage(Role.ASSISTANT, text="Catering: Buffet style, vegetarian options, $24/person"),
        ChatMessage(Role.ASSISTANT, text="Timeline: Dec 15, 6-10pm. Weather: 45°F, clear. Calendar event created."),
    ]

    # Execute synthesis
    coordinator_agent = create_coordinator_agent()
    executor = EventPlanningCoordinator(coordinator_agent)

    # Mock ctx
    ctx = Mock(WorkflowContext)
    output_buffer = []
    ctx.yield_output = lambda x: output_buffer.append(x)

    await executor._synthesize_plan(ctx, conversation)

    # Assert comprehensive output
    final_output = output_buffer[0]
    assert "Executive Summary" in final_output
    assert "Venue Details" in final_output
    assert "Budget Breakdown" in final_output
    assert "Catering Plan" in final_output
    assert "Event Timeline" in final_output
    assert "Logistics" in final_output
    assert "Calendar" in final_output
    assert "Next Steps" in final_output
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/workflow/test_synthesis.py::test_synthesis_creates_comprehensive_itinerary -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/spec_to_agents/workflow/executors.py src/spec_to_agents/prompts/event_coordinator.py tests/workflow/test_synthesis.py
git commit -m "feat: comprehensive event itinerary synthesis

Coordinator now creates detailed event itineraries with:
- Complete venue, budget, catering, logistics details
- Specific event timeline with times
- Weather forecast and calendar confirmation
- Client action items

Transforms workflow from simple plan to executable event document.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Add Calendar Event Verification to Coordinator

**Files:**
- Create: `src/spec_to_agents/workflow/calendar_utils.py`
- Modify: `src/spec_to_agents/workflow/executors.py:272-311`
- Test: `tests/workflow/test_calendar_utils.py`

**Step 1: Write failing test for calendar verification**

Create `tests/workflow/test_calendar_utils.py`:

```python
"""Tests for calendar event verification utilities."""

def test_extract_calendar_event_from_conversation():
    """Should extract calendar event details from logistics response."""
    conversation = [
        ChatMessage(Role.USER, text="Plan event for Dec 15"),
        ChatMessage(Role.ASSISTANT, text="Calendar event created: Corporate Party on 2025-12-15 from 18:00-22:00"),
    ]

    event_details = extract_calendar_event_from_conversation(conversation)

    assert event_details is not None
    assert event_details["event_title"] == "Corporate Party"
    assert event_details["date"] == "2025-12-15"
    assert event_details["start_time"] == "18:00"
    assert event_details["end_time"] == "22:00"

def test_extract_calendar_event_not_found():
    """Should return None if no calendar event mentioned."""
    conversation = [
        ChatMessage(Role.USER, text="Plan event"),
        ChatMessage(Role.ASSISTANT, text="I recommend The Foundry"),
    ]

    event_details = extract_calendar_event_from_conversation(conversation)

    assert event_details is None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/workflow/test_calendar_utils.py -v
```

Expected: FAIL with "module not found"

**Step 3: Implement calendar verification utility**

Create `src/spec_to_agents/workflow/calendar_utils.py`:

```python
"""Utilities for calendar event verification in workflow synthesis."""

import re
from typing import TypedDict

from agent_framework import ChatMessage


class CalendarEventDetails(TypedDict):
    """Calendar event details extracted from conversation."""

    event_title: str
    date: str
    start_time: str
    end_time: str | None
    location: str | None


def extract_calendar_event_from_conversation(
    conversation: list[ChatMessage],
) -> CalendarEventDetails | None:
    """
    Extract calendar event details from logistics manager response.

    Searches conversation for calendar event creation confirmation and
    parses event details (title, date, time, location).

    Parameters
    ----------
    conversation : list[ChatMessage]
        Full conversation history including logistics response

    Returns
    -------
    CalendarEventDetails | None
        Parsed event details if found, None otherwise

    Notes
    -----
    Looks for patterns like:
    - "Calendar event created: <title> on <date> from <time>-<time>"
    - "Created calendar event '<title>' for <date>"
    """
    # Pattern: "Calendar event created: 'Title' on YYYY-MM-DD from HH:MM-HH:MM"
    pattern = r"Calendar event created:?\s*['\"]?([^'\"]+)['\"]?\s*on\s*(\d{4}-\d{2}-\d{2})\s*from\s*(\d{2}:\d{2})-(\d{2}:\d{2})"

    for message in reversed(conversation):  # Search from most recent
        if not hasattr(message, "contents"):
            continue

        for content in message.contents:
            if not hasattr(content, "text"):
                continue

            match = re.search(pattern, content.text, re.IGNORECASE)
            if match:
                return CalendarEventDetails(
                    event_title=match.group(1).strip(),
                    date=match.group(2),
                    start_time=match.group(3),
                    end_time=match.group(4),
                    location=None,  # Could enhance to extract location
                )

    return None
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/workflow/test_calendar_utils.py -v
```

Expected: PASS

**Step 5: Integrate calendar verification into synthesis**

Update `_synthesize_plan` to verify calendar event:

```python
# In _synthesize_plan method, before synthesis_instruction:

# Check if calendar event was created
from spec_to_agents.workflow.calendar_utils import extract_calendar_event_from_conversation

calendar_event = extract_calendar_event_from_conversation(conversation)
calendar_note = ""
if calendar_event:
    calendar_note = (
        f"\n\nIMPORTANT: Logistics manager created calendar event:\n"
        f"- Event: {calendar_event['event_title']}\n"
        f"- Date: {calendar_event['date']}\n"
        f"- Time: {calendar_event['start_time']} to {calendar_event['end_time']}\n"
        f"Confirm this in your Calendar Confirmation section."
    )
else:
    calendar_note = "\n\nNOTE: No calendar event was detected. Recommend client create calendar entry manually."

synthesis_instruction = ChatMessage(
    Role.USER,
    text=(
        f"All specialists have completed their work. Please synthesize a COMPREHENSIVE "
        f"event itinerary...{calendar_note}"
    ),
)
```

**Step 6: Run integration test**

```bash
uv run pytest tests/workflow/ -v
```

Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/spec_to_agents/workflow/calendar_utils.py src/spec_to_agents/workflow/executors.py tests/workflow/test_calendar_utils.py
git commit -m "feat: calendar event verification in synthesis

Coordinator now extracts and verifies calendar event creation from
logistics manager response. Includes event details in final itinerary
confirmation.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Integration Testing & Documentation

**Files:**
- Create: `tests/integration/test_full_workflow.py`
- Modify: `README.md` (if needed)

**Step 1: Write integration test**

Create comprehensive end-to-end test:

```python
"""Integration test for complete event planning workflow."""

import pytest
from agent_framework import Role, ChatMessage
from spec_to_agents.workflow.core import create_workflow


@pytest.mark.integration
async def test_complete_event_planning_workflow():
    """Test full workflow from user request to comprehensive itinerary."""
    # Setup
    workflow = create_workflow()

    # Execute
    user_request = "Plan a corporate holiday party for 50 people in Seattle on December 15, 2025. Budget is $5,000."

    outputs = []
    async for event in workflow.run_stream(user_request):
        if event.type == "workflow_output":
            outputs.append(event.data)

    # Assert: Should have one comprehensive output
    assert len(outputs) == 1
    final_itinerary = outputs[0]

    # Verify all required sections present
    required_sections = [
        "Executive Summary",
        "Venue",
        "Budget",
        "Catering",
        "Timeline",
        "Logistics",
        "Calendar",
        "Next Steps",
    ]

    for section in required_sections:
        assert section in final_itinerary, f"Missing section: {section}"

    # Verify specific details are included
    assert "December 15" in final_itinerary or "2025-12-15" in final_itinerary
    assert "50 people" in final_itinerary or "50" in final_itinerary
    assert "$5,000" in final_itinerary or "$5k" in final_itinerary
    assert "Seattle" in final_itinerary

    # Verify calendar event mentioned
    assert "calendar event" in final_itinerary.lower()


@pytest.mark.integration
async def test_workflow_with_user_input():
    """Test workflow handles human-in-the-loop interaction."""
    # This test would require mocking ctx.request_info
    # and simulating user responses
    pass
```

**Step 2: Run integration test**

```bash
uv run pytest tests/integration/test_full_workflow.py::test_complete_event_planning_workflow -v -s
```

Expected: PASS (may take 30-60 seconds for full workflow)

**Step 3: Manual testing with DevUI**

```bash
uv run app
```

Test cases:
1. Basic request: "Plan corporate party for 50 people in Seattle, $5k budget"
2. Request requiring clarification: "Help me plan an event in Seattle"
3. Request with date: "Plan party for 50 people on December 15, 2025"

Verify:
- ✅ Specialists return natural text
- ✅ Coordinator routes correctly
- ✅ Final output has all sections
- ✅ Calendar event is mentioned/confirmed
- ✅ Timeline has specific times
- ✅ Budget shows allocation
- ✅ Next steps are actionable

**Step 4: Document changes**

If changes significantly impact usage, update relevant docs. Otherwise skip.

**Step 5: Commit**

```bash
git add tests/integration/test_full_workflow.py
git commit -m "test: add integration tests for complete workflow

Tests verify end-to-end workflow from user request to comprehensive
event itinerary with all required sections and details.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Validation Checklist

Before considering this plan complete, verify:

- [ ] All specialist agents (venue, budget, catering, logistics) removed `response_format=SpecialistOutput`
- [ ] All specialist prompts updated to remove structured output sections
- [ ] All specialists return natural, conversational text responses
- [ ] Coordinator has new `_analyze_specialist_response_for_routing()` method
- [ ] Coordinator `on_specialist_response` handler uses text analysis for routing
- [ ] Coordinator synthesis creates comprehensive itinerary with all 8 sections
- [ ] Calendar event verification extracts and confirms event details
- [ ] Integration tests pass for complete workflow
- [ ] Manual testing with DevUI shows expected behavior
- [ ] All unit tests pass: `uv run pytest tests/`
- [ ] Code formatted: `uv run ruff .`
- [ ] Type checking passes: `uv run mypy .`

---

## Known Edge Cases

1. **Specialist doesn't signal next step clearly** - Coordinator's LLM-based routing should handle ambiguous responses gracefully by defaulting to next logical specialist or requesting clarification

2. **Calendar event creation fails** - Logistics manager will note failure in response; synthesis will recommend manual calendar creation

3. **User interrupts mid-workflow** - Service-managed threads preserve state; workflow can resume

4. **Budget exceeds what's reasonable** - Budget analyst will note constraints; may route back to venue for cheaper option

5. **No date provided** - Logistics manager will request date before proceeding (acceptable for this specialist only)

---

## Future Enhancements

After completing this plan, consider:

1. **Structured final output** - Create a Pydantic model for the final event itinerary (separate from SpecialistOutput) to enable programmatic access to event details

2. **Email integration** - Automatically send event itinerary and calendar invite to client

3. **Vendor management** - Track vendor contacts, contracts, and payment schedules

4. **Budget tracking** - Monitor actuals vs. planned expenses

5. **Multi-event workflows** - Support planning multiple related events (conference with multiple sessions)

6. **PDF export** - Generate professional PDF event planning documents

---

## References

- **@superpowers:test-driven-development** - Follow RED-GREEN-REFACTOR for all changes
- **@superpowers:verification-before-completion** - Run tests before claiming tasks complete
- **@superpowers:requesting-code-review** - Consider code review after Task 5 (major routing change)

---

**Implementation Notes:**

- Each task follows TDD: write test → run (fail) → implement → run (pass) → commit
- Commits are frequent and atomic (one task = one commit)
- Tests verify behavior, not implementation details
- Integration test is the ultimate validation
- Manual DevUI testing catches UI/UX issues tests might miss
