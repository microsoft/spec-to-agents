# Quickstart - Multi-Agent Event Planning System

**Date**: 2025-10-04  
**Purpose**: Manual testing scenario and acceptance validation

## Prerequisites

1. **Backend Running**:
   ```powershell
   cd backend
   uv run app/main.py
   ```
   Verify: `http://127.0.0.1:8080/v1/health` returns `{"status": "healthy"}`

2. **Frontend Running**:
   ```powershell
   cd frontend
   npm run dev
   ```
   Verify: `http://localhost:5173` loads

3. **Azure Resources** (for full integration):
   - Azure OpenAI endpoint configured
   - Cosmos DB provisioned
   - Managed identity credentials (`az login` for local)

4. **Running Tests** (optional for validation):
   
   **Backend Tests**:
   ```powershell
   cd backend
   
   # Run all tests
   uv run pytest
   
   # Run specific test suites
   uv run pytest tests/unit/
   uv run pytest tests/contract/
   uv run pytest tests/integration/
   
   # Run with coverage
   uv run pytest --cov=src --cov-report=html
   ```
   
   **Frontend Tests**:
   ```powershell
   cd frontend
   
   # Run tests in watch mode
   npm test
   
   # Run tests once (CI mode)
   npm run test:ci
   
   # Run with coverage
   npm run test:coverage
   
   # Run with UI
   npm run test:ui
   ```

---

## Scenario 1: Basic Event Planning Flow

**Acceptance Criteria**: FR-001, FR-002, FR-003, FR-004

**User Story**: Plan a company holiday party with complete information provided.

### Steps:

1. **Open Application**
   - Navigate to `http://localhost:5173`
   - Verify: Application loads with event planning interface

2. **Submit Event Request**
   - Input text: "I need to plan a company holiday party for 100 employees in Seattle in December 2025, budget is $10,000"
   - Click "Start Planning"
   - **Expected**:
     - Session created (201 response)
     - Session ID displayed in UI
     - Workflow status panel shows "Initialization" phase
     - Event Coordinator agent status: "Active"

3. **Observe Agent Orchestration**
   - **Expected sequence**:
     1. Event Coordinator: "Active" → "Completed" (~5-10s)
     2. Budget Analyst: "Pending" → "Active" → "Completed" (~10-15s)
     3. Venue Specialist + Catering Coordinator: Both "Active" simultaneously (~30-45s)
     4. Logistics Manager: "Pending" → "Active" → "Completed" (~15-20s)
   
   - **Verify**:
     - Real-time status updates (<1s latency)
     - Workflow phase transitions: Initialization → Budget Analysis → Parallel Research → Logistics Planning → Completed
     - Visual workflow diagram updates with agent status colors

4. **Review Budget Allocation**
   - **Expected output** (Budget Analyst):
     ```
     Total Budget: $10,000
     - Venue: $4,000 (40%)
     - Catering: $3,500 (35%)
     - Logistics: $1,500 (15%)
     - Contingency: $1,000 (10%)
     
     Justification: Balanced allocation for corporate event...
     ```
   - **Verify**: Sum equals total budget

5. **Review Venue Recommendations**
   - **Expected output** (Venue Specialist):
     - 3-5 venue options
     - Each with: name, location, capacity, cost, amenities
     - Match score 0-100
     - Pros/cons listed
   - **Verify**: 
     - All venues within budget allocation
     - Capacity >= 100 attendees
     - Located in Seattle area

6. **Review Catering Options**
   - **Expected output** (Catering Coordinator):
     - 2-3 catering proposals
     - Menu style (buffet, plated, cocktail)
     - Cost per person and total cost
     - Dietary accommodations available
   - **Verify**: Total cost within budget allocation

7. **Review Event Timeline**
   - **Expected output** (Logistics Manager):
     - Timeline with milestones (setup, arrival, event, teardown)
     - Total duration estimate
     - Responsible parties identified
   - **Verify**: Chronological order, realistic timeframes

8. **Verify Complete Plan**
   - Click "View Full Plan"
   - **Expected**: All sections populated (budget, venues, catering, timeline)
   - Download/save plan functionality works

**Pass Criteria**:
- ✅ Workflow completes in <2 minutes
- ✅ All 5 agents execute successfully
- ✅ Complete event plan generated
- ✅ No errors in console or UI

---

## Scenario 2: User Handoff for Clarification

**Acceptance Criteria**: FR-011, FR-012, FR-013

**User Story**: Agent needs clarification mid-workflow, system pauses and asks user.

### Steps:

1. **Submit Incomplete Request**
   - Input text: "Plan a wedding for 150 people in Portland, budget $20,000"
   - Click "Start Planning"

