# Plan MD Generator - Common Patterns

## Overview
This document describes common plan generation strategies and best practices for different types of documentation.

---

## Pattern 1: Sprint Planning Document

### Use Case
Generate sprint plans with user stories, tasks, and acceptance criteria.

### Template Structure

```markdown
# Sprint {{SPRINT_NUMBER}} Plan

## Sprint Goal
{{GOAL_STATEMENT}}

## Capacity
- Team Size: {{TEAM_SIZE}} developers
- Sprint Duration: {{DURATION}} days
- Available Points: {{CAPACITY}} story points

## User Stories

### Story 1: {{STORY_TITLE}}
**As a** {{USER_TYPE}}
**I want** {{FEATURE}}
**So that** {{BENEFIT}}

**Story Points:** {{POINTS}}
**Priority:** {{PRIORITY}}

#### Acceptance Criteria
- [ ] {{CRITERION_1}}
- [ ] {{CRITERION_2}}

#### Tasks
1. [{{ESTIMATE}}h] {{TASK_1}} - @{{ASSIGNEE}}
2. [{{ESTIMATE}}h] {{TASK_2}} - @{{ASSIGNEE}}

#### Definition of Done
- [ ] Code reviewed and merged
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests added
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] Product owner approved
```

### Implementation

```python
class SprintPlanGenerator:
    """Generate sprint planning documents"""

    def generate(self, sprint_data):
        plan = f"# Sprint {sprint_data['number']} Plan\n\n"
        plan += f"## Sprint Goal\n{sprint_data['goal']}\n\n"

        # Add capacity
        plan += "## Capacity\n"
        plan += f"- Team Size: {sprint_data['team_size']} developers\n"
        plan += f"- Sprint Duration: {sprint_data['duration']} days\n"
        plan += f"- Available Points: {sprint_data['capacity']} story points\n\n"

        # Add stories
        plan += "## User Stories\n\n"
        for story in sprint_data['stories']:
            plan += self._format_story(story)

        return plan

    def _format_story(self, story):
        result = f"### Story {story['id']}: {story['title']}\n"
        result += f"**As a** {story['user_type']}\n"
        result += f"**I want** {story['feature']}\n"
        result += f"**So that** {story['benefit']}\n\n"
        result += f"**Story Points:** {story['points']}\n"
        result += f"**Priority:** {story['priority']}\n\n"

        # Acceptance criteria
        result += "#### Acceptance Criteria\n"
        for criterion in story['acceptance_criteria']:
            result += f"- [ ] {criterion}\n"
        result += "\n"

        # Tasks
        result += "#### Tasks\n"
        for task in story['tasks']:
            result += f"1. [{task['estimate']}h] {task['description']} - @{task['assignee']}\n"
        result += "\n"

        return result
```

---

## Pattern 2: Migration Plan with Phases

### Use Case
Document complex migrations with multiple phases and rollback procedures.

### Best Practices

1. **Phase Structure**
   - Pre-migration preparation
   - Migration execution
   - Verification and validation
   - Post-migration cleanup

2. **Include Per-Phase**
   - Clear objectives
   - Detailed steps
   - Success criteria
   - Rollback procedures
   - Estimated duration

3. **Risk Mitigation**
   - Backup procedures
   - Testing in lower environments
   - Monitoring and alerting
   - Communication plan

### Example

```markdown
# Database Migration Plan: PostgreSQL 12 to 14

## Pre-Migration Phase

### Step 1: Backup Current Database
**Duration:** 2 hours

**Actions:**
1. Create full backup: `pg_dump -Fc prod_db > backup_$(date +%Y%m%d).dump`
2. Verify backup: `pg_restore --list backup_*.dump | wc -l`
3. Copy to S3: `aws s3 cp backup_*.dump s3://backups/`

**Acceptance Criteria:**
- [ ] Backup file created successfully
- [ ] Backup contains all tables
- [ ] Backup uploaded to S3
- [ ] Backup size matches expectations

**Rollback:** N/A (pre-migration)

---

### Step 2: Test Migration on Staging
**Duration:** 4 hours
**Dependencies:** Step 1

[Continue pattern...]
```

---

## Pattern 3: API Development Plan

### Use Case
Plan API endpoint implementation with clear contracts and testing.

### Key Elements

```markdown
## Endpoint: POST /api/v1/users

