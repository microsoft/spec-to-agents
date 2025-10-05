
# Implementation Plan: Multi-Agent Event Planning System

**Branch**: `001-af-concurrent-workflows` | **Date**: 2025-10-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-af-concurrent-workflows/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Build a multi-agent event planning system that orchestrates five specialized AI agents (Event Coordinator, Budget Analyst, Venue Specialist, Catering Coordinator, and Logistics Manager) to help users plan comprehensive events through natural language interaction. The system supports concurrent agent execution, user-handoff for clarifications, real-time progress visualization, and persistent session management with 24-hour resumption capability.

**Technical Approach**: Web application with FastAPI backend using Microsoft Agent Framework for agent orchestration, Cosmos DB for session persistence, and React/Vite frontend with real-time workflow visualization. Agents execute concurrently where possible with dependency-based ordering. All Azure resources use managed identity authentication.

## Technical Context

**Language/Version**: 
- Backend: Python 3.13+
- Frontend: TypeScript 5.8+ with React 19

**Primary Dependencies**:
- Backend: FastAPI (ASGI server), agent-framework-core, agent-framework-azure-ai, azure-cosmos, azure-identity, azure-openai, pydantic, uvicorn
- Frontend: Vite, React 19, TypeScript, Tailwind CSS 4, shadcn/ui (Radix UI), @xyflow/react, lucide-react, next-themes

**Package Management**:
- Backend: `uv` (NOT pip or poetry)
- Frontend: `npm`

**Storage**: Azure Cosmos DB (NoSQL) for:
- Conversation history and session state
- Event plan drafts and agent outputs
- Workflow execution state and agent status

**Testing**: 
- Backend: pytest with async support (run via `uv run pytest`), contract tests for all endpoints, pytest-asyncio for async tests, pytest-mock for mocking
- Frontend: Vitest + React Testing Library (run via `npm test`), component tests, integration tests
- Integration: End-to-end user scenario tests combining backend + frontend
- Commands:
  - Backend: `cd backend && uv run pytest` or `uv run pytest tests/` for specific directories
  - Frontend: `cd frontend && npm test` (watch mode) or `npm run test:ci` (single run)
  - Coverage: `uv run pytest --cov=src` (backend), `npm run test:coverage` (frontend)

**Target Platform**: Azure Container Apps (via AZD templates)

**Authentication**: Managed Identity ONLY
- Local dev: `AzureCliCredential` 
- Cloud: `ManagedIdentityCredential`
- NO API keys or secrets in code

**Project Type**: Web application (frontend + backend)

**Performance Goals**:
- API response: <200ms p95 latency
- Workflow initiation: <3s to start first agent
- UI updates: <1s latency for real-time status
- Complete workflow: <2 minutes for standard requests
- Frontend bundle: <300KB gzipped

**Constraints**:
- 10 concurrent user sessions
- 500 attendees maximum per event
- 24-hour session persistence window
- 95% uptime for demo/PoC
- WCAG 2.1 AA accessibility compliance

**Scale/Scope**:
- Demo/PoC focused
- 5 specialized agents with configurable instructions
- 10 concurrent planning sessions
- Real-time workflow visualization with agent status tracking
- Multi-step user handoff with context preservation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Quality & Consistency ✅
- ✅ Backend: Ruff configured (line 88, imports sorted, type hints required per pyproject.toml)
- ✅ Frontend: ESLint + TypeScript strict mode configured
- ✅ Pydantic models for all data structures = type safety + validation
- ✅ Agent Framework provides structured agent patterns (no duplication)

### II. Testing Standards (TDD Mandatory) ✅
- ✅ Contract tests for all API endpoints (100% coverage target)
- ✅ Integration tests for all 6 acceptance scenarios
- ✅ Unit tests for business logic (80%+ target)
- ✅ Performance tests: <200ms API, <3s workflow start, <1s UI updates
- ✅ pytest configured for backend (async support, mocking, coverage)
- ✅ npm test configured for frontend (Vitest + React Testing Library)
- ✅ Test commands: `uv run pytest` (backend), `npm test` (frontend)

