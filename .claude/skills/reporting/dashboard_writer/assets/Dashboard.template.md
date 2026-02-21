# Dashboard - {{PERIOD_LABEL}}

**Generated:** {{TIMESTAMP}}
**Period:** {{PERIOD_START}} to {{PERIOD_END}}
**Status:** {{HEALTH_EMOJI}} {{HEALTH_STATUS}}

---

## Executive Summary

### Key Highlights

- ✅ **{{TASKS_COMPLETED}}** tasks completed ({{TASKS_TREND}})
- 🚀 **{{DEPLOYMENTS}}** deployments to production ({{DEPLOYMENT_SUCCESS}}% success rate)
- 💰 **${{REVENUE}}** revenue generated ({{REVENUE_TREND}})
- ⏱️ **{{AVG_RESPONSE_TIME}}** hours average response time ({{RESPONSE_TIME_TREND}})
- 🎯 **{{MILESTONES_ON_TRACK}}%** of milestones on track

### Overall Health: {{HEALTH_EMOJI}} {{HEALTH_DESCRIPTION}}

{{HEALTH_DETAIL}}

---

## Team Metrics

### Response Times

| Metric | Current | Previous | Trend |
|--------|---------|----------|-------|
| Average | {{AVG_RESPONSE_TIME}}h | {{PREV_AVG_RESPONSE_TIME}}h | {{RESPONSE_TIME_TREND}} |
| Median | {{MEDIAN_RESPONSE_TIME}}h | {{PREV_MEDIAN_RESPONSE_TIME}}h | {{MEDIAN_TREND}} |
| 95th Percentile | {{P95_RESPONSE_TIME}}h | {{PREV_P95}}h | {{P95_TREND}} |

{{#if RESPONSE_TIME_OVER_TARGET}}
⚠️ Response time above target ({{RESPONSE_TIME_TARGET}}h)
{{/if}}

### Throughput

- **Tasks Completed:** {{TASKS_COMPLETED}} ({{TASKS_CHANGE}})
- **Story Points:** {{STORY_POINTS}} (velocity: {{VELOCITY}})
- **Commits:** {{COMMITS}} ({{COMMITS_CHANGE}})
- **Deployments:** {{DEPLOYMENTS}} ({{DEPLOYMENT_FREQUENCY}})

### Quality

- **Test Coverage:** {{TEST_COVERAGE}}% (target: {{TEST_COVERAGE_TARGET}}%) {{TEST_COVERAGE_INDICATOR}}
- **Bug Rate:** {{BUG_RATE}} bugs per feature ({{BUG_RATE_TREND}})
- **Deployment Success:** {{DEPLOYMENT_SUCCESS}}% (target: {{DEPLOYMENT_SUCCESS_TARGET}}%) {{DEPLOYMENT_INDICATOR}}
- **Rollback Rate:** {{ROLLBACK_RATE}}% (target: <5%) {{ROLLBACK_INDICATOR}}

---

## Financial Metrics

### Revenue

- **Period Revenue:** ${{REVENUE}} ({{REVENUE_TREND}})
- **Cumulative YTD:** ${{YTD_REVENUE}}
- **Target:** ${{REVENUE_TARGET}} ({{PERCENT_TO_TARGET}}% achieved) {{REVENUE_TARGET_INDICATOR}}

### Expenses

- **Period Expenses:** ${{EXPENSES}}
- **Burn Rate:** ${{BURN_RATE}}/month
- **Runway:** {{RUNWAY_MONTHS}} months

### Budget Status

| Category | Budget | Spent | Remaining | % Used |
|----------|--------|-------|-----------|--------|
| Engineering | ${{ENG_BUDGET}} | ${{ENG_SPENT}} | ${{ENG_REMAINING}} | {{ENG_PERCENT}}% |
| Operations | ${{OPS_BUDGET}} | ${{OPS_SPENT}} | ${{OPS_REMAINING}} | {{OPS_PERCENT}}% |
| Marketing | ${{MKT_BUDGET}} | ${{MKT_SPENT}} | ${{MKT_REMAINING}} | {{MKT_PERCENT}}% |

{{#if OVER_BUDGET}}
⚠️ **Warning:** {{OVER_BUDGET_CATEGORIES}} over budget
{{/if}}

---

## Project Status

### Active Projects ({{ACTIVE_COUNT}})

| Project | Progress | Status | Owner | Next Milestone | Risk |
|---------|----------|--------|-------|----------------|------|
{{#each ACTIVE_PROJECTS}}
| {{name}} | {{progress_bar}} | {{status_emoji}} {{status}} | {{owner}} | {{next_milestone}} ({{days_remaining}} days) | {{risk}} |
{{/each}}

{{#if BLOCKED_PROJECTS}}
### Blocked Projects ({{BLOCKED_COUNT}})

{{#each BLOCKED_PROJECTS}}
- **{{name}}**: Blocked on {{blocker}} ({{blocker_age}} days)
  - Owner: {{owner}}
  - Impact: {{impact}}
  - Resolution: {{resolution_plan}}
{{/each}}
{{/if}}

### Recently Completed ({{COMPLETED_COUNT}})

{{#each COMPLETED_PROJECTS}}
- ✅ **{{name}}** - Completed {{completion_date}}
  - Outcome: {{outcome}}
  - Metrics: {{metrics}}
{{/each}}

---

## Deadlines & Milestones

### Upcoming (Next 7 Days)

{{#each UPCOMING_DEADLINES}}
- **{{deadline_date}}**: {{milestone_name}}
  - Status: {{status_emoji}} {{status}}
  - Owner: {{owner}}
  - Risk: {{risk_level}}
  {{#if at_risk}}
  - ⚠️ At risk: {{risk_reason}}
  {{/if}}
{{/each}}

{{#if OVERDUE_ITEMS}}
### Overdue ({{OVERDUE_COUNT}})

{{#each OVERDUE_ITEMS}}
- 🔴 **{{name}}** ({{days_overdue}} days overdue)
  - Original deadline: {{original_date}}
  - Owner: {{owner}}
  - Action: {{action_plan}}
{{/each}}
{{/if}}

### This Quarter

| Milestone | Target Date | Status | Progress | Risk |
|-----------|-------------|--------|----------|------|
{{#each QUARTERLY_MILESTONES}}
| {{milestone}} | {{date}} | {{status_emoji}} {{status}} | {{progress_bar}} | {{risk}} |
{{/each}}

---

## Recent Activities

### Completed This {{PERIOD_TYPE}}

{{#each RECENT_TASKS}}
{{index}}. ✅ **{{title}}** ({{duration}}h)
   - Type: {{type}}
   - Owner: {{assignee}}
   {{#if revenue}}
   - Revenue: ${{revenue}}
   {{/if}}
{{/each}}

{{#if MORE_TASKS}}
[See all {{TOTAL_TASKS}} completed tasks →]
{{/if}}

### Deployments

{{#each DEPLOYMENTS}}
- 🚀 **{{version}}** deployed at {{timestamp}}
  - Success: {{success_emoji}}
  - Changes: {{change_count}}
  {{#if rollback}}
  - ⚠️ Rolled back: {{rollback_reason}}
  {{/if}}
{{/each}}

### Key Accomplishments

{{#each ACCOMPLISHMENTS}}
- 🎯 {{description}}
{{/each}}

---

## Action Items

### Next Steps

{{#each NEXT_STEPS}}
- [ ] {{action}} (Owner: {{owner}}, Due: {{due_date}})
{{/each}}

### Pending Approvals

{{#each PENDING_APPROVALS}}
- ⏳ **{{item}}** - Waiting on {{approver}} ({{days_pending}} days)
{{/each}}

### Decisions Needed

{{#each DECISIONS}}
- ❓ **{{question}}**
  - Context: {{context}}
  - Impact: {{impact}}
  - Decision by: {{due_date}}
{{/each}}

---

## Risks & Issues

{{#if RISKS}}
### Current Risks

{{#each RISKS}}
- {{severity_emoji}} **{{risk}}**
  - Impact: {{impact}}
  - Likelihood: {{likelihood}}
  - Mitigation: {{mitigation}}
{{/each}}
{{/if}}

{{#if TECHNICAL_DEBT}}
### Technical Debt

{{#each TECHNICAL_DEBT}}
- {{priority}} **{{item}}**
  - Impact: {{impact}}
  - Effort: {{effort}}
{{/each}}
{{/if}}

{{#if BLOCKERS}}
### Current Blockers

{{#each BLOCKERS}}
- 🚫 **{{blocker}}**
  - Affecting: {{affected_projects}}
  - Age: {{days_blocked}} days
  - Owner: {{owner}}
{{/each}}
{{/if}}

---

## Trends

### Week-over-Week

| Metric | Current | Previous | Change | Trend |
|--------|---------|----------|--------|-------|
| Tasks Completed | {{TASKS_CURRENT}} | {{TASKS_PREV}} | {{TASKS_CHANGE}} | {{TASKS_TREND_EMOJI}} |
| Response Time | {{RESPONSE_CURRENT}}h | {{RESPONSE_PREV}}h | {{RESPONSE_CHANGE}}h | {{RESPONSE_TREND_EMOJI}} |
| Revenue | ${{REVENUE_CURRENT}} | ${{REVENUE_PREV}} | ${{REVENUE_CHANGE}} | {{REVENUE_TREND_EMOJI}} |
| Deployment Success | {{DEPLOY_CURRENT}}% | {{DEPLOY_PREV}}% | {{DEPLOY_CHANGE}}% | {{DEPLOY_TREND_EMOJI}} |

{{#if NOTABLE_TRENDS}}
### Notable Trends

{{#each NOTABLE_TRENDS}}
- {{emoji}} **{{metric}}**: {{description}}
{{/each}}
{{/if}}

---

## Focus Areas for Next {{PERIOD_TYPE}}

{{#each FOCUS_AREAS}}
{{index}}. **{{area}}**: {{goal}}
   - Success criteria: {{criteria}}
   - Owner: {{owner}}
{{/each}}

---

## Notes

{{ADDITIONAL_NOTES}}

---

**Dashboard Version:** {{DASHBOARD_VERSION}}
**Data Sources:** {{DATA_SOURCES}}
**Next Update:** {{NEXT_UPDATE}}

---

_Generated by Dashboard Writer skill • [Archive]({{ARCHIVE_PATH}}) • [Feedback](#)_
