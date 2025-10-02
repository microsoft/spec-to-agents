# Quickstart Guide: Event Orchestration System (EODS) v0.1

**Date**: 2025-10-02  
**Purpose**: Executable guide for validating EODS implementation through end-to-end scenarios  
**Target Audience**: Developers, QA engineers, stakeholders validating implementation

---

## Prerequisites

### Development Environment
- **Python**: 3.13+ with `uv` package manager
- **Node.js**: 20+ with npm
- **Azure CLI**: Latest version, logged in (`az login`)
- **Azure Resources** (or local alternatives):
  - Azure SQL Database (or SQL Server 2022+ locally)
  - CosmosDB Account (or CosmosDB Emulator)
  - Azure OpenAI deployment (or OpenAI API key for local testing)
- **VS Code Extensions**:
  - Python, Pylance, Azure Tools, REST Client
  - MCPs configured: context7, playwright

### Authentication
All commands assume **Azure CLI credentials** are active. The system uses `AzureCLICredential` for local development.

```powershell
# Verify Azure login
az account show
# If not logged in:
az login
```

---

## Quick Start: 3-Minute Setup

### 1. Clone and Setup Backend
```powershell
# From repository root
cd backend

# Create virtual environment and install dependencies (uv auto-creates venv)
uv pip install -e ".[dev]"

# Set environment variables
$env:AZURE_SQL_SERVER = "your-server.database.windows.net"
$env:AZURE_SQL_DATABASE = "eods-db"
$env:COSMOS_DB_URL = "https://your-account.documents.azure.com:443/"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4"

# Run database migrations
uv run alembic upgrade head

# Start backend API
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend API now running at **http://localhost:8000** (OpenAPI docs: http://localhost:8000/docs)

### 2. Setup Frontend
```powershell
# From repository root
cd frontend

# Install dependencies
npm install

# Set environment variables
$env:VITE_API_BASE_URL = "http://localhost:8000"
$env:VITE_WS_URL = "ws://localhost:8000"

# Start frontend dev server
npm run dev
```

Frontend now running at **http://localhost:5173**

---

## Validation Scenario 1: Small Meetup (Beginner Level)

**Goal**: Validate basic workflow for a 20-person meetup  
**Expected Duration**: 5 minutes  
**Instruction Level**: Beginner

### Step 1: Create EventBrief
```bash
# Using REST Client (VS Code extension) or curl
POST http://localhost:8000/api/event-briefs
Content-Type: application/json

{
  "title": "Developer Meetup Q4 2025",
  "date_range_start": "2025-11-15T18:00:00Z",
  "date_range_end": "2025-11-15T21:00:00Z",
  "audience_size": 20,
  "event_type": "meetup",
  "objectives": "Network local developers, share tech talks on AI/ML",
  "constraints": "Budget $500, downtown location, accessible venue"
}
```

**Expected Response**:
```json
{
  "id": "evt-20251002-developer-meetup",
  "version": 1,
  "lifecycle_state": "Initiate",
  "title": "Developer Meetup Q4 2025",
  ...
  "created_at": "2025-10-02T10:00:00Z"
}
```

**Validation**:
- ✅ EventBrief created with unique ID
- ✅ Lifecycle state is "Initiate"
- ✅ All required fields present

### Step 2: Trigger Agent Orchestration (Beginner Level)
```bash
POST http://localhost:8000/api/agents/orchestrate
Content-Type: application/json

{
  "event_brief_id": "evt-20251002-developer-meetup",
  "instruction_level": "Beginner",
  "target_phase": "Confirm"
}
```

**Expected Response**:
```json
{
  "session_id": "session-001",
  "status": "in_progress",
  "websocket_url": "ws://localhost:8000/ws/agents/sessions/session-001"
}
```

**What Happens**:
1. **Event Planner Agent** (Beginner):
   - Creates basic Requirements
   - Generates simple Timeline with minimum milestones
   - Creates TaskRegister with no resource conflicts
   - **Output**: Timeline with 3 milestones, TaskRegister with 5 tasks

2. **Venue Researcher Agent** (Beginner):
   - Defines simple VenueCriteria (local, capacity 20, budget ≤$300)
   - Searches for venues (5 leads required)
   - Generates VenueShortlist (≥3 candidates within budget)
   - **Output**: VenueShortlist with 3 candidates, VenueScorecard

3. **Budget Analyst Agent** (Beginner):
   - Develops basic CostModel (venue, food, materials)
   - Produces BudgetBaseline with variance ≤5%
   - **Output**: BudgetBaseline $500, CostModel with 3 categories

4. **Logistics Coordinator Agent** (Beginner):
   - Creates operational plan (registration, tech talk, networking)
   - Generates Schedule with no resource conflicts
   - Creates ResourceRoster (AV equipment, tables, chairs)
   - **Output**: LogisticsPlan with 3 workflows, Schedule with 3 sessions

5. **Lifecycle Transitions**:
   - Initiate → Plan (after Requirements + Timeline)
   - Plan → Research (after Timeline quality gate)
   - Research → Budget (after VenueScorecard quality gate)
   - Budget → Logistics (after BudgetDecision quality gate)
   - Logistics → Confirm (after LogisticsPlan quality gate)

### Step 3: Monitor Agent Progress (Real-Time)
**Option A: WebSocket (Recommended)**
```typescript
// Frontend: src/hooks/useAgentSession.ts
const ws = new WebSocket('ws://localhost:8000/ws/agents/sessions/session-001');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Agent: ${update.agent_name}, State: ${update.state}, Message: ${update.message}`);
};
```

