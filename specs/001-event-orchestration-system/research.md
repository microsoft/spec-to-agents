# Research: Event Orchestration System (EODS) v0.1

**Date**: 2025-10-02  
**Feature**: Event Orchestration System  
**Purpose**: Resolve technical unknowns and establish best practices for implementation

---

## Research Summary

All technical unknowns from the initial planning phase have been resolved through the user-provided technical stack specification. This document consolidates those decisions with rationale and implementation guidance.

---

## 1. Agent Framework (AF) Integration

### Decision
Use **Microsoft Agent Framework** (`agent-framework-core`, `agent-framework-azure-ai`) for all agentic workflow orchestration.

### Rationale
- **Native Azure Integration**: Built for Azure OpenAI and AI Foundry, aligning with infrastructure requirements
- **Declarative Workflow Definition**: Supports spec-driven agent definitions matching EODS design philosophy
- **Group Chat Patterns**: Native support for multi-agent collaboration via shared context (blackboard pattern)
- **Production Ready**: Microsoft-supported framework demonstrating enterprise-grade orchestration

### Implementation Guidance
- Define agents in `backend/src/spec2agent/agents/` with AF declarative syntax
- Use AF's `GroupChat` for multi-agent interactions (e.g., Budget Analyst + Logistics Coordinator conflict resolution)
- Leverage AF's built-in retry/fallback policies for LLM reliability
- Integrate AF telemetry with Application Insights for observability

### Alternatives Considered
- **LangChain**: More mature ecosystem but adds complexity; AF is purpose-built for Azure
- **Semantic Kernel**: Microsoft alternative but less focused on agent orchestration patterns
- **Custom Implementation**: Rejected due to reinventing orchestration primitives AF provides

### References
- Agent Framework documentation: https://aka.ms/agent-framework
- Azure AI Foundry agent creation: https://ai.azure.com

---

## 2. Authentication & Authorization Strategy

### Decision
**Managed Identity via azure-identity** with `AzureCLICredential` (local dev) and `ManagedIdentityCredential` (Azure deployment). Zero secrets in code, configs, or pipelines.

### Rationale
- **Security Best Practice**: Eliminates secret sprawl and rotation burden
- **Constitutional Alignment**: Meets governance requirement for production-ready security
- **Azure Native**: Seamless integration with Azure SQL, CosmosDB, Key Vault, OpenAI
- **Developer Experience**: `AzureCLICredential` uses `az login` for local development without config changes

### Implementation Guidance
```python
from azure.identity import AzureCLICredential, ManagedIdentityCredential, ChainedTokenCredential

# Automatically try CLI (local) then Managed Identity (Azure)
credential = ChainedTokenCredential(
    AzureCLICredential(),
    ManagedIdentityCredential()
)

# Use with Azure SQL
connection_string = f"Driver={{ODBC Driver 18 for SQL Server}};Server=...;Authentication=ActiveDirectoryMsi"

# Use with CosmosDB
from azure.cosmos import CosmosClient
client = CosmosClient(url=cosmos_url, credential=credential)

# Use with Azure OpenAI
from openai import AzureOpenAI
client = AzureOpenAI(azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token)
```

### Implementation Checklist
- [ ] Assign Managed Identity to Container Apps in Bicep templates
- [ ] Grant SQL Database Contributor role to Managed Identity
- [ ] Grant CosmosDB Data Contributor role to Managed Identity
- [ ] Grant Cognitive Services OpenAI User role to Managed Identity
- [ ] Test credential chain locally with `az login`
- [ ] Verify no secrets in `appsettings.json`, environment variables, or `.env` files

### Alternatives Considered
- **Connection Strings with Secrets**: Rejected for security concerns and constitutional violation
- **Service Principals with Certificates**: More complex than Managed Identity without additional benefits

### References
- azure-identity documentation: https://learn.microsoft.com/python/api/azure-identity
- Managed Identity best practices: https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/

---

