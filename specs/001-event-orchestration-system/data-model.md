# Data Model: Event Orchestration System (EODS) v0.1

**Date**: 2025-10-02  
**Feature**: Event Orchestration System  
**Purpose**: Define all data entities, relationships, validation rules, and state transitions

---

## Overview

The Event Orchestration System manages **22 artifact types** organized across **8 lifecycle states** (Initiate → Plan → Research → Budget → Logistics → Confirm → Execute → Postmortem). Artifacts are stored in a hybrid database architecture:
- **Azure SQL**: Structured artifacts requiring relational integrity and ACID guarantees
- **CosmosDB**: Flexible documents with variable schemas (logs, traces, agent decisions)

---

## Entity Relationship Diagram

```
EventBrief (1) ──┬──> (1) Requirements
                 ├──> (1) StakeholderMap
                 ├──> (1) Timeline ──> (N) TaskRegister
                 ├──> (1) BudgetBaseline ──> (1) CostModel ──> (1) BudgetDecision
                 ├──> (N) RiskRegister
                 ├──> (1) VenueCriteria ──┬──> (N) VenueLeads
                 │                        ├──> (N) VenueShortlist
                 │                        ├──> (1) VenueScorecard
                 │                        ├──> (N) VenueAvailability
                 │                        └──> (N) VenueNegotiationNotes
                 ├──> (1) LogisticsPlan ──┬──> (1) Schedule
                 │                        ├──> (1) ResourceRoster
                 │                        ├──> (1) ContingencyPlan
                 │                        └──> (N) VendorContracts
                 ├──> (1) CommunicationsPlan
                 ├──> (N) ChangeLog
                 └──> (N) DecisionLog
```

---

## Storage Architecture

### Azure SQL Entities (Structured Data)

#### 1. EventBrief
**Purpose**: Root entity representing an event planning session  
**Lifecycle State**: Initiate → Plan → Research → Budget → Logistics → Confirm → Execute → Postmortem

```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum

class LifecycleState(str, Enum):
    INITIATE = "Initiate"
    PLAN = "Plan"
    RESEARCH = "Research"
    BUDGET = "Budget"
    LOGISTICS = "Logistics"
    CONFIRM = "Confirm"
    EXECUTE = "Execute"
    POSTMORTEM = "Postmortem"

class EventBrief(SQLModel, table=True):
    __tablename__ = "event_briefs"
    
    # Primary Key
    id: str = Field(primary_key=True)  # Format: evt-YYYYMMDD-{name}
    version: int = Field(default=1)
    
    # Core Attributes
    title: str = Field(max_length=200)
    date_range_start: datetime
    date_range_end: datetime
    audience_size: int = Field(gt=0)
    event_type: str = Field(max_length=50)  # meetup, conference, workshop
    objectives: str
    constraints: str
    
    # Lifecycle Management
    lifecycle_state: LifecycleState = Field(default=LifecycleState.INITIATE)
    
    # Audit Fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(default="system")
    
    # Relationships (lazy loading)
    requirements: Optional["Requirements"] = Relationship(back_populates="event_brief")
    stakeholder_map: Optional["StakeholderMap"] = Relationship(back_populates="event_brief")
    timeline: Optional["Timeline"] = Relationship(back_populates="event_brief")
    budget_baseline: Optional["BudgetBaseline"] = Relationship(back_populates="event_brief")
    venue_criteria: Optional["VenueCriteria"] = Relationship(back_populates="event_brief")
    logistics_plan: Optional["LogisticsPlan"] = Relationship(back_populates="event_brief")
    communications_plan: Optional["CommunicationsPlan"] = Relationship(back_populates="event_brief")
    risk_register: List["RiskRegister"] = Relationship(back_populates="event_brief")
```

**Validation Rules**:
- `date_range_end` must be after `date_range_start`
- `audience_size` must be > 0
- `event_type` must be one of: meetup, conference, workshop, gala, festival
- Lifecycle state transitions must follow valid paths (enforced by state machine)

**Indexes**:
- Primary: `id`
- Composite: `(lifecycle_state, created_at)` for dashboard queries
- Full-text: `(title, objectives)` for search

---

#### 2. Requirements
**Purpose**: Functional and non-functional requirements derived from EventBrief

```python
class Requirements(SQLModel, table=True):
    __tablename__ = "requirements"
    
    id: str = Field(primary_key=True)  # req-{event_brief_id}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Requirements Categories
    functional_requirements: str  # JSON array of requirement strings
    nonfunctional_requirements: str  # JSON array
    must_haves: str  # JSON array
    nice_to_haves: str  # JSON array
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event_brief: "EventBrief" = Relationship(back_populates="requirements")
```

**Validation Rules**:
- All JSON arrays must be valid JSON
- `must_haves` must have at least 1 item
- Requirements must map to EventBrief objectives

---

#### 3. StakeholderMap
**Purpose**: Identifies stakeholders with roles and decision rights

```python
class StakeholderMap(SQLModel, table=True):
    __tablename__ = "stakeholder_maps"
    
    id: str = Field(primary_key=True)  # stk-{event_brief_id}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Stakeholders stored as JSON array
    # [{"name": "Alice", "role": "Sponsor", "email": "alice@example.com", "decision_rights": ["Budget Approval"]}]
    stakeholders: str  # JSON array of stakeholder objects
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event_brief: "EventBrief" = Relationship(back_populates="stakeholder_map")
```

**Validation Rules**:
- At least 1 stakeholder with "Owner" role required
- Email addresses must be valid format
- Decision rights must reference valid approval types

---

#### 4. Timeline
**Purpose**: Event phases, milestones, dependencies, and critical path

```python
class Timeline(SQLModel, table=True):
    __tablename__ = "timelines"
    
    id: str = Field(primary_key=True)  # tl-{event_brief_id}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Timeline Data (JSON structures)
    phases: str  # [{"name": "Planning", "start": "2025-06-01", "end": "2025-06-15"}]
    milestones: str  # [{"name": "Venue Confirmed", "date": "2025-07-01", "dependencies": []}]
    critical_path: str  # ["milestone-1", "milestone-2"]
    
    # Quality Gate Fields
    has_milestones: bool = Field(default=False)
    has_dependencies: bool = Field(default=False)
    has_critical_path: bool = Field(default=False)
    has_orphan_tasks: bool = Field(default=True)  # Must be False to pass gate
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event_brief: "EventBrief" = Relationship(back_populates="timeline")
    tasks: List["TaskRegister"] = Relationship(back_populates="timeline")
```

**Validation Rules** (Quality Gate FR-027):
- `has_milestones` must be True
- `has_dependencies` must be True
- `has_critical_path` must be True
- `has_orphan_tasks` must be False
- All milestone dates must be within EventBrief date range

---

#### 5. TaskRegister
**Purpose**: Tracks all tasks with dependencies and status

```python
class TaskStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class TaskRegister(SQLModel, table=True):
    __tablename__ = "task_registers"
    
    id: str = Field(primary_key=True)  # task-{timeline_id}-{seq}
    timeline_id: str = Field(foreign_key="timelines.id")
    version: int = Field(default=1)
    
    # Task Details
    title: str = Field(max_length=200)
    description: str
    owner: str  # Agent or human name
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED)
    start_date: datetime
    end_date: datetime
    dependencies: str  # JSON array of task IDs
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    timeline: "Timeline" = Relationship(back_populates="tasks")
```

**Validation Rules**:
- `end_date` must be after `start_date`
- Dependencies must reference existing task IDs
- No circular dependencies allowed
- Owner must be valid agent or stakeholder

---

#### 6. BudgetBaseline
**Purpose**: Total budget and category allocations

```python
class BudgetBaseline(SQLModel, table=True):
    __tablename__ = "budget_baselines"
    
    id: str = Field(primary_key=True)  # bud-{event_brief_id}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Budget Summary
    total_budget: float = Field(gt=0)
    currency: str = Field(default="USD", max_length=3)
    
    # Category Allocations (JSON)
    # [{"category": "Venue", "allocated": 50000, "percentage": 0.5}]
    category_allocations: str
    
    # Financial Assumptions
    assumptions: str  # Text field
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event_brief: "EventBrief" = Relationship(back_populates="budget_baseline")
    cost_model: Optional["CostModel"] = Relationship(back_populates="budget_baseline")
```

**Validation Rules**:
- `total_budget` > 0
- Sum of category allocations must equal total_budget
- Currency must be ISO 4217 code

---

#### 7. CostModel
**Purpose**: Detailed budget line items

```python
class CostModel(SQLModel, table=True):
    __tablename__ = "cost_models"
    
    id: str = Field(primary_key=True)  # cost-{budget_baseline_id}
    budget_baseline_id: str = Field(foreign_key="budget_baselines.id")
    version: int = Field(default=1)
    
    # Line Items (JSON)
    # [{"category": "Venue", "item": "Room Rental", "quantity": 3, "unit_cost": 5000, "total": 15000}]
    line_items: str
    
    # Variance Rules (JSON)
    # {"max_variance_percent": 5, "require_approval_threshold": 1000}
    variance_rules: str
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    budget_baseline: "BudgetBaseline" = Relationship(back_populates="cost_model")
    budget_decision: Optional["BudgetDecision"] = Relationship(back_populates="cost_model")
```

**Validation Rules**:
- Sum of line_items.total must match budget_baseline.total_budget
- All quantities must be > 0
- Variance rules must be valid JSON

---

#### 8. BudgetDecision
**Purpose**: Approved budget with change tracking

```python
class BudgetDecision(SQLModel, table=True):
    __tablename__ = "budget_decisions"
    
    id: str = Field(primary_key=True)  # bdec-{cost_model_id}
    cost_model_id: str = Field(foreign_key="cost_models.id")
    version: int = Field(default=1)
    
    # Approved Totals
    approved_total: float = Field(gt=0)
    approved_date: datetime
    
    # Approvals (JSON)
    # [{"approver": "CFO", "role": "Financial Authority", "timestamp": "2025-10-02T10:00:00Z"}]
    approvals: str
    
    # Change References
    change_log_ids: str  # JSON array of change log IDs
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    cost_model: "CostModel" = Relationship(back_populates="budget_decision")
```

**Validation Rules** (Quality Gate FR-029):
- At least 1 approval required
- `approvals` must be valid JSON array
- `change_log_ids` must reference existing ChangeLog documents in CosmosDB

---

#### 9. VenueCriteria
**Purpose**: Requirements for venue selection

```python
class VenueCriteria(SQLModel, table=True):
    __tablename__ = "venue_criteria"
    
    id: str = Field(primary_key=True)  # vc-{event_brief_id}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Criteria
    location_preferences: str  # JSON array: ["downtown", "near transit"]
    min_capacity: int = Field(gt=0)
    max_capacity: int = Field(gt=0)
    required_amenities: str  # JSON array: ["WiFi", "AV equipment"]
    accessibility_requirements: str  # JSON array
    layout_requirements: str  # Text description
    budget_range_min: float = Field(gt=0)
    budget_range_max: float = Field(gt=0)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event_brief: "EventBrief" = Relationship(back_populates="venue_criteria")
    venue_leads: List["VenueLeads"] = Relationship(back_populates="venue_criteria")
    venue_shortlist: List["VenueShortlist"] = Relationship(back_populates="venue_criteria")
    venue_scorecard: Optional["VenueScorecard"] = Relationship(back_populates="venue_criteria")
```

**Validation Rules**:
- `max_capacity` >= `min_capacity`
- `budget_range_max` >= `budget_range_min`
- `min_capacity` must accommodate EventBrief.audience_size

---

#### 10. VenueLeads
**Purpose**: Initial venue candidate list

```python
class VenueLeads(SQLModel, table=True):
    __tablename__ = "venue_leads"
    
    id: str = Field(primary_key=True)  # vl-{venue_criteria_id}-{seq}
    venue_criteria_id: str = Field(foreign_key="venue_criteria.id")
    version: int = Field(default=1)
    
    # Venue Details
    venue_name: str = Field(max_length=200)
    source: str  # "web search", "recommendation", "database"
    contact_info: str  # JSON: {"phone": "...", "email": "...", "website": "..."}
    initial_notes: str
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    venue_criteria: "VenueCriteria" = Relationship(back_populates="venue_leads")
```

---

#### 11. VenueShortlist
**Purpose**: Refined candidates with cost estimates

```python
class VenueShortlist(SQLModel, table=True):
    __tablename__ = "venue_shortlists"
    
    id: str = Field(primary_key=True)  # vs-{venue_criteria_id}-{seq}
    venue_criteria_id: str = Field(foreign_key="venue_criteria.id")
    version: int = Field(default=1)
    
    # Venue Details
    venue_name: str = Field(max_length=200)
    capacity: int = Field(gt=0)
    location: str
    cost_estimate: float = Field(gt=0)
    
    # Scoring
    initial_score: float = Field(ge=0, le=1)  # 0.0 to 1.0
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    venue_criteria: "VenueCriteria" = Relationship(back_populates="venue_shortlist")
```

**Validation Rules**:
- `capacity` must meet VenueCriteria.min_capacity
- `cost_estimate` must be within VenueCriteria budget range
- `initial_score` between 0.0 and 1.0

---

#### 12. VenueScorecard
**Purpose**: Weighted scoring matrix for venue selection

```python
class VenueScorecard(SQLModel, table=True):
    __tablename__ = "venue_scorecards"
    
    id: str = Field(primary_key=True)  # vsc-{venue_criteria_id}
    venue_criteria_id: str = Field(foreign_key="venue_criteria.id")
    version: int = Field(default=1)
    
    # Scoring Criteria (JSON)
    # [{"criterion": "Location", "weight": 0.3}, {"criterion": "Cost", "weight": 0.4}]
    criteria_weights: str
    
    # Candidate Scores (JSON)
    # [{"venue_id": "vs-001", "scores": {"Location": 0.9, "Cost": 0.7}, "total": 0.79}]
    candidate_scores: str
    
    # Selection
    selected_venue_id: Optional[str] = Field(default=None)
    selection_rationale: Optional[str] = Field(default=None)
    
    # Quality Gate Fields
    weights_sum_valid: bool = Field(default=False)  # Must be True (sum = 1.0)
    all_candidates_scored: bool = Field(default=False)  # Must be True
    rationale_captured: bool = Field(default=False)  # Must be True
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    venue_criteria: "VenueCriteria" = Relationship(back_populates="venue_scorecard")
```

**Validation Rules** (Quality Gate FR-028):
- Sum of criteria weights must equal 1.0
- All shortlist candidates must have scores
- `selection_rationale` required when `selected_venue_id` is set

---

#### 13. LogisticsPlan
**Purpose**: Operational workflows and resources

```python
class LogisticsPlan(SQLModel, table=True):
    __tablename__ = "logistics_plans"
    
    id: str = Field(primary_key=True)  # lp-{event_brief_id}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Operational Workflows (JSON)
    # [{"workflow": "Registration", "steps": [...], "resources": [...]}]
    workflows: str
    
    # Resources (JSON references to ResourceRoster)
    resource_ids: str  # JSON array
    
    # Vendors (JSON references to VendorContracts)
    vendor_ids: str  # JSON array
    
    # Layouts (JSON)
    # [{"area": "Main Hall", "layout": "theater", "capacity": 500}]
    layouts: str
    
    # Policies (text)
    policies: str
    
    # Quality Gate Fields
    workflows_linked_to_tasks: bool = Field(default=False)  # Must be True
    contingency_triggers_defined: bool = Field(default=False)  # Must be True
    owners_assigned: bool = Field(default=False)  # Must be True
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event_brief: "EventBrief" = Relationship(back_populates="logistics_plan")
    schedule: Optional["Schedule"] = Relationship(back_populates="logistics_plan")
    resource_roster: Optional["ResourceRoster"] = Relationship(back_populates="logistics_plan")
    contingency_plan: Optional["ContingencyPlan"] = Relationship(back_populates="logistics_plan")
```

**Validation Rules** (Quality Gate FR-030):
- All workflows must link to TaskRegister tasks
- Contingency triggers must be defined
- All workflows must have assigned owners

---

#### 14. Schedule
**Purpose**: Detailed event sessions timeline

```python
class Schedule(SQLModel, table=True):
    __tablename__ = "schedules"
    
    id: str = Field(primary_key=True)  # sch-{logistics_plan_id}
    logistics_plan_id: str = Field(foreign_key="logistics_plans.id")
    version: int = Field(default=1)
    
    # Sessions (JSON)
    # [{"title": "Keynote", "start": "2025-06-01T09:00:00Z", "end": "...", "location": "Hall A", "resources": [...]}]
    sessions: str
    
    # Conflict Detection
    has_resource_conflicts: bool = Field(default=False)  # Must be False
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    logistics_plan: "LogisticsPlan" = Relationship(back_populates="schedule")
```

**Validation Rules**:
- No overlapping sessions in same location
- No resource double-booking (checked via ResourceRoster)
- All session times within EventBrief date range

---

#### 15. ResourceRoster
**Purpose**: Catalog of resources (people, equipment, spaces)

```python
class ResourceType(str, Enum):
    PERSON = "Person"
    EQUIPMENT = "Equipment"
    SPACE = "Space"

class ResourceRoster(SQLModel, table=True):
    __tablename__ = "resource_rosters"
    
    id: str = Field(primary_key=True)  # rr-{logistics_plan_id}
    logistics_plan_id: str = Field(foreign_key="logistics_plans.id")
    version: int = Field(default=1)
    
    # Resources (JSON)
    # [{"id": "res-001", "type": "Person", "name": "John Doe", "role": "AV Tech", "availability": [...], "assignments": [...]}]
    resources: str
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    logistics_plan: "LogisticsPlan" = Relationship(back_populates="resource_roster")
```

**Validation Rules**:
- No resource assigned to overlapping time slots
- Resource availability must cover assignment times

---

#### 16. ContingencyPlan
**Purpose**: Incident response scenarios

```python
class ContingencyPlan(SQLModel, table=True):
    __tablename__ = "contingency_plans"
    
    id: str = Field(primary_key=True)  # cp-{logistics_plan_id}
    logistics_plan_id: str = Field(foreign_key="logistics_plans.id")
    version: int = Field(default=1)
    
    # Scenarios (JSON)
    # [{"scenario": "Venue Cancellation", "trigger": "...", "response": "...", "owner": "..."}]
    scenarios: str
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    logistics_plan: "LogisticsPlan" = Relationship(back_populates="contingency_plan")
```

**Validation Rules**:
- At least 1 scenario per high-risk item in RiskRegister
- All scenarios must have assigned owners
- Response procedures must reference TaskRegister tasks

---

#### 17. VendorContracts
**Purpose**: Vendor terms and SLAs

```python
class VendorContracts(SQLModel, table=True):
    __tablename__ = "vendor_contracts"
    
    id: str = Field(primary_key=True)  # vc-{event_brief_id}-{vendor}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Vendor Details
    vendor_name: str = Field(max_length=200)
    service_type: str  # "catering", "av", "venue", etc.
    
    # Contract Terms (JSON)
    # {"start_date": "...", "end_date": "...", "total_cost": 10000, "payment_terms": "..."}
    terms: str
    
    # SLA (JSON)
    # [{"metric": "Response Time", "target": "< 1 hour", "penalty": "5% discount"}]
    sla: str
    
    # Cancellation Policy
    cancellation_policy: str
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Validation Rules**:
- `terms.total_cost` must fit within BudgetBaseline allocation
- SLA metrics must be measurable
- Cancellation policy must specify notice period and penalties

---

#### 18. CommunicationsPlan
**Purpose**: Stakeholder communication strategy

```python
class CommunicationsPlan(SQLModel, table=True):
    __tablename__ = "communications_plans"
    
    id: str = Field(primary_key=True)  # cp-{event_brief_id}
    event_brief_id: str = Field(foreign_key="event_briefs.id")
    version: int = Field(default=1)
    
    # Communications (JSON)
    # [{"audience": "Sponsors", "channel": "email", "cadence": "weekly", "message": "...", "owner": "..."}]
    communications: str
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event_brief: "EventBrief" = Relationship(back_populates="communications_plan")
```

**Validation Rules**:
- All audiences from StakeholderMap must have communication plan
- Cadence must be valid: daily, weekly, biweekly, monthly, milestone-based
- All communications must have assigned owners

---

### CosmosDB Documents (Flexible Schemas)

#### 19. RiskRegister
**Purpose**: Catalog of risks with mitigation strategies  
**Container**: `risks`  
**Partition Key**: `event_brief_id`

```json
{
  "id": "risk-evt-123-001",
  "type": "risk",
  "event_brief_id": "evt-20251002-conference",
  "version": 1,
  "description": "Venue cancellation within 30 days of event",
  "probability": "low",
  "impact": "high",
  "rating": 7,
  "rating_methodology": "probability (1-5) * impact (1-5)",
  "owner": "Event Planner Agent",
  "mitigation_strategies": [
    "Contract requires 60-day cancellation notice",
    "Backup venue identified in VenueShortlist",
    "Insurance policy covers venue cancellation"
  ],
  "status": "mitigated",
  "created_at": "2025-10-02T10:00:00Z",
  "updated_at": "2025-10-02T12:00:00Z"
}
```

**Validation Rules**:
- `probability` ∈ {very_low, low, medium, high, very_high}
- `impact` ∈ {very_low, low, medium, high, very_high}
- `rating` must be consistent with methodology
- High-rated risks (>= 8) require mitigation strategies

---

#### 20. ChangeLog
**Purpose**: Tracks all artifact changes  
**Container**: `changelogs`  
**Partition Key**: `event_brief_id`

```json
{
  "id": "change-evt-123-045",
  "type": "change",
  "event_brief_id": "evt-20251002-conference",
  "version": 1,
  "change_type": "budget_adjustment",
  "description": "Increased venue budget by $5,000 due to AV equipment requirements",
  "date": "2025-10-02T14:00:00Z",
  "impact": "BudgetBaseline.category_allocations['Venue'] increased; BudgetDecision requires re-approval",
  "impacted_artifacts": [
    {"artifact_type": "BudgetBaseline", "artifact_id": "bud-evt-123", "version": 2}
  ],
  "approvals": [
    {"approver": "CFO", "status": "pending", "requested_at": "2025-10-02T14:05:00Z"}
  ],
  "initiated_by": "Budget Analyst Agent",
  "_ts": 1696257600
}
```

**Validation Rules** (Quality Gate FR-029):
- `impacted_artifacts` must reference existing artifacts
- Budget changes > $1,000 require approval
- All approvals must be captured before BudgetDecision is updated

---

#### 21. DecisionLog
**Purpose**: Records all agent and human decisions  
**Container**: `decisions`  
**Partition Key**: `event_brief_id`

```json
{
  "id": "dec-evt-123-012",
  "type": "decision",
  "event_brief_id": "evt-20251002-conference",
  "version": 1,
  "timestamp": "2025-10-02T11:30:00Z",
  "owner": "Venue Researcher Agent",
  "description": "Selected Venue A (Grand Conference Center) over Venue B (City Hall)",
  "rationale": "Venue A scored 0.89 vs Venue B 0.76 on VenueScorecard. Key differentiators: accessibility (A: 1.0, B: 0.6), AV equipment (A: 1.0, B: 0.8)",
  "alternatives_considered": [
    {"option": "Venue B", "score": 0.76, "pros": ["Lower cost", "Central location"], "cons": ["Limited accessibility", "Older AV equipment"]}
  ],
  "impacted_artifacts": [
    {"artifact_type": "VenueScorecard", "artifact_id": "vsc-evt-123", "field": "selected_venue_id"}
  ],
  "approvals": [
    {"approver": "Event Planner Agent", "status": "approved", "timestamp": "2025-10-02T11:45:00Z"},
    {"approver": "Human Stakeholder", "status": "approved", "timestamp": "2025-10-02T12:00:00Z"}
  ],
  "decision_type": "venue_selection",
  "_ts": 1696248600
}
```

**Validation Rules** (FR-025):
- Human approvals required for: BudgetDecision, VendorContracts, final Venue selection
- Rationale must reference quantitative criteria (e.g., scorecard scores)
- All alternatives must be documented

---

#### 22. Agent Execution Traces
**Purpose**: Telemetry for agent orchestration debugging  
**Container**: `traces`  
**Partition Key**: `event_brief_id`

```json
{
  "id": "trace-evt-123-session-001-step-042",
  "type": "trace",
  "event_brief_id": "evt-20251002-conference",
  "session_id": "session-001",
  "agent_name": "Event Planner Agent",
  "instruction_level": "Intermediate",
  "timestamp": "2025-10-02T10:15:32.123Z",
  "step": 42,
  "action": "invoke_agent",
  "target_agent": "Venue Researcher Agent",
  "input_artifacts": [
    {"type": "VenueCriteria", "id": "vc-evt-123", "version": 1}
  ],
  "output_artifacts": [
    {"type": "VenueLeads", "id": "vl-vc-123-001", "version": 1}
  ],
  "duration_ms": 1250,
  "status": "success",
  "correlation_id": "corr-20251002-10152",
  "_ts": 1696244132
}
```

**Validation Rules**:
- All agent invocations must be traced
- Correlation IDs enable end-to-end tracing across agents
- Failures include error messages and stack traces

---

## State Transitions & Lifecycle Management

### Lifecycle State Machine

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Event Planning Lifecycle                      │
└──────────────────────────────────────────────────────────────────────┘

[Initiate] → [Plan] → [Research] → [Budget] → [Logistics] → [Confirm] → [Execute] → [Postmortem]
    ↓           ↓          ↓            ↓           ↓            ↓           ↓           ↓
 EventBrief   Timeline   Venues     CostModel   LogPlan    BudgetDec    Schedule   Metrics
 Requirements TaskReg    Scorecard  BudgetBase  Resources  Approvals    Runbook    Lessons
 StakeMap     RiskReg                           VendorCon
```

### Transition Preconditions (Quality Gates)

| From State     | To State       | Required Artifacts                                                                   | Quality Gates                                                                         |
| -------------- | -------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| **Initiate**   | **Plan**       | EventBrief, Requirements, StakeholderMap                                             | EventBrief validated, Stakeholders identified                                         |
| **Plan**       | **Research**   | Timeline (with QG), TaskRegister                                                     | Timeline QG passed (FR-027): milestones, dependencies, critical path, no orphans      |
| **Research**   | **Budget**     | VenueCriteria, VenueShortlist (≥3), VenueScorecard                                   | VenueScorecard QG passed (FR-028): weights sum to 1, all scored, rationale captured   |
| **Budget**     | **Logistics**  | BudgetBaseline, CostModel, BudgetDecision                                            | BudgetDecision QG passed (FR-029): approvals recorded, changes in ChangeLog           |
| **Logistics**  | **Confirm**    | LogisticsPlan, Schedule, ResourceRoster, ContingencyPlan                             | LogisticsPlan QG passed (FR-030): workflows linked, triggers defined, owners assigned |
| **Confirm**    | **Execute**    | All artifacts validated, Human approvals on BudgetDecision + VendorContracts + Venue | All approvals received, no blocking risks                                             |
| **Execute**    | **Postmortem** | Schedule executed, ContingencyPlan triggered (if incidents)                          | Event completed or cancelled                                                          |
| **Postmortem** | (End)          | Metrics, Lessons Learned document                                                    | Post-event review complete                                                            |

### Transition Implementation

```python
# backend/src/spec2agent/orchestration/lifecycle_manager.py

from typing import List, Dict
from sqlmodel import Session, select
from .models import EventBrief, LifecycleState

class LifecycleTransitionError(Exception):
    """Raised when preconditions for state transition are not met"""
    pass

class LifecycleManager:
    """Manages EventBrief lifecycle state transitions with quality gate enforcement"""
    
    VALID_TRANSITIONS = {
        LifecycleState.INITIATE: [LifecycleState.PLAN],
        LifecycleState.PLAN: [LifecycleState.RESEARCH],
        LifecycleState.RESEARCH: [LifecycleState.BUDGET],
        LifecycleState.BUDGET: [LifecycleState.LOGISTICS],
        LifecycleState.LOGISTICS: [LifecycleState.CONFIRM],
        LifecycleState.CONFIRM: [LifecycleState.EXECUTE],
        LifecycleState.EXECUTE: [LifecycleState.POSTMORTEM],
        LifecycleState.POSTMORTEM: []
    }
    
    def __init__(self, session: Session):
        self.session = session
    
    def transition(self, event_brief_id: str, target_state: LifecycleState) -> EventBrief:
        """Transition EventBrief to target state after validating preconditions"""
        
        # Load event brief
        event_brief = self.session.get(EventBrief, event_brief_id)
        if not event_brief:
            raise ValueError(f"EventBrief {event_brief_id} not found")
        
        # Check valid transition
        if target_state not in self.VALID_TRANSITIONS[event_brief.lifecycle_state]:
            raise LifecycleTransitionError(
                f"Invalid transition from {event_brief.lifecycle_state} to {target_state}"
            )
        
        # Validate preconditions
        self._validate_preconditions(event_brief, target_state)
        
        # Update state
        event_brief.lifecycle_state = target_state
        event_brief.updated_at = datetime.utcnow()
        self.session.add(event_brief)
        self.session.commit()
        self.session.refresh(event_brief)
        
        return event_brief
    
    def _validate_preconditions(self, event_brief: EventBrief, target_state: LifecycleState):
        """Validate quality gates for state transition"""
        
        if target_state == LifecycleState.PLAN:
            self._validate_plan_preconditions(event_brief)
        elif target_state == LifecycleState.RESEARCH:
            self._validate_research_preconditions(event_brief)
        elif target_state == LifecycleState.BUDGET:
            self._validate_budget_preconditions(event_brief)
        elif target_state == LifecycleState.LOGISTICS:
            self._validate_logistics_preconditions(event_brief)
        elif target_state == LifecycleState.CONFIRM:
            self._validate_confirm_preconditions(event_brief)
        elif target_state == LifecycleState.EXECUTE:
            self._validate_execute_preconditions(event_brief)
    
    def _validate_research_preconditions(self, event_brief: EventBrief):
        """Validate Timeline quality gate (FR-027)"""
        if not event_brief.timeline:
            raise LifecycleTransitionError("Timeline not found")
        
        tl = event_brief.timeline
        if not tl.has_milestones:
            raise LifecycleTransitionError("Timeline missing milestones")
        if not tl.has_dependencies:
            raise LifecycleTransitionError("Timeline missing dependencies")
        if not tl.has_critical_path:
            raise LifecycleTransitionError("Timeline missing critical path")
        if tl.has_orphan_tasks:
            raise LifecycleTransitionError("Timeline has orphan tasks")
    
    # ... similar validators for other states ...
```

---

## Validation & Constraints Summary

### Global Constraints
- All artifact IDs follow naming convention: `{type}-{parent_id}-{suffix}`
- All timestamps in UTC ISO 8601 format
- All JSON fields validated against schemas on write
- All foreign keys enforced with cascading deletes
- All currency fields use ISO 4217 codes

### Performance Optimization
- Indexes on: `event_brief_id`, `lifecycle_state`, `created_at`, `updated_at`
- Composite indexes on frequently joined columns
- Lazy loading for relationships to minimize query overhead
- Connection pooling for both SQL and CosmosDB

### Security
- All database connections use Managed Identity (no connection strings)
- Row-level security on sensitive artifacts (VendorContracts, BudgetDecision)
- Audit fields (created_by, updated_at) populated automatically
- Change history tracked in ChangeLog (immutable, append-only)

---

## Phase 1 Checklist: Data Model Complete

- [x] 18 SQL entities defined with SQLModel schemas
- [x] 4 CosmosDB document types defined with JSON schemas
- [x] All relationships and foreign keys specified
- [x] Validation rules documented for each entity
- [x] Quality gates mapped to entity fields
- [x] State machine transitions defined with preconditions
- [x] Indexes and performance optimizations identified
- [x] Security constraints documented

**Status**: ✅ **COMPLETE** - Ready for contract generation
