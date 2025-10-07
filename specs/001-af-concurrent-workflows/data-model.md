# Phase 1: Data Model - Multi-Agent Event Planning System

**Date**: 2025-10-04  
**Status**: Complete

## Entity Definitions

All entities use **Pydantic v2** for validation, serialization, and type safety.

---

### 1. Event Request

**Purpose**: Represents the initial user request to plan an event.

**Fields**:
```python
class EventRequest(BaseModel):
    """User's initial event planning request."""
    
    event_type: str  # e.g., "corporate party", "wedding", "conference"
    attendee_count: int = Field(gt=0, le=500)  # Max 500 per NFR-005
    budget: float = Field(gt=0)  # Total budget in USD
    location: str  # City or venue area
    date_timeframe: str  # e.g., "December 2025", "June 15, 2026"
    additional_details: str | None = None  # Optional user notes
    preferences: dict[str, Any] = Field(default_factory=dict)  # Dietary, style, etc.
    
    # Metadata
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Validation Rules**:
- `attendee_count`: Must be 1-500 (NFR-005)
- `budget`: Must be positive
- `date_timeframe`: Free text (agent parses)

**Relationships**:
- One EventRequest → One SessionContext
- One EventRequest → One EventPlan (output)

---

### 2. Session Context

**Purpose**: Represents the persistent state of a planning session.

**Fields**:
```python
class SessionContext(BaseModel):
    """Persistent session state for conversation and workflow."""
    
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str | None = None  # Optional user identification
    
    # Request and state
    event_request: EventRequest
    workflow_state: WorkflowState
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # created_at + 24 hours (NFR per spec)
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Cosmos DB fields
    id: str = Field(alias="_id", default_factory=lambda: str(uuid4()))
    partition_key: str = Field(alias="session_id")
    ttl: int = 86400  # 24 hours in seconds
```

**Status Enum**:
```python
class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"  # User handoff in progress
    COMPLETED = "completed"
    EXPIRED = "expired"
    ERROR = "error"
```

**Relationships**:
- One SessionContext → One EventRequest
- One SessionContext → One WorkflowState
- One SessionContext → Many ConversationMessage

**Storage**: Cosmos DB `sessions` container

---

### 3. Workflow State

**Purpose**: Tracks agent orchestration state and execution progress.

**Fields**:
```python
class WorkflowState(BaseModel):
    """State of the multi-agent workflow execution."""
    
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    current_phase: WorkflowPhase
    agent_statuses: dict[AgentRole, AgentStatus] = Field(default_factory=dict)
    execution_history: list[AgentExecution] = Field(default_factory=list)
    
    # Dependencies and coordination
    pending_agents: list[AgentRole] = Field(default_factory=list)
    completed_agents: list[AgentRole] = Field(default_factory=list)
    failed_agents: list[AgentRole] = Field(default_factory=list)
    
    # User interaction
    pending_question: UserQuestion | None = None
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
```

**Phase Enum**:
```python
class WorkflowPhase(str, Enum):
    INITIALIZATION = "initialization"  # Coordinator analyzing request
    BUDGET_ANALYSIS = "budget_analysis"  # Budget Analyst working
    PARALLEL_RESEARCH = "parallel_research"  # Venue + Catering concurrent
    LOGISTICS_PLANNING = "logistics_planning"  # Logistics Manager final phase
    USER_HANDOFF = "user_handoff"  # Waiting for user response
    COMPLETED = "completed"
    ERROR = "error"
```

**Agent Status Tracking**:
```python
class AgentStatus(str, Enum):
    PENDING = "pending"  # Not started, waiting for dependencies
    ACTIVE = "active"  # Currently executing
    COMPLETED = "completed"  # Finished successfully
    WAITING = "waiting"  # Paused for user input
    FAILED = "failed"  # Encountered error
```

**Agent Roles**:
```python
class AgentRole(str, Enum):
    EVENT_COORDINATOR = "event_coordinator"
    BUDGET_ANALYST = "budget_analyst"
    VENUE_SPECIALIST = "venue_specialist"
    CATERING_COORDINATOR = "catering_coordinator"
    LOGISTICS_MANAGER = "logistics_manager"
```

---

### 4. Agent Execution

**Purpose**: Records a single agent's execution details.

**Fields**:
```python
class AgentExecution(BaseModel):
    """Record of a single agent execution."""
    
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_role: AgentRole
    
    # Execution details
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_ms: int | None = None
    status: AgentStatus
    
    # Input/Output
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    
    # OpenAI usage (for monitoring)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
```

**Relationships**:
- Many AgentExecution → One WorkflowState

---

### 5. User Question (Handoff)

**Purpose**: Represents a question from an agent requiring user input.

**Fields**:
```python
class UserQuestion(BaseModel):
    """Agent question requiring user response for handoff."""
    
    question_id: str = Field(default_factory=lambda: str(uuid4()))
    requesting_agent: AgentRole
    
    # Question details
    question_text: str  # Human-readable question
    context: str  # Why this info is needed
    question_type: QuestionType
    options: list[str] | None = None  # For multiple choice
    
    # Response
    user_response: str | None = None
    responded_at: datetime | None = None
    
    # Metadata
    asked_at: datetime = Field(default_factory=datetime.utcnow)
```

**Question Type Enum**:
```python
class QuestionType(str, Enum):
    FREE_TEXT = "free_text"
    MULTIPLE_CHOICE = "multiple_choice"
    YES_NO = "yes_no"
    NUMERIC = "numeric"
```

**Example**:
```json
{
  "question_id": "abc-123",
  "requesting_agent": "catering_coordinator",
  "question_text": "What dietary restrictions should we accommodate?",
  "context": "To suggest appropriate catering options",
  "question_type": "multiple_choice",
  "options": ["Vegetarian", "Vegan", "Gluten-free", "None", "Other"],
  "asked_at": "2025-10-04T12:00:00Z"
}
```

---

### 6. Event Plan (Output)

**Purpose**: The final comprehensive event plan produced by all agents.

**Fields**:
```python
class EventPlan(BaseModel):
    """Complete event plan output from all agents."""
    
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str  # Links back to session
    event_request: EventRequest  # Original request
    
    # Agent outputs
    budget_allocation: BudgetAllocation
    venue_recommendations: list[VenueRecommendation]
    catering_options: list[CateringOption]
    event_timeline: EventTimeline
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1  # Increments on modifications
    
    # Cosmos DB fields
    id: str = Field(alias="_id", default_factory=lambda: str(uuid4()))
    partition_key: str = Field(alias="user_id")  # Partition by user
```

**Relationships**:
- One EventPlan → One EventRequest
- One EventPlan → One BudgetAllocation
- One EventPlan → Many VenueRecommendation
- One EventPlan → Many CateringOption
- One EventPlan → One EventTimeline

**Storage**: Cosmos DB `event_plans` container (no TTL - permanent)

---

### 7. Budget Allocation

**Purpose**: Budget breakdown from Budget Analyst agent.

**Fields**:
```python
class BudgetAllocation(BaseModel):
    """Budget breakdown across categories."""
    
    total_budget: float
    allocations: dict[str, CategoryAllocation]
    justification: str  # Why these percentages
    
    # Standard categories
    @property
    def venue_budget(self) -> float:
        return self.allocations.get("venue", CategoryAllocation(amount=0)).amount
    
    @property
    def catering_budget(self) -> float:
        return self.allocations.get("catering", CategoryAllocation(amount=0)).amount
    
    @property
    def logistics_budget(self) -> float:
        return self.allocations.get("logistics", CategoryAllocation(amount=0)).amount
    
    @property
    def contingency(self) -> float:
        return self.allocations.get("contingency", CategoryAllocation(amount=0)).amount


class CategoryAllocation(BaseModel):
    """Single budget category allocation."""
    
    category: str
    amount: float
    percentage: float  # 0-100
    rationale: str
```

**Validation**:
- Sum of all allocations must equal total_budget
- All percentages must sum to 100

---

### 8. Venue Recommendation

**Purpose**: Venue suggestion from Venue Specialist agent.

**Fields**:
```python
class VenueRecommendation(BaseModel):
    """Single venue recommendation."""
    
    venue_name: str
    location: str
    capacity: int
    cost: float
    
    # Details
    amenities: list[str] = Field(default_factory=list)
    availability: str  # e.g., "Available for your date"
    
    # Scoring
    match_score: float = Field(ge=0, le=100)  # 0-100 match to criteria
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    tradeoffs: str | None = None  # If not perfect match
    
    # Contact
    website: str | None = None
    phone: str | None = None
```

**Ranking**: Venues sorted by `match_score` descending

---

### 9. Catering Option

**Purpose**: Catering proposal from Catering Coordinator agent.

**Fields**:
```python
class CateringOption(BaseModel):
    """Single catering proposal."""
    
    menu_style: MenuStyle
    description: str
    cost_per_person: float
    total_cost: float  # cost_per_person * attendee_count
    
    # Menu details
    sample_menu_items: list[str] = Field(default_factory=list)
    dietary_accommodations: list[str] = Field(default_factory=list)
    service_type: ServiceType
    
    # Extras
    includes_beverages: bool = False
    includes_dessert: bool = False
    setup_included: bool = False


class MenuStyle(str, Enum):
    BUFFET = "buffet"
    PLATED = "plated"
    COCKTAIL = "cocktail"
    FAMILY_STYLE = "family_style"


class ServiceType(str, Enum):
    FULL_SERVICE = "full_service"
    DROP_OFF = "drop_off"
    SELF_SERVE = "self_serve"
```

---

### 10. Event Timeline

**Purpose**: Event schedule from Logistics Manager agent.

**Fields**:
```python
class EventTimeline(BaseModel):
    """Event schedule and logistics plan."""
    
    milestones: list[Milestone] = Field(default_factory=list)
    total_duration: str  # e.g., "6 hours"
    setup_time: str  # e.g., "2 hours before"
    teardown_time: str  # e.g., "1 hour after"
    
    # Coordination
    responsible_parties: dict[str, str] = Field(default_factory=dict)
    critical_deadlines: list[str] = Field(default_factory=list)


class Milestone(BaseModel):
    """Single timeline milestone."""
    
    time: str  # e.g., "14:00" or "2 hours before event"
    event: str  # e.g., "Setup begins", "Guests arrive"
    description: str
    responsible_party: str | None = None
    duration: str | None = None
```

**Example**:
```json
{
  "milestones": [
    {"time": "14:00", "event": "Setup begins", "description": "Venue staff sets up tables and chairs"},
    {"time": "16:45", "event": "Catering arrives", "description": "Food delivery and setup"},
    {"time": "17:00", "event": "Guests start arriving", "description": "Cocktail hour begins"},
    {"time": "18:00", "event": "Dinner service", "description": "Plated dinner service"},
    {"time": "20:00", "event": "Event concludes", "description": "Guests depart"},
    {"time": "21:00", "event": "Teardown complete", "description": "Venue cleanup finished"}
  ]
}
```

---

### 11. Conversation Message

**Purpose**: Individual message in conversation history.

**Fields**:
```python
class ConversationMessage(BaseModel):
    """Single message in conversation."""
    
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    agent_role: AgentRole | None = None  # If from agent
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
```

**Relationships**:
- Many ConversationMessage → One SessionContext

**Storage**: Embedded in SessionContext document (max 100 messages)

---

## Entity Relationship Diagram

```
SessionContext (1)
├─── EventRequest (1)
├─── WorkflowState (1)
│    ├─── AgentExecution (0..*)
│    └─── UserQuestion (0..1)
├─── ConversationMessage (0..*)
└─── EventPlan (0..1)
     ├─── BudgetAllocation (1)
     ├─── VenueRecommendation (1..*)
     ├─── CateringOption (1..*)
     └─── EventTimeline (1)
```

---

## Validation Rules Summary

| Entity              | Key Validation                         | Rationale                   |
| ------------------- | -------------------------------------- | --------------------------- |
| EventRequest        | `attendee_count` 1-500                 | NFR-005 max capacity        |
| EventRequest        | `budget` > 0                           | Must have positive budget   |
| SessionContext      | `ttl` = 86400                          | 24-hour expiration (FR-022) |
| WorkflowState       | Status transitions follow phase order  | Prevent invalid state       |
| AgentExecution      | `duration_ms` calculated on completion | Performance monitoring      |
| BudgetAllocation    | Sum = total_budget                     | Budget integrity            |
| VenueRecommendation | `match_score` 0-100                    | Normalized ranking          |
| EventTimeline       | Milestones in chronological order      | Logical timeline            |

---

## State Transitions

### Session Status Transitions
```
ACTIVE → PAUSED (user handoff)
PAUSED → ACTIVE (user responds)
ACTIVE → COMPLETED (workflow done)
ACTIVE → ERROR (failure)
ACTIVE → EXPIRED (24h TTL)
```

### Agent Status Transitions
```
PENDING → ACTIVE (dependency satisfied)
ACTIVE → WAITING (needs user input)
WAITING → ACTIVE (user responds)
ACTIVE → COMPLETED (success)
ACTIVE → FAILED (error)
```

### Workflow Phase Transitions
```
INITIALIZATION → BUDGET_ANALYSIS
BUDGET_ANALYSIS → PARALLEL_RESEARCH
PARALLEL_RESEARCH → LOGISTICS_PLANNING
LOGISTICS_PLANNING → COMPLETED

Any phase → USER_HANDOFF (agent needs input)
USER_HANDOFF → [previous phase] (resume)
Any phase → ERROR (failure)
```

---

## Cosmos DB Schema

### Container: `sessions`
- **Partition Key**: `/session_id`
- **TTL**: 86400 seconds (24 hours)
- **Indexes**:
  - `/session_id` (automatic)
  - `/user_id` (for user's sessions query)
  - `/created_at` (for time-based queries)
  - `/status` (for active sessions query)

### Container: `event_plans`
- **Partition Key**: `/user_id`
- **TTL**: None (permanent storage)
- **Indexes**:
  - `/user_id` (automatic)
  - `/session_id` (link to session)
  - `/created_at` (for recent plans)

---

**Status**: ✅ Data model complete with 11 entities, validation rules, and relationships defined.