**Option B: Polling**
```bash
GET http://localhost:8000/api/agents/sessions/session-001
```

**Expected Updates**:
```json
// Update 1 (Event Planner thinking)
{
  "session_id": "session-001",
  "current_agent": "Event Planner Agent",
  "status": "in_progress",
  "artifacts_generated": [
    {"artifact_type": "Requirements", "artifact_id": "req-evt-20251002-developer-meetup"}
  ]
}

// Update 2 (Venue Researcher responding)
{
  "current_agent": "Venue Researcher Agent",
  "artifacts_generated": [
    {"artifact_type": "VenueShortlist", "artifact_id": "vs-vc-001-001"}
  ]
}

// Final Update
{
  "status": "completed",
  "artifacts_generated": [/* 10+ artifacts */],
  "errors": []
}
```

### Step 4: Verify Artifacts Created
```bash
# Check lifecycle state transitioned to Confirm
GET http://localhost:8000/api/event-briefs/evt-20251002-developer-meetup
# Expected: "lifecycle_state": "Confirm"

# Verify Timeline created
GET http://localhost:8000/api/event-briefs/evt-20251002-developer-meetup/timeline
# Expected: has_milestones: true, has_dependencies: true, has_critical_path: true

# Verify VenueShortlist has ≥3 candidates
GET http://localhost:8000/api/event-briefs/evt-20251002-developer-meetup/venue-shortlist
# Expected: Array with 3+ venues

# Verify BudgetBaseline within ≤5% variance
GET http://localhost:8000/api/event-briefs/evt-20251002-developer-meetup/budget-baseline
# Expected: total_budget: 500, variance ≤ 5%

# Verify LogisticsPlan quality gates passed
GET http://localhost:8000/api/event-briefs/evt-20251002-developer-meetup/logistics-plan
# Expected: workflows_linked_to_tasks: true, contingency_triggers_defined: true
```

### Step 5: Human Approval (Budget Decision)
```bash
# Check pending approvals
GET http://localhost:8000/api/approvals/pending
# Expected: 1 approval for budget_decision

# Approve budget
POST http://localhost:8000/api/approvals/{approvalId}
Content-Type: application/json

{
  "decision": "approved",
  "comments": "Budget looks reasonable for meetup"
}
```

### Step 6: Transition to Execute
```bash
POST http://localhost:8000/api/event-briefs/evt-20251002-developer-meetup/transition
Content-Type: application/json

{
  "target_state": "Execute"
}
```

**Expected**: 200 OK, lifecycle_state updated to "Execute"

### Success Criteria (Beginner Scenario)
- ✅ EventBrief lifecycle: Initiate → Plan → Research → Budget → Logistics → Confirm → Execute
- ✅ Timeline quality gate passed (FR-027): milestones ✓, dependencies ✓, critical path ✓, no orphans ✓
- ✅ VenueShortlist ≥3 candidates within budget (FR-036: budget fit ≥95%)
- ✅ BudgetBaseline variance ≤5% (FR-037)
- ✅ LogisticsPlan quality gate passed (FR-030): workflows linked ✓, triggers defined ✓, owners assigned ✓
- ✅ Human approval recorded for BudgetDecision
- ✅ All artifacts persisted in database (Azure SQL + CosmosDB)

---

## Validation Scenario 2: Mid-Size Conference (Intermediate Level)

**Goal**: Validate multi-vendor coordination and dependency management  
**Expected Duration**: 15 minutes  
**Instruction Level**: Intermediate

