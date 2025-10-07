# Phase 0: Research - Multi-Agent Event Planning System

**Date**: 2025-10-04  
**Status**: Complete

## Research Areas

### 1. Azure Cosmos DB for Session Persistence

**Decision**: Use Azure Cosmos DB NoSQL API with managed identity authentication

**Rationale**:
- Native Azure integration with Container Apps
- Automatic scaling for demo/PoC (serverless tier available)
- JSON document storage perfect for session state and conversation history
- TTL (Time-To-Live) support for 24-hour session expiration
- Query performance with indexed fields (session_id, user_id, timestamp)
- SDK: `azure-cosmos` Python client with async support
- Managed Identity: No connection strings or keys needed

**Alternatives Considered**:
- **PostgreSQL/Azure SQL**: Rejected - Overkill for unstructured session data, more complex schema management
- **Redis/Azure Cache**: Rejected - Excellent for in-memory but requires separate persistent backup for 24-hour retention
- **Table Storage**: Rejected - Limited query capabilities, less developer-friendly for complex documents

**Implementation Notes**:
- Database: `event-planning-db`
- Container: `sessions` (partition key: `/session_id`, TTL: 86400 seconds)
- Container: `event_plans` (partition key: `/user_id`, no TTL for saved plans)
- Connection: `DefaultAzureCredential` (AzureCliCredential local, ManagedIdentity cloud)

---

### 2. Microsoft Agent Framework Best Practices

**Decision**: Use Agent Framework's WorkflowBuilder with concurrent execution support

**Rationale**:
- Native support for agent orchestration with dependency management
- Built-in Azure OpenAI integration via `agent-framework-azure-ai`
- Workflow visualization compatible with existing DevUI frontend
- Concurrent agent execution via workflow edges and fan-in/fan-out patterns
- User handoff capability through workflow pause/resume
- Already integrated in project (`agent-framework-core` dependency)

**Key Patterns**:
```python
# Concurrent execution example
workflow = (
    WorkflowBuilder()
    .add_edge(coordinator, budget_analyst)
    .add_edge(budget_analyst, venue_specialist)  # Sequential dependency
    .add_edge(budget_analyst, catering_coordinator)  # Parallel after budget
    .add_edge(venue_specialist, logistics_manager)  # Fan-in to logistics
    .add_edge(catering_coordinator, logistics_manager)
    .set_start_executor(coordinator)
    .build()
)
```

**User Handoff Pattern**:
- Agent returns structured question via Pydantic model
- Workflow pauses, persists state to Cosmos DB
- Frontend displays question dialog
- User response resumes workflow from saved state
- New context injected into waiting agent

**Alternatives Considered**:
- **LangChain/LangGraph**: Rejected - Not aligned with project's Agent Framework choice
- **Custom orchestration**: Rejected - Reinventing wheel, loses DevUI integration

---

### 3. Real-Time Agent Status Updates

**Decision**: Server-Sent Events (SSE) via FastAPI streaming responses

**Rationale**:
- Native FastAPI support with `StreamingResponse`
- Simpler than WebSockets for unidirectional server→client updates
- Agent Framework already emits events during workflow execution
- Frontend can use EventSource API (built into browsers)
- Automatic reconnection handling
- <1s latency target achievable with event streaming

