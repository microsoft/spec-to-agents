# Tasks: Event Orchestration System (EODS) v0.1

**Feature**: Event Orchestration System  
**Input**: Design documents from `specs/001-event-orchestration-system/`  
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

## Tech Stack Summary
- **Backend**: Python 3.13+, FastAPI, Pydantic, SQLModel, agent-framework (AF)
- **Frontend**: TypeScript 5.8+, React 19, Vite 7, Tailwind CSS
- **Database**: Azure SQL (structured), CosmosDB (flexible docs)
- **Auth**: Managed Identity via azure-identity
- **Testing**: pytest, Vitest, Playwright MCP

## Project Structure
```
backend/
  src/spec2agent/
    models/          # SQLModel entities
    services/        # Business logic
    agents/          # Agent Framework definitions
    repositories/    # Data access layer
    api/             # FastAPI routes
  tests/
    contract/        # API contract tests
    integration/     # Multi-component tests
    unit/            # Isolated unit tests
frontend/
  src/
    components/      # React components
    hooks/           # Custom hooks
    services/        # API clients
    pages/           # Route pages
  tests/
    unit/            # Component tests
    visual/          # Playwright visual tests
```

## Execution Flow (main)
```
1. ✓ Loaded plan.md: Python 3.13+, FastAPI, React 19, agent-framework
2. ✓ Loaded data-model.md: 18 SQL entities, 4 CosmosDB documents
3. ✓ Loaded contracts/openapi.yaml: 40+ API endpoints
4. ✓ Loaded quickstart.md: 3 test scenarios (Beginner/Intermediate/Advanced)
5. → Generated 90+ tasks organized by TDD principles
6. → Tests before implementation (contract tests → models → endpoints)
7. → Parallel tasks marked [P] for efficiency
8. → Dependencies documented (blocking relationships)
```

---

## Phase 3.1: Setup (Backend & Frontend Initialization)

### Backend Setup
- [ ] **T001** [P] Create backend project structure: `backend/src/spec2agent/{models,services,agents,repositories,api}`, `backend/tests/{contract,integration,unit}`
- [ ] **T002** [P] Initialize Python project with `pyproject.toml` (FastAPI, SQLModel, Pydantic, agent-framework-core, azure-identity, azure-cosmos, pyodbc dependencies)
- [ ] **T003** [P] Configure Ruff linter and formatter in `backend/pyproject.toml` with strict type checking
- [ ] **T004** [P] Create Alembic migration setup in `backend/alembic/` for Azure SQL schema versioning
- [ ] **T005** [P] Configure pytest with coverage in `backend/pyproject.toml` (pytest-asyncio, pytest-mock, pytest-cov plugins)

### Frontend Setup
- [ ] **T006** [P] Create frontend project structure: `frontend/src/{components,hooks,services,pages}`, `frontend/tests/{unit,visual}`
- [ ] **T007** [P] Initialize Vite project with `package.json` (React 19, TypeScript 5.8+, Tailwind CSS dependencies)
- [ ] **T008** [P] Configure TypeScript strict mode in `frontend/tsconfig.json`
- [ ] **T009** [P] Configure Tailwind CSS in `frontend/tailwind.config.js` with design tokens
- [ ] **T010** [P] Configure Vitest and React Testing Library in `frontend/vite.config.ts`

### Infrastructure Setup
- [ ] **T011** Create Azure SQL connection utility with Managed Identity in `backend/src/spec2agent/repositories/sql_repository.py`
- [ ] **T012** Create CosmosDB connection utility with Managed Identity in `backend/src/spec2agent/repositories/cosmos_repository.py`
- [ ] **T013** [P] Create environment variable validation in `backend/src/spec2agent/config.py` (AZURE_SQL_SERVER, COSMOS_DB_URL, etc.)

---