### III. User Experience Consistency ✅
- ✅ Radix UI + Tailwind CSS already in use (shadcn/ui components)
- ✅ Dark/light theme support via next-themes (existing)
- ✅ Lucide React icons for consistency
- ✅ Real-time agent status visualization with @xyflow/react
- ✅ Loading states for >300ms operations
- ✅ Actionable error messages (no stack traces to users)
- ✅ WCAG 2.1 AA compliance required

### IV. Performance Requirements ✅
- ✅ API latency target: <200ms p95 (measured via middleware)
- ✅ Frontend bundle: <300KB gzipped (Vite code-splitting)
- ✅ Cosmos DB: Connection pooling, indexed queries
- ✅ Agent Framework: Concurrent execution support built-in
- ✅ Resource management: Async context managers (Python), useEffect cleanup (React)

**Initial Assessment**: PASS - No constitutional violations identified. Architecture aligns with all four core principles.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

**Structure Decision**: Web application with separate backend and frontend. Extends existing structure with event planning agents and workflows.

```
backend/
├── app/
│   └── main.py                          # FastAPI server entry point (EXTEND)
├── src/
│   └── spec2agent/
│       ├── agents/
│       │   ├── event_coordinator.py     # NEW: Event Coordinator agent
│       │   ├── budget_analyst.py        # NEW: Budget Analyst agent
│       │   ├── venue_specialist.py      # NEW: Venue Specialist agent
│       │   ├── catering_coordinator.py  # NEW: Catering Coordinator agent
│       │   └── logistics_manager.py     # NEW: Logistics Manager agent
│       ├── workflows/
│       │   └── event_planning.py        # NEW: Event planning workflow orchestration
│       ├── api/
│       │   ├── _server.py               # EXISTING: FastAPI app (extend)
│       │   ├── _session.py              # EXISTING: Session management (extend)
│       │   └── models/
│       │       ├── event_models.py      # NEW: Event planning Pydantic models
│       │       └── workflow_models.py   # NEW: Workflow state models
│       └── storage/
│           ├── __init__.py              # NEW: Storage module
│           ├── cosmos_client.py         # NEW: Cosmos DB client with managed identity
│           └── session_repository.py    # NEW: Session persistence layer
└── tests/
    ├── contract/
    │   ├── test_event_planning_api.py   # NEW: API contract tests
    │   └── test_agent_endpoints.py      # NEW: Agent-specific endpoint tests
    ├── integration/
    │   ├── test_event_planning_flow.py  # NEW: End-to-end scenario tests
    │   └── test_user_handoff.py         # NEW: User interaction tests
    └── unit/
        ├── test_agents.py               # NEW: Agent logic unit tests
        ├── test_workflows.py            # NEW: Workflow orchestration tests
        └── test_storage.py              # NEW: Storage layer tests

frontend/
├── src/
│   ├── components/
│   │   ├── agent/                       # EXISTING: Agent UI components
│   │   ├── workflow/                    # EXISTING: Workflow visualization
│   │   ├── event-planning/              # NEW: Event planning specific components
│   │   │   ├── EventPlanningChat.tsx    # NEW: Chat interface
│   │   │   ├── AgentStatusPanel.tsx     # NEW: Real-time agent status
│   │   │   ├── EventPlanSummary.tsx     # NEW: Plan output display
│   │   │   └── HandoffDialog.tsx        # NEW: User question dialog
│   │   └── shared/                      # EXISTING: Shared UI components
│   ├── services/
│   │   ├── api.ts                       # EXISTING: API client (extend)
│   │   └── eventPlanningService.ts      # NEW: Event planning API calls
│   ├── types/
│   │   ├── agent-framework.ts           # EXISTING: Agent types
│   │   └── event-planning.ts            # NEW: Event planning types
│   └── hooks/
│       ├── useEventPlanning.ts          # NEW: Event planning state hook
│       └── useAgentStatus.ts            # NEW: Real-time status hook
└── tests/
    └── event-planning/                  # NEW: Frontend tests
        ├── EventPlanningChat.test.tsx
        └── AgentStatusPanel.test.tsx

infra/                                   # EXISTING: Azure infrastructure
└── main.bicep                           # EXTEND: Add Cosmos DB resources

azure.yaml                               # EXISTING: AZD configuration (extend)
```

