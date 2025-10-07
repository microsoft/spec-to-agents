# Spec-to-Agents Constitution

<!--
Sync Impact Report - Constitution v1.0.0

VERSION CHANGE: Initial → 1.0.0 (New constitution)

MODIFIED PRINCIPLES: N/A (Initial version)

ADDED SECTIONS:
- I. Code Quality & Consistency
- II. Testing Standards (TDD Mandatory)
- III. User Experience Consistency
- IV. Performance Requirements
- Development Workflow
- Quality Gates

REMOVED SECTIONS: N/A (Initial version)

TEMPLATES STATUS:
✅ plan-template.md - Reviewed and aligned (Constitution Check section, TDD flow, performance validation)
✅ spec-template.md - Reviewed and aligned (Requirements completeness, testability)
✅ tasks-template.md - Reviewed and aligned (TDD phase ordering, parallel execution rules)
✅ agent-file-template.md - Reviewed and aligned (Generic structure, no agent-specific references)

FOLLOW-UP TODOs:
- Monitor performance metrics in production to validate <200ms p95 target
- Review and update linting configurations as project evolves
-->

## Core Principles

### I. Code Quality & Consistency
**MUST**: All code must follow language-specific linting and formatting standards.
- **Backend (Python)**: Ruff with line length 88, imports sorted, type hints required
- **Frontend (TypeScript/React)**: ESLint with React hooks rules, TypeScript strict mode
- **Rationale**: Consistent code reduces cognitive load, prevents bugs, and enables efficient code reviews. Type safety (Python 3.13+, TypeScript) catches errors at development time rather than runtime.

**MUST**: All functions and classes require docstrings/documentation.
- Public APIs must document parameters, return types, and exceptions
- Complex algorithms require explanation comments
- **Rationale**: Documentation as code ensures maintainability and onboarding efficiency.

**MUST**: No code duplication (DRY principle).
- Extract shared logic into utilities/services
- Use composition and dependency injection over inheritance
- **Rationale**: Single source of truth reduces maintenance burden and bug surface area.

### II. Testing Standards (TDD Mandatory)
**NON-NEGOTIABLE**: Test-Driven Development is mandatory for all features.
- **Red Phase**: Write failing tests first (contract tests, integration tests)
- **Green Phase**: Implement minimal code to pass tests
- **Refactor Phase**: Clean up while maintaining green tests
- **Rationale**: TDD ensures requirements are testable, reduces defects, and provides living documentation.

**MUST**: Test coverage targets:
- **Unit tests**: Critical business logic and utilities (aim for 80%+ coverage)
- **Contract tests**: All API endpoints (100% of contracts)
- **Integration tests**: All user scenarios from specs (100% of acceptance criteria)
- **Rationale**: Layered testing strategy catches bugs at appropriate levels—unit tests for logic, contract tests for interfaces, integration tests for user flows.

**MUST**: Tests must be independent and parallelizable.
- No shared state between tests
- Tests marked [P] in tasks.md can run concurrently
- Use test fixtures and dependency injection
- **Rationale**: Parallel execution speeds up CI/CD, independent tests prevent flaky failures.

**MUST**: Performance tests for critical paths.
- API endpoints: <200ms p95 latency
- Frontend interactions: <100ms perceived response time
- **Rationale**: Performance is a feature; regression testing prevents degradation.

### III. User Experience Consistency
**MUST**: Follow established UI component patterns.
- Use Radix UI primitives and Tailwind CSS utility classes
- Maintain dark/light theme support via next-themes
- Consistent spacing, typography, and interaction patterns
- **Rationale**: Design system ensures consistent, accessible, and maintainable UI.

**MUST**: All user-facing errors must be actionable.
- Clear error messages explaining what went wrong and how to fix it
- No technical stack traces exposed to end users
- Log full context server-side for debugging
- **Rationale**: User-centric error handling reduces support burden and improves experience.

**MUST**: Loading and async states must be explicit.
- Show loading spinners for operations >300ms
- Optimistic updates where appropriate (with rollback)
- Disable controls during async operations to prevent double-submission
- **Rationale**: Perceived performance and preventing user confusion.

**MUST**: Accessibility standards (WCAG 2.1 AA minimum).
- Semantic HTML, ARIA labels where needed
- Keyboard navigation support
- Sufficient color contrast (4.5:1 for text)
- **Rationale**: Inclusive design is not optional; legal and ethical imperative.