## Phase 3.2: Tests First - Backend Contract Tests (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### EventBriefs API Contract Tests
- [ ] **T014** [P] Contract test POST /api/event-briefs in `backend/tests/contract/test_event_briefs_post.py`
- [ ] **T015** [P] Contract test GET /api/event-briefs in `backend/tests/contract/test_event_briefs_get.py`
- [ ] **T016** [P] Contract test GET /api/event-briefs/{id} in `backend/tests/contract/test_event_brief_get_by_id.py`
- [ ] **T017** [P] Contract test PATCH /api/event-briefs/{id} in `backend/tests/contract/test_event_brief_patch.py`
- [ ] **T018** [P] Contract test DELETE /api/event-briefs/{id} in `backend/tests/contract/test_event_brief_delete.py`
- [ ] **T019** [P] Contract test POST /api/event-briefs/{id}/transition in `backend/tests/contract/test_event_brief_transition.py`

### Planning API Contract Tests
- [ ] **T020** [P] Contract test POST /api/event-briefs/{id}/requirements in `backend/tests/contract/test_requirements_post.py`
- [ ] **T021** [P] Contract test GET /api/event-briefs/{id}/requirements in `backend/tests/contract/test_requirements_get.py`
- [ ] **T022** [P] Contract test POST /api/event-briefs/{id}/timeline in `backend/tests/contract/test_timeline_post.py`
- [ ] **T023** [P] Contract test GET /api/event-briefs/{id}/timeline in `backend/tests/contract/test_timeline_get.py`
- [ ] **T024** [P] Contract test POST /api/event-briefs/{id}/tasks in `backend/tests/contract/test_task_post.py`
- [ ] **T025** [P] Contract test GET /api/event-briefs/{id}/tasks in `backend/tests/contract/test_task_list.py`

### Venue API Contract Tests
- [ ] **T026** [P] Contract test POST /api/event-briefs/{id}/venue-criteria in `backend/tests/contract/test_venue_criteria_post.py`
- [ ] **T027** [P] Contract test POST /api/event-briefs/{id}/venue-shortlist in `backend/tests/contract/test_venue_shortlist_post.py`
- [ ] **T028** [P] Contract test GET /api/event-briefs/{id}/venue-shortlist in `backend/tests/contract/test_venue_shortlist_get.py`
- [ ] **T029** [P] Contract test POST /api/event-briefs/{id}/venue-scorecard in `backend/tests/contract/test_venue_scorecard_post.py`

### Budget API Contract Tests
- [ ] **T030** [P] Contract test POST /api/event-briefs/{id}/budget-baseline in `backend/tests/contract/test_budget_baseline_post.py`
- [ ] **T031** [P] Contract test POST /api/event-briefs/{id}/cost-model in `backend/tests/contract/test_cost_model_post.py`
- [ ] **T032** [P] Contract test POST /api/event-briefs/{id}/budget-decision in `backend/tests/contract/test_budget_decision_post.py`

### Logistics API Contract Tests
- [ ] **T033** [P] Contract test POST /api/event-briefs/{id}/logistics-plan in `backend/tests/contract/test_logistics_plan_post.py`
- [ ] **T034** [P] Contract test POST /api/event-briefs/{id}/schedule in `backend/tests/contract/test_schedule_post.py`

### Agent & Approval API Contract Tests
- [ ] **T035** [P] Contract test POST /api/agents/orchestrate in `backend/tests/contract/test_agent_orchestrate.py`
- [ ] **T036** [P] Contract test GET /api/agents/sessions/{id} in `backend/tests/contract/test_agent_session_get.py`
- [ ] **T037** [P] Contract test GET /api/approvals/pending in `backend/tests/contract/test_approvals_pending.py`
- [ ] **T038** [P] Contract test POST /api/approvals/{id} in `backend/tests/contract/test_approval_submit.py`

### Integration Tests (User Stories from Quickstart)
- [ ] **T039** [P] Integration test: Small Meetup scenario (Beginner level) in `backend/tests/integration/test_scenario_beginner.py`
- [ ] **T040** [P] Integration test: Mid-Size Conference scenario (Intermediate level) in `backend/tests/integration/test_scenario_intermediate.py`
- [ ] **T041** [P] Integration test: Large Event scenario (Advanced level) in `backend/tests/integration/test_scenario_advanced.py`
- [ ] **T042** [P] Integration test: Lifecycle state transitions with quality gates in `backend/tests/integration/test_lifecycle_transitions.py`
- [ ] **T043** [P] Integration test: Human approval workflow in `backend/tests/integration/test_approval_workflow.py`
- [ ] **T044** [P] Integration test: Error handling (venue cancellation) in `backend/tests/integration/test_error_handling.py`