## Phase 0: Outline & Research ✅

**Status**: Complete

**Research Areas Completed**:

1. **Azure Cosmos DB for Session Persistence**
   - Decision: NoSQL API with managed identity, TTL for 24-hour expiration
   - Containers: `sessions` (session_id partition), `event_plans` (user_id partition)

2. **Microsoft Agent Framework Orchestration**
   - Decision: WorkflowBuilder with concurrent execution support
   - Pattern: Fan-out (Budget → Venue + Catering parallel) and fan-in (→ Logistics)

3. **Real-Time Agent Status Updates**
   - Decision: Server-Sent Events (SSE) via FastAPI StreamingResponse
   - Latency target: <1s update frequency

4. **Agent Prompt Engineering**
   - Decision: Domain-specific instructions with Pydantic structured outputs
   - Each agent has clear role, input schema, output schema

5. **Workflow Visualization**
   - Decision: Extend existing @xyflow/react component
   - Custom nodes for agent status, color-coded states

6. **Performance Optimization**
   - Decision: Multi-layer (API async, agent concurrency, DB indexes, frontend code-splitting)
   - Caching: Agent instructions, OpenAI responses, static assets

7. **Managed Identity Authentication**
   - Decision: DefaultAzureCredential (AzureCliCredential local, ManagedIdentity cloud)
   - No connection strings or API keys

8. **Testing Strategy**
   - Decision: 3-layer (unit 80%+, contract 100%, integration 100%)
   - Mocking: pytest-mock for OpenAI, real Cosmos DB test container

**Output**: `research.md` with 8 research areas documented

## Phase 1: Design & Contracts ✅

**Status**: Complete

### 1. Data Model (`data-model.md`) ✅

**11 Entities Defined**:
- `EventRequest`: User's initial planning request with validation
- `SessionContext`: Persistent session state with 24h TTL
- `WorkflowState`: Agent orchestration state tracking
- `AgentExecution`: Individual agent run records
- `UserQuestion`: Handoff questions requiring user input
- `EventPlan`: Final output with all agent results
- `BudgetAllocation`: Budget breakdown by category
- `VenueRecommendation`: Venue suggestions with scoring
- `CateringOption`: Catering proposals with pricing
- `EventTimeline`: Event schedule with milestones
- `ConversationMessage`: Chat message history

**Relationships**: ERD with 1:1, 1:many mappings defined

**Validation**: Pydantic models with field constraints (attendee_count 1-500, budget >0, etc.)

### 2. API Contracts (`contracts/api-endpoints.md`) ✅

**10 REST Endpoints**:
1. `POST /v1/sessions` - Create planning session
2. `GET /v1/sessions/{id}` - Get session status
3. `GET /v1/sessions/{id}/status/stream` - SSE status stream
4. `POST /v1/sessions/{id}/questions/{qid}/answer` - Answer handoff
5. `GET /v1/sessions/{id}/plan` - Get event plan
6. `PATCH /v1/sessions/{id}/request` - Modify requirements
7. `GET /v1/sessions/{id}/conversation` - Conversation history
8. `GET /v1/users/{uid}/sessions` - List user sessions
9. `DELETE /v1/sessions/{id}` - Delete session
10. `GET /v1/health` - Health check

**Schemas**: All request/response bodies defined via Pydantic models

**Error Handling**: Consistent error response format with codes

### 3. Contract Tests (To Be Generated) ⏭️

**Test Files to Create** (Phase 3):
- `tests/contract/test_session_api.py` - Endpoints 1-2, 6, 9
- `tests/contract/test_sse_stream.py` - Endpoint 3
- `tests/contract/test_handoff_api.py` - Endpoint 4
- `tests/contract/test_plan_api.py` - Endpoints 5, 7
- `tests/contract/test_user_api.py` - Endpoint 8
- `tests/contract/test_health_api.py` - Endpoint 10

**Each Test Validates**:
- Request schema via Pydantic
- Response schema via Pydantic
- HTTP status codes
- Error response format

### 4. Integration Test Scenarios (`quickstart.md`) ✅