## 3. Database Strategy: Azure SQL + CosmosDB

### Decision
**Hybrid storage**: Azure SQL for structured artifacts requiring relational integrity (EventBrief, Timeline, TaskRegister, BudgetBaseline); CosmosDB for flexible, versioned documents (RiskRegister, DecisionLog, ChangeLog, agent execution traces).

### Rationale
- **SQL for Structured Data**: Lifecycle state transitions, artifact relationships, and approval workflows benefit from ACID guarantees and referential integrity
- **CosmosDB for Flexibility**: Agent execution traces, decision logs, and risk registers have variable schemas; CosmosDB's JSON storage simplifies versioning
- **Performance**: CosmosDB low-latency reads for real-time agent status; SQL for complex joins and reporting
- **Constitutional Alignment**: Meets scalability and performance requirements (100 concurrent users, <200ms p95)

### Implementation Guidance

#### Azure SQL Schema (SQLModel)
```python
# backend/src/spec2agent/models/event_brief.py
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional

class EventBrief(SQLModel, table=True):
    __tablename__ = "event_briefs"
    
    id: str = Field(primary_key=True)  # UUID
    version: int = Field(default=1)
    title: str
    date_range_start: datetime
    date_range_end: datetime
    audience_size: int
    event_type: str
    objectives: str
    constraints: str
    lifecycle_state: str = Field(default="Initiate")  # Enum: Initiate, Plan, Research, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    timeline: Optional["Timeline"] = Relationship(back_populates="event_brief")
    budget: Optional["BudgetBaseline"] = Relationship(back_populates="event_brief")
```

#### CosmosDB Document Structure
```json
// Decision Log Document
{
  "id": "dec-20251002-001",
  "type": "decision",
  "eventBriefId": "evt-20251002-meetup",
  "timestamp": "2025-10-02T14:30:00Z",
  "owner": "Event Planner Agent",
  "description": "Selected Venue A over Venue B due to accessibility requirements",
  "rationale": "Venue A scores 0.92 vs Venue B 0.78; accessibility mandatory per EventBrief",
  "impactedArtifacts": ["venue-shortlist-v2", "budget-baseline-v3"],
  "approvals": [
    {"role": "Human Approver", "status": "approved", "timestamp": "2025-10-02T15:00:00Z"}
  ]
}
```

#### Connection Management
```python
# backend/src/spec2agent/repositories/sql_repository.py
from sqlmodel import create_engine, Session
from azure.identity import ChainedTokenCredential, AzureCLICredential, ManagedIdentityCredential

credential = ChainedTokenCredential(AzureCLICredential(), ManagedIdentityCredential())

# Azure SQL with Managed Identity
# NOTE: pyodbc with ODBC Driver 18 supports ActiveDirectoryMsi authentication
connection_string = (
    f"mssql+pyodbc://@{sql_server_name}.database.windows.net/{database_name}"
    f"?driver=ODBC+Driver+18+for+SQL+Server"
    f"&Authentication=ActiveDirectoryMsi"
    f"&Encrypt=yes"
)
engine = create_engine(connection_string, echo=False, pool_pre_ping=True)

# CosmosDB with Managed Identity
from azure.cosmos import CosmosClient
cosmos_client = CosmosClient(url=cosmos_url, credential=credential)
database = cosmos_client.get_database_client("eods")
```

### Implementation Checklist
- [ ] Design SQL schema with SQLModel classes for 15 structured artifacts
- [ ] Create Bicep template for Azure SQL with Managed Identity access
- [ ] Create Bicep template for CosmosDB with Managed Identity access
- [ ] Implement repository pattern with SQL and Cosmos clients
- [ ] Add connection pooling and retry logic
- [ ] Write contract tests for repository CRUD operations

### Alternatives Considered
- **PostgreSQL**: Rejected because Azure SQL better integrates with Managed Identity and Azure ecosystem
- **SQL Only**: Rejected because agent traces and decision logs have flexible schemas
- **CosmosDB Only**: Rejected because lifecycle state machine and relational integrity require SQL

### References
- SQLModel documentation: https://sqlmodel.tiangolo.com/
- Azure SQL with Managed Identity: https://learn.microsoft.com/azure/azure-sql/database/authentication-aad-overview
- CosmosDB Python SDK: https://learn.microsoft.com/azure/cosmos-db/nosql/sdk-python

---

## 4. MCP Integration for Development Acceleration

### Decision
Integrate **context7 MCP** (documentation discovery) and **playwright MCP** (visual QA and UI automation) as development tools.

### Rationale
- **context7**: Accelerates research on agent-framework, Azure SDK, React 19 patterns by fetching up-to-date docs
- **playwright**: Enables visual regression testing and UI modification validation without manual browser testing
- **Constitutional Alignment**: Improves development velocity and quality assurance (Principle II: Code Quality)

### Implementation Guidance

#### MCP Configuration (`mcp.json`)
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp-server"],
      "env": {
        "PLAYWRIGHT_HEADLESS": "true"
      }
    }
  }
}
```

#### Usage Patterns
- **context7**: Query docs during agent implementation (`context7.get_docs("agent-framework group chat patterns")`)
- **playwright**: Automate visual QA tests in `frontend/tests/visual/` directory
- **playwright**: Validate UI changes (e.g., "click 'Start Planning' button, verify EventBrief form renders")

### Implementation Checklist
- [ ] Create/update `mcp.json` at repository root
- [ ] Test context7 MCP with agent-framework documentation queries
- [ ] Test playwright MCP with sample UI navigation script
- [ ] Add visual regression tests to CI/CD pipeline
- [ ] Document MCP usage in README for onboarding

### Alternatives Considered
- **Manual Documentation Lookup**: Slower and error-prone
- **Selenium/Puppeteer Directly**: More boilerplate than MCP abstraction

### References
- MCP specification: https://modelcontextprotocol.io/
- context7 MCP: https://www.npmjs.com/package/@context7/mcp-server
- playwright MCP: https://www.npmjs.com/package/@playwright/mcp-server

---

## 5. Frontend Architecture: Vite + React 19 + TypeScript

### Decision
**Vite 7** as build tool, **React 19** with TypeScript for component library, **Tailwind CSS** for styling.

### Rationale
- **Vite**: Fastest build tool for modern frontend; aligns with performance requirements (FCP < 1.5s)
- **React 19**: Latest stable version with improved concurrent rendering for real-time agent updates
- **TypeScript**: Type safety required by constitution; strict mode eliminates runtime type errors
- **Tailwind CSS**: Utility-first styling accelerates UI development; aligns with UX consistency principle

### Implementation Guidance

#### Key React Patterns
```typescript
// frontend/src/hooks/useAgentStatus.ts
import { useState, useEffect } from 'react';
import { AgentStatus } from '../types/agent';

export function useAgentStatus(agentId: string): AgentStatus {
  const [status, setStatus] = useState<AgentStatus>({ state: 'idle' });
  
  useEffect(() => {
    const ws = new WebSocket(`ws://backend/agents/${agentId}/status`);
    ws.onmessage = (event) => setStatus(JSON.parse(event.data));
    return () => ws.close();
  }, [agentId]);
  
  return status;
}

// frontend/src/components/AgentChat.tsx
export function AgentChat({ sessionId }: { sessionId: string }) {
  const plannerStatus = useAgentStatus('event-planner');
  const researcherStatus = useAgentStatus('venue-researcher');
  
  return (
    <div className="agent-chat">
      <AgentMessage agent="planner" status={plannerStatus} />
      <AgentMessage agent="researcher" status={researcherStatus} />
    </div>
  );
}
```

#### Performance Optimizations
- **Code Splitting**: Use `React.lazy()` for route-level components
- **Bundle Analysis**: Add `vite-plugin-bundle-analyzer` to enforce <2MB gzipped limit
- **Image Optimization**: Use WebP format with `vite-imagetools`
- **Tree Shaking**: Configure Tailwind to purge unused styles

### Implementation Checklist
- [ ] Configure Vite with TypeScript strict mode
- [ ] Set up Tailwind CSS with design system tokens
- [ ] Create base component library (Button, Card, Modal, Form)
- [ ] Implement WebSocket service for real-time agent status
- [ ] Add bundle size monitoring to CI/CD
- [ ] Configure React DevTools for debugging

### Alternatives Considered
- **Next.js**: Overkill for SPA without SSR requirements
- **Angular**: Less ecosystem momentum than React; steeper learning curve
- **Vue**: Smaller community for agent visualization patterns

### References
- Vite documentation: https://vitejs.dev/
- React 19 release notes: https://react.dev/blog/2024/04/25/react-19
- Tailwind CSS: https://tailwindcss.com/

---

## 6. Testing Strategy: pytest + Vitest + Playwright MCP

### Decision
**pytest** for backend, **Vitest + React Testing Library** for frontend unit/integration, **Playwright MCP** for E2E and visual regression.

### Rationale
- **pytest**: Industry standard for Python; rich plugin ecosystem (pytest-asyncio, pytest-mock)
- **Vitest**: Vite-native test runner; faster than Jest for TypeScript projects
- **React Testing Library**: Encourages testing user behavior over implementation details
- **Playwright MCP**: Automates browser testing without manual setup; supports visual diffs

### Implementation Guidance

#### Backend Contract Test Example
```python
# backend/tests/contract/test_event_brief_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_event_brief_contract():
    """Contract test: POST /api/event-briefs validates schema"""
    payload = {
        "title": "Tech Conference 2025",
        "date_range_start": "2025-06-01T09:00:00Z",
        "date_range_end": "2025-06-03T17:00:00Z",
        "audience_size": 500,
        "event_type": "conference",
        "objectives": "Showcase AI innovations",
        "constraints": "Budget $100k, downtown venue"
    }
    
    response = client.post("/api/event-briefs", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["lifecycle_state"] == "Initiate"
    assert data["title"] == payload["title"]
```

#### Frontend Component Test Example
```typescript
// frontend/tests/components/AgentChat.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { AgentChat } from '../../src/components/AgentChat';
import { vi } from 'vitest';

vi.mock('../../src/hooks/useAgentStatus', () => ({
  useAgentStatus: (agentId: string) => ({
    state: agentId === 'event-planner' ? 'thinking' : 'idle',
    message: 'Analyzing event requirements...'
  })
}));

test('AgentChat displays agent status', async () => {
  render(<AgentChat sessionId="session-123" />);
  
  await waitFor(() => {
    expect(screen.getByText('Event Planner')).toBeInTheDocument();
    expect(screen.getByText('Analyzing event requirements...')).toBeInTheDocument();
  });
});
```

#### Playwright MCP Visual Test
```python
# frontend/tests/visual/test_event_dashboard.py
import pytest

@pytest.mark.visual
def test_event_dashboard_renders(playwright_mcp):
    """Visual regression test for event dashboard"""
    playwright_mcp.navigate("http://localhost:5173/dashboard")
    playwright_mcp.wait_for_selector("[data-testid='event-list']")
    
    screenshot = playwright_mcp.screenshot(full_page=True)
    playwright_mcp.compare_snapshot(screenshot, "event-dashboard.png", threshold=0.02)
```

### Implementation Checklist
- [ ] Configure pytest with coverage reporting (pytest-cov)
- [ ] Set up Vitest with React Testing Library
- [ ] Configure Playwright MCP for visual regression
- [ ] Add pre-commit hook to run tests locally
- [ ] Integrate test suites into CI/CD pipeline
- [ ] Establish coverage thresholds (80% backend, 75% frontend)

### Alternatives Considered
- **Jest**: Slower than Vitest for Vite projects
- **Cypress**: Less programmatic control than Playwright MCP

### References
- pytest documentation: https://docs.pytest.org/
- Vitest documentation: https://vitest.dev/
- React Testing Library: https://testing-library.com/react
- Playwright MCP: https://www.npmjs.com/package/@playwright/mcp-server

---

## 7. Observability: Application Insights + Structured Logging

### Decision
**Azure Application Insights** for telemetry, distributed tracing, and alerting. **Structured logging** with correlation IDs for debugging.

### Rationale
- **Constitutional Requirement**: Metrics and logs must be auditable (FR-039)
- **Production Readiness**: Application Insights provides out-of-box dashboards, anomaly detection, and alerting
- **Distributed Tracing**: Correlates frontend requests → backend API → agent orchestration → LLM calls
- **Performance Monitoring**: Tracks p95 latency, error rates, and resource utilization

### Implementation Guidance

#### Backend Logging
```python
# backend/src/spec2agent/utils/logging.py
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.trace import config_integration

config_integration.trace_integrations(['logging', 'requests'])

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=app_insights_connection_string))