---

## Phase 3.3: Backend Core Implementation (ONLY after tests are failing)

### Database Models (SQLModel)
- [ ] **T045** [P] EventBrief model in `backend/src/spec2agent/models/event_brief.py`
- [ ] **T046** [P] Requirements model in `backend/src/spec2agent/models/requirements.py`
- [ ] **T047** [P] StakeholderMap model in `backend/src/spec2agent/models/stakeholder_map.py`
- [ ] **T048** [P] Timeline model in `backend/src/spec2agent/models/timeline.py`
- [ ] **T049** [P] TaskRegister model in `backend/src/spec2agent/models/task_register.py`
- [ ] **T050** [P] BudgetBaseline model in `backend/src/spec2agent/models/budget_baseline.py`
- [ ] **T051** [P] CostModel model in `backend/src/spec2agent/models/cost_model.py`
- [ ] **T052** [P] BudgetDecision model in `backend/src/spec2agent/models/budget_decision.py`
- [ ] **T053** [P] VenueCriteria model in `backend/src/spec2agent/models/venue_criteria.py`
- [ ] **T054** [P] VenueLeads model in `backend/src/spec2agent/models/venue_leads.py`
- [ ] **T055** [P] VenueShortlist model in `backend/src/spec2agent/models/venue_shortlist.py`
- [ ] **T056** [P] VenueScorecard model in `backend/src/spec2agent/models/venue_scorecard.py`
- [ ] **T057** [P] LogisticsPlan model in `backend/src/spec2agent/models/logistics_plan.py`
- [ ] **T058** [P] Schedule model in `backend/src/spec2agent/models/schedule.py`
- [ ] **T059** [P] ResourceRoster model in `backend/src/spec2agent/models/resource_roster.py`
- [ ] **T060** [P] ContingencyPlan model in `backend/src/spec2agent/models/contingency_plan.py`
- [ ] **T061** [P] VendorContracts model in `backend/src/spec2agent/models/vendor_contracts.py`
- [ ] **T062** [P] CommunicationsPlan model in `backend/src/spec2agent/models/communications_plan.py`

### CosmosDB Document Schemas
- [ ] **T063** [P] RiskRegister document schema in `backend/src/spec2agent/models/risk_register.py`
- [ ] **T064** [P] ChangeLog document schema in `backend/src/spec2agent/models/change_log.py`
- [ ] **T065** [P] DecisionLog document schema in `backend/src/spec2agent/models/decision_log.py`
- [ ] **T066** [P] AgentTrace document schema in `backend/src/spec2agent/models/agent_trace.py`

### Service Layer
- [ ] **T067** EventBriefService CRUD operations in `backend/src/spec2agent/services/event_brief_service.py`
- [ ] **T068** LifecycleManager with state machine validation in `backend/src/spec2agent/services/lifecycle_manager.py`
- [ ] **T069** RequirementsService in `backend/src/spec2agent/services/requirements_service.py`
- [ ] **T070** TimelineService with quality gate validation in `backend/src/spec2agent/services/timeline_service.py`
- [ ] **T071** TaskRegisterService with dependency validation in `backend/src/spec2agent/services/task_register_service.py`
- [ ] **T072** VenueService with scorecard calculation in `backend/src/spec2agent/services/venue_service.py`
- [ ] **T073** BudgetService with variance analysis in `backend/src/spec2agent/services/budget_service.py`
- [ ] **T074** LogisticsService with conflict detection in `backend/src/spec2agent/services/logistics_service.py`
- [ ] **T075** ApprovalService with human workflow in `backend/src/spec2agent/services/approval_service.py`

