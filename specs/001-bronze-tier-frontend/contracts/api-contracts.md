# API Contracts: Bronze Tier Frontend (Silver Tier Preparation)

**Feature**: Bronze Tier Frontend  
**Date**: 2026-02-21  
**Branch**: 1-bronze-tier-frontend

## Overview

This document defines the API contracts that will be implemented in Silver tier. Bronze tier uses mock data with identical interfaces for seamless migration.

---

## Base Configuration

```typescript
// Base URL configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

// Request headers
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
};

// Timeout configuration
const REQUEST_TIMEOUT = 30000; // 30 seconds
```

---

## Endpoints

### GET /api/ai-status

Retrieves the current AI Employee status.

**Request**:
```http
GET /api/ai-status
Authorization: Bearer <token> (Silver tier+)
```

**Response (200 OK)**:
```json
{
  "data": {
    "id": "status-001",
    "type": "Thinking",
    "updatedAt": "2026-02-21T10:30:00Z",
    "message": "Analyzing user requirements...",
    "startedAt": "2026-02-21T10:28:00Z"
  }
}
```

**Error Responses**:
```json
// 503 Service Unavailable
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "AI Employee service is currently unavailable"
  }
}
```

---

### GET /api/plans

Retrieves a list of plans with optional filtering and pagination.

**Request**:
```http
GET /api/plans?status=Ready&page=1&pageSize=10&sort=newest
Authorization: Bearer <token>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by status (Draft, Ready, Done) |
| page | number | 1 | Page number |
| pageSize | number | 10 | Items per page (max 50) |
| sort | string | newest | Sort order (newest, oldest, status) |

**Response (200 OK)**:
```json
{
  "data": {
    "items": [
      {
        "id": "plan-001",
        "title": "Q1 Marketing Strategy",
        "status": "Ready",
        "createdAt": "2026-02-15T09:00:00Z",
        "description": "Comprehensive marketing plan for Q1 2026",
        "updatedAt": "2026-02-18T14:30:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "pageSize": 10,
    "totalPages": 3
  }
}
```

---

### GET /api/plans/:id

Retrieves a specific plan by ID.

**Request**:
```http
GET /api/plans/plan-001
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "data": {
    "id": "plan-001",
    "title": "Q1 Marketing Strategy",
    "status": "Ready",
    "createdAt": "2026-02-15T09:00:00Z",
    "description": "Comprehensive marketing plan for Q1 2026",
    "updatedAt": "2026-02-18T14:30:00Z",
    "completedAt": null,
    "taskIds": ["task-001", "task-002"]
  }
}
```

**Error Responses**:
```json
// 404 Not Found
{
  "error": {
    "code": "PLAN_NOT_FOUND",
    "message": "Plan with ID 'plan-001' not found"
  }
}
```

---

### POST /api/plans

Creates a new plan (used by "Generate Plan" action).

**Request**:
```http
POST /api/plans
Authorization: Bearer <token>

{
  "title": "New Marketing Campaign",
  "description": "Plan for Q2 marketing campaign",
  "relatedActionItemId": "action-001"
}
```

**Request Body Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| title | string | Yes | Plan title (1-100 chars) |
| description | string | No | Plan description (max 500 chars) |
| relatedActionItemId | string | No | Related action item ID |

**Response (201 Created)**:
```json
{
  "data": {
    "id": "plan-004",
    "title": "New Marketing Campaign",
    "status": "Draft",
    "createdAt": "2026-02-21T11:00:00Z",
    "description": "Plan for Q2 marketing campaign"
  },
  "meta": {
    "timestamp": "2026-02-21T11:00:00Z",
    "requestId": "req-abc123"
  }
}
```

**Error Responses**:
```json
// 400 Bad Request
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": {
      "title": "Title is required",
      "title": "Title must be less than 100 characters"
    }
  }
}
```

---

### PATCH /api/plans/:id

Updates an existing plan.

**Request**:
```http
PATCH /api/plans/plan-001
Authorization: Bearer <token>

{
  "status": "Ready",
  "description": "Updated description"
}
```

**Response (200 OK)**:
```json
{
  "data": {
    "id": "plan-001",
    "title": "Q1 Marketing Strategy",
    "status": "Ready",
    "createdAt": "2026-02-15T09:00:00Z",
    "description": "Updated description",
    "updatedAt": "2026-02-21T11:30:00Z"
  }
}
```

---

### GET /api/action-items

Retrieves list of action items requiring user attention.

**Request**:
```http
GET /api/action-items?priority=high&page=1&pageSize=10
Authorization: Bearer <token>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| priority | string | - | Filter by priority (low, medium, high, urgent) |
| type | string | - | Filter by type (InputRequired, DecisionNeeded, etc.) |
| page | number | 1 | Page number |
| pageSize | number | 10 | Items per page |

**Response (200 OK)**:
```json
{
  "data": {
    "items": [
      {
        "id": "action-001",
        "type": "InputRequired",
        "priority": "high",
        "createdAt": "2026-02-21T09:00:00Z",
        "title": "Provide budget approval",
        "description": "Review and approve the Q1 marketing budget proposal",
        "context": "The marketing team is waiting for budget confirmation.",
        "relatedPlanId": "plan-001",
        "dueDate": "2026-02-23T17:00:00Z"
      }
    ],
    "total": 8,
    "page": 1,
    "pageSize": 10,
    "totalPages": 1
  }
}
```

