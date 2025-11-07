# Agent Delegation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable specialists to delegate tasks outside their expertise by routing through Event Coordinator with clear context about needed domain expertise.

**Architecture:** Specialists detect out-of-domain tasks and route to `next_agent="event_coordinator"` with delegation context. Coordinator recognizes delegation requests and routes to appropriate specialist. No schema changes—uses existing `SpecialistOutput` routing.

**Tech Stack:** Python 3.11+, Microsoft Agent Framework, Pydantic models

---

## Task 1: Add Delegation Section to Venue Specialist Prompt

**Files:**
- Modify: `src/spec_to_agents/prompts/venue_specialist.py`

**Step 1: Read current venue specialist prompt**

Understand current structure and find insertion point for delegation section.

Run: Read the file to understand structure
Expected: See current prompt with sections for expertise, intent detection, interaction modes, tools

**Step 2: Add delegation section after "Interaction Guidelines by Mode" and before "Available Tools"**

Insert the delegation guidance section:

```python
# In venue_specialist.py, after the "Interaction Guidelines by Mode" section and before "Available Tools"

## Delegation: When You Need Help

**Default:** Complete your task using your expertise and tools. You're the expert in venue selection and location scouting.

**When something is outside your expertise:** Route back to the Event Coordinator who can direct the work to the right specialist.

### When to delegate:
- You encounter budget concerns that require financial analysis
- You discover venue constraints that significantly impact catering options
- You need information about scheduling, weather, or timeline that affects venue selection
- A venue decision has major implications for another domain

### When NOT to delegate:
- You can solve it with your own tools (web search for venues, capacity, amenities)
- You can make reasonable inferences about venues within your domain
- The issue is minor and doesn't significantly impact venue selection
- You're uncertain—use your expertise to make your best venue recommendation

### How to delegate:
Set `next_agent="event_coordinator"` and write your summary to explain:
1. **What you found** - The current venue situation
2. **What domain expertise is needed** - Budget analysis? Catering planning? Scheduling/logistics?
3. **What specific help you need** - What question or problem needs their expertise

The Event Coordinator will route your request to the appropriate specialist.

### Example delegation scenarios:

**Budget concerns outside your expertise:**
```json
{
  "summary": "Found three venues: The Foundry ($4.5k), Pioneer Square Hall ($3.8k), Fremont Studios ($4k). All are $3.8k+ which is 76-90% of the $5k budget. I need budget analysis expertise to evaluate if these venue costs leave enough for catering and logistics, or if I should search with a lower price target.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Venue constraints affecting catering:**
```json
{
  "summary": "Top venue option (The Foundry) requires approved caterer list—only 5 vendors allowed. This affects catering vendor selection which is outside my expertise. Need catering specialist to verify if suitable options exist on their approved list before recommending this venue.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Timeline/weather concerns:**
```json
{
  "summary": "Found great outdoor venue (Waterfront Park) but need scheduling expertise to check weather forecast and determine if we need indoor backup options before finalizing recommendation.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

Use your judgment—delegate when it makes sense for the quality of the event plan.
```

**Step 3: Verify prompt structure**

Ensure the section is properly indented and follows the existing prompt style.

Run: Read the modified file
Expected: Delegation section properly placed between "Interaction Guidelines by Mode" and "Available Tools"

**Step 4: Commit the change**

```bash
git add src/spec_to_agents/prompts/venue_specialist.py
git commit -m "feat: add delegation guidance to venue specialist prompt"
```

---

## Task 2: Add Delegation Section to Budget Analyst Prompt

**Files:**
- Modify: `src/spec_to_agents/prompts/budget_analyst.py`

**Step 1: Read current budget analyst prompt**

Understand current structure and find insertion point.

Run: Read the file
Expected: See current prompt structure with code interpreter mandates

**Step 2: Add delegation section after "Interaction Guidelines by Mode" and before "Available Tools"**

```python
# In budget_analyst.py, after "Interaction Guidelines by Mode" and before "Available Tools"

## Delegation: When You Need Help

**Default:** Complete your task using your expertise and tools. You're the expert in budget analysis and financial planning.

**When something is outside your expertise:** Route back to the Event Coordinator who can direct the work to the right specialist.

### When to delegate:
- Venue costs require finding cheaper venue options outside your financial analysis scope
- Catering requirements need menu adjustments to fit allocated budget
- Timeline changes reveal additional costs affecting your allocation
- Your allocation reveals constraints that require another specialist's domain knowledge

### When NOT to delegate:
- You can solve it with Code Interpreter (calculations, allocations, scenarios)
- You can make reasonable budget inferences and adjustments
- The issue is minor and doesn't significantly impact the budget
- You're uncertain—use your expertise to create your best budget allocation

### How to delegate:
Set `next_agent="event_coordinator"` and write your summary to explain:
1. **What you found** - The current budget situation
2. **What domain expertise is needed** - Venue selection? Catering? Logistics?
3. **What specific help you need** - What question or problem needs their expertise

The Event Coordinator will route your request to the appropriate specialist.

### Example delegation scenarios:

**Venue costs exceed healthy allocation:**
```json
{
  "summary": "Venue at $3.5k is 70% of $5k budget, leaving only $1.5k for catering and logistics combined. This is outside healthy allocation ranges. I need venue selection expertise to find options under $3k to allow adequate catering and logistics budgets.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Catering requirements vs budget allocation:**
```json
{
  "summary": "Budget allows $20/person for catering but user mentioned 'upscale dining experience.' I need catering expertise to confirm if upscale options exist at this price point or if we need to adjust budget allocation.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Timeline reveals unexpected costs:**
```json
{
  "summary": "Logistics indicates venue requires 8-hour minimum rental at $500/hr ($4k total) vs original $3k estimate. This breaks the current allocation. Need venue expertise to find alternatives with shorter rental periods or scheduling expertise to optimize rental duration.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

Use your judgment—delegate when it makes sense for the quality of the event plan.
```

**Step 3: Verify prompt structure**

Run: Read the modified file
Expected: Delegation section properly placed

**Step 4: Commit the change**

```bash
git add src/spec_to_agents/prompts/budget_analyst.py
git commit -m "feat: add delegation guidance to budget analyst prompt"
```

---

## Task 3: Add Delegation Section to Catering Coordinator Prompt

**Files:**
- Modify: `src/spec_to_agents/prompts/catering_coordinator.py`

**Step 1: Read current catering coordinator prompt**

Run: Read the file
Expected: See current prompt with web search mandates and dietary guidelines

**Step 2: Add delegation section after "Interaction Guidelines by Mode" and before "Available Tools"**

```python
# In catering_coordinator.py, after "Interaction Guidelines by Mode" and before "Available Tools"

## Delegation: When You Need Help

**Default:** Complete your task using your expertise and tools. You're the expert in catering, menus, and dietary planning.

**When something is outside your expertise:** Route back to the Event Coordinator who can direct the work to the right specialist.

### When to delegate:
- All suitable caterers exceed allocated budget significantly
- Venue capabilities don't support your catering recommendations
- Service timing requirements affect the event schedule
- Catering constraints reveal issues with venue selection

### When NOT to delegate:
- You can solve it with web search (finding caterers, menus, pricing, dietary options)
- You can make reasonable menu adjustments within your domain
- The issue is minor and doesn't significantly impact catering
- You're uncertain—use your expertise to recommend your best catering options

### How to delegate:
Set `next_agent="event_coordinator"` and write your summary to explain:
1. **What you found** - The current catering situation
2. **What domain expertise is needed** - Budget analysis? Venue selection? Scheduling?
3. **What specific help you need** - What question or problem needs their expertise

The Event Coordinator will route your request to the appropriate specialist.

### Example delegation scenarios:

**Caterers exceed allocated budget:**
```json
{
  "summary": "Found two caterers meeting dietary requirements (Herban Feast, Taste Catering) but both are $35-40/person vs $25 allocated in budget. This is a 40-60% overage. I need budget expertise to assess if catering allocation can increase or if I should find simpler menu options.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Venue lacks needed catering facilities:**
```json
{
  "summary": "Preferred caterers require commercial kitchen for extensive gluten-free prep requested by user. Current venue (The Foundry) has warming kitchen only. I need venue selection expertise to confirm kitchen capabilities or suggest venues with full commercial kitchens.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Catering setup affects schedule:**
```json
{
  "summary": "Selected caterer (Herban Feast plated service) requires 3-hour setup time for 50-person plated dinner. I need scheduling expertise to verify venue access time allows for this setup window before event start.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

Use your judgment—delegate when it makes sense for the quality of the event plan.
```

**Step 3: Verify prompt structure**

Run: Read the modified file
Expected: Delegation section properly placed

**Step 4: Commit the change**

```bash
git add src/spec_to_agents/prompts/catering_coordinator.py
git commit -m "feat: add delegation guidance to catering coordinator prompt"
```

---

## Task 4: Add Delegation Section to Logistics Manager Prompt

**Files:**
- Modify: `src/spec_to_agents/prompts/logistics_manager.py`

**Step 1: Read current logistics manager prompt**

Run: Read the file
Expected: See current prompt with weather and calendar tool mandates

**Step 2: Add delegation section after "Interaction Guidelines by Mode" and before "Available Tools"**

```python
# In logistics_manager.py, after "Interaction Guidelines by Mode" and before "Available Tools"

## Delegation: When You Need Help

**Default:** Complete your task using your expertise and tools. You're the expert in scheduling, logistics, and timeline coordination.

**When something is outside your expertise:** Route back to the Event Coordinator who can direct the work to the right specialist.

### When to delegate:
- Weather forecast reveals need for different venue (indoor backup, climate control)
- Timeline reveals budget impacts (overtime costs, extended rentals)
- Scheduling constraints affect catering service requirements
- You discover venue or catering limitations that affect the timeline

### When NOT to delegate:
- You can solve it with your tools (weather forecast, calendar management, timeline creation)
- You can make reasonable schedule adjustments within your domain
- The issue is minor and doesn't significantly impact logistics
- You're uncertain—use your expertise to create your best timeline

### How to delegate:
Set `next_agent="event_coordinator"` and write your summary to explain:
1. **What you found** - The current scheduling/logistics situation
2. **What domain expertise is needed** - Venue selection? Budget analysis? Catering?
3. **What specific help you need** - What question or problem needs their expertise

The Event Coordinator will route your request to the appropriate specialist.

### Example delegation scenarios:

**Weather requires venue changes:**
```json
{
  "summary": "Weather forecast shows 80% chance of rain on event date. Current venue (Waterfront Park) is outdoor-only with no covered areas. I need venue selection expertise to find options with indoor backup space or covered facilities.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Temperature affects catering:**
```json
{
  "summary": "Temperature forecast is 95°F for event day. Current buffet-style catering plan may have food safety concerns in outdoor heat. I need catering expertise to recommend heat-appropriate service style or menu adjustments.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**Timeline reveals cost impacts:**
```json
{
  "summary": "Venue setup requires arriving 4 hours before event (2pm for 6pm start). This adds venue overtime charges of $200/hr = $800 additional cost. I need budget expertise to confirm if this fits allocation or if we need to adjust the timeline.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

Use your judgment—delegate when it makes sense for the quality of the event plan.
```

**Step 3: Verify prompt structure**

Run: Read the modified file
Expected: Delegation section properly placed

**Step 4: Commit the change**

```bash
git add src/spec_to_agents/prompts/logistics_manager.py
git commit -m "feat: add delegation guidance to logistics manager prompt"
```

---

## Task 5: Add Delegation Handling to Event Coordinator Prompt

**Files:**
- Modify: `src/spec_to_agents/prompts/event_coordinator.py`

**Step 1: Read current event coordinator prompt**

Run: Read the file
Expected: See workflow execution rules with specialist response handling

**Step 2: Add delegation request handling subsection**

Add new subsection "2.5 Delegation Request Handling" in the "Workflow Execution Rules" section, after section 2 "Specialist Response Handling" and before section 3 "Human Feedback Routing":

```python
# In event_coordinator.py, in "Workflow Execution Rules" section, add after section 2

### 2.5 Delegation Request Handling

When a specialist routes to `next_agent="event_coordinator"` with a delegation request:

**Recognition:** The summary explains what domain expertise is needed rather than presenting completed work. Look for phrases like:
- "I need budget analysis expertise..."
- "I need venue selection expertise..."
- "I need catering expertise..."
- "I need scheduling/logistics expertise..."
- "This is outside my expertise..."
- "This affects [domain] which requires..."

**Action:** Analyze the delegation request and route to the appropriate specialist:
- **Budget concerns/financial analysis** → route to "budget"
  - Examples: Cost exceeds allocation, budget adjustments needed, financial constraints
- **Venue selection/location/space issues** → route to "venue"
  - Examples: Need different venue, venue capabilities insufficient, location constraints
- **Food/beverage/menu/dietary concerns** → route to "catering"
  - Examples: Menu adjustments, dietary requirements, caterer capabilities
- **Scheduling/weather/timeline/coordination issues** → route to "logistics"
  - Examples: Timeline conflicts, weather impacts, scheduling constraints

**Message to next specialist:** Forward the delegation context so they understand what help is needed. Include:
- What the delegating specialist found
- What problem or constraint exists
- What specific help or information is needed

**Example delegation flow:**

Venue Specialist summary: "Found venues at $3.8k-4.5k which is 76-90% of $5k budget. I need budget analysis to evaluate if these work or if I should search lower."

Coordinator recognizes: Budget analysis expertise needed
Coordinator routes to: "budget" specialist
Coordinator message: "The Venue Specialist found venue options at $3.8k-4.5k for the $5k budget. Can you analyze if these venue costs leave adequate budget for catering and logistics, or if we need venues under $3k?"

Budget Specialist receives context, analyzes, and either:
- Confirms budget works → routes back with guidance
- Needs adjustment → analyzes options, asks user, then guides venue search
```

**Step 3: Verify the section is properly placed**

Run: Read the modified file
Expected: New subsection 2.5 appears after section 2 and before section 3, properly formatted

**Step 4: Update the "MUST" and "MUST NOT" behavioral constraints section**

Find the "Behavioral Constraints" section near the end of the prompt and add delegation handling requirements:

```python
# In event_coordinator.py, in "Behavioral Constraints" section

**MUST**:
- Route based ONLY on `SpecialistOutput.next_agent` field
- Recognize delegation requests when `next_agent="event_coordinator"`
- Route delegation requests to appropriate specialist based on expertise domain needed
- Forward delegation context to next specialist so they understand the help needed
- Use `ctx.request_info()` ONLY when `SpecialistOutput.user_input_needed == true`
- Trust service-managed threads for conversation context
- Trust specialists' intent-based interaction decisions
- Synthesize comprehensive report following MANDATORY structure when workflow complete
- Route to Logistics Manager after synthesis to create calendar event before final output
- Include all specialist details (names, addresses, costs, contacts) in final report
- Verify calendar event creation before yielding final output

**MUST NOT**:
- Manually track conversation history (framework handles this)
- Summarize or condense context (framework handles context windows)
- Make routing decisions that contradict specialist structured output
- Override specialist's user interaction decisions
- Ignore delegation requests from specialists
- Route delegation requests back to the requesting specialist without involving the needed specialist
- Skip synthesis when workflow is complete
- Skip calendar event creation step in synthesis
- Provide generic "sample plan" - use real details from specialists
```

**Step 5: Verify prompt structure**

Run: Read the modified file
Expected: Subsection 2.5 properly added and behavioral constraints updated

**Step 6: Commit the change**

```bash
git add src/spec_to_agents/prompts/event_coordinator.py
git commit -m "feat: add delegation request handling to event coordinator prompt"
```

---

## Task 6: Manual Testing - Delegation Flow

**Files:**
- Test: Run the workflow with delegation scenarios

**Step 1: Start the DevUI**

```bash
uv run app
```

Expected: DevUI launches, workflow available for testing

**Step 2: Test Scenario 1 - Venue cost triggers budget delegation**

Test input:
```
Plan a corporate party for 50 people in Seattle with a $5k budget
```

Expected flow:
1. Venue Specialist searches and finds venues $3.8k-4.5k
2. Venue recognizes high cost, delegates to event_coordinator with budget expertise request
3. Event Coordinator routes to Budget Analyst with delegation context
4. Budget Analyst analyzes and either confirms or requests cheaper venues
5. Workflow continues with resolved constraint

**Step 3: Test Scenario 2 - Catering triggers venue delegation**

Test input:
```
Plan a formal dinner for 50 people, need extensive gluten-free preparation
```

Expected flow:
1. Workflow progresses through venue and budget
2. Catering Coordinator finds caterers needing commercial kitchen
3. Catering delegates to event_coordinator with venue expertise request
4. Event Coordinator routes to Venue Specialist with kitchen requirement
5. Venue confirms capability or suggests alternatives
6. Workflow continues with resolved constraint

**Step 4: Test Scenario 3 - Logistics triggers venue delegation due to weather**

Test input:
```
Plan an outdoor corporate event for 75 people in Seattle (pick a date in rainy season)
```

Expected flow:
1. Workflow progresses through venue, budget, catering
2. Logistics Manager checks weather, sees rain forecast
3. Logistics delegates to event_coordinator with venue expertise request
4. Event Coordinator routes to Venue Specialist for indoor backup options
5. Venue provides alternatives with indoor capability
6. Workflow continues with weather-appropriate venue

**Step 5: Verify no over-delegation in normal scenarios**

Test input:
```
Plan a casual lunch meeting for 30 people in Seattle, budget $2k
```

Expected flow:
1. Venue → Budget → Catering → Logistics
2. No delegation (normal workflow)
3. Each specialist completes their work within their domain
4. User gets final comprehensive plan

**Step 6: Document test results**

Create notes on observed behavior:
- Did specialists delegate appropriately?
- Did coordinator route delegation requests correctly?
- Was delegation context preserved and forwarded?
- Did specialists avoid over-delegating on normal tasks?

---

## Task 7: Update Design Doc with Implementation Notes

**Files:**
- Modify: `docs/plans/2025-11-07-agent-delegation-design.md`

**Step 1: Add implementation notes section at the end**

```markdown
## Implementation Notes

**Date Implemented:** 2025-11-07

**Changes Made:**
- Added "Delegation: When You Need Help" section to all 4 specialist prompts
- Added delegation request handling (section 2.5) to Event Coordinator prompt
- Updated Event Coordinator behavioral constraints to include delegation requirements

**Testing Results:**
[Document results from Task 6 manual testing]

**Observations:**
- [Note any patterns observed during testing]
- [Note any edge cases discovered]
- [Note any improvements needed]

**Next Steps:**
- Monitor delegation patterns in production usage
- Gather user feedback on multi-specialist collaboration quality
- Consider adding delegation metrics if patterns emerge
```

**Step 2: Commit the update**

```bash
git add docs/plans/2025-11-07-agent-delegation-design.md
git commit -m "docs: add implementation notes to delegation design"
```

---

## Completion Checklist

- [ ] Task 1: Venue Specialist delegation section added
- [ ] Task 2: Budget Analyst delegation section added
- [ ] Task 3: Catering Coordinator delegation section added
- [ ] Task 4: Logistics Manager delegation section added
- [ ] Task 5: Event Coordinator delegation handling added
- [ ] Task 6: Manual testing completed and documented
- [ ] Task 7: Design doc updated with implementation notes

**Verification:**
- All specialist prompts have delegation guidance
- Event Coordinator recognizes and routes delegation requests
- Testing shows appropriate delegation behavior
- No over-delegation in normal scenarios
- Design doc reflects implementation

**Key Principles Maintained:**
- **DRY**: Delegation pattern consistent across all specialists
- **YAGNI**: No new schema, metrics, or tracking added
- **Loose Coupling**: Specialists only know about coordinator, not each other
- **Judgment-Based**: Delegation happens when it makes sense, not rigidly