**Implementation Pattern**:
```python
@app.get("/v1/workflows/{workflow_id}/status")
async def stream_workflow_status(workflow_id: str):
    async def event_generator():
        async for event in workflow.stream_events():
            yield f"data: {event.model_dump_json()}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Frontend Pattern**:
```typescript
const eventSource = new EventSource(`/v1/workflows/${workflowId}/status`);
eventSource.onmessage = (event) => {
    const status = JSON.parse(event.data);
    updateAgentStatus(status);
};
```

**Alternatives Considered**:
- **WebSockets**: Rejected - Overkill for one-way status updates, more complex server management
- **Polling**: Rejected - Higher latency, more server load, doesn't meet <1s requirement
- **Long polling**: Rejected - More complex than SSE, no native browser API

---

### 4. Agent Prompt Engineering for Event Planning

**Decision**: Domain-specific instructions with structured output schemas

**Rationale**:
- Each agent has specialized instructions for its role
- Pydantic schemas enforce structured outputs (prevents hallucination)
- Agent Framework supports tools/functions for structured data
- Clear agent responsibilities prevent overlap/confusion

**Agent Instructions**:

1. **Event Coordinator**:
   - Role: Analyze requests, decompose into tasks, delegate to specialists
   - Output: Task breakdown with priority and dependencies
   - Tools: `identify_conflicts`, `request_clarification`

2. **Budget Analyst**:
   - Role: Allocate budget across categories based on event type
   - Output: Budget breakdown with category amounts and justification
   - Input: Total budget, event type, attendee count

3. **Venue Specialist**:
   - Role: Recommend venues matching criteria
   - Output: 3-5 venue options with pros/cons, cost, capacity
   - Input: Location, budget allocation, capacity, date

4. **Catering Coordinator**:
   - Role: Suggest catering options within budget
   - Output: Menu styles, dietary options, cost per person
   - Input: Budget allocation, attendee count, event formality

5. **Logistics Manager**:
   - Role: Create event timeline and coordination plan
   - Output: Timeline with milestones, setup/teardown schedule
   - Input: Venue details, catering plan, event duration

**Alternatives Considered**:
- **Generic instructions**: Rejected - Agents produce vague outputs, require more clarification
- **No structured outputs**: Rejected - Parsing natural language error-prone, violates type safety principle

---

### 5. Workflow Visualization with @xyflow/react

**Decision**: Extend existing workflow-flow.tsx component for event planning agents

**Rationale**:
- Already integrated in frontend (`@xyflow/react` ^12.8.4)
- Existing `WorkflowFlow` component provides base visualization
- Supports custom node types for agent status (active/waiting/complete)
- Real-time layout updates via React state
- Compatible with Agent Framework event streaming

**Customizations Needed**:
- Custom node component for agent status badges
- Edge highlighting for active dependencies
- Color coding: blue (active), green (complete), gray (waiting), red (error)
- Agent output preview in node tooltips

**Alternatives Considered**:
- **D3.js**: Rejected - More complex, requires manual layout algorithm
- **Cytoscape**: Rejected - Larger bundle size, not React-native
- **Custom SVG**: Rejected - Reinventing wheel, loses interactivity features

---

### 6. Performance Optimization Strategies

**Decision**: Multi-layered caching and concurrent agent execution

**Performance Targets**:
- API response: <200ms p95
- Workflow start: <3s
- UI update: <1s
- Complete flow: <2min

**Strategies**:

1. **API Layer**:
   - FastAPI async handlers (non-blocking)
   - Response compression (gzip middleware)
   - Request validation via Pydantic (fail fast)

2. **Agent Execution**:
   - Concurrent execution where no dependencies (venue + catering in parallel)
   - Streaming responses for long-running workflows
   - Timeout per agent (30s max to prevent hanging)

3. **Database**:
   - Cosmos DB indexed queries (session_id, user_id, timestamp)
   - Batch reads for conversation history (last 20 messages)
   - Connection pooling via async client

4. **Frontend**:
   - Code splitting by route (Vite dynamic imports)
   - React.lazy for heavy components (workflow visualization)
   - Memoization for agent status updates (useMemo, React.memo)
   - Debounced UI updates (max 1 update per second per agent)

5. **Caching**:
   - Agent instruction caching (loaded once at startup)
   - OpenAI response caching (same prompt = cached result)
   - Static asset caching (Vite build optimization)

**Measurement**:
- FastAPI middleware for request timing
- Agent Framework built-in telemetry
- Performance tests in pytest (assert latency < thresholds)

---

### 7. Managed Identity Authentication Pattern

**Decision**: DefaultAzureCredential with environment-based credential chain

**Rationale**:
- Single code path for local and cloud environments
- No secrets in code or config files (constitution compliance)
- Automatic fallback: AzureCliCredential (local) → ManagedIdentity (cloud)
- Works with Cosmos DB, Azure OpenAI, and other Azure services

**Implementation Pattern**:
```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Single credential instance
credential = DefaultAzureCredential()

# For Azure OpenAI
token_provider = get_bearer_token_provider(
    credential, 
    "https://cognitiveservices.azure.com/.default"
)