### API Endpoints (FastAPI)
- [ ] **T076** EventBriefs CRUD endpoints in `backend/src/spec2agent/api/event_briefs.py`
- [ ] **T077** EventBrief lifecycle transition endpoint in `backend/src/spec2agent/api/event_briefs.py` (extend existing)
- [ ] **T078** Requirements endpoints in `backend/src/spec2agent/api/planning.py`
- [ ] **T079** Timeline endpoints in `backend/src/spec2agent/api/planning.py` (extend)
- [ ] **T080** TaskRegister endpoints in `backend/src/spec2agent/api/planning.py` (extend)
- [ ] **T081** Venue endpoints (criteria, shortlist, scorecard) in `backend/src/spec2agent/api/venues.py`
- [ ] **T082** Budget endpoints (baseline, cost-model, decision) in `backend/src/spec2agent/api/budget.py`
- [ ] **T083** Logistics endpoints (plan, schedule) in `backend/src/spec2agent/api/logistics.py`
- [ ] **T084** Approval endpoints in `backend/src/spec2agent/api/approvals.py`

### Validation & Error Handling
- [ ] **T085** Input validation with Pydantic schemas in `backend/src/spec2agent/api/schemas.py`
- [ ] **T086** Error handling middleware in `backend/src/spec2agent/api/middleware/error_handler.py`
- [ ] **T087** Structured logging with correlation IDs in `backend/src/spec2agent/utils/logging.py`

---

## Phase 3.4: Agent Orchestration & Integration

### Agent Framework Setup
- [ ] **T088** Event Planner Agent definition (Beginner instructions) in `backend/src/spec2agent/agents/event_planner.py`
- [ ] **T089** Event Planner Agent Intermediate instructions in `backend/src/spec2agent/agents/event_planner.py` (extend)
- [ ] **T090** Event Planner Agent Advanced instructions in `backend/src/spec2agent/agents/event_planner.py` (extend)
- [ ] **T091** [P] Venue Researcher Agent definition (all levels) in `backend/src/spec2agent/agents/venue_researcher.py`
- [ ] **T092** [P] Budget Analyst Agent definition (all levels) in `backend/src/spec2agent/agents/budget_analyst.py`
- [ ] **T093** [P] Logistics Coordinator Agent definition (all levels) in `backend/src/spec2agent/agents/logistics_coordinator.py`
- [ ] **T094** Agent orchestration service with GroupChat pattern in `backend/src/spec2agent/services/agent_orchestration_service.py`

### WebSocket Real-Time Status
- [ ] **T095** WebSocket endpoint for agent status in `backend/src/spec2agent/api/websocket.py`
- [ ] **T096** Agent status broadcasting service in `backend/src/spec2agent/services/websocket_service.py`

### Agent API Endpoints
- [ ] **T097** Agent orchestration endpoint (POST /api/agents/orchestrate) in `backend/src/spec2agent/api/agents.py`
- [ ] **T098** Agent session status endpoint in `backend/src/spec2agent/api/agents.py` (extend)
- [ ] **T099** Agent status endpoint in `backend/src/spec2agent/api/agents.py` (extend)

### Database Migrations
- [ ] **T100** Create Alembic migration for all SQL tables in `backend/alembic/versions/001_initial_schema.py`
- [ ] **T101** Create CosmosDB containers setup script in `backend/scripts/setup_cosmos.py`

---

## Phase 3.5: Frontend Implementation

### Core Components
- [ ] **T102** [P] EventBriefCard component in `frontend/src/components/EventBriefCard.tsx`
- [ ] **T103** [P] AgentChat component with real-time updates in `frontend/src/components/AgentChat.tsx`
- [ ] **T104** [P] AgentMessage component (thinking/responding/idle states) in `frontend/src/components/AgentMessage.tsx`
- [ ] **T105** [P] ApprovalModal component in `frontend/src/components/ApprovalModal.tsx`
- [ ] **T106** [P] Button, Card, Modal base components in `frontend/src/components/ui/`

### Custom Hooks
- [ ] **T107** [P] useAgentStatus hook with WebSocket in `frontend/src/hooks/useAgentStatus.ts`
- [ ] **T108** [P] useEventBriefs hook (list/create/update) in `frontend/src/hooks/useEventBriefs.ts`
- [ ] **T109** [P] useApprovals hook in `frontend/src/hooks/useApprovals.ts`