# Usage
logger.info("Agent orchestration started", extra={
    "custom_dimensions": {
        "event_brief_id": "evt-123",
        "agent": "Event Planner",
        "correlation_id": "corr-456"
    }
})
```

#### Frontend Telemetry
```typescript
// frontend/src/services/telemetry.ts
import { ApplicationInsights } from '@microsoft/applicationinsights-web';

const appInsights = new ApplicationInsights({
  config: {
    connectionString: import.meta.env.VITE_APP_INSIGHTS_CONNECTION_STRING
  }
});
appInsights.loadAppInsights();

export function trackAgentInteraction(agentName: string, action: string) {
  appInsights.trackEvent({
    name: 'AgentInteraction',
    properties: { agent: agentName, action }
  });
}
```

### Implementation Checklist
- [ ] Add Application Insights to Bicep templates
- [ ] Configure opencensus integration in backend
- [ ] Add Application Insights SDK to frontend
- [ ] Define custom metrics for agent performance (timeline slippage, budget variance)
- [ ] Create Application Insights dashboards for SLOs
- [ ] Set up alerts for error rate > 5%, p95 latency > 5s

### Alternatives Considered
- **ELK Stack**: More complex to manage than Application Insights
- **Datadog**: Third-party cost vs. native Azure integration

### References
- Application Insights Python: https://learn.microsoft.com/azure/azure-monitor/app/opencensus-python
- Application Insights JavaScript: https://learn.microsoft.com/azure/azure-monitor/app/javascript

---

## Summary of Decisions

| Area                    | Decision                                  | Key Rationale                                                      |
| ----------------------- | ----------------------------------------- | ------------------------------------------------------------------ |
| **Agent Orchestration** | Microsoft Agent Framework                 | Native Azure integration, declarative design, group chat patterns  |
| **Authentication**      | Managed Identity (azure-identity)         | Zero secrets, AAD token-based, aligns with security best practices |
| **Database**            | Azure SQL + CosmosDB hybrid               | SQL for structured artifacts, CosmosDB for flexible schemas        |
| **Frontend**            | Vite + React 19 + TypeScript + Tailwind   | Performance, type safety, modern patterns, design consistency      |
| **Testing**             | pytest + Vitest + Playwright MCP          | TDD compliance, contract tests, visual regression automation       |
| **Observability**       | Application Insights + Structured Logging | Distributed tracing, auditable metrics, anomaly detection          |
| **Dev Tools**           | context7 MCP + playwright MCP             | Accelerate research and QA automation                              |

---

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items resolved (none identified)
- [x] Technology stack decisions documented with rationale
- [x] Best practices established for each technology
- [x] Alternatives considered and trade-offs documented
- [x] Implementation guidance provided with code examples
- [x] Constitutional alignment verified for all decisions
- [x] References and documentation links provided

**Status**: ✅ **COMPLETE** - Ready for Phase 1 (Design & Contracts)