### IV. Performance Requirements
**MUST**: Backend API endpoints must respond within 200ms (p95).
- Measure and log latency for all endpoints
- Fail performance tests if p95 exceeds target
- **Rationale**: Fast APIs enable responsive UIs and scale to concurrent users.

**MUST**: Frontend bundle size constraints.
- Initial bundle <300KB gzipped
- Code-split routes and lazy-load heavy components
- **Rationale**: Fast initial load improves user retention and mobile experience.

**MUST**: Database queries must be optimized.
- Use connection pooling
- Add indexes for common query patterns
- N+1 query detection in tests
- **Rationale**: Database is often the bottleneck; proactive optimization prevents scaling issues.

**MUST**: Efficient resource management.
- Close connections, file handles, and async contexts
- Use context managers (Python) and cleanup hooks (React)
- **Rationale**: Resource leaks cause production failures; prevention through code patterns.

## Development Workflow

### Spec-First Development
**MUST**: Features begin with a specification document.
- User scenarios and acceptance criteria defined first
- No implementation before spec approval
- Specs focus on WHAT and WHY, not HOW
- **Rationale**: Spec-driven development aligns stakeholders, enables TDD, and prevents scope creep.

### Branching Strategy
**MUST**: Feature branches follow naming convention: `[###-feature-name]`.
- All work occurs in feature branches
- Branch from main, merge back via PR
- Delete branches after merge
- **Rationale**: Clean history, isolated changes, easy rollback.

### Code Review Requirements
**MUST**: All code changes require PR review before merge.
- At least one approval from maintainer
- All CI checks must pass (tests, linting, performance)
- Constitution compliance verified
- **Rationale**: Peer review catches bugs, shares knowledge, enforces standards.

### Continuous Integration
**MUST**: CI pipeline runs on every PR and commit to main.
- Run all tests (unit, contract, integration)
- Run linting and type checking
- Run performance tests
- Generate coverage reports
- **Rationale**: Automated quality gates prevent regressions and maintain standards.

## Quality Gates

### Pre-Implementation Gates
1. **Spec Approval**: Feature spec reviewed and accepted
2. **Constitution Check**: Design reviewed for compliance
3. **Research Complete**: All technical unknowns resolved

### Implementation Gates
1. **Tests First**: All tests written and failing before implementation
2. **Green Tests**: All tests pass after implementation
3. **Performance Pass**: p95 latency <200ms for API, bundle size <300KB for frontend
4. **Coverage Target**: Test coverage meets thresholds (unit 80%+, contract 100%, integration 100%)
5. **Lint Pass**: No linting errors or warnings
6. **Type Safety**: No type errors (Python mypy, TypeScript tsc)

### Pre-Merge Gates
1. **Code Review Approval**: At least one maintainer approval
2. **CI Green**: All automated checks pass
3. **Manual Testing**: Quickstart scenario validated
4. **Documentation Updated**: README, API docs, and agent files updated

## Governance

### Amendment Process
**MUST**: Constitution changes follow formal process.
1. Propose amendment with rationale
2. Review impact on existing codebase
3. Update version following semantic versioning:
   - **MAJOR**: Breaking changes to principles (e.g., removing TDD requirement)
   - **MINOR**: New principles added (e.g., adding security principle)
   - **PATCH**: Clarifications, typos, non-semantic changes
4. Update all dependent templates and documentation
5. Communicate changes to all contributors

### Version History
Current amendments require review of:
- `.specify/templates/plan-template.md` (Constitution Check section)
- `.specify/templates/spec-template.md` (Requirements completeness)
- `.specify/templates/tasks-template.md` (TDD ordering, parallel rules)
- `.specify/templates/agent-file-template.md` (Generic guidance)

### Compliance Review
**MUST**: All PRs include constitution compliance verification.
- Reviewers check adherence to principles
- Violations require justification in Complexity Tracking section
- Unjustifiable violations block merge

### Complexity Justification
When principles must be violated (e.g., skipping tests for prototype, performance trade-off):
1. Document in plan.md Complexity Tracking section
2. Explain why violation necessary
3. Document simpler alternatives considered
4. Get explicit approval from maintainer
5. Create follow-up task to resolve technical debt

**Version**: 1.0.0 | **Ratified**: 2025-10-04 | **Last Amended**: 2025-10-04