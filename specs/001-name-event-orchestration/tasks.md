# Tasks: Event Orchestration System (EODS) v0.1

**Input**: Design documents from `C:\Users\alexlavaee\source\repos\spec-to-agents\specs\001-name-event-orchestration/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
1. TDD-first: write failing tests (contract/unit/integration) before implementation.
2. Implement models → adapters → services → API endpoints → frontend.
3. Integrate observability, Managed Identity, and infra packaging.
4. Polish: performance, docs, migration scripts, PR & constitution checks.

## Phase 3.1: Setup
- [ ] T001 Create Dockerfile stage that installs ODBC Driver 18 and unixODBC for Linux containers
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\Dockerfile`
  - Reason: required to connect pyodbc to Azure SQL in containers
  - Depends: none
  - Example Task agent command: `create file backend/Dockerfile + apt packages msodbcsql18 & unixodbc` (author CI-ready Dockerfile)

- [ ] T002 Add CI job skeleton for Managed Identity / workload-federation (CI pipeline YAML)
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\.github\workflows\ci-managed-identity.yml`
  - Purpose: ensure CI can obtain tokens (no secrets) for Azure-driven gating & MCP calls
  - Depends: none

- [ ] T003 Add observability bootstrap (OpenTelemetry + Prometheus exporter) in backend
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\src\spec2agent\observability.py`
  - Purpose: provide correlation_id linking used by DecisionLog/ChangeLog and services
  - Depends: none

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE IMPLEMENTATION
- [ ] T004 [P] Create contract test for POST `/events` (failing)
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\specs\001-name-event-orchestration\contracts\test_orchestration_contracts.py`
  - Task: Replace skip stub with a failing assertion that validates request/response shape from `orchestration-openapi.yaml` (use OpenAPI schema validation/fixture)
  - Example command: `python -m pytest specs/001-name-event-orchestration/contracts/test_orchestration_contracts.py::test_create_event_contract -q`
  - Depends: T001,T003 (for test infra) optional

- [ ] T005 [P] Create contract test for POST `/events/{eventId}/actions/start` (failing)
  - Path: same contract test file (add separate test function)
  - Reason: enforce lifecycle start behavior contract
  - Depends: T004

- [ ] T006 [P] Add integration scenario tests for S-01..S-03 (failing)
  - Files:
    - `C:\Users\alexlavaee\source\repos\spec-to-agents\specs\001-name-event-orchestration\integration\test_s01_small_meetup.py`
    - `...\integration\test_s02_mid_size.py`
    - `...\integration\test_s03_large_event.py`
  - Each test should drive the system via the API and assert expected artifacts produced (timeline, budgetdecision, postmortem) - tests MUST fail initially
  - Mark: [P] - these are independent scenarios

- [ ] T007 [P] Add failing unit tests for agent instruction_sets semantics (Beginner/Intermediate/Advanced)
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\specs\001-name-event-orchestration\tests\unit\test_instruction_sets.py`
  - Purpose: ensure instruction_set parsing and validation required by AF

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T008 [P] Implement SQLModel/Pydantic `EventBrief` model
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\src\spec2agent\models\event_brief.py`
  - Accepts schema fields from `data-model.md`
  - Depends: T004,T006

- [ ] T009 [P] Implement `Timeline` and `TaskRegister` models
  - Paths:
    - `...\models\timeline.py`
    - `...\models\task_register.py`
  - Depends: T008

- [ ] T010 [P] Implement `BudgetBaseline`, `CostModel`, `DecisionLog`, `ChangeLog` models
  - Path: `...\models\budget.py`, `...\models\logs.py`
  - Ensure version & correlation_id fields included
  - Depends: T008

- [ ] T011 Implement Azure SQL adapter (pyodbc + Managed Identity token flow)
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\src\spec2agent\services\storage\azure_sql_adapter.py`
  - Implement token-based connection retrieval using azure-identity ManagedIdentityCredential/AzureCLICredential for local dev
  - Depends: T008,T001

- [ ] T012 Implement CosmosDB adapter (for flexible artifacts)
  - Path: `...\services\storage\cosmos_adapter.py`
  - Use azure-cosmos SDK and ensure Managed Identity auth
  - Depends: T010

- [ ] T013 Implement Orchestrator service that maps AF lifecycle events to agent instruction_sets and artifact flows
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\src\spec2agent\services\orchestrator.py`
  - Responsibilities: instantiate AF flows, persist artifacts to adapters, write DecisionLog/ChangeLog entries
  - Depends: T008..T012

- [ ] T014 Implement FastAPI endpoints: POST `/events` (create EventBrief + start orchestration)
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\src\spec2agent\api\events.py`
  - Must return 201 with EventResponse schema (per contracts)
  - Depends: T013, T011

- [ ] T015 Implement FastAPI endpoint: POST `/events/{eventId}/actions/start` (trigger lifecycle start)
  - Same file as T014 (sequential, no [P])
  - Depends: T014

