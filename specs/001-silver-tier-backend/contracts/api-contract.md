# API Contract: Silver Tier Backend REST API

**Date**: 2026-02-22
**Feature**: Silver Tier Backend
**Branch**: 001-silver-tier-backend
**Version**: 1.0.0

## Overview

This document defines the REST API contract for the Silver Tier Backend. All endpoints follow RESTful conventions and return JSON responses.

---

## Base URL

```
/api/v1
```

---

## Authentication

**None** - Single-user mode with no authentication (per spec clarification).

All API calls are trusted.

---

## Standard Response Format

### Success Response

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

### List Response

```json
{
  "data": [ ... ],
  "meta": {
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error message",
    "details": [ ... ]  // Optional, for validation errors
  }
}
```

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Validation error, invalid input |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Status transition violation |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | AI service unavailable |

---

## Endpoints

### Task Management

#### Create Task

```http
POST /api/v1/tasks
Content-Type: application/json
```

**Request Body**:
```json
{
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the API"
}
```

**Validation**:
- `title`: required, string, 1-200 characters
- `description`: optional, string, 0-1000 characters (empty string treated as null)

**Success Response** (201 Created):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the API",
    "status": "Pending",
    "createdAt": "2026-02-22T00:00:00Z",
    "updatedAt": "2026-02-22T00:00:00Z",
    "completedAt": null
  },
  "meta": {
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

---

#### List Tasks

```http
GET /api/v1/tasks?status=Pending&page=1&pageSize=20
```

**Query Parameters**:
- `status`: optional, filter by status (Pending | In Progress | Done)
- `page`: optional, default 1, page number
- `pageSize`: optional, default 20, items per page (max 100)

**Success Response** (200 OK):
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Complete project documentation",
      "description": "Write comprehensive documentation for the API",
      "status": "Pending",
      "createdAt": "2026-02-22T00:00:00Z",
      "updatedAt": "2026-02-22T00:00:00Z",
      "completedAt": null
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "pageSize": 20,
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

---

#### Get Task

```http
GET /api/v1/tasks/:id
```

**Path Parameters**:
- `id`: required, UUID

**Success Response** (200 OK):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the API",
    "status": "Pending",
    "createdAt": "2026-02-22T00:00:00Z",
    "updatedAt": "2026-02-22T00:00:00Z",
    "completedAt": null
  },
  "meta": {
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found"
  }
}
```

---

#### Update Task Status

```http
PATCH /api/v1/tasks/:id/status
Content-Type: application/json
```

**Path Parameters**:
- `id`: required, UUID

**Request Body**:
```json
{
  "status": "In Progress"
}
```

**Validation**:
- `status`: required, must follow linear progression (Pending → In Progress → Done)

**Success Response** (200 OK):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the API",
    "status": "In Progress",
    "createdAt": "2026-02-22T00:00:00Z",
    "updatedAt": "2026-02-22T00:01:00Z",
    "completedAt": null
  },
  "meta": {
    "timestamp": "2026-02-22T00:01:00Z"
  }
}
```

**Error Response** (409 Conflict - Invalid Transition):
```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Cannot transition from Pending to Done. Must go through In Progress."
  }
}
```

---

#### Delete Task

```http
DELETE /api/v1/tasks/:id
```

**Path Parameters**:
- `id`: required, UUID

**Success Response** (204 No Content):
- No response body

**Error Response** (404 Not Found):
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found"
  }
}
```

---

### Plan Management

#### Generate Plan

```http
POST /api/v1/tasks/:taskId/plans
```

**Path Parameters**:
- `taskId`: required, UUID

**Success Response** (201 Created):
```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "taskId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "Active",
    "createdAt": "2026-02-22T00:02:00Z",
    "updatedAt": "2026-02-22T00:02:00Z",
    "steps": [
      {
        "id": "step-001",
        "order": 1,
        "title": "Research documentation tools",
        "description": "Evaluate available documentation generation tools",
        "estimatedDuration": 60,
        "completed": false
      },
      {
        "id": "step-002",
        "order": 2,
        "title": "Create API documentation structure",
        "description": "Define sections and organization",
        "estimatedDuration": 30,
        "completed": false
      }
    ]
  },
  "meta": {
    "timestamp": "2026-02-22T00:02:00Z"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found"
  }
}
```

**Error Response** (503 Service Unavailable - AI Down):
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "AI service is temporarily unavailable"
  }
}
```

---

#### List Plans

```http
GET /api/v1/plans?status=Active&page=1&pageSize=20
```

**Query Parameters**:
- `status`: optional, filter by status (Draft | Active | Completed | Archived)
- `page`: optional, default 1
- `pageSize`: optional, default 20 (max 100)