# For Cosmos DB
from azure.cosmos.aio import CosmosClient
cosmos_client = CosmosClient(
    url=os.environ["COSMOS_DB_URL"],
    credential=credential
)
```

**Local Development**:
1. Run `az login`
2. Credential chain uses AzureCliCredential
3. Works with personal Azure account

**Cloud Deployment**:
1. Container App has managed identity enabled (via Bicep)
2. Managed identity granted RBAC roles:
   - Cosmos DB: `Cosmos DB Built-in Data Contributor`
   - Azure OpenAI: `Cognitive Services OpenAI User`
3. DefaultAzureCredential automatically uses managed identity

**Alternatives Considered**:
- **Connection strings**: Rejected - Violates constitution (no secrets)
- **Service principals in environment**: Rejected - Still secrets, rotation burden
- **Separate credential types**: Rejected - Code duplication for local vs cloud

---

### 8. Testing Strategy for Multi-Agent Workflows

**Decision**: Three-layer testing approach with mocked agents for unit tests

**Test Layers**:

1. **Unit Tests** (80%+ coverage):
   - Individual agent logic (without OpenAI calls)
   - Workflow orchestration rules
   - Storage layer (mocked Cosmos DB)
   - Pydantic model validation
   - Mock pattern: `pytest-mock` for agent responses
   - **Backend**: Run with `uv run pytest tests/unit/`
   - **Frontend**: Run with `npm test -- --run tests/unit/`

2. **Contract Tests** (100% of endpoints):
   - API request/response schemas
   - Status codes and error handling
   - Authentication checks
   - FastAPI TestClient for synchronous testing
   - One test file per endpoint
   - **Backend**: Run with `uv run pytest tests/contract/`

3. **Integration Tests** (100% of acceptance scenarios):
   - End-to-end user flows with real Agent Framework
   - Mocked Azure OpenAI (deterministic responses)
   - Real Cosmos DB (test container with auto-cleanup)
   - User handoff scenarios
   - Error recovery flows
   - **Backend**: Run with `uv run pytest tests/integration/`
   - **Frontend**: Run with `npm test -- --run tests/integration/`

**Performance Tests**:
- Separate test suite (`tests/performance/`)
- Measures: API latency, workflow duration, concurrent sessions
- Assertions: <200ms API, <3s workflow start, <2min completion
- Run in CI with performance regression detection
- **Command**: `uv run pytest tests/performance/ --benchmark`

**pytest Configuration** (already in pyproject.toml):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

**Additional pytest plugins needed**:
- `pytest-asyncio`: For async test support
- `pytest-mock`: For mocking
- `pytest-cov`: For coverage reports
- Install: Already in dev dependencies

**npm test Configuration** (to be added to frontend package.json):
```json
{
  "scripts": {
    "test": "vitest",
    "test:ci": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui"
  }
}
```

**Frontend test dependencies** (to be added):
- `vitest`: Fast Vite-native test runner
- `@testing-library/react`: React component testing
- `@testing-library/jest-dom`: DOM matchers
- `@testing-library/user-event`: User interaction simulation
- `@vitest/ui`: Optional UI for test results

**Mocking Strategy**:
```python
# Unit test example
@pytest.fixture
def mock_openai_response():
    return {
        "budget_breakdown": {
            "venue": 4000,
            "catering": 3500,
            "logistics": 1500,
            "contingency": 1000
        }
    }

async def test_budget_analyst(mock_openai_response, monkeypatch):
    # Mock agent response
    monkeypatch.setattr("agent.execute", return_value=mock_openai_response)
    # Test orchestration logic
    result = await budget_analyst.analyze(event_request)
    assert result.total == 10000
```

**Alternatives Considered**:
- **Only integration tests**: Rejected - Slow, expensive (OpenAI calls), flaky
- **No mocking**: Rejected - Tests fail without Azure resources, non-deterministic
- **Recorded responses**: Rejected - Brittle, hard to maintain as prompts evolve

---

## Summary of Decisions

| Area                | Decision                            | Key Benefit                                 |
| ------------------- | ----------------------------------- | ------------------------------------------- |
| Session Storage     | Cosmos DB NoSQL + Managed Identity  | Serverless, auto-scaling, no secrets        |
| Agent Orchestration | Agent Framework WorkflowBuilder     | Concurrent execution, existing integration  |
| Real-Time Updates   | Server-Sent Events (SSE)            | Simple, low latency, native browser support |
| Agent Prompts       | Domain-specific + Pydantic schemas  | Structured outputs, type safety             |
| Workflow Viz        | @xyflow/react (extend existing)     | Already integrated, React-native            |
| Performance         | Multi-layer caching + concurrency   | Meets <200ms API, <3s start, <1s updates    |
| Authentication      | DefaultAzureCredential              | Single pattern, local + cloud, no secrets   |
| Testing             | 3-layer (unit/contract/integration) | Fast feedback, comprehensive coverage       |

**Status**: ✅ All research complete, ready for Phase 1 design.
