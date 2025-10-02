
# Implementation Plan: Event Orchestration System (EODS) v0.1

**Branch**: `001-event-orchestration-system` | **Date**: 2025-10-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `C:\Users\alexlavaee\source\repos\spec-to-agents\specs\001-event-orchestration-system\spec.md`

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
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
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
The Event Orchestration System (EODS) v0.1 is a declarative, spec-driven multi-agent system for end-to-end event planning and execution. The system coordinates four specialized agent roles (Event Planner, Venue Researcher, Budget Analyst, Logistics Coordinator) through a shared artifact catalog with 22 artifact types, enforcing quality gates at each workflow transition. The system supports events ranging from small meetups (20 attendees) to large conferences (800+ attendees) through three instruction levels (Beginner, Intermediate, Advanced), following an 8-state lifecycle (Initiate → Plan → Research → Budget → Logistics → Confirm → Execute → Postmortem) with mandatory human approvals on critical decisions.

## Technical Context
**Language/Version**: Python 3.13+ (backend), TypeScript 5.8+ (frontend)  
**Primary Dependencies**: FastAPI, Pydantic, SQLModel, agent-framework (AF), React 19, Vite 7, Tailwind CSS  
**Storage**: Azure SQL (relational artifacts), CosmosDB (NoSQL documents), pyodbc with ODBC Driver 18  
**Testing**: pytest (backend), Vitest + React Testing Library (frontend), Playwright via playwright MCP for visual QA  
**Target Platform**: Azure Container Apps (backend), Azure Static Web Apps or App Service (frontend)  
**Project Type**: web (frontend + backend)  
**Performance Goals**: API p95 < 200ms (non-LLM), < 5s (agent orchestration); Frontend FCP < 1.5s, TTI < 3.5s; 100 concurrent users, 10 concurrent planning sessions  
**Constraints**: Backend < 512MB baseline / < 1GB under load; Frontend bundle < 2MB gzipped; All Azure resource access via Managed Identity (azure-identity with AzureCLICredential/ManagedIdentityCredential); Zero secrets in code/configs  
**Scale/Scope**: Multi-agent orchestration system with 4 agent roles, 22 artifact types, 8 lifecycle states, 50+ functional requirements; Support for 20-800 attendee events

**Additional Context from User**:
- **Auth Strategy**: Managed Identity (AAD tokens) for all resource access (DB, MCPs, Azure services)
- **AI Orchestration**: agent-framework (AF) for workflow execution; AI Foundry for agent creation
- **Dev Acceleration**: context7 MCP for docs discovery, playwright MCP for visual QA and UI modifications
- **Quality Requirements**: Full lifecycle validation with persisted approvals in Azure SQL; MCP integrations functional; Quality gates enforced; Metrics/logs auditable

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development ✅
- **Compliance**: Design will generate contract tests BEFORE implementation (Phase 1)
- **Strategy**: Contract tests from API specs → Integration tests from user stories → Unit tests for domain logic
- **Coverage Targets**: Backend ≥80%, Frontend ≥75%, Critical paths (agent orchestration, lifecycle transitions) 100%
- **Verification**: All tests written in Phase 1, must fail before Phase 4 implementation begins

### Principle II: Code Quality Standards ✅
- **Type Safety**: Python full type hints (mypy strict), TypeScript strict mode (no `any` except documented third-party interfaces)
- **Code Style**: Black (Python), ESLint (TypeScript), max cyclomatic complexity ≤10
- **Documentation**: Docstrings for all agents, artifact schemas, API endpoints; inline comments for complex orchestration logic
- **Error Handling**: Structured logging with correlation IDs; user-facing errors actionable; no silent failures

### Principle III: User Experience Consistency ✅
- **Responsiveness**: UI updates < 100ms, async operations loading states < 200ms, progress indicators for > 500ms operations
- **Agent Visualization**: Real-time agent status (thinking/responding/waiting), group chat chronological display, decision transparency
- **Accessibility**: WCAG 2.1 AA compliance (semantic HTML, ARIA, keyboard nav, screen reader support)
- **Feedback**: Success/error notifications, form validation, destructive action confirmations, helpful empty states

### Principle IV: Performance Requirements ✅
- **Response Times**: API p95 < 200ms (non-LLM), < 5s (agent orchestration); Frontend FCP < 1.5s, TTI < 3.5s
- **Scalability**: 100 concurrent users, 10 concurrent planning sessions; Backend < 512MB baseline, Frontend bundle < 2MB gzipped
- **Resource Optimization**: Code splitting, lazy loading, async I/O, connection pooling, LLM response caching
- **Monitoring**: Application Insights integration, performance budgets in CI/CD, alerting on latency/error rate degradation

### Additional Constitutional Alignment
- **Managed Identity**: All Azure resource access via azure-identity (no secrets in code/configs) - aligns with security best practices
- **Agent Framework Showcase**: Real-time orchestration transparency demonstrates AF production readiness - aligns with UX consistency
- **MCP Integration**: context7 and playwright MCPs accelerate development and QA - aligns with quality standards

**Initial Gate Status**: ✅ PASS - No constitutional violations detected; design aligns with all four core principles

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
```
backend/
├── src/
│   └── spec2agent/
│       ├── models/              # SQLModel entities for artifacts (EventBrief, Timeline, Budget, etc.)
│       ├── schemas/             # Pydantic schemas for API contracts and validation
│       ├── agents/              # Agent Framework agent definitions (Planner, Researcher, Analyst, Coordinator)
│       ├── orchestration/       # Workflow orchestration logic, lifecycle state machine
│       ├── repositories/        # Data access layer (Azure SQL via pyodbc, CosmosDB)
│       ├── auth/                # Managed Identity setup (azure-identity integration)
│       ├── api/                 # FastAPI routers and endpoints
│       └── __init__.py
├── tests/
│   ├── contract/                # API contract tests (OpenAPI validation)
│   ├── integration/             # End-to-end workflow tests (lifecycle transitions)
│   └── unit/                    # Agent logic, repository, schema validation tests
├── main.py                      # FastAPI application entry point
└── pyproject.toml               # Dependencies: agent-framework, FastAPI, SQLModel, pyodbc, etc.

frontend/
├── src/
│   ├── components/              # React components (AgentChat, ArtifactViewer, WorkflowTimeline)
│   ├── pages/                   # Route pages (EventDashboard, PlanningSession, Approvals)
│   ├── services/                # API client (httpx wrapper), WebSocket handlers
│   ├── hooks/                   # React hooks for agent state, artifact subscriptions
│   ├── types/                   # TypeScript types matching backend schemas
│   └── utils/                   # Helpers (formatting, validation, auth token management)
├── tests/
│   ├── components/              # Component unit tests (Vitest + React Testing Library)
│   ├── integration/             # E2E tests via Playwright MCP
│   └── visual/                  # Visual regression tests via Playwright MCP
├── public/                      # Static assets
├── index.html
├── vite.config.ts
└── package.json                 # Dependencies: React 19, Vite 7, Tailwind CSS

infra/                           # Bicep templates for Azure resources
├── main.bicep                   # Main infrastructure template
├── container-apps.bicep         # Backend container app
├── sql.bicep                    # Azure SQL database
├── cosmos.bicep                 # CosmosDB account
└── keyvault.bicep               # Key Vault for secrets

mcp.json                         # MCP server configuration (context7, playwright)
```

**Structure Decision**: Web application (frontend + backend) structure selected. Repository already contains `backend/` and `frontend/` directories, confirming web architecture. Backend uses `src/spec2agent/` namespace for Python package organization. Frontend follows standard Vite + React project structure. Infrastructure as Code in `/infra` for Azure deployments. MCP configuration at root for development acceleration.

## Phase 0: Outline & Research ✅ COMPLETE

**Completed**: 2025-10-02

**Summary**: All technical unknowns resolved through user-provided technical stack specification. Research consolidated decisions for:
1. Agent Framework (AF) integration with Azure AI Foundry
2. Managed Identity authentication strategy (azure-identity)
3. Hybrid database architecture (Azure SQL + CosmosDB)
4. MCP integration (context7, playwright)
5. Frontend architecture (Vite + React 19 + TypeScript + Tailwind)
6. Testing strategy (pytest, Vitest, Playwright MCP)
7. Observability (Application Insights + structured logging)

**Output**: `research.md` (7 major decisions documented with rationale, alternatives, and implementation guidance)

## Phase 1: Design & Contracts ✅ COMPLETE

**Completed**: 2025-10-02

**Summary**:
1. **Data Model**: Defined 18 Azure SQL entities (SQLModel) + 4 CosmosDB document types with full schemas, relationships, validation rules, quality gates, and state machine transitions
2. **API Contracts**: Generated comprehensive OpenAPI 3.1 specification (`contracts/openapi.yaml`) with 40+ endpoints covering EventBriefs, Planning, Venues, Budget, Logistics, Agents, and Approvals
3. **Quickstart Guide**: Created executable validation guide (`quickstart.md`) with 3 scenarios (Beginner/Intermediate/Advanced) mapping to user stories, including error handling, performance validation, and UI testing via Playwright MCP
4. **Agent Context**: Updated GitHub Copilot context file (`.github/copilot-instructions.md`) with Python 3.13+, TypeScript 5.8+, FastAPI, React 19, agent-framework, Azure SQL, CosmosDB, and MCP integration details

**Outputs**:
- ✅ `data-model.md` (22 artifact types, lifecycle state machine, validation rules)
- ✅ `contracts/openapi.yaml` (OpenAPI 3.1 spec with 40+ endpoints, full schemas)
- ✅ `quickstart.md` (3 validation scenarios with success criteria)
- ✅ `.github/copilot-instructions.md` (agent context updated)

**Quality Gates Verified**:
- All entities map to feature requirements (FR-015 to FR-022)
- Quality gate fields embedded in data model (Timeline, VenueScorecard, BudgetDecision, LogisticsPlan)
- API contracts enforce validation rules
- Quickstart scenarios validate metrics thresholds (FR-035 to FR-038)

**Next**: Phase 2 (Task Planning) - Execute via `/tasks` command

## Phase 2: Task Planning Approach ✅ COMPLETE
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base template
- Generate tasks from Phase 1 artifacts:
  * **data-model.md**: 18 SQL entities + 4 CosmosDB documents → 22 model creation tasks
  * **contracts/openapi.yaml**: 40+ endpoints → 40+ contract test tasks
  * **quickstart.md**: 3 validation scenarios → 12+ integration test tasks
  * Agent orchestration logic, lifecycle management, quality gates → 10+ service layer tasks
  * Frontend components (AgentChat, EventDashboard, Approvals) → 8+ UI tasks

**Task Categories** (Estimated ~70 tasks):
1. **Infrastructure Setup** (5 tasks): Database migrations, Bicep templates, MCP configuration, CI/CD pipeline, Application Insights
2. **Backend Models** (22 tasks): SQLModel entity classes, Pydantic schemas, CosmosDB document models
3. **Backend Contract Tests** (40 tasks): One test per endpoint, must fail before implementation
4. **Backend Services** (12 tasks): Repository pattern, lifecycle manager, agent orchestration, quality gate validators, approval workflow
5. **Backend API Implementation** (40 tasks): FastAPI routers, endpoint handlers, authentication middleware
6. **Frontend Components** (8 tasks): EventBrief CRUD, AgentChat, Timeline viewer, Budget tracker, Approval UI
7. **Frontend Tests** (10 tasks): Component tests (Vitest), integration tests (Playwright MCP), visual regression
8. **Integration Tests** (12 tasks): Beginner/Intermediate/Advanced scenarios from quickstart.md
9. **Documentation** (3 tasks): README updates, API docs generation, architecture diagrams

**Ordering Strategy** (Constitutional TDD Compliance):
1. **Tests First**: Contract tests, model tests, service tests, component tests, integration tests
2. **Dependency Order**: Models → Repositories → Services → API → UI
3. **Parallel Execution**: Mark [P] for independent file operations (contract tests, model creation, components)

**Estimated Output**: 70-75 numbered, TDD-ordered tasks in `tasks.md`

**IMPORTANT**: This phase is executed by the `/tasks` command, NOT by `/plan`

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
- [x] Phase 0: Research complete (/plan command) - 2025-10-02 ✅
- [x] Phase 1: Design complete (/plan command) - 2025-10-02 ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - 2025-10-02 ✅
- [ ] Phase 3: Tasks generated (/tasks command) - **READY TO EXECUTE**
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved (none existed) ✅
- [x] Complexity deviations documented (none required) ✅

**Artifact Generation Summary**:
- [x] research.md (7 decisions documented)
- [x] data-model.md (22 entities, state machine, validation)
- [x] contracts/openapi.yaml (40+ endpoints, OpenAPI 3.1)
- [x] quickstart.md (3 scenarios, success criteria)
- [x] .github/copilot-instructions.md (agent context updated)

**Ready for Next Command**: `/tasks` (will generate ~70 tasks from Phase 1 artifacts)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