**6 Manual Test Scenarios**:
1. Basic event planning flow (FR-001 to FR-004)
2. User handoff for clarification (FR-011 to FR-013)
3. Modify requirements mid-planning (FR-014)
4. Session resumption after disconnect (FR-022, NFR-009)
5. Concurrent user sessions (NFR-004)
6. Error handling with partial results (FR-018)

**Performance Validation**: Metrics and measurement approach defined

**Accessibility Validation**: WCAG 2.1 AA checklist included

### 5. Agent File Update ⏭️

**Action Required** (Phase 3): Run update script after implementation begins
```powershell
.\.specify\scripts\powershell\update-agent-context.ps1 -AgentType copilot
```

**Expected Additions**:
- Cosmos DB SDK usage patterns
- Agent Framework workflow patterns
- SSE streaming examples
- Pydantic model definitions

**Output**: `data-model.md`, `contracts/api-endpoints.md`, `quickstart.md` created

## Phase 2: Task Planning Approach ✅

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **From Data Model** (11 entities):
   - Each Pydantic model → creation task [P]
   - File: `backend/src/spec2agent/api/models/event_models.py`
   - File: `backend/src/spec2agent/api/models/workflow_models.py`
   - Estimated: 2-3 tasks

2. **From API Contracts** (10 endpoints):
   - Each endpoint → contract test task [P]
   - Each endpoint → implementation task (after tests)
   - Files: `tests/contract/test_*.py` and route handlers
   - Estimated: 20 tasks (10 tests + 10 implementations)

3. **From Research** (8 decisions):
   - Cosmos DB client setup → 1 task
   - Agent Framework workflow → 5 agent tasks + 1 orchestration
   - SSE streaming → 1 task
   - Estimated: 8 tasks

4. **From Quickstart** (6 scenarios):
   - Each scenario → integration test task
   - Files: `tests/integration/test_*.py`
   - Estimated: 6 tasks

5. **Frontend Components** (from structure):
   - EventPlanningChat.tsx [P]
   - AgentStatusPanel.tsx [P]
   - EventPlanSummary.tsx [P]
   - HandoffDialog.tsx [P]
   - Estimated: 4 tasks

6. **Infrastructure** (Azure resources):
   - Cosmos DB Bicep module
   - AZD configuration updates
   - Estimated: 2 tasks

**Ordering Strategy**:
1. **Setup Phase**: Models, storage layer, infrastructure
2. **Test Phase (TDD)**: All contract tests [P], integration tests [P]
3. **Backend Implementation**: Agents [P], workflow, API routes
4. **Frontend Implementation**: Components [P], services, hooks
5. **Integration**: Connect frontend to backend, E2E validation
6. **Polish**: Performance optimization, accessibility, documentation

**Parallel Execution Groups**:
- Group A [P]: All 11 Pydantic model definitions (independent)
- Group B [P]: All 10 contract test files (independent)
- Group C [P]: All 5 agent implementations (independent)
- Group D [P]: All 4 frontend components (independent)

**Estimated Total**: 40-45 numbered, ordered tasks in tasks.md

**Dependencies**:
- Contract tests → API implementation (TDD)
- Pydantic models → Storage layer → API implementation
- Agents → Workflow orchestration
- Backend API → Frontend services → Frontend components

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅
- [ ] Phase 3: Tasks generated (/tasks command) ⏭️
- [ ] Phase 4: Implementation complete ⏭️
- [ ] Phase 5: Validation passed ⏭️

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅ (from spec)
- [x] Complexity deviations documented ✅ (none required)

**Artifacts Generated**:
- [x] `specs/001-af-concurrent-workflows/plan.md` (this file)
- [x] `specs/001-af-concurrent-workflows/research.md`
- [x] `specs/001-af-concurrent-workflows/data-model.md`
- [x] `specs/001-af-concurrent-workflows/contracts/api-endpoints.md`
- [x] `specs/001-af-concurrent-workflows/quickstart.md`

**Next Steps**:
1. Run `/tasks` command to generate `tasks.md` from this plan
2. Execute tasks in TDD order (tests first, then implementation)
3. Run quickstart scenarios for validation
4. Update `.github/copilot-instructions.md` with new patterns

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
