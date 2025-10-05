# API Contracts - Multi-Agent Event Planning System

**Date**: 2025-10-04  
**API Version**: v1  
**Base URL**: `/v1`

## Overview

REST API for multi-agent event planning system. All endpoints require proper request/response schemas defined via Pydantic models.

---

## Endpoints

### 1. Create Planning Session

**Endpoint**: `POST /v1/sessions`

**Purpose**: Initiate a new event planning session with initial request.

**Request Body**:
```json
{
  "event_type": "corporate holiday party",
  "attendee_count": 100,
  "budget": 10000.0,
  "location": "Seattle",
  "date_timeframe": "December 2025",
  "additional_details": "Prefer downtown venue",
  "preferences": {
    "dietary_restrictions": ["vegetarian", "gluten-free"],
    "formality": "casual"
  }
}
```

**Response** (201 Created):
```json
{
  "session_id": "abc-123-def-456",
  "status": "active",
  "workflow_id": "workflow-789",
  "created_at": "2025-10-04T12:00:00Z",
  "expires_at": "2025-10-05T12:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request data (e.g., attendee_count > 500)
- `500 Internal Server Error`: Server error

**Schema**: `EventRequest` → `SessionContext`

---

### 2. Get Session Status

**Endpoint**: `GET /v1/sessions/{session_id}`

**Purpose**: Retrieve current session state including workflow progress.

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response** (200 OK):
```json
{
  "session_id": "abc-123-def-456",
  "status": "active",
  "workflow_state": {
    "workflow_id": "workflow-789",
    "current_phase": "parallel_research",
    "agent_statuses": {
      "event_coordinator": "completed",
      "budget_analyst": "completed",
      "venue_specialist": "active",
      "catering_coordinator": "active",
      "logistics_manager": "pending"
    },
    "pending_question": null
  },
  "created_at": "2025-10-04T12:00:00Z",
  "updated_at": "2025-10-04T12:05:30Z",
  "expires_at": "2025-10-05T12:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Session does not exist or expired
- `500 Internal Server Error`: Server error

**Schema**: `SessionContext`

---

### 3. Stream Workflow Status (SSE)

**Endpoint**: `GET /v1/sessions/{session_id}/status/stream`

**Purpose**: Server-Sent Events stream for real-time agent status updates.

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response**: `text/event-stream`

**Event Format**:
```
data: {"agent_role": "venue_specialist", "status": "active", "timestamp": "2025-10-04T12:05:30Z"}

data: {"agent_role": "venue_specialist", "status": "completed", "output_summary": "3 venues found", "timestamp": "2025-10-04T12:06:15Z"}

data: {"phase": "logistics_planning", "active_agents": ["logistics_manager"], "timestamp": "2025-10-04T12:06:20Z"}
```

**Event Types**:
- `agent_status_change`: Agent status updated
- `phase_change`: Workflow phase transition
- `user_handoff`: Question for user
- `workflow_complete`: All agents finished
- `error`: Workflow error

**Error Responses**:
- `404 Not Found`: Session does not exist
- `500 Internal Server Error`: Server error

**Schema**: Custom event objects (agent status, phase change, etc.)

---

### 4. Answer User Question

**Endpoint**: `POST /v1/sessions/{session_id}/questions/{question_id}/answer`

**Purpose**: Provide user response to agent question (handoff).

**Path Parameters**:
- `session_id` (string, required): Session UUID
- `question_id` (string, required): Question UUID

**Request Body**:
```json
{
  "user_response": "formal sit-down dinner"
}
```

**Response** (200 OK):
```json
{
  "question_id": "question-123",
  "status": "answered",
  "workflow_resumed": true,
  "resumed_at": "2025-10-04T12:10:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Session or question does not exist
- `400 Bad Request`: Question already answered
- `500 Internal Server Error`: Server error

**Schema**: `UserQuestion` update

---

### 5. Get Event Plan

**Endpoint**: `GET /v1/sessions/{session_id}/plan`

**Purpose**: Retrieve the complete event plan (after workflow completion).

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response** (200 OK):
```json
{
  "plan_id": "plan-456",
  "session_id": "abc-123-def-456",
  "event_request": { ... },
  "budget_allocation": {
    "total_budget": 10000.0,
    "allocations": {
      "venue": {"amount": 4000.0, "percentage": 40, "rationale": "..."},
      "catering": {"amount": 3500.0, "percentage": 35, "rationale": "..."},
      "logistics": {"amount": 1500.0, "percentage": 15, "rationale": "..."},
      "contingency": {"amount": 1000.0, "percentage": 10, "rationale": "..."}
    },
    "justification": "Balanced allocation for corporate event..."
  },
  "venue_recommendations": [
    {
      "venue_name": "Seattle Convention Center",
      "location": "Downtown Seattle",
      "capacity": 150,
      "cost": 3800.0,
      "match_score": 95,
      "pros": ["Central location", "Modern facilities"],
      "cons": ["Slightly over budget"],
      "amenities": ["AV equipment", "Catering kitchen", "Parking"]
    }
  ],
  "catering_options": [
    {
      "menu_style": "buffet",
      "description": "Casual buffet with international cuisine",
      "cost_per_person": 35.0,
      "total_cost": 3500.0,
      "dietary_accommodations": ["vegetarian", "gluten-free"],
      "service_type": "full_service"
    }
  ],
  "event_timeline": {
    "milestones": [
      {"time": "14:00", "event": "Setup begins", "description": "..."},
      {"time": "17:00", "event": "Guests arrive", "description": "..."}
    ],
    "total_duration": "6 hours"
  },
  "created_at": "2025-10-04T12:15:00Z",
  "version": 1
}
```

**Error Responses**:
- `404 Not Found`: Session or plan does not exist
- `409 Conflict`: Workflow not yet complete
- `500 Internal Server Error`: Server error

**Schema**: `EventPlan`

---

### 6. Update Event Request

**Endpoint**: `PATCH /v1/sessions/{session_id}/request`

**Purpose**: Modify event requirements mid-planning (triggers re-orchestration).

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Request Body** (partial update):
```json
{
  "budget": 15000.0,
  "preferences": {
    "formality": "formal"
  }
}
```

**Response** (200 OK):
```json
{
  "session_id": "abc-123-def-456",
  "updated_fields": ["budget", "preferences.formality"],
  "workflow_restarted": true,
  "affected_agents": ["budget_analyst", "venue_specialist", "catering_coordinator"],
  "updated_at": "2025-10-04T12:20:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Session does not exist
- `400 Bad Request`: Invalid update data
- `409 Conflict`: Cannot update completed workflow
- `500 Internal Server Error`: Server error

**Schema**: `EventRequest` partial update

---

### 7. Get Conversation History

**Endpoint**: `GET /v1/sessions/{session_id}/conversation`

**Purpose**: Retrieve full conversation history for session.

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Query Parameters**:
- `limit` (integer, optional, default=50): Max messages to return
- `offset` (integer, optional, default=0): Pagination offset

**Response** (200 OK):
```json
{
  "session_id": "abc-123-def-456",
  "messages": [
    {
      "message_id": "msg-1",
      "role": "user",
      "content": "I need to plan a company holiday party...",
      "timestamp": "2025-10-04T12:00:00Z"
    },
    {
      "message_id": "msg-2",
      "role": "agent",
      "agent_role": "event_coordinator",
      "content": "I'll help you plan this event. Let me start by...",
      "timestamp": "2025-10-04T12:00:05Z"
    }
  ],
  "total_messages": 15,
  "has_more": false
}
```

**Error Responses**:
- `404 Not Found`: Session does not exist
- `500 Internal Server Error`: Server error

**Schema**: List of `ConversationMessage`

---

### 8. List User Sessions

**Endpoint**: `GET /v1/users/{user_id}/sessions`

**Purpose**: Get all sessions for a user (active and expired).

**Path Parameters**:
- `user_id` (string, required): User identifier

**Query Parameters**:
- `status` (string, optional): Filter by status (active, completed, expired)
- `limit` (integer, optional, default=20): Max results
- `offset` (integer, optional, default=0): Pagination offset

**Response** (200 OK):
```json
{
  "user_id": "user-789",
  "sessions": [
    {
      "session_id": "abc-123",
      "status": "completed",
      "event_type": "corporate holiday party",
      "created_at": "2025-10-04T12:00:00Z",
      "updated_at": "2025-10-04T12:15:00Z"
    }
  ],
  "total_sessions": 3,
  "has_more": false
}
```

**Error Responses**:
- `404 Not Found`: User has no sessions
- `500 Internal Server Error`: Server error

**Schema**: List of `SessionContext` (summary view)

---

### 9. Delete Session

**Endpoint**: `DELETE /v1/sessions/{session_id}`

**Purpose**: Manually delete a session before TTL expiration.

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response** (204 No Content): Empty body

**Error Responses**:
- `404 Not Found`: Session does not exist
- `500 Internal Server Error`: Server error

---

### 10. Health Check

**Endpoint**: `GET /v1/health`

**Purpose**: API health and dependency status.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "cosmos_db": "connected",
    "azure_openai": "available",
    "agent_framework": "initialized"
  },
  "timestamp": "2025-10-04T12:00:00Z"
}
```

**Error Responses**:
- `503 Service Unavailable`: One or more dependencies unhealthy

---

## Error Response Format

All error responses follow consistent schema:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "attendee_count must be between 1 and 500",
    "details": {
      "field": "attendee_count",
      "value": 600,
      "constraint": "le=500"
    },
    "timestamp": "2025-10-04T12:00:00Z",
    "request_id": "req-123"
  }
}
```

**Error Codes**:
- `VALIDATION_ERROR`: Request validation failed
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Operation conflict (e.g., modify completed workflow)
- `RATE_LIMIT`: Too many requests
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: Dependency unavailable

---

## Authentication

**Current**: None (demo/PoC)

**Future**: Azure AD B2C or managed identity tokens

---

## Rate Limiting

**Current**: None (demo/PoC)

**Future**: 100 requests/minute per user

---

## CORS Configuration

**Allowed Origins**:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative frontend)
- Production domain (TBD during deployment)

**Allowed Methods**: `GET`, `POST`, `PATCH`, `DELETE`, `OPTIONS`

**Allowed Headers**: `Content-Type`, `Authorization`

---

## Contract Testing Requirements

Each endpoint requires:
1. **Schema validation test**: Request/response match Pydantic models
2. **Status code test**: Correct HTTP status for success/error cases
3. **Error handling test**: Proper error response format
4. **Edge case test**: Boundary values (e.g., attendee_count=500)

Tests must be written BEFORE implementation (TDD).

---

**Status**: ✅ 10 API endpoints defined with request/response schemas.