### Request Specification
```json
{
  "email": "string (required, valid email)",
  "password": "string (required, min 8 chars)",
  "name": "string (optional)"
}
```

### Response Specification
**Success (201 Created):**
```json
{
  "id": "uuid",
  "email": "string",
  "name": "string",
  "created_at": "ISO 8601 timestamp"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Invalid email format",
  "field": "email"
}
```

### Implementation Steps
1. Define Pydantic model
2. Create database migration
3. Implement endpoint handler
4. Add validation logic
5. Write unit tests
6. Add integration tests
7. Update API documentation

### Test Cases
```python
def test_create_user_success():
    """Test successful user creation"""
    response = client.post("/api/v1/users", json={
        "email": "test@example.com",
        "password": "SecureP@ss123"
    })
    assert response.status_code == 201
    assert "id" in response.json()

def test_create_user_invalid_email():
    """Test user creation with invalid email"""
    response = client.post("/api/v1/users", json={
        "email": "invalid",
        "password": "SecureP@ss123"
    })
    assert response.status_code == 400
    assert response.json()["field"] == "email"
```
```

---

## Pattern 4: Deployment Runbook

### Use Case
Step-by-step deployment guide with verification at each stage.

### Structure

```markdown
# Production Deployment Runbook

## Pre-Deployment Checklist
- [ ] All tests passing on CI
- [ ] Code review approved
- [ ] Staging deployment successful
- [ ] Database migrations tested
- [ ] Rollback plan prepared
- [ ] Team notified
- [ ] Monitoring ready

## Deployment Steps

### 1. Pre-Deploy: Database Backup
**Time:** 10 minutes
**Responsible:** DBA

```bash
# Create backup
pg_dump -h prod-db.example.com -U app_user app_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify
ls -lh backup_*.sql
```

**Verification:**
- Backup file exists and size > 0
- Backup timestamp is current

---

### 2. Deploy: Application Update
**Time:** 5 minutes
**Responsible:** DevOps

```bash
# Pull latest image
docker pull app:v2.1.0

# Rolling update
kubectl set image deployment/app app=app:v2.1.0

# Watch rollout
kubectl rollout status deployment/app
```

**Verification:**
- All pods running: `kubectl get pods -l app=myapp`
- Health check passing: `curl https://api.example.com/health`

---

### 3. Post-Deploy: Smoke Tests
**Time:** 10 minutes
**Responsible:** QA

[Continue...]
```

---

## Pattern 5: Onboarding Guide

### Use Case
New team member onboarding with progressive steps.

### Progressive Disclosure

```markdown
# Developer Onboarding Plan

## Week 1: Environment Setup

### Day 1: Access and Tools
**Goal:** Get basic access and tools installed

- [ ] Receive laptop and credentials
- [ ] Install development tools
  - [ ] Git
  - [ ] Docker
  - [ ] IDE (VS Code recommended)
- [ ] Join Slack channels
- [ ] Access GitHub organization
- [ ] Complete security training

**Resources:**
- [Development Setup Guide](./setup.md)
- [Tool Installation Scripts](./scripts/setup.sh)

---

### Day 2-3: Codebase Familiarization
**Goal:** Understand project structure

- [ ] Clone repositories
- [ ] Run application locally
- [ ] Explore codebase structure
- [ ] Read architecture docs
- [ ] Set up local database

**Exercises:**
1. Make a small UI change (change button color)
2. Add a new API endpoint (echo service)
3. Write a unit test

---

### Day 4-5: First Contribution
**Goal:** Submit first pull request

- [ ] Pick a "good first issue"
- [ ] Create feature branch
- [ ] Implement solution
- [ ] Write tests
- [ ] Submit PR for review
```

---

## Best Practices Summary

1. **Clear Objectives** - Every section has explicit goals
2. **Actionable Steps** - Specific commands, not vague instructions
3. **Verification Points** - Check progress at each stage
4. **Rollback Plans** - Always include recovery procedures
5. **Time Estimates** - Set expectations for duration
6. **Responsibility** - Assign owners for each step
7. **Prerequisites** - Document dependencies clearly
8. **Testing** - Include test cases and validation
9. **References** - Link to related documentation
10. **Iteration** - Update plans based on feedback

---

**Last Updated:** 2026-02-06
