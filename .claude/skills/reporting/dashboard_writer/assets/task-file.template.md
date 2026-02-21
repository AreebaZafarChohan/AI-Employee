---
id: "{{TASK_ID}}"
title: "{{TASK_TITLE}}"
type: "{{feature|bug|refactor|docs|test|chore}}"
status: "done"
priority: "{{low|medium|high|critical}}"

# Timestamps
created_at: "{{ISO_TIMESTAMP}}"
started_at: "{{ISO_TIMESTAMP}}"
completed_at: "{{ISO_TIMESTAMP}}"

# Metrics
duration_hours: {{DURATION}}
response_time_hours: {{RESPONSE_TIME}}

# Financial (optional)
revenue: {{REVENUE_USD}}
cost: {{COST_USD}}

# People
assignee: "{{OWNER_NAME}}"
reviewer: "{{REVIEWER_NAME}}"

# Links (optional)
pr_url: "{{PR_URL}}"
issue_url: "{{ISSUE_URL}}"
deploy_url: "{{DEPLOY_URL}}"

# Outcome
outcome: "{{success|partial|failed}}"
success_criteria_met: {{true|false}}

# Tags
tags:
  - "{{TAG_1}}"
  - "{{TAG_2}}"

---

# {{TASK_TITLE}}

## Description

{{TASK_DESCRIPTION}}

## Acceptance Criteria

- [x] Criterion 1
- [x] Criterion 2
- [x] Criterion 3

## Implementation Notes

{{IMPLEMENTATION_NOTES}}

## Testing

{{TESTING_NOTES}}

## Deployment

{{DEPLOYMENT_NOTES}}

## Lessons Learned

{{LESSONS_LEARNED}}

---

**Completed:** {{COMPLETED_DATE}}
**Duration:** {{DURATION}} hours
**Outcome:** {{OUTCOME}}