### Step 1: Create Conference EventBrief
```bash
POST http://localhost:8000/api/event-briefs
Content-Type: application/json

{
  "title": "AI Summit 2025",
  "date_range_start": "2025-06-01T09:00:00Z",
  "date_range_end": "2025-06-03T17:00:00Z",
  "audience_size": 200,
  "event_type": "conference",
  "objectives": "Showcase enterprise AI solutions, 3-day event with keynotes and workshops",
  "constraints": "Budget $50k, city center venue, multi-track sessions, AV equipment required"
}
```

### Step 2: Trigger Intermediate Orchestration
```bash
POST http://localhost:8000/api/agents/orchestrate
Content-Type: application/json

{
  "event_brief_id": "evt-20251002-ai-summit",
  "instruction_level": "Intermediate",
  "target_phase": "Confirm"
}
```

**What's Different (Intermediate Level)**:
1. **Event Planner Agent**:
   - Integrates resources, dependencies, and risks
   - Timeline includes **critical path analysis**
   - TaskRegister with **dependency chains**
   - RiskRegister with **mitigation strategies**

2. **Venue Researcher Agent**:
   - Multi-criteria venue evaluation (location, capacity, AV, cost, accessibility)
   - VenueScorecard with **weighted criteria** (sum = 1.0)
   - Availability checks for 2+ venues
   - Budget fit ≥95% required

3. **Budget Analyst Agent**:
   - Detailed CostModel with multiple vendors (venue, catering, AV, marketing)
   - Identifies savings ≥10%
   - Variance analysis with **risk reserves ≥90%**

4. **Logistics Coordinator Agent**:
   - Complex workflows (registration, multi-track sessions, vendor coordination)
   - Schedule with **resource conflict detection**
   - ContingencyPlan for vendor cancellations
   - **On-time task rate ≥95%**

### Step 3: Monitor Multi-Agent Collaboration
Watch for **Multi-Agent Pattern** interactions:
- Budget Analyst + Logistics Coordinator negotiate vendor contracts
- Conflicts recorded in **DecisionLog** (CosmosDB)
- ChangeLog tracks budget adjustments

**Query DecisionLog**:
```bash
# CosmosDB query (via API wrapper)
GET http://localhost:8000/api/event-briefs/evt-20251002-ai-summit/decisions
# Expected: Multiple decisions with rationale and alternatives considered
```

### Step 4: Verify Metrics (Intermediate Level)
```bash
# Event Planner Metrics (FR-035)
GET http://localhost:8000/api/metrics/event-briefs/evt-20251002-ai-summit/planner
# Expected:
# - timeline_slippage: ≤10%
# - risk_coverage: ≥90%
# - stakeholder_satisfaction: ≥80%

# Venue Researcher Metrics (FR-036)
GET http://localhost:8000/api/metrics/event-briefs/evt-20251002-ai-summit/venue
# Expected:
# - shortlist_quality_score: ≥0.8
# - budget_fit: ≥95%
# - confirmed_holds: ≥2

# Budget Analyst Metrics (FR-037)
GET http://localhost:8000/api/metrics/event-briefs/evt-20251002-ai-summit/budget
# Expected:
# - budget_variance: ≤5%
# - savings_identified: ≥10%
# - risk_reserve_adequacy: ≥90%

# Logistics Coordinator Metrics (FR-038)
GET http://localhost:8000/api/metrics/event-briefs/evt-20251002-ai-summit/logistics
# Expected:
# - on_time_task_rate: ≥95%
# - incident_resolution_time: ≤15 minutes
# - utilization_balance: ≥80%
```

### Success Criteria (Intermediate Scenario)
- ✅ All Beginner criteria PLUS:
- ✅ Critical path analysis in Timeline
- ✅ Dependency chains in TaskRegister
- ✅ VenueScorecard weights sum to 1.0 (FR-028)
- ✅ Budget savings ≥10% identified
- ✅ Risk reserves ≥90%
- ✅ Multi-agent collaboration logged in DecisionLog
- ✅ All metrics thresholds met (FR-035 to FR-038)

---

## Validation Scenario 3: Large Event (Advanced Level)

**Goal**: Validate strategic optimization and contingency planning  
**Expected Duration**: 30 minutes  
**Instruction Level**: Advanced

### Step 1: Create Large Event EventBrief
```bash
POST http://localhost:8000/api/event-briefs
Content-Type: application/json

{
  "title": "Microsoft Build 2026",
  "date_range_start": "2026-05-20T08:00:00Z",
  "date_range_end": "2026-05-22T18:00:00Z",
  "audience_size": 800,
  "event_type": "conference",
  "objectives": "Global developer conference with keynotes, breakout sessions, hands-on labs, expo",
  "constraints": "Budget $500k, multi-venue coordination, tight timeline (6 months), hybrid event (in-person + virtual)"
}
```