---

### GET /api/action-items/:id

Retrieves a specific action item by ID.

**Request**:
```http
GET /api/action-items/action-001
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
  "data": {
    "id": "action-001",
    "type": "InputRequired",
    "priority": "high",
    "createdAt": "2026-02-21T09:00:00Z",
    "title": "Provide budget approval",
    "description": "Review and approve the Q1 marketing budget proposal",
    "context": "The marketing team is waiting for budget confirmation to proceed with campaign planning.",
    "relatedPlanId": "plan-001",
    "dueDate": "2026-02-23T17:00:00Z"
  }
}
```

---

### POST /api/action-items/:id/generate-plan

Generates a plan from an action item (Silver tier implementation of "Generate Plan" button).

**Request**:
```http
POST /api/action-items/action-001/generate-plan
Authorization: Bearer <token>

{
  "title": "Budget Approval Plan",
  "description": "Optional custom description"
}
```

**Response (201 Created)**:
```json
{
  "data": {
    "id": "plan-005",
    "title": "Budget Approval Plan",
    "status": "Draft",
    "createdAt": "2026-02-21T12:00:00Z",
    "description": "Budget Approval Plan",
    "relatedActionItemId": "action-001"
  }
}
```

---

### GET /api/activity-feed

Retrieves activity feed items.

**Request**:
```http
GET /api/activity-feed?limit=20&before=2026-02-21T12:00:00Z
Authorization: Bearer <token>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | number | 20 | Maximum items to return (max 100) |
| before | string | now | Get items before this timestamp (ISO 8601) |

**Response (200 OK)**:
```json
{
  "data": {
    "items": [
      {
        "id": "activity-001",
        "type": "PlanCreated",
        "timestamp": "2026-02-21T11:00:00Z",
        "title": "New plan created",
        "description": "Q1 Marketing Strategy plan was created",
        "relatedEntityId": "plan-001",
        "relatedEntityType": "plan",
        "icon": "file-text"
      }
    ]
  }
}
```

---

### GET /api/tasks

Retrieves list of tasks (for dashboard preview).

**Request**:
```http
GET /api/tasks?status=InProgress&limit=5
Authorization: Bearer <token>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by status (Pending, InProgress, Blocked, Completed) |
| limit | number | 10 | Maximum items to return |

**Response (200 OK)**:
```json
{
  "data": {
    "items": [
      {
        "id": "task-001",
        "title": "Research competitors",
        "status": "InProgress",
        "createdAt": "2026-02-20T09:00:00Z",
        "description": "Analyze top 5 competitors in the market",
        "planId": "plan-001",
        "estimatedCompletion": "2026-02-25T17:00:00Z"
      }
    ]
  }
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Specific field error"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request validation failed |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Insufficient permissions |
| PLAN_NOT_FOUND | 404 | Plan ID not found |
| ACTION_ITEM_NOT_FOUND | 404 | Action item ID not found |
| CONFLICT | 409 | Resource conflict (e.g., invalid state transition) |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

---

## Rate Limiting (Silver Tier+)

```http
// Rate limit headers included in all responses
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645473600
```

**Response (429 Too Many Requests)**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again in 60 seconds.",
    "details": {
      "retryAfter": 60
    }
  }
}
```

---

## OpenAPI Specification

A complete OpenAPI 3.0 specification is available in:
- `contracts/openapi.yaml` (full specification)

**Quick reference**:
```yaml
openapi: 3.0.3
info:
  title: AI Employee API
  version: 1.0.0
  description: API for AI Employee system

servers:
  - url: /api
    description: Bronze/Silver tier API

paths:
  /ai-status:
    get:
      summary: Get current AI status
      tags:
        - AI Status
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AiStatus'

  /plans:
    get:
      summary: List plans
      tags:
        - Plans
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [Draft, Ready, Done]
      responses:
        '200':
          description: Successful response
    post:
      summary: Create plan
      tags:
        - Plans
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreatePlanRequest'
      responses:
        '201':
          description: Plan created

components:
  schemas:
    AiStatus:
      type: object
      properties:
        id:
          type: string
        type:
          type: string
          enum: [Idle, Thinking, Planning]
        updatedAt:
          type: string
          format: date-time
        message:
          type: string
    
    Plan:
      type: object
      properties:
        id:
          type: string
        title:
          type: string
        status:
          type: string
          enum: [Draft, Ready, Done]
        createdAt:
          type: string
          format: date-time
        description:
          type: string
```

---

## Migration Checklist (Bronze → Silver)

- [ ] Set up API backend infrastructure
- [ ] Implement authentication (if required for Silver)
- [ ] Create database schema for entities
- [ ] Implement all API endpoints
- [ ] Add rate limiting middleware
- [ ] Set up error handling middleware
- [ ] Add request logging
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Update frontend API base URL configuration
- [ ] Replace mock data imports with API calls
- [ ] Add loading states for async operations
- [ ] Add error boundaries and retry logic
- [ ] Test all API integrations
- [ ] Performance test under load

---

## Next Steps

1. ✅ API contracts defined
2. ➡️ Write `quickstart.md` developer guide
3. ➡️ Update agent context with technology stack