### API Services
- [ ] **T110** [P] EventBriefsAPI client in `frontend/src/services/eventBriefsApi.ts`
- [ ] **T111** [P] AgentsAPI client in `frontend/src/services/agentsApi.ts`
- [ ] **T112** [P] ApprovalsAPI client in `frontend/src/services/approvalsApi.ts`
- [ ] **T113** [P] WebSocket service in `frontend/src/services/websocket.ts`

### Pages
- [ ] **T114** Dashboard page (event list) in `frontend/src/pages/Dashboard.tsx`
- [ ] **T115** Planning page (agent chat UI) in `frontend/src/pages/Planning.tsx`
- [ ] **T116** Approvals page in `frontend/src/pages/Approvals.tsx`

### Frontend Tests
- [ ] **T117** [P] AgentChat component test in `frontend/tests/unit/AgentChat.test.tsx`
- [ ] **T118** [P] useAgentStatus hook test in `frontend/tests/unit/useAgentStatus.test.ts`
- [ ] **T119** [P] EventBriefCard component test in `frontend/tests/unit/EventBriefCard.test.tsx`

---

## Phase 3.6: Visual Regression & E2E Tests (Playwright MCP)

- [ ] **T120** [P] Visual test: Event dashboard renders in `frontend/tests/visual/test_event_dashboard.py`
- [ ] **T121** [P] Visual test: Agent chat UI in `frontend/tests/visual/test_agent_chat.py`
- [ ] **T122** [P] Visual test: Approval workflow in `frontend/tests/visual/test_approval_workflow.py`
- [ ] **T123** [P] E2E test: Create EventBrief and trigger orchestration in `frontend/tests/visual/test_e2e_orchestration.py`

---

## Phase 3.7: Observability & Monitoring

- [ ] **T124** [P] Application Insights integration in `backend/src/spec2agent/utils/telemetry.py`
- [ ] **T125** [P] Custom metrics for agent performance in `backend/src/spec2agent/utils/metrics.py`
- [ ] **T126** [P] Frontend telemetry with Application Insights in `frontend/src/services/telemetry.ts`
- [ ] **T127** Create Application Insights dashboards for SLOs (via Azure Portal or IaC)

---

## Phase 3.8: Polish & Finalization

### Unit Tests
- [ ] **T128** [P] Unit tests for LifecycleManager in `backend/tests/unit/test_lifecycle_manager.py`
- [ ] **T129** [P] Unit tests for validation logic in `backend/tests/unit/test_validation.py`
- [ ] **T130** [P] Unit tests for VenueScorecard calculation in `backend/tests/unit/test_venue_scorecard.py`
- [ ] **T131** [P] Unit tests for BudgetVariance analysis in `backend/tests/unit/test_budget_variance.py`

### Performance & Load Testing
- [ ] **T132** Performance test: API p95 latency < 200ms in `backend/tests/performance/test_api_latency.py`
- [ ] **T133** Load test: 100 concurrent users in `backend/tests/performance/test_load.py`
- [ ] **T134** Frontend performance audit (Lighthouse) in `frontend/scripts/lighthouse.sh`

### Documentation
- [ ] **T135** [P] Update README.md with setup instructions
- [ ] **T136** [P] Create API documentation from OpenAPI spec in `docs/api.md`
- [ ] **T137** [P] Create agent extension guide in `docs/agent-extension-guide.md`
- [ ] **T138** [P] Document Managed Identity setup in `docs/auth-setup.md`

### Code Quality
- [ ] **T139** Remove code duplication (DRY violations)
- [ ] **T140** Run Ruff linter and fix all errors
- [ ] **T141** Run TypeScript strict checks and fix all errors
- [ ] **T142** Verify test coverage (backend ≥80%, frontend ≥75%)

### Manual Testing
- [ ] **T143** Execute manual testing checklist from `specs/001-event-orchestration-system/quickstart.md`

---

## Dependencies & Blocking Relationships