### Step 2: Trigger Advanced Orchestration
```bash
POST http://localhost:8000/api/agents/orchestrate
Content-Type: application/json

{
  "event_brief_id": "evt-20251002-build-2026",
  "instruction_level": "Advanced",
  "target_phase": "Execute"
}
```

**What's Different (Advanced Level)**:
1. **Event Planner Agent**:
   - **Strategic optimization** of timeline with contingency planning
   - **CommunicationsPlan** for multiple stakeholder audiences
   - Risk coverage ≥90% with high-impact scenario planning

2. **Venue Researcher Agent**:
   - Multi-venue coordination (main hall + breakout rooms + expo hall)
   - Negotiation playbook with terms and concessions
   - Availability holds for ≥2 venues with fallback options
   - VenueNegotiationNotes with documented terms

3. **Budget Analyst Agent**:
   - Multi-vendor contracts with cancellation risks
   - Risk-adjusted reserves with **hedging strategies**
   - Contingencies for vendor cancellations

4. **Logistics Coordinator Agent**:
   - High-complexity workflows (registration, 20+ sessions, virtual streaming, expo coordination)
   - **ContingencyPlan** triggers for high-impact incidents
   - Incident resolution time ≤15 minutes
   - Resource utilization balance ≥80%

### Step 3: Test Error Handling (Inject Failures)
```bash
# Simulate venue cancellation
POST http://localhost:8000/api/test/inject-failure
Content-Type: application/json

{
  "event_brief_id": "evt-20251002-build-2026",
  "failure_type": "venue_cancellation",
  "venue_id": "vs-vc-001-001"
}
```

**Expected System Behavior** (FR-032, FR-034):
1. RiskRegister updated with "venue_cancellation" incident
2. ContingencyPlan triggered automatically
3. Event Planner Agent escalates to stakeholders (Human-Agent pattern)
4. DecisionLog records resolution: Activate backup venue from VenueShortlist
5. ChangeLog documents venue change with approvals
6. BudgetDecision updated if cost impact > $1,000

**Verify ContingencyPlan Execution**:
```bash
GET http://localhost:8000/api/event-briefs/evt-20251002-build-2026/contingency-plan/executions
# Expected: 1 execution with scenario="venue_cancellation", status="resolved", resolution_time ≤15 min
```

### Step 4: Test Human Approval Timeout (FR-025)
```bash
# Request budget approval with timeout
POST http://localhost:8000/api/approvals/{approvalId}/test-timeout
Content-Type: application/json

{
  "timeout_minutes": 1
}
```

**Expected System Behavior**:
1. After 1 minute, escalation triggered
2. Backup approver notified (from CommunicationsPlan)
3. Workflow progression blocked until approval received
4. Timeout logged in DecisionLog with escalation path

### Step 5: Verify Advanced Metrics
```bash
# Logistics Coordinator Advanced Metrics (FR-038)
GET http://localhost:8000/api/metrics/event-briefs/evt-20251002-build-2026/logistics
# Expected:
# - on_time_task_rate: ≥95%
# - incident_resolution_time: ≤15 minutes (even with injected failures)
# - utilization_balance: ≥80%
# - contingency_plan_effectiveness: 100% (all triggers resolved)
```

### Success Criteria (Advanced Scenario)
- ✅ All Intermediate criteria PLUS:
- ✅ Multi-venue coordination successful
- ✅ Negotiation playbook generated
- ✅ Contingency plans triggered and resolved within SLA
- ✅ Human approval timeout escalation worked
- ✅ Error handling for injected failures (venue cancellation)
- ✅ Risk coverage ≥90% with high-impact scenarios mitigated
- ✅ Incident resolution time ≤15 minutes across all scenarios

---

## UI Validation (Playwright MCP)

### Visual Regression Tests
```bash
# Run Playwright visual tests via MCP
npx playwright test --config=frontend/tests/visual/playwright.config.ts
```

**Test Cases**:
1. **Event Dashboard Render**:
   - Navigate to `http://localhost:5173/dashboard`
   - Verify EventBrief cards display correctly
   - Compare snapshot: `event-dashboard.png`

2. **Agent Chat UI**:
   - Navigate to `http://localhost:5173/planning/evt-20251002-developer-meetup`
   - Verify real-time agent status updates (thinking, responding, idle)
   - Verify group chat chronological display
   - Compare snapshot: `agent-chat.png`

3. **Approval Workflow**:
   - Navigate to `http://localhost:5173/approvals`
   - Click "Approve" button for pending budget
   - Verify confirmation dialog appears
   - Verify success notification