## Phase 3.4: Integration & Platform
- [ ] T016 Configure DB migrations and schema versioning tasks (skeleton)
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\migrations\README.md` and migration tool config
  - Purpose: support `version` field and migration scripts
  - Depends: T008..T011

- [ ] T017 Implement Agent-Framework (AF) integration hooks and instruction_set loader
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\src\spec2agent\services\af_integration.py`
  - Ensure instruction_sets loaded from repo, versioned, and included in DecisionLog entries
  - Depends: T013

- [ ] T018 Implement tracing and log correlation integration across services (OpenTelemetry configuration)
  - Path: `...\observability.py` (extend T003), and wire into API middleware
  - Checks: attach correlation_id to DB writes and logs
  - Depends: T003, T011

- [ ] T019 [P] Implement frontend components for approvals and DecisionLog viewing
  - Paths:
    - `C:\Users\alexlavaee\source\repos\spec-to-agents\frontend\src\components\Approvals.tsx`
    - `...\frontend\src\components\DecisionLogView.tsx`
  - Purpose: allow human approvals flows (blocked gating) and show audit trails
  - Depends: T014, T015 (API readiness)

- [ ] T020 [P] Add Playwright visual QA test(s) for the Approvals UI and timeline rendering
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\specs\001-name-event-orchestration\visual\playwright\test_approvals.spec.ts`
  - These should be runnable via the configured Playwright MCP in CI
  - Depends: T019

## Phase 3.5: Polish, Tests, and Validation
- [ ] T021 [P] Implement unit tests for models and storage adapters (failing → implement)
  - Files: `...\tests\unit\test_models.py`, `...\tests\unit\test_storage_adapters.py`
  - Depends: T008..T012

- [ ] T022 [P] Implement unit & integration tests for orchestrator flows (failing → implement)
  - File: `...\tests\integration\test_orchestration_flow.py`
  - Scenario coverage derived from S-01..S-03
  - Depends: T013..T015

- [ ] T023 Add performance smoke tests asserting p95 baselines (documented; fail if not met)
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\tests\perf\test_baselines.py`
  - Targets: single-agent p95 ≤ 2s; multi-agent p95 ≤ 5s; gating checks ≤ 3s
  - Depends: T013, T018

- [ ] T024 Add migration & compatibility checklist and sample migration task
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\backend\migrations\migrate_v0_to_v1.py` (skeleton)
  - Purpose: document steps for schema/ instruction_set migration
  - Depends: T016

- [ ] T025 [P] Update quickstart and developer docs with Managed Identity, ODBC packaging, and local dev notes
  - File: `C:\Users\alexlavaee\source\repos\spec-to-agents\specs\001-name-event-orchestration\quickstart.md` (extend)
  - Depends: T001, T002

- [ ] T026 Add PR template and automated Constitution Check task in CI
  - Path: `.github/PULL_REQUEST_TEMPLATE.md` and CI step that verifies plan/tasks include constitution mapping
  - Purpose: enforce constitution compliance in PRs

- [ ] T027 [P] Update agent instruction_sets & repo agent context files (e.g., `.github/copilot-instructions.md`) to reflect final tech choices and recent changes
  - Path: `C:\Users\alexlavaee\source\repos\spec-to-agents\.github\copilot-instructions.md` (update already scaffolded; ensure kept within markers)
  - Action: run `./.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` after plan changes
  - Depends: T013

## Parallel Execution Examples
- Run contract tests in parallel:
  - T004, T005, T006 can run concurrently: `python -m pytest specs/001-name-event-orchestration/contracts/ -q`
- Implement model files in parallel (each in its own file): T008, T009, T010
- UI work + Playwright tests: T019 and T020 are parallel once API endpoints are available

## Dependency Summary (high-level)
- Setup tasks (T001-T003) → Contract & integration tests (T004-T007)
- Contract/tests (T004-T007) → Models (T008-T010)
- Models → Storage adapters (T011,T012) → Orchestrator (T013)
- Orchestrator → API endpoints (T014,T015) → Frontend (T019)
- Observability (T003,T018) integrated throughout
- Polish tasks (T021-T027) run after core features in place

## Constitution Check (tasks → principles)
- Code Quality: T008-T010 (models), T011-T013 (adapters/services) + linting/CI (T002) satisfy code quality. PR template (T026) enforces checks.
- Testing Standards: T004-T007 + T021-T022 create failing tests first and CI gate (T002) enforces coverage.
- UX Consistency: T019-T020 and Playwright visual QA ensure consistent patterns and accessibility.
- Performance: T023 adds performance smoke tests; T003/T018 provide instrumentation for measurement.
- Observability & Versioning: T003, T016, T018, T024 ensure logs, traces, and migrations are covered.

---
*This tasks.md is generated from plan & design artifacts on 2025-09-26.*