### Critical Path
```
Setup (T001-T013) → Contract Tests (T014-T044) → Models (T045-T066) → Services (T067-T075) 
→ API Endpoints (T076-T084) → Agents (T088-T094) → Frontend (T102-T116) → Polish (T128-T143)
```

### Specific Dependencies
- **T014-T044** MUST complete and FAIL before starting T045
- **T045-T066** (Models) block T067-T075 (Services)
- **T067-T075** (Services) block T076-T084 (API Endpoints)
- **T088-T094** (Agents) require T067 (EventBriefService) to be complete
- **T097-T099** (Agent API) require T094 (Orchestration Service) to be complete
- **T100-T101** (Migrations) require T045-T066 (Models) to be complete
- **T110-T113** (Frontend API clients) require T076-T084 (Backend APIs) to be complete
- **T114-T116** (Pages) require T102-T109 (Components/Hooks) to be complete
- **T120-T123** (Visual tests) require T114-T116 (Pages) to be complete
- **T143** (Manual testing) requires all implementation tasks to be complete

### Parallel Execution Groups
```
# Setup Phase (all independent)
Task T001, T002, T003, T004, T005, T006, T007, T008, T009, T010

# Contract Tests (all independent - different test files)
Task T014-T038 (25 tests can run in parallel)

# Integration Tests (all independent)
Task T039-T044 (6 tests can run in parallel)

# Models (all independent - different files)
Task T045-T066 (22 models can run in parallel)

# Visual Tests (all independent)
Task T120-T123 (4 tests can run in parallel)

# Documentation (all independent)
Task T135-T138 (4 docs can run in parallel)
```

---

## Validation Checklist
*GATE: Verify before marking feature complete*

- [ ] All 40+ API endpoints have contract tests
- [ ] All 22 entities have SQLModel/document definitions
- [ ] All 4 agents have instruction sets (Beginner, Intermediate, Advanced)
- [ ] All 3 quickstart scenarios pass integration tests
- [ ] All quality gates (FR-027 to FR-030) implemented and tested
- [ ] Human approval workflow (FR-025) fully functional
- [ ] WebSocket real-time updates working
- [ ] Visual regression tests pass (snapshot comparison)
- [ ] Performance requirements met (p95 < 200ms, FCP < 1.5s)
- [ ] Code coverage thresholds met (backend 80%, frontend 75%)
- [ ] All tests pass (contract, integration, unit, visual, performance)
- [ ] Managed Identity authentication working (no secrets in code)
- [ ] Application Insights telemetry flowing
- [ ] Documentation complete (README, API docs, agent guide)

---

## Notes for LLM Execution

### TDD Workflow
1. Write contract test (it MUST fail)
2. Implement minimum code to pass test
3. Refactor for quality
4. Commit

### Parallel Execution Best Practices
- [P] tasks are truly independent (different files, no shared state)
- Launch parallel tasks in batches to manage context window
- Monitor test failures collectively before proceeding

### Common Pitfalls to Avoid
- ❌ Don't implement before tests are written and failing
- ❌ Don't mark [P] if tasks modify the same file
- ❌ Don't skip quality gates validation
- ❌ Don't forget to link workflows to TaskRegister (FR-030)
- ❌ Don't skip human approval for budget/venue/vendor decisions (FR-025)

### File Path Conventions
- Backend models: `backend/src/spec2agent/models/{entity_name}.py`
- Backend services: `backend/src/spec2agent/services/{service_name}_service.py`
- Backend API: `backend/src/spec2agent/api/{resource_name}.py`
- Backend tests: `backend/tests/{contract|integration|unit}/test_{feature}.py`
- Frontend components: `frontend/src/components/{ComponentName}.tsx`
- Frontend hooks: `frontend/src/hooks/use{HookName}.ts`
- Frontend tests: `frontend/tests/{unit|visual}/test_{feature}.{tsx|py}`

---

**Total Tasks**: 143  
**Estimated Effort**: 3-4 weeks for full implementation (with 2-3 developers)  
**Critical Path Duration**: ~2 weeks (assuming serial execution of blocking tasks)  
**Parallelization Potential**: ~60% of tasks can run in parallel

**Status**: ✅ Tasks generated and ready for execution
