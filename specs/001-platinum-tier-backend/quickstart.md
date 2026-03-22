# Quickstart: Platinum Tier Backend

**Feature**: Platinum Tier Backend Upgrade
**Date**: 2026-03-08

## Overview
This guide shows how to interact with the new autonomous multi-agent platform using standard HTTP commands.

## Prerequisites
- Platinum Tier backend running at `localhost:3000`
- API Token for authentication

## Common Operations

### 1. Submit a High-Level Goal
```bash
curl -X POST http://localhost:3000/api/goals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "title": "AI Industry Briefing",
    "description": "Research and draft a weekly industry briefing on AI trends.",
    "priority": 1
  }'
```
**Response**: `{"goal_id": "...", "status": "PENDING_PLAN"}`

### 2. View Autonomous Plan
Wait a few moments for the `PlannerAgent` to decompose the goal.
```bash
curl http://localhost:3000/api/goals/<GOAL_ID>/plan \
  -H "Authorization: Bearer <TOKEN>"
```

### 3. Approve the Plan
```bash
curl -X POST http://localhost:3000/api/goals/<GOAL_ID>/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"action": "APPROVE"}'
```

### 4. Set Cost Threshold
```bash
curl -X POST http://localhost:3000/api/cost/threshold \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"threshold_usd": 10.00}'
```

### 5. Check System Cost Status
```bash
curl http://localhost:3000/api/cost/threshold \
  -H "Authorization: Bearer <TOKEN>"
```