**Success Response** (200 OK):
```json
{
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "taskId": "550e8400-e29b-41d4-a716-446655440000",
      "taskTitle": "Complete project documentation",
      "status": "Active",
      "createdAt": "2026-02-22T00:02:00Z",
      "updatedAt": "2026-02-22T00:02:00Z",
      "steps": [
        {
          "id": "step-001",
          "order": 1,
          "title": "Research documentation tools",
          "description": "Evaluate available documentation generation tools",
          "estimatedDuration": 60,
          "completed": false
        }
      ]
    }
  ],
  "meta": {
    "total": 10,
    "page": 1,
    "pageSize": 20,
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

---

#### Get Plan

```http
GET /api/v1/plans/:id
```

**Path Parameters**:
- `id`: required, UUID

**Success Response** (200 OK):
```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "taskId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "Active",
    "createdAt": "2026-02-22T00:02:00Z",
    "updatedAt": "2026-02-22T00:02:00Z",
    "steps": [
      {
        "id": "step-001",
        "order": 1,
        "title": "Research documentation tools",
        "description": "Evaluate available documentation generation tools",
        "estimatedDuration": 60,
        "completed": false
      }
    ]
  },
  "meta": {
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

---

#### Update Plan Status

```http
PATCH /api/v1/plans/:id/status
Content-Type: application/json
```

**Path Parameters**:
- `id`: required, UUID

**Request Body**:
```json
{
  "status": "Completed"
}
```

**Validation**:
- `status`: required, one of (Draft | Active | Completed | Archived)

**Success Response** (200 OK):
```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "taskId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "Completed",
    "createdAt": "2026-02-22T00:02:00Z",
    "updatedAt": "2026-02-22T00:03:00Z",
    "steps": [ ... ]
  },
  "meta": {
    "timestamp": "2026-02-22T00:03:00Z"
  }
}
```

---

#### Delete Plan

```http
DELETE /api/v1/plans/:id
```

**Path Parameters**:
- `id`: required, UUID

**Success Response** (204 No Content):
- No response body

---

### Activity Log

#### List Activity Logs

```http
GET /api/v1/activity-logs?startTime=2026-02-22T00:00:00Z&endTime=2026-02-22T23:59:59Z&type=task.created&page=1&pageSize=50
```

**Query Parameters**:
- `startTime`: optional, ISO 8601 datetime, filter activities after this time
- `endTime`: optional, ISO 8601 datetime, filter activities before this time
- `type`: optional, filter by activity type
- `page`: optional, default 1
- `pageSize`: optional, default 50 (max 1000)

**Success Response** (200 OK):
```json
{
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "type": "task.created",
      "description": "Task 'Complete project documentation' created",
      "timestamp": "2026-02-22T00:00:00Z",
      "metadata": {
        "taskId": "550e8400-e29b-41d4-a716-446655440000"
      }
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440003",
      "type": "state.changed",
      "description": "System state changed from Idle to Thinking",
      "timestamp": "2026-02-22T00:00:01Z",
      "metadata": {
        "from": "Idle",
        "to": "Thinking"
      }
    }
  ],
  "meta": {
    "total": 150,
    "page": 1,
    "pageSize": 50,
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

**Note**: Results returned in chronological order (newest first by default).

---

### System Endpoints

#### Get System State

```http
GET /api/v1/system/state
```

**Success Response** (200 OK):
```json
{
  "data": {
    "state": "Thinking",
    "lastActivity": "2026-02-22T00:00:01Z"
  },
  "meta": {
    "timestamp": "2026-02-22T00:00:05Z"
  }
}
```

**State Values**:
- `Idle` - System is idle, waiting for input
- `Thinking` - System is analyzing/processing
- `Planning` - System is generating a plan

---

#### Health Check

```http
GET /api/v1/system/health
```

**Success Response** (200 OK):
```json
{
  "data": {
    "status": "healthy",
    "uptime": 3600,
    "timestamp": "2026-02-22T00:00:00Z"
  },
  "meta": {
    "timestamp": "2026-02-22T00:00:00Z"
  }
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "data": {
    "status": "unhealthy",
    "checks": {
      "database": "down",
      "ai_provider": "up"
    }
  }
}
```

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request body failed validation |
| NOT_FOUND | 404 | Resource not found |
| INVALID_TRANSITION | 409 | Status transition not allowed |
| SERVICE_UNAVAILABLE | 503 | External service unavailable |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## CORS Configuration

All endpoints support CORS with configuration via environment variables:

- `CORS_ORIGIN`: Comma-separated list of allowed origins (default: `*` for development)
- `CORS_METHODS`: Allowed HTTP methods (default: `GET,POST,PUT,PATCH,DELETE`)
- `CORS_HEADERS`: Allowed headers (default: `Content-Type,Authorization`)

**Response Headers**:
```
Access-Control-Allow-Origin: https://frontend.example.com
Access-Control-Allow-Methods: GET,POST,PUT,PATCH,DELETE
Access-Control-Allow-Headers: Content-Type
Access-Control-Allow-Credentials: true
```

---

## Rate Limiting

**Silver Tier**: No rate limiting implemented (single-user, local deployment).

Future tiers may add rate limiting with these headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645516800
```

---

## Versioning

API version is included in the path: `/api/v1/...`

Future breaking changes will increment the major version: `/api/v2/...`