2. **Wait for Handoff**
   - **Expected**: Catering Coordinator pauses and asks:
     ```
     Question: What dietary restrictions should we accommodate?
     Context: To suggest appropriate catering options for your guests
     Options: Vegetarian, Vegan, Gluten-free, None, Other
     ```
   - **Verify**:
     - Workflow status: "User Handoff"
     - Catering Coordinator status: "Waiting"
     - Dialog appears with question and options
     - Other agents paused

3. **Answer Question**
   - Select: "Vegetarian" and "Gluten-free"
   - Click "Submit Answer"
   - **Expected**:
     - Dialog closes
     - Workflow resumes immediately
     - Catering Coordinator status: "Active" → "Completed"
     - Workflow status: Returns to "Parallel Research"

4. **Verify Answer Used**
   - Review catering options
   - **Expected**: All proposals include vegetarian and gluten-free options
   - Menu items reflect dietary accommodations

**Pass Criteria**:
- ✅ Question displayed with clear context
- ✅ Workflow pauses during handoff
- ✅ Answer captured and used in agent output
- ✅ Workflow resumes automatically after response

---

## Scenario 3: Modify Requirements Mid-Planning

**Acceptance Criteria**: FR-014

**User Story**: User changes budget after initial agents complete.

### Steps:

1. **Start Normal Planning**
   - Input: "Corporate event, 80 people, Denver, $8,000 budget"
   - Wait for Budget Analyst to complete

2. **Modify Budget**
   - Click "Modify Requirements"
   - Change budget to $12,000
   - Click "Update"
   - **Expected**:
     - API PATCH request to `/v1/sessions/{id}/request`
     - Confirmation: "Budget updated. Re-orchestrating affected agents..."
     - Affected agents: Budget Analyst, Venue Specialist, Catering Coordinator

3. **Observe Re-Orchestration**
   - **Expected**:
     - Budget Analyst: Re-runs with new budget
     - Venue/Catering agents: Reset and re-run
     - Logistics Manager: Preserved (unaffected)
     - New budget allocation displayed
     - Updated venue/catering options

4. **Verify Plan Updated**
   - Compare original vs. updated recommendations
   - **Expected**: Higher-budget options now included

**Pass Criteria**:
- ✅ Modification triggers selective re-orchestration
- ✅ Only affected agents re-run
- ✅ Unaffected outputs preserved
- ✅ Updated plan reflects new requirements

---

## Scenario 4: Session Resumption After Disconnect

**Acceptance Criteria**: FR-022, NFR-009

**User Story**: User disconnects mid-planning, returns within 24 hours.

### Steps:

1. **Start Planning Session**
   - Input: "Birthday party, 50 people, Austin, $5,000"
   - Note session ID from UI
   - Wait for Budget Analyst to complete

2. **Simulate Disconnect**
   - Close browser tab (or refresh page)
   - Wait 30 seconds

3. **Reconnect**
   - Open new browser tab
   - Navigate to `http://localhost:5173`
   - **Expected**: "Resume Previous Session?" prompt with session ID
   - Click "Resume"

4. **Verify State Restored**
   - **Expected**:
     - Original event request displayed
     - Budget allocation already completed
     - Venue/Catering agents resume from "Pending" state
     - Conversation history intact
     - Workflow continues where it left off

5. **Complete Planning**
   - Verify workflow completes normally
   - Final plan includes all outputs

**Pass Criteria**:
- ✅ Session state persisted to Cosmos DB
- ✅ Resumption within 24 hours succeeds
- ✅ No data loss (conversation, completed agents)
- ✅ Workflow continues seamlessly

---

## Scenario 5: Concurrent User Sessions

**Acceptance Criteria**: NFR-004

**User Story**: Multiple users plan events simultaneously without interference.

### Steps:

1. **Open Two Browser Windows** (simulate 2 users)

2. **User 1 Planning**
   - Window 1: Start planning "Conference, 200 people, Boston, $30,000"
   - Note session ID: `session-A`

3. **User 2 Planning** (concurrent)
   - Window 2: Start planning "Team offsite, 25 people, San Francisco, $3,000"
   - Note session ID: `session-B`

4. **Verify Isolation**
   - **Window 1**: Should only see session-A data
   - **Window 2**: Should only see session-B data
   - No cross-contamination of agent outputs

5. **Complete Both**
   - Both workflows complete independently
   - Each produces correct plan for their event

6. **Verify Database**
   - Query Cosmos DB: Two distinct sessions with different partition keys
   - No shared state between sessions

**Pass Criteria**:
- ✅ 10 concurrent sessions supported (test with 10 browser windows)
- ✅ Complete isolation between sessions
- ✅ No performance degradation with multiple users
- ✅ All sessions complete successfully

