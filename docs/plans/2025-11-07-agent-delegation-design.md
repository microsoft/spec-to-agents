# Design: Agent Delegation Through Event Coordinator

**Date:** 2025-11-07
**Status:** Approved
**Author:** Claude Code

## Problem

Specialist agents sometimes encounter tasks or problems that fall outside their domain expertise. Currently, agents either:
1. Attempt the task anyway (stepping outside their expertise)
2. Ask the user for help (when another specialist could handle it)
3. Ignore the problem (leaving gaps in the event plan)

This results in suboptimal recommendations and missed opportunities for specialists to collaborate.

## Solution Overview

Enable specialists to **delegate through the Event Coordinator** when they recognize a task requires expertise from another domain.

**Key architectural principle:** Specialists don't need to know about each other. They only know:
1. Their own expertise domain
2. The Event Coordinator can route to whoever can help

**Key delegation principle:** Use your judgment. Delegate when another specialist's expertise would meaningfully improve the outcome.

## Design

### 1. No Schema Changes Required

The existing `SpecialistOutput` schema already supports delegation through the coordinator:

```python
class SpecialistOutput(BaseModel):
    summary: str
    next_agent: Literal["event_coordinator", "venue", "budget", "catering", "logistics"] | None
    user_input_needed: bool = False
    user_prompt: str | None = None
```

**Normal routing (work complete, proceeding to next phase):**
```python
{
  "summary": "Found 3 venues: The Foundry ($3k), Pioneer Square ($2.5k), Fremont Studios ($3.5k). Which direction appeals to you?",
  "next_agent": null,
  "user_input_needed": true,
  "user_prompt": "Which direction appeals to you?"
}
```

**Delegation routing (need help from another domain):**
```python
{
  "summary": "Found venues but all are $4k+ which seems high for a $5k total budget. This is outside my venue expertise—I need someone who handles budget analysis to evaluate if these prices work or if I should search with a lower price target.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

The distinction: delegation uses `next_agent="event_coordinator"` and the summary explains **what expertise is needed** rather than presenting completed work.

### 2. Specialist Prompt Modifications

Each specialist prompt gets a new **"Delegation: When You Need Help"** section:

```markdown
## Delegation: When You Need Help

**Default:** Complete your task using your expertise and tools. You're the expert in your domain.

**When something is outside your expertise:** Route back to the Event Coordinator who can direct the work to the right specialist.

### When to delegate:
- You encounter a problem that requires expertise from another domain
- You discover constraints or information that conflict with another specialist's work
- You need domain-specific knowledge you don't have
- A decision in your area has significant implications for another domain

### When NOT to delegate:
- You can solve it with your own tools and expertise
- You can make reasonable inferences within your domain
- The issue is minor and doesn't significantly impact the event
- You're uncertain—use your expertise to make your best recommendation

### How to delegate:
Set `next_agent="event_coordinator"` and write your summary to explain:
1. **What you found** - The current situation
2. **What domain expertise is needed** - Budget analysis? Venue selection? Catering planning? Scheduling/logistics?
3. **What specific help you need** - What question or problem needs their expertise

The Event Coordinator will route your request to the appropriate specialist.

### Example delegation scenarios:

**You discover budget concerns outside your expertise:**
```json
{
  "summary": "Found three venues: The Foundry ($4.5k), Pioneer Square Hall ($3.8k), Fremont Studios ($4k). All are $3.8k+ which is 76-90% of the $5k budget. I need budget analysis expertise to evaluate if these venue costs leave enough for catering and logistics, or if I should search with a lower price target.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**You discover constraints affecting another domain:**
```json
{
  "summary": "Top venue option (The Foundry) requires approved caterer list—only 5 vendors allowed. This affects catering vendor selection which is outside my expertise. Need catering specialist to verify if suitable options exist on their approved list before recommending this venue.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

**You need information from another domain to proceed:**
```json
{
  "summary": "Weather forecast shows 80% rain probability. Current venue recommendation (Waterfront Park) is outdoor-only. I need venue selection expertise to find options with indoor backup space before finalizing the schedule.",
  "next_agent": "event_coordinator",
  "user_input_needed": false
}
```

Use your judgment—delegate when it makes sense for the quality of the event plan.
```

### 3. Specialist Prompt Placement

Add the "Delegation: When You Need Help" section:
- **After** "Interaction Guidelines by Mode"
- **Before** "Available Tools"

**Reasoning:** Agents understand their primary behavior first, then learn about delegation as an advanced pattern, then see their tools.

### 4. Event Coordinator Modifications

The Event Coordinator prompt needs minor updates to handle delegation requests:

**Add to "Workflow Execution Rules" section:**

```markdown
### 2.5 Delegation Request Handling

When a specialist routes to `next_agent="event_coordinator"` with a delegation request:

**Recognition:** The summary explains what domain expertise is needed (e.g., "need budget analysis", "need catering expertise", "need venue selection")

**Action:** Analyze the delegation request and route to the appropriate specialist:
- Budget concerns/financial analysis → route to "budget"
- Venue selection/location/space issues → route to "venue"
- Food/beverage/menu concerns → route to "catering"
- Scheduling/weather/timeline issues → route to "logistics"

**Message to next specialist:** Forward the delegation context so they understand what help is needed.

**Example:**
Specialist summary: "Found venues at $4k+ which seems high. Need budget analysis to evaluate if these work or if I should search lower."

Coordinator action:
- Recognizes: Budget analysis expertise needed
- Routes to: "budget" specialist
- Message: "The Venue Specialist found options at $3.8k-4.5k for your $5k budget. Can you analyze if these venue costs leave adequate budget for catering and logistics?"
```

### 5. Architecture: True Star Topology

This design maintains clean separation:

```
         Event Coordinator (knows all specialists)
              /    |    |    \
             /     |    |     \
          Venue Budget Catering Logistics
          (knows coordinator only)
```

**Specialists:** Know their domain + can route to coordinator for help
**Coordinator:** Knows all specialists + orchestrates routing

**Benefits:**
- Loose coupling between specialists
- Easy to add new specialists without updating existing prompts
- Clear separation of concerns
- True hub-and-spoke architecture

## Implementation Plan

### Files to Modify

**Specialist prompts** - Add delegation section:
- `src/spec_to_agents/prompts/venue_specialist.py`
- `src/spec_to_agents/prompts/budget_analyst.py`
- `src/spec_to_agents/prompts/catering_coordinator.py`
- `src/spec_to_agents/prompts/logistics_manager.py`

**Coordinator prompt** - Add delegation handling:
- `src/spec_to_agents/prompts/event_coordinator.py`

### Changes Summary

**Specialists (4 files):**
- Add "Delegation: When You Need Help" section with 2-3 examples
- Examples should show routing to `next_agent="event_coordinator"`
- Examples should describe needed expertise domain, not specific specialist names

**Event Coordinator (1 file):**
- Add "Delegation Request Handling" subsection to workflow execution rules
- Add logic to recognize delegation requests and route to appropriate specialist
- Maintain existing routing behavior for normal specialist outputs

## Examples of Expected Behavior

### Example 1: Venue triggers budget delegation

```
User: "Plan corporate party for 50 people in Seattle, $5k budget"

Venue: [searches] "I found three venues: The Foundry ($4.5k), Pioneer Square Hall ($3.8k), Fremont Studios ($4k). All are $3.8k+ which is 76-90% of your $5k budget. I need budget analysis expertise to evaluate if these venue costs work or if I should search with a lower price target."
→ Delegates to coordinator (next_agent="event_coordinator")

Coordinator: [recognizes budget expertise needed] Routes to Budget Analyst
→ "Venue Specialist found options at $3.8k-4.5k for the $5k budget. Can you analyze if these leave adequate room for catering and logistics?"

Budget: [analyzes] "The $3.8k venue (Pioneer Square Hall) could work if we're tight elsewhere: Venue $3.8k (76%), Catering $800 (16%), Logistics $400 (8%). That's only $16/person for food. Would you prefer: (a) venue around $3k for better catering budget, or (b) keep Pioneer Square Hall with simple catering?"
→ Asks user (user_input_needed=true)

User: "Let's find a cheaper venue"

Budget: "Got it, aiming for $3k venue to allow $25-30/person catering."
→ Routes back through coordinator (next_agent="event_coordinator")

Coordinator: [recognizes need for venue with budget constraint] Routes to Venue
→ "Please find venues under $3k to allow adequate catering budget"

Venue: [searches with constraint] "Found three venues under $3k: ..."
```

### Example 2: Catering discovers venue limitation, delegates

```
User: [after venue selected] "The Foundry looks good"

Coordinator: Routes to Budget → Budget allocates → Routes to Catering

Catering: [researching caterers] "I found two excellent caterers (Herban Feast, Taste Catering) but both need commercial kitchen for gluten-free prep. I need venue expertise to verify if The Foundry has full kitchen capabilities or to suggest alternatives with commercial kitchens."
→ Delegates to coordinator (next_agent="event_coordinator")

Coordinator: [recognizes venue expertise needed] Routes to Venue
→ "Caterers need commercial kitchen for gluten-free prep. Does The Foundry have this capability?"

Venue: [checks details] "The Foundry has warming kitchen only. Two alternatives with commercial kitchens: Pioneer Square Hall ($2.8k), Fremont Studios ($3.2k). Both match capacity and style."
→ Routes back to coordinator, asks user preference

User: "Pioneer Square Hall sounds good"

Coordinator: Routes back to Catering with updated venue info
→ "Venue is now Pioneer Square Hall with full commercial kitchen"

Catering: [continues] "Perfect! With full kitchen, both caterers work well..."
```

### Example 3: Normal flow (no delegation needed)

```
User: "Corporate party, 50 people, Seattle, $5k"

Venue: [searches] "Found three venues: The Foundry ($3k), Pioneer Square ($2.5k), Fremont Studios ($3.5k). Which direction appeals to you?"
→ Normal user interaction (user_input_needed=true)

User: "The Foundry"

Venue: "Got it!"
→ Normal routing to budget (next_agent="budget")

Budget: [calculates] "For $5k with $3k venue: Venue $3k (60%), Catering $1.2k (24%), Logistics $500 (10%), Contingency $300 (6%). Work for you?"
→ Normal flow continues, no delegation needed
```

## Success Criteria

1. **Specialists stay in their domain** - Don't attempt work outside their expertise
2. **Delegation is natural** - Happens when it makes sense, not rigidly
3. **Clear delegation context** - Summaries explain what expertise is needed and why
4. **Coordinator routes effectively** - Recognizes delegation requests and sends to right specialist
5. **Maintains collaborative mode** - Delegation doesn't bypass user decision points
6. **Loose coupling maintained** - Specialists don't need to know about each other

## Implementation Notes

**Date Implemented:** 2025-11-07

**Architecture Decision:** Changed from coordinator hub routing to direct peer-to-peer delegation

**Rationale:**
During implementation, we realized that having specialists route delegation requests through the Event Coordinator added unnecessary indirection. Instead, specialists now route directly to each other using the `next_agent` field with specific specialist IDs ("venue", "budget", "catering", "logistics"). This approach is:
- **Simpler**: Eliminates the coordinator's delegation recognition and re-routing logic
- **More direct**: Specialists specify exactly who they need help from
- **More efficient**: Reduces message passing hops (specialist → peer vs specialist → coordinator → peer)
- **Maintains loose coupling**: Specialists still only know about roles/capabilities, not implementation details

**Files Modified:**
- `src/spec_to_agents/prompts/venue_specialist.py` - Added direct peer delegation section
- `src/spec_to_agents/prompts/budget_analyst.py` - Added direct peer delegation section
- `src/spec_to_agents/prompts/catering_coordinator.py` - Added direct peer delegation section
- `src/spec_to_agents/prompts/logistics_manager.py` - Added direct peer delegation section
- `src/spec_to_agents/prompts/event_coordinator.py` - Removed delegation handling subsection and constraints (2025-11-07)

**Event Coordinator Changes:**
The Event Coordinator prompt was simplified by removing:
- Section "2.5 Delegation Request Handling" (no longer needed)
- Delegation-related behavioral constraints in the MUST and MUST NOT sections
- Specialists now handle peer-to-peer routing autonomously

**Key Pattern:**
Specialists use `next_agent="<specialist_id>"` to route directly to peers when they need help from another domain. The summary explains what was found and what specific help is needed. The receiving specialist sees this context and provides their expertise, then routes back or continues the workflow as appropriate.

**Example:**
```json
{
  "summary": "Found venues at $3.8k-4.5k which is 76-90% of $5k budget. Budget Analyst: can you evaluate if these venue costs leave adequate budget for catering and logistics, or should I search with a lower price target?",
  "next_agent": "budget",
  "user_input_needed": false
}
```

## Non-Goals

- **Not adding new message types** - Use existing SpecialistOutput schema
- **Not making delegation mandatory** - Judgment-based, not checklist-based
- **Not supporting multi-hop delegation chains** - Keep it simple: delegate to coordinator, coordinator routes
- **Not adding delegation metrics** - No tracking/logging beyond normal conversation flow
- **Not listing all specialists in specialist prompts** - They only know about coordinator

## Testing Scenarios

Test cases that should trigger delegation:
1. **Venue costs exceed typical budget allocation** - Venue → Coordinator → Budget
2. **Venue has catering restrictions** - Venue → Coordinator → Catering
3. **Catering needs exceed venue capabilities** - Catering → Coordinator → Venue
4. **Weather requires venue changes** - Logistics → Coordinator → Venue
5. **Timeline reveals budget impacts** - Logistics → Coordinator → Budget

Verify:
- Specialists delegate when appropriate (not over-delegating)
- Delegation requests have clear context about needed expertise
- Coordinator successfully routes to correct specialist
- Multi-specialist collaboration resolves the issue
- User still gets decision points (collaborative mode maintained)