**Playwright MCP Commands**:
```python
# Via MCP server
playwright_mcp.navigate("http://localhost:5173/dashboard")
playwright_mcp.wait_for_selector("[data-testid='event-list']")
screenshot = playwright_mcp.screenshot(full_page=True)
playwright_mcp.compare_snapshot(screenshot, "event-dashboard.png", threshold=0.02)
```

---

## Performance Validation

### API Response Times (FR-039)
```bash
# Use Apache Bench or k6
ab -n 100 -c 10 http://localhost:8000/api/event-briefs
# Expected: p95 latency < 200ms
```

### Agent Orchestration Latency
```bash
# Measure end-to-end orchestration time (Beginner level)
time curl -X POST http://localhost:8000/api/agents/orchestrate -d '{...}'
# Expected: Total time < 30 seconds for Beginner level
```

### Frontend Performance
```bash
# Run Lighthouse audit
npm run lighthouse
# Expected:
# - First Contentful Paint < 1.5s
# - Time to Interactive < 3.5s
# - Bundle size < 2MB gzipped
```

---

## Troubleshooting

### Issue: "EventBrief not found" after creation
**Cause**: Database connection not established or migration not run  
**Fix**: Check `AZURE_SQL_SERVER` environment variable, run `alembic upgrade head`

### Issue: "Managed Identity authentication failed"
**Cause**: Not logged into Azure CLI or insufficient permissions  
**Fix**: Run `az login`, verify `az account show`, ensure SQL DB Contributor role assigned

### Issue: "Quality gate failed: Timeline missing milestones"
**Cause**: Event Planner Agent did not generate complete Timeline  
**Fix**: Check agent logs, verify instruction level matches event complexity, retry with explicit milestone requirements

### Issue: "WebSocket connection refused"
**Cause**: Backend not running or CORS misconfiguration  
**Fix**: Verify backend at http://localhost:8000/docs, check CORS origins in `main.py`

### Issue: "Playwright MCP tests fail"
**Cause**: Frontend not running or incorrect URL  
**Fix**: Verify frontend at http://localhost:5173, check `VITE_API_BASE_URL` environment variable

---

## Next Steps After Quickstart

1. **Run Full Test Suite**:
   ```bash
   # Backend
   cd backend
   uv run pytest tests/ --cov=src --cov-report=html
   
   # Frontend
   cd frontend
   npm test -- --coverage
   ```

2. **Review Generated Artifacts**:
   - Inspect Azure SQL tables: `event_briefs`, `timelines`, `budgets`
   - Query CosmosDB containers: `decisions`, `changelogs`, `risks`, `traces`

3. **Monitor Application Insights**:
   - Navigate to Azure Portal → Application Insights
   - Review distributed traces for agent orchestration
   - Check custom metrics for agent performance

4. **Extend with Custom Agent**:
   - Follow `/docs/agent-extension-guide.md`
   - Define new agent with instruction sets
   - Add integration tests

---

## Summary Checklist

### Beginner Scenario (Small Meetup)
- [ ] EventBrief created (Initiate state)
- [ ] Agent orchestration completed (Confirm state)
- [ ] Timeline quality gate passed
- [ ] VenueShortlist ≥3 candidates
- [ ] BudgetBaseline variance ≤5%
- [ ] LogisticsPlan quality gate passed
- [ ] Human approval recorded
- [ ] All artifacts in database

### Intermediate Scenario (Mid-Size Conference)
- [ ] All Beginner checklist items
- [ ] Critical path analysis in Timeline
- [ ] VenueScorecard weights sum to 1.0
- [ ] Budget savings ≥10%
- [ ] Risk reserves ≥90%
- [ ] Multi-agent collaboration logged
- [ ] All metrics thresholds met

### Advanced Scenario (Large Event)
- [ ] All Intermediate checklist items
- [ ] Multi-venue coordination
- [ ] Negotiation playbook generated
- [ ] Contingency plan executed successfully
- [ ] Error handling verified (venue cancellation)
- [ ] Human approval timeout escalation tested
- [ ] Incident resolution time ≤15 minutes

### UI & Performance
- [ ] Event dashboard renders correctly
- [ ] Agent chat real-time updates working
- [ ] Approval workflow functional
- [ ] Visual regression tests pass
- [ ] API p95 latency < 200ms
- [ ] Frontend FCP < 1.5s, TTI < 3.5s
- [ ] Bundle size < 2MB gzipped

---

**Quickstart Complete!** ✅

This guide validates the core functionality of the Event Orchestration System across all instruction levels, quality gates, agent interactions, and performance requirements specified in the feature spec.
