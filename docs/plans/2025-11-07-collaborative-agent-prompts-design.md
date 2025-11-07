# Design: Collaborative Agent Prompts

**Date:** 2025-11-07
**Status:** Approved
**Author:** Claude Code

## Problem

The event planning workflow is too autonomous - agents make all decisions without showing options or getting user input. This creates a poor user experience where users feel they have no control over venue selection, budget allocation, menu choices, or timeline decisions.

**User feedback:** "The system is just going and doing things without asking the user what they want or if the option it found looks good."

## Solution Overview

Change all specialist agents to default to **Collaborative Mode** - they should present options and ask for user preferences at every major decision point, rather than making autonomous decisions.

**Key principle:** Be conversational and helpful, like a knowledgeable colleague helping plan an event. Don't overdo formatting or be annoying with excessive structure.

## Design Principles

### 1. Natural Conversational Flow
- Write like you're talking to a friend, not filling out a form
- Use casual but professional language
- Give opinions naturally ("my top pick", "makes sense", "solid option")

### 2. Present Options, Lead with Recommendation
- Always show 2-3 options (not 1, not 5)
- Make a clear recommendation, but let user choose
- Explain why you recommend something briefly

### 3. Keep It Clean and Scannable
- No emoji overload or excessive formatting
- Just the essentials: name, price, key differentiator
- Use white space and simple structure

### 4. Always Ask a Clear Question
- End with one simple question
- Make it easy to respond (natural language, no instructions)
- Don't give multiple options for how to respond

### 5. Don't Be Annoying
- No robotic patterns ("OPTION A", "RECOMMENDED" in caps)
- No over-explaining or listing every detail
- No visual progress bars or ASCII art
- Trust the user to understand without hand-holding

## Agent-Specific Patterns

### Venue Specialist

**Behavior Change:**
- **Before:** Research → pick best match → route to budget
- **After:** Research → present 3 venues → ask preference → route to budget

**Output Pattern:**
```
I found three venues that work well:

The Foundry ($3k) - Modern downtown space, 60 capacity, excellent AV.
This one's my top pick for a corporate event.

Pioneer Square Hall ($2.5k) - Historic charm, 50 capacity, more intimate feel.

Fremont Studios ($3.5k) - Industrial creative space, 75 capacity,
great for something unique.

Which direction appeals to you?
```

**Key elements:**
- Three options, brief descriptions
- Lead with top pick naturally
- Price and key differentiators only
- Simple preference question

**Structured output:**
```json
{
  "summary": "[Natural presentation of 3 venues as shown above]",
  "next_agent": null,
  "user_input_needed": true,
  "user_prompt": "Which direction appeals to you?"
}
```

### Budget Analyst

**Behavior Change:**
- **Before:** Calculate allocation → route to catering
- **After:** Calculate allocation → present breakdown → ask approval → route to catering

**Output Pattern:**
```
For your $5k budget, here's what makes sense:

Venue: $3,000 (60%)
Catering: $1,200 (24%)
Logistics: $500 (10%)
Contingency: $300 (6%)

That's $100 per person, pretty standard for corporate events. Work for you?
```

**Key elements:**
- Clean breakdown with percentages
- Per-person calculation (more relatable)
- One line of context
- Quick yes/no question

**Structured output:**
```json
{
  "summary": "[Natural presentation of budget as shown above]",
  "next_agent": null,
  "user_input_needed": true,
  "user_prompt": "Work for you?"
}
```

### Catering Coordinator

**Behavior Change:**
- **Before:** Research → select menu → route to logistics
- **After:** Research → present 2-3 options → ask preference → route to logistics

**Output Pattern:**
```
Two solid options at $28-30/person:

Herban Feast - Plated service. Herb chicken or vegetarian risotto, sides,
dessert. More formal presentation, includes staff.

Taste Catering - Buffet style. Three proteins, bigger variety, easier for
dietary needs. More casual vibe.

Both handle veg/vegan/GF. Which style fits better?
```

**Key elements:**
- 2-3 caterer options
- Mention service style and food concretely
- Note dietary coverage casually
- Ask about style fit, not just "which one"

**Structured output:**
```json
{
  "summary": "[Natural presentation of catering options as shown above]",
  "next_agent": null,
  "user_input_needed": true,
  "user_prompt": "Which style fits better?"
}
```

### Logistics Manager

**Behavior Change:**
- **Before:** Create timeline → route to coordinator
- **After:** Create timeline → present schedule → ask confirmation → route to coordinator

**Output Pattern:**
```
Here's the timeline for December 15th:

5:00 PM - Setup
6:00 PM - Doors open
6:30 PM - Reception
7:30 PM - Dinner
10:00 PM - Wrap up

Weather looks good - 45°F and clear. I've added it to your calendar and
coordinated with the venue and caterer.

Does this timing work?
```

**Key elements:**
- Clean timeline (no excessive formatting)
- Weather mentioned as reassurance
- Note coordination already done
- Simple confirmation question

**Structured output:**
```json
{
  "summary": "[Natural presentation of timeline as shown above]",
  "next_agent": null,
  "user_input_needed": true,
  "user_prompt": "Does this timing work?"
}
```

## Implementation Changes

### What Changes in Prompts

**Section to modify:** "Intent Detection & Interaction Mode"

**Current default:**
```python
**Autonomous Mode (DEFAULT)**:
- User provided specific constraints
- Language is prescriptive
- **Behavior:** Make expert decisions, proceed to next agent
```

**New default:**
```python
**Collaborative Mode (DEFAULT)**:
- Present 2-3 options based on research
- Lead with recommendation but show alternatives
- **Behavior:** Present options naturally, ask preference, proceed after confirmation
```

**Fallback to Autonomous:** Only if user explicitly says "just pick for me" or "your choice"

### What Stays the Same

- Tool usage mandates (still call web_search, code interpreter, etc.)
- Structured output format (SpecialistOutput model)
- Routing logic (coordinator handles all routing)
- Service-managed threads (conversation history management)

### Tone Guidelines to Add

Add this section to each specialist prompt:

```
## Conversational Guidelines

**Do:**
- Write naturally, like helping a friend plan an event
- Give opinions: "my top pick", "makes sense", "solid option"
- Keep descriptions brief (one line per key point)
- Ask one clear question at the end

**Don't:**
- Use robotic formatting (OPTION A, RECOMMENDED in caps)
- Overload with emoji or ASCII art
- List every possible detail
- Give multiple ways to respond or complex instructions
```

## Expected User Experience

**Before (Autonomous):**
```
User: "Plan a corporate party for 50 people in Seattle, budget $5k"
Venue: [searches] "I selected The Foundry at $3k. Moving to budget."
Budget: [calculates] "Allocated $3k venue, $1.2k catering, $500 logistics. Moving to catering."
Catering: [searches] "Selected Herban Feast buffet at $28/person. Moving to logistics."
Logistics: [creates timeline] "Timeline created. Here's your final event plan."
```

**After (Collaborative):**
```
User: "Plan a corporate party for 50 people in Seattle, budget $5k"
Venue: [searches] "I found three venues that work well: The Foundry ($3k)...,
       Pioneer Square Hall ($2.5k)..., Fremont Studios ($3.5k)...
       Which direction appeals to you?"
User: "The Foundry looks good"
Budget: [calculates] "For your $5k budget, here's what makes sense:
        Venue $3k (60%), Catering $1.2k (24%)... Work for you?"
User: "Yes"
Catering: [searches] "Two solid options: Herban Feast - Plated service...,
          Taste Catering - Buffet style... Which style fits better?"
User: "Buffet"
Logistics: [creates timeline] "Here's the timeline for Dec 15th: 5pm Setup,
           6pm Doors open... Does this timing work?"
User: "Perfect"
Coordinator: [synthesizes] "Here's your complete event plan..."
```

## Success Criteria

1. **User sees options at every decision point** (venue, budget, catering, logistics)
2. **Responses feel natural and conversational**, not robotic
3. **One clear question per interaction**, easy to respond to
4. **No formatting overload** - clean, scannable text
5. **Users feel in control** of their event planning decisions

## Non-Goals

- Don't implement "Autonomous Mode" removal - keep it available if user explicitly requests it
- Don't change coordinator routing logic
- Don't add workflow-level preferences (keep it simple)
- Don't change tool usage or structured output requirements

## Rollback Plan

If collaborative mode creates too many interactions or negative feedback:
- Revert prompts to current autonomous default
- Consider Approach B (confirmation gates) or Approach C (explicit preference) instead