---

## Scenario 6: Error Handling and Partial Results

**Acceptance Criteria**: FR-018

**User Story**: One agent fails, system provides partial results.

### Steps:

1. **Simulate Agent Failure**
   - Start planning: "Gala, 300 people, Chicago, $50,000"
   - **Test approach**: Mock Venue Specialist to throw exception

2. **Observe Error Handling**
   - **Expected**:
     - Venue Specialist status: "Failed"
     - Error notification: "Venue Specialist encountered an error. Continuing with other agents..."
     - Catering Coordinator and Logistics Manager continue normally
     - Workflow status: "Completed (Partial)"

3. **Review Partial Plan**
   - **Expected**:
     - Budget allocation: ✅ Present
     - Venue recommendations: ❌ Missing (with explanation)
     - Catering options: ✅ Present
     - Event timeline: ✅ Present (with note about missing venue details)

4. **Retry Option**
   - Click "Retry Failed Agent"
   - **Expected**: Venue Specialist re-runs, fills in missing data

**Pass Criteria**:
- ✅ Single agent failure doesn't halt entire workflow
- ✅ Partial results displayed with clear indication of what's missing
- ✅ Retry mechanism available
- ✅ User informed of issue with actionable message

---

## Performance Validation

**Acceptance Criteria**: NFR-001, NFR-002, NFR-003

### Metrics to Measure:

1. **API Response Time**
   - POST `/v1/sessions`: <500ms to acknowledge
   - GET `/v1/sessions/{id}`: <200ms

2. **Workflow Initiation**
   - Time from POST to first agent active: <3 seconds

3. **Complete Workflow**
   - Total time for simple request (all info provided): <2 minutes
   - Measure: From "Start Planning" to "Workflow Completed"

4. **UI Update Latency**
   - Agent status change to UI update: <1 second
   - Test: Monitor SSE event timestamp vs. UI render

5. **Frontend Performance**
   - Initial page load: <3 seconds
   - Bundle size: <300KB gzipped
   - Check: Vite build output size

### Measurement Tools:
- Browser DevTools Network tab
- FastAPI middleware request timing
- `console.time()` in frontend
- Lighthouse performance audit

**Pass Criteria**:
- ✅ All metrics within constitutional targets
- ✅ No performance regressions vs. baseline

---

## Accessibility Validation

**Acceptance Criteria**: Constitution III (WCAG 2.1 AA)

### Checks:

1. **Keyboard Navigation**
   - Tab through all interactive elements
   - Enter/Space activates buttons
   - Esc closes dialogs

2. **Screen Reader**
   - NVDA/JAWS announces agent status changes
   - Form labels properly associated
   - Error messages read aloud

3. **Color Contrast**
   - Text contrast ratio ≥ 4.5:1
   - Agent status colors distinguishable

4. **ARIA Labels**
   - Agent status regions have aria-live="polite"
   - Workflow diagram has descriptive labels

**Pass Criteria**:
- ✅ Full keyboard accessibility
- ✅ Screen reader compatible
- ✅ WCAG 2.1 AA compliant (automated + manual test)

---

## Troubleshooting

### Issue: Workflow stuck in "Active" state
- **Cause**: Agent timeout or OpenAI API error
- **Check**: Backend logs for exception
- **Fix**: Implement 30s timeout per agent

### Issue: SSE connection drops
- **Cause**: Network interruption or server restart
- **Check**: Browser console for EventSource errors
- **Fix**: Implement automatic reconnection with exponential backoff

### Issue: Cosmos DB connection failed
- **Cause**: Managed identity not configured
- **Check**: `az account show` for active login
- **Fix**: Run `az login` or verify managed identity RBAC

### Issue: Agent outputs missing
- **Cause**: Pydantic validation error in response parsing
- **Check**: Backend logs for validation errors
- **Fix**: Update Pydantic schemas to match agent output format

---

## Acceptance Checklist

- [ ] Scenario 1: Basic planning flow ✅
- [ ] Scenario 2: User handoff ✅
- [ ] Scenario 3: Modify requirements ✅
- [ ] Scenario 4: Session resumption ✅
- [ ] Scenario 5: Concurrent sessions ✅
- [ ] Scenario 6: Error handling ✅
- [ ] Performance metrics within targets ✅
- [ ] Accessibility WCAG 2.1 AA ✅
- [ ] All 22 functional requirements validated ✅
- [ ] All 9 non-functional requirements validated ✅
- [ ] Backend test suite passes (`uv run pytest`) ✅
- [ ] Frontend test suite passes (`npm test`) ✅
- [ ] Test coverage meets targets (80%+ unit, 100% contract/integration) ✅

**Status**: Ready for manual testing after implementation.
