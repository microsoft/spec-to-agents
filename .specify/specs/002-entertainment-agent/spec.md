# Feature Specification: Entertainment Agent

## Overview

Add an **Entertainment Agent** to the event planning workflow that researches and recommends entertainment options (speakers, performers, activities) based on event type, audience size, venue capabilities, and budget constraints.

## User Stories

### US-1: Entertainment Research
**As a** event planner  
**I want** the system to research entertainment options automatically  
**So that** I can select appropriate entertainment that fits my event type and budget  

**Acceptance Criteria:**
- Agent searches for entertainment options based on event type (corporate, social, conference)
- Agent considers audience size and demographics
- Agent respects budget allocation from Budget Agent
- Agent checks venue capabilities (stage, A/V equipment) from Venue Agent
- Agent provides 3-5 concrete recommendations with costs

**Example Interaction:**
```
User: "Plan a corporate party for 50 people, $5k budget, at Seattle downtown venue"

Workflow:
1. Venue Agent → Recommends venue with stage + A/V
2. Budget Agent → Allocates $500 for entertainment (10% of budget)
3. Entertainment Agent → Searches for options:
   - Local jazz band ($400)
   - Professional DJ ($350)
   - Team trivia host ($250)
4. Entertainment Agent → Recommends jazz band (fits budget, venue has stage)
```

### US-2: Entertainment Coordination
**As a** event planner  
**I want** entertainment to integrate with logistics and catering  
**So that** I have a cohesive event schedule  

**Acceptance Criteria:**
- Agent coordinates performance timing with Logistics Agent
- Agent considers catering schedule (e.g., entertainment during dinner vs. after)
- Agent validates venue setup requirements (stage, sound system)
- Agent outputs structured recommendations with timing

**Example Interaction:**
```
Logistics Agent: "Event 6-10pm, dinner 7-8pm"
Entertainment Agent: 
- Background jazz during dinner (7-8pm)
- Interactive trivia after dinner (8:30-9:30pm)
```

### US-3: Structured Output Format
**As a** workflow developer  
**I want** entertainment recommendations in structured JSON  
**So that** the coordinator can synthesize a complete event plan  

**Acceptance Criteria:**
- Uses `SpecialistOutput` Pydantic model
- Includes `summary`, `next_agent`, `user_input_needed`, `user_prompt` fields
- Returns `next_agent=None` when complete (routes back to coordinator)
- Optionally requests user input for selection between options

**Example Output:**
```json
{
  "summary": "Recommended 3 entertainment options: Jazz band ($400), DJ ($350), Trivia host ($250). Jazz band fits budget and venue has stage.",
  "next_agent": null,
  "user_input_needed": false,
  "user_prompt": null
}
```

## Functional Requirements

### FR-1: Web Search Integration
- Agent uses `web_search` tool (same as Venue/Catering agents)
- Searches for local entertainment vendors
- Queries include location, event type, and audience size

### FR-2: Budget Awareness
- Agent receives budget allocation from Budget Agent via workflow context
- Stays within allocated entertainment budget
- Provides cost breakdown for each recommendation

### FR-3: Venue Compatibility
- Agent receives venue details from Venue Agent via workflow context
- Validates venue has required equipment (stage, sound system, microphone)
- Adjusts recommendations based on venue capabilities

### FR-4: Timing Coordination
- Agent receives event schedule from Logistics Agent via workflow context
- Proposes entertainment timing that doesn't conflict with meals or key activities
- Suggests duration for each entertainment option

### FR-5: MCP Tool Support
- Agent conditionally includes `sequential-thinking` MCP tool
- Uses MCP for complex reasoning (e.g., comparing entertainment options)

## Non-Functional Requirements

### NFR-1: Performance
- Web searches complete within 10 seconds
- Agent response time < 30 seconds total

### NFR-2: Error Handling
- Gracefully handle no search results (suggest generic options)
- Handle missing budget allocation (use $300-500 default)
- Handle missing venue details (assume basic A/V available)

### NFR-3: Code Quality
- Follows existing agent creation pattern (`agents/entertainment_specialist.py`)
- Includes functional test coverage (`tests/functional/test_entertainment_agent.py`)
- Uses dependency injection with `@inject` decorator
- Matches code style of existing agents

## Out of Scope

- ❌ Direct booking/payment integration
- ❌ Contract negotiation with vendors
- ❌ Entertainment vendor management database
- ❌ Custom entertainment search API (use generic web search)
- ❌ User reviews or ratings integration

## Dependencies

### Internal Dependencies
- Budget Agent must run before Entertainment Agent (needs budget allocation)
- Venue Agent must run before Entertainment Agent (needs venue capabilities)
- Logistics Agent should run before Entertainment Agent (for timing coordination)

### External Dependencies
- `web_search` tool (already implemented)
- `SpecialistOutput` Pydantic model (already implemented)
- `sequential-thinking` MCP tool (optional, already implemented)

## Success Metrics

- ✅ Agent integrates into workflow with correct routing
- ✅ Entertainment recommendations respect budget constraints
- ✅ Recommendations match venue capabilities
- ✅ Structured output parses correctly in coordinator
- ✅ Functional tests pass in console mode
- ✅ DevUI displays entertainment recommendations

## Review & Acceptance Checklist

- [ ] User stories have clear acceptance criteria
- [ ] Functional requirements are testable
- [ ] Non-functional requirements are measurable
- [ ] Out-of-scope items are explicitly stated
- [ ] Dependencies are identified and validated
- [ ] Success metrics are defined
- [ ] Code follows existing patterns
- [ ] Tests cover happy path and error cases

---

**Feature ID**: 002-entertainment-agent  
**Created**: 2025-01-11  
**Status**: Ready for Planning