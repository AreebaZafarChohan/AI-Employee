---
name: dashboard-writer
description: Update Dashboard.md with recent actions, metrics (response time, revenue, status). Compose daily/weekly summaries by reading Done folder entries and aggregating key metrics for statuses, billing, and deadlines.
---

# Dashboard Writer

## Purpose

This skill maintains a living Dashboard.md file that provides real-time visibility into project status, team metrics, and business KPIs.

It prevents:
- Stale or missing status updates
- Manual metric aggregation overhead
- Incomplete visibility into progress
- Missing deadlines and blockers
- Scattered status information

---

## When to Use This Skill

This skill MUST be invoked when:

- **End of day/week summary** - Generate period summaries automatically
- **Status update requested** - Update Dashboard.md with current state
- **After completing tasks** - Record completion metrics and outcomes
- **Before planning meetings** - Prepare current state overview
- **When metrics change** - Update revenue, response times, or other KPIs
- **Deadline approaching** - Highlight upcoming deadlines and blockers

If this skill is NOT applied → status information becomes stale and stakeholders lack visibility.

---

## Overview

### Core Responsibilities

1. **Data Collection**: Read entries from Done folder (completed tasks, actions)
2. **Metric Aggregation**: Calculate counts, averages, totals for key metrics
3. **Summary Generation**: Compose human-readable daily/weekly summaries
4. **Dashboard Updating**: Write structured sections to Dashboard.md
5. **Trend Analysis**: Compare current period to previous periods

### Dashboard Sections

A complete Dashboard.md includes:

1. **Executive Summary**: High-level overview, key numbers, status
2. **Project Status**: Active projects, progress, blockers
3. **Team Metrics**: Response time, throughput, quality metrics
4. **Financial Metrics**: Revenue, burn rate, budget status
5. **Deadlines**: Upcoming milestones, overdue items, critical dates
6. **Recent Activities**: Completed tasks, deployed features, resolved issues
7. **Action Items**: Next steps, pending approvals, decisions needed
8. **Risks & Issues**: Blockers, technical debt, dependencies

---

## Impact Analysis Workflow

### 1. Data Source Discovery

Before dashboard generation, the skill MUST:

**Locate Done Folder:**
```bash
# Search for Done/done folders in project
find . -type d -iname "done" -o -type d -iname "completed" -o -type d -iname "archive"

# Common locations:
# - ./done/
# - ./tasks/done/
# - ./history/done/
# - ./archive/completed/
# - ./.specify/done/
```

**Identify Data Formats:**
- Task files (*.task.md, *.todo.md)
- Prompt History Records (*.prompt.md)
- Git commits (git log)
- Issue tracking (GitHub, Jira)
- Time tracking logs (*.time.json)
- Deployment logs (*.deploy.log)

**Parse Data Structure:**
```yaml
data_sources:
  done_folder:
    path: "./done/"
    formats: ["*.task.md", "*.prompt.md"]
    fields: ["id", "title", "completed_at", "duration", "outcome"]
  git_history:
    command: "git log --since='1 week ago' --pretty=format:'%h|%an|%ad|%s'"
    fields: ["commit_hash", "author", "date", "message"]
  time_tracking:
    path: "./logs/time/"
    format: "*.time.json"
    fields: ["task_id", "duration_minutes", "timestamp"]
  deployments:
    path: "./logs/deploy/"
    format: "*.deploy.log"
    fields: ["version", "timestamp", "success", "rollback"]
```

### 2. Metric Calculation

**Define Metric Types:**

**Count Metrics:**
```yaml
counts:
  tasks_completed: "Number of tasks completed in period"
  deployments: "Number of production deployments"
  commits: "Number of git commits"
  issues_resolved: "Number of issues closed"
  features_shipped: "Number of features deployed"
  bugs_fixed: "Number of bugs resolved"
```

**Time Metrics:**
```yaml
time_metrics:
  avg_response_time:
    description: "Average time to respond to requests"
    unit: "hours"
    calculation: "sum(response_times) / count(requests)"
  avg_task_duration:
    description: "Average time to complete tasks"
    unit: "hours"
    calculation: "sum(task_durations) / count(tasks)"
  cycle_time:
    description: "Time from task start to completion"
    unit: "days"
    calculation: "avg(completed_at - started_at)"
```

**Financial Metrics:**
```yaml
financial:
  revenue:
    description: "Revenue generated in period"
    unit: "USD"
    calculation: "sum(invoices.paid)"
  burn_rate:
    description: "Monthly expense rate"
    unit: "USD/month"
    calculation: "sum(expenses) / months"
  budget_status:
    description: "Budget remaining percentage"
    unit: "percentage"
    calculation: "(budget - spent) / budget * 100"
```

**Quality Metrics:**
```yaml
quality:
  bug_rate:
    description: "Bugs per feature deployed"
    unit: "ratio"
    calculation: "count(bugs) / count(features)"
  test_coverage:
    description: "Code coverage percentage"
    unit: "percentage"
    source: "test_reports/*.json"
  deployment_success:
    description: "Successful deployment percentage"
    unit: "percentage"
    calculation: "(deployments_success / total_deployments) * 100"
```

### 3. Time Period Handling

**Period Definitions:**
```yaml
periods:
  daily:
    start: "today 00:00"
    end: "now"
    comparison: "yesterday"
  weekly:
    start: "monday 00:00 this week"
    end: "now"
    comparison: "last week"
  monthly:
    start: "first day of this month 00:00"
    end: "now"
    comparison: "last month"
  quarterly:
    start: "first day of this quarter 00:00"
    end: "now"
    comparison: "last quarter"
```

**Time Period Selection:**
```javascript
function getPeriod(periodType = 'daily') {
  const now = new Date();

  switch (periodType) {
    case 'daily':
      return {
        start: startOfDay(now),
        end: now,
        label: format(now, 'MMMM dd, yyyy'),
        comparison: {
          start: startOfDay(subDays(now, 1)),
          end: endOfDay(subDays(now, 1)),
          label: 'yesterday'
        }
      };

    case 'weekly':
      return {
        start: startOfWeek(now, { weekStartsOn: 1 }), // Monday
        end: now,
        label: `Week of ${format(startOfWeek(now), 'MMM dd, yyyy')}`,
        comparison: {
          start: startOfWeek(subWeeks(now, 1)),
          end: endOfWeek(subWeeks(now, 1)),
          label: 'last week'
        }
      };

    case 'monthly':
      return {
        start: startOfMonth(now),
        end: now,
        label: format(now, 'MMMM yyyy'),
        comparison: {
          start: startOfMonth(subMonths(now, 1)),
          end: endOfMonth(subMonths(now, 1)),
          label: 'last month'
        }
      };
  }
}
```

### 4. Data Aggregation Pipeline

**Step 1: Collect Raw Data**
```javascript
async function collectData(period) {
  const data = {
    tasks: await readDoneFolder(period),
    commits: await getGitLog(period),
    deployments: await readDeploymentLogs(period),
    timeTracking: await readTimeTracking(period),
    issues: await fetchIssues(period)
  };

  return data;
}
```

**Step 2: Calculate Metrics**
```javascript
function calculateMetrics(data) {
  return {
    counts: {
      tasks_completed: data.tasks.length,
      commits: data.commits.length,
      deployments: data.deployments.length,
      issues_resolved: data.issues.filter(i => i.status === 'closed').length
    },
    time: {
      avg_response_time: average(data.tasks.map(t => t.response_time)),
      avg_task_duration: average(data.tasks.map(t => t.duration)),
      cycle_time: average(data.tasks.map(t =>
        (t.completed_at - t.started_at) / (1000 * 60 * 60 * 24)
      ))
    },
    financial: {
      revenue: sum(data.tasks.filter(t => t.revenue).map(t => t.revenue)),
      expenses: sum(data.tasks.filter(t => t.cost).map(t => t.cost))
    },
    quality: {
      deployment_success: (data.deployments.filter(d => d.success).length /
                          data.deployments.length) * 100,
      bug_rate: data.issues.filter(i => i.type === 'bug').length /
                data.tasks.filter(t => t.type === 'feature').length
    }
  };
}
```

**Step 3: Compare to Previous Period**
```javascript
function calculateTrends(current, previous) {
  const trends = {};

  for (const [category, metrics] of Object.entries(current)) {
    trends[category] = {};
    for (const [metric, value] of Object.entries(metrics)) {
      const prevValue = previous[category]?.[metric] || 0;
      const change = value - prevValue;
      const percentChange = prevValue > 0 ? (change / prevValue) * 100 : 0;

      trends[category][metric] = {
        current: value,
        previous: prevValue,
        change,
        percentChange,
        direction: change > 0 ? 'up' : change < 0 ? 'down' : 'same',
        emoji: change > 0 ? '📈' : change < 0 ? '📉' : '➡️'
      };
    }
  }

  return trends;
}
```

### 5. Dashboard Section Generation

**Executive Summary Template:**
```markdown
# Dashboard - {{DATE}}

## Executive Summary

**Period:** {{PERIOD_LABEL}}
**Generated:** {{TIMESTAMP}}
**Status:** {{OVERALL_STATUS}}

### Key Highlights

- ✅ **{{TASKS_COMPLETED}}** tasks completed ({{TREND_EMOJI}} {{PERCENT_CHANGE}}% vs {{COMPARISON_PERIOD}})
- 🚀 **{{DEPLOYMENTS}}** deployments to production ({{DEPLOYMENT_SUCCESS}}% success rate)
- 💰 **${{REVENUE}}** revenue generated ({{REVENUE_TREND}})
- ⏱️ **{{AVG_RESPONSE_TIME}}** hours average response time
- 🎯 **{{PERCENT_ON_TRACK}}%** of milestones on track

### Overall Health: {{HEALTH_INDICATOR}}

{{HEALTH_EMOJI}} {{HEALTH_DESCRIPTION}}
```

**Project Status Template:**
```markdown
## Project Status

### Active Projects ({{ACTIVE_COUNT}})

| Project | Progress | Status | Owner | Next Milestone | Risk |
|---------|----------|--------|-------|----------------|------|
| {{PROJECT_NAME}} | {{PROGRESS_BAR}} {{PERCENT}}% | {{STATUS_EMOJI}} {{STATUS}} | {{OWNER}} | {{MILESTONE}} ({{DAYS_REMAINING}} days) | {{RISK_LEVEL}} |

### Blocked Projects ({{BLOCKED_COUNT}})

{{#each blocked_projects}}
- **{{name}}**: Blocked on {{blocker}} ({{blocker_age}} days)
  - Owner: {{owner}}
  - Impact: {{impact}}
  - Resolution: {{resolution_plan}}
{{/each}}

### Recently Completed ({{COMPLETED_COUNT}})

{{#each completed_projects}}
- ✅ **{{name}}** - Completed {{completion_date}}
  - Outcome: {{outcome}}
  - Metrics: {{metrics}}
{{/each}}
```

**Team Metrics Template:**
```markdown
## Team Metrics

### Response Times

| Metric | Current | Previous | Trend |
|--------|---------|----------|-------|
| Avg Response Time | {{avg_response_time}} hours | {{prev_response_time}} hours | {{trend_emoji}} {{change}}% |
| Median Response Time | {{median_response_time}} hours | {{prev_median}} hours | {{trend_emoji}} {{change}}% |
| 95th Percentile | {{p95_response_time}} hours | {{prev_p95}} hours | {{trend_emoji}} {{change}}% |

### Throughput

- **Tasks Completed:** {{tasks_completed}} ({{trend_emoji}} {{change}} vs {{period}})
- **Story Points:** {{story_points}} ({{velocity}} velocity)
- **Deployments:** {{deployments}} ({{deployment_frequency}})

### Quality

- **Test Coverage:** {{test_coverage}}% (target: 80%)
- **Bug Rate:** {{bug_rate}} bugs per feature ({{trend_emoji}} {{change}})
- **Deployment Success:** {{deployment_success}}% (target: 95%)
- **Rollback Rate:** {{rollback_rate}}% (target: <5%)
```

**Financial Dashboard Template:**
```markdown
## Financial Metrics

### Revenue

- **Period Revenue:** ${{revenue}} ({{trend_emoji}} {{change}}% vs {{period}})
- **Cumulative YTD:** ${{ytd_revenue}}
- **Target:** ${{target}} ({{percent_to_target}}% achieved)

### Expenses

- **Period Expenses:** ${{expenses}}
- **Burn Rate:** ${{burn_rate}}/month
- **Runway:** {{runway_months}} months

### Budget Status

| Category | Budget | Spent | Remaining | % Used |
|----------|--------|-------|-----------|--------|
| Engineering | ${{eng_budget}} | ${{eng_spent}} | ${{eng_remaining}} | {{eng_percent}}% |
| Operations | ${{ops_budget}} | ${{ops_spent}} | ${{ops_remaining}} | {{ops_percent}}% |
| Marketing | ${{mkt_budget}} | ${{mkt_spent}} | ${{mkt_remaining}} | {{mkt_percent}}% |

{{#if over_budget}}
⚠️ **Warning:** {{over_budget_categories}} over budget
{{/if}}
```

**Deadlines Section Template:**
```markdown
## Deadlines & Milestones

### Upcoming (Next 7 Days)

{{#each upcoming_deadlines}}
- **{{deadline_date}}**: {{milestone_name}}
  - Status: {{status_emoji}} {{status}}
  - Owner: {{owner}}
  - Risk: {{risk_level}}
  {{#if at_risk}}
  - ⚠️ At risk: {{risk_reason}}
  {{/if}}
{{/each}}

### Overdue ({{overdue_count}})

{{#each overdue_items}}
- 🔴 **{{name}}** ({{days_overdue}} days overdue)
  - Original deadline: {{original_date}}
  - Owner: {{owner}}
  - Action: {{action_plan}}
{{/each}}

### This Quarter

| Milestone | Target Date | Status | Progress | Risk |
|-----------|-------------|--------|----------|------|
| {{milestone}} | {{date}} | {{status_emoji}} {{status}} | {{progress_bar}} {{percent}}% | {{risk}} |
```

---

## Environment Variable Strategy

This skill requires configuration for data sources and formatting:

**Runtime Variables:**
```yaml
# Data sources
DASHBOARD_DONE_FOLDER: "{{DONE_FOLDER_PATH}}"                # Path to completed tasks
DASHBOARD_TIME_TRACKING_FOLDER: "{{TIME_LOGS_PATH}}"         # Time tracking data
DASHBOARD_DEPLOYMENT_LOGS: "{{DEPLOY_LOGS_PATH}}"            # Deployment logs

# Output configuration
DASHBOARD_PATH: "{{DASHBOARD_FILE_PATH}}"                    # Dashboard.md location
DASHBOARD_ARCHIVE_PATH: "{{ARCHIVE_PATH}}"                   # Historical dashboards

# Period defaults
DASHBOARD_DEFAULT_PERIOD: "{{daily|weekly|monthly}}"         # Default summary period
DASHBOARD_TIMEZONE: "{{TIMEZONE}}"                           # Timezone for date calculations

# Metric thresholds
DASHBOARD_RESPONSE_TIME_TARGET: "{{TARGET_HOURS}}"           # Target response time
DASHBOARD_DEPLOYMENT_SUCCESS_TARGET: "{{TARGET_PERCENT}}"    # Target success rate
DASHBOARD_TEST_COVERAGE_TARGET: "{{TARGET_PERCENT}}"         # Target test coverage

# Financial configuration
DASHBOARD_REVENUE_TARGET_MONTHLY: "{{TARGET_USD}}"           # Monthly revenue target
DASHBOARD_BURN_RATE_BUDGET: "{{BUDGET_USD}}"                 # Monthly budget

# Integration endpoints
DASHBOARD_ISSUE_TRACKER_URL: "{{JIRA_OR_GITHUB_URL}}"        # Issue tracking system
DASHBOARD_ISSUE_TRACKER_TOKEN: "{{API_TOKEN}}"               # Auth token
DASHBOARD_TIME_TRACKING_API: "{{TIME_API_URL}}"              # Time tracking API
```

**Default Values:**
```yaml
DASHBOARD_DONE_FOLDER: "./done/"
DASHBOARD_PATH: "./Dashboard.md"
DASHBOARD_ARCHIVE_PATH: "./archive/dashboards/"
DASHBOARD_DEFAULT_PERIOD: "weekly"
DASHBOARD_TIMEZONE: "UTC"
DASHBOARD_RESPONSE_TIME_TARGET: "4"
DASHBOARD_DEPLOYMENT_SUCCESS_TARGET: "95"
DASHBOARD_TEST_COVERAGE_TARGET: "80"
```

**Impact Notes:**
- Done folder must be readable and contain parseable task files
- Time tracking data should follow consistent format (JSON or structured logs)
- Archive path ensures historical dashboard versions are preserved
- Timezone setting critical for accurate day/week boundaries
- Targets used to highlight metrics that need attention

---

## Network & Topology Implications

**Internal Dependencies:**
- **Done Folder**: Local file system (completed tasks, PHRs)
- **Git Repository**: Local git commands (commit history)
- **File System**: Read access to logs, time tracking data

**External Dependencies:**
- **Issue Tracker API**: GitHub Issues, Jira, Linear (optional)
- **Time Tracking API**: Toggl, Harvest, Clockify (optional)
- **Analytics Service**: Custom metrics endpoints (optional)
- **Notification Service**: Slack/email for dashboard updates (optional)

**Network Considerations:**
- If issue tracker is external, network latency impacts data freshness
- API rate limits may restrict how often metrics can be updated
- Consider caching external data to reduce API calls
- Webhook integration for real-time updates (advanced)

---

## Auth / CORS / Security Impact

**Authentication Considerations:**
- Issue tracker APIs require authentication tokens
- Time tracking APIs need API keys
- Git repository access (already authenticated in local environment)

**Authorization Levels:**
```yaml
roles:
  viewer:
    - read_dashboard
  contributor:
    - read_dashboard
    - update_metrics
  admin:
    - read_dashboard
    - update_metrics
    - configure_thresholds
    - archive_dashboards
```

**Security Requirements:**
- API tokens stored in environment variables (never in code)
- Dashboard.md may contain sensitive metrics (revenue, burn rate)
- Consider separate public vs private dashboards
- Archive folder should be protected (historical sensitive data)

---

## Blueprints & Templates Used

### Blueprint: Dashboard Structure Template

**Purpose:** Standard structure for Dashboard.md

**Template Variables:**
```yaml
DATE: "{{CURRENT_DATE}}"
PERIOD_LABEL: "{{PERIOD_DESCRIPTION}}"
TIMESTAMP: "{{ISO_TIMESTAMP}}"
OVERALL_STATUS: "{{green|yellow|red}}"

# Counts
TASKS_COMPLETED: "{{COUNT}}"
DEPLOYMENTS: "{{COUNT}}"
ISSUES_RESOLVED: "{{COUNT}}"

# Trends
TREND_EMOJI: "{{📈|📉|➡️}}"
PERCENT_CHANGE: "{{PERCENT}}"
COMPARISON_PERIOD: "{{PERIOD_NAME}}"

# Health
HEALTH_INDICATOR: "{{Excellent|Good|Fair|Poor}}"
HEALTH_EMOJI: "{{🟢|🟡|🔴}}"
HEALTH_DESCRIPTION: "{{DESCRIPTION}}"
```

### Blueprint: Metric Aggregation Template

**Purpose:** Calculate and format metrics from raw data

**Implementation:**
```javascript
async function aggregateMetrics(period) {
  const data = await collectData(period);
  const previousData = await collectData(period.comparison);

  const current = calculateMetrics(data);
  const previous = calculateMetrics(previousData);
  const trends = calculateTrends(current, previous);

  return {
    current,
    previous,
    trends,
    period: period.label,
    comparisonPeriod: period.comparison.label
  };
}
```

### Blueprint: Summary Generation Template

**Purpose:** Generate natural language summaries

**Template:**
```markdown
## {{PERIOD_TYPE}} Summary

{{PERIOD_LABEL}}

{{#if positive_trend}}
✅ Strong performance this {{period}}:
{{/if}}

{{#if negative_trend}}
⚠️ Areas needing attention:
{{/if}}

### What Went Well
{{#each highlights}}
- {{description}} ({{metric}}: {{value}})
{{/each}}

### Challenges
{{#each challenges}}
- {{description}} ({{metric}}: {{value}})
{{/each}}

### Key Accomplishments
{{#each accomplishments}}
- ✅ {{description}}
{{/each}}

### Next Period Focus
{{#each focus_areas}}
- 🎯 {{area}}: {{goal}}
{{/each}}
```

---

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [ ] Done folder exists and is readable
- [ ] Dashboard.md path is writable
- [ ] Date/time parsing works correctly across timezones
- [ ] Metric calculations handle missing data gracefully
- [ ] Archive mechanism preserves previous dashboard versions
- [ ] Templates render without errors
- [ ] All required sections present in output

### Quality Checks (Skill Degraded If Failed)

- [ ] Trends show meaningful comparisons
- [ ] Visual indicators (emojis, colors) enhance readability
- [ ] Numbers formatted consistently (commas, currency symbols)
- [ ] Percentages calculated and displayed correctly
- [ ] Dates formatted in user-friendly way
- [ ] Links to related resources work
- [ ] Historical data comparison available

### Data Integrity Checks

- [ ] No duplicate entries counted
- [ ] Time periods calculated correctly (no overlaps or gaps)
- [ ] Metric definitions consistent across periods
- [ ] Missing data handled (not just ignored silently)
- [ ] Outliers detected and flagged
- [ ] Data source timestamps verified

---

## Anti-Patterns

### ❌ Hardcoding Time Periods

**Problem:** Dashboard breaks when dates change

**Example:**
```javascript
// WRONG
const startDate = new Date('2024-01-01');

// CORRECT
const startDate = startOfWeek(new Date());
```

### ❌ Ignoring Missing Data

**Problem:** Metrics misleading when data incomplete

**Example:**
```javascript
// WRONG
const avg = sum(values) / values.length;  // NaN if empty

// CORRECT
const avg = values.length > 0 ? sum(values) / values.length : 0;
// Or better: indicate data unavailable
const avg = values.length > 0 ? sum(values) / values.length : 'N/A';
```

### ❌ No Historical Comparison

**Problem:** Can't see trends without previous period data

**Example:**
```markdown
<!-- WRONG -->
Tasks completed: 15

<!-- CORRECT -->
Tasks completed: 15 (📈 +25% vs last week)
```

### ❌ Unclear Metric Definitions

**Problem:** Users don't know what metrics mean

**Example:**
```markdown
<!-- WRONG -->
Response time: 4.2

<!-- CORRECT -->
Avg Response Time: 4.2 hours (time from request to first response)
Target: < 4 hours
```

### ❌ Stale Dashboard

**Problem:** Dashboard not updated regularly

**Mitigation:**
```yaml
# Set up automated refresh
schedule:
  daily: "0 17 * * *"    # 5 PM daily
  weekly: "0 9 * * 1"    # 9 AM Monday
  monthly: "0 9 1 * *"   # 9 AM 1st of month
```

### ❌ Overloading with Data

**Problem:** Too much information, hard to find key insights

**Example:**
```markdown
<!-- WRONG: 50 metrics listed -->

<!-- CORRECT: Focus on key metrics -->
Top 5 Metrics:
1. Tasks completed: 15 (target: 12) ✅
2. Response time: 4.2h (target: <4h) ⚠️
3. Revenue: $50K (target: $45K) ✅
4. Deployment success: 98% (target: 95%) ✅
5. Bug rate: 0.8 (target: <1.0) ✅

[See all metrics →]
```

---

## Enforcement Behavior

When this skill is active:

### Agent Responsibilities

1. **Regular Updates**
   - Update dashboard at configured intervals (daily, weekly)
   - Trigger update after major milestones
   - Regenerate on demand when requested

2. **Data Freshness**
   - Check data source timestamps
   - Flag stale data sources
   - Indicate when data was last updated

3. **Metric Accuracy**
   - Validate calculations
   - Handle edge cases (division by zero, missing data)
   - Show confidence level if data incomplete

4. **Trend Analysis**
   - Compare to previous period
   - Highlight significant changes
   - Provide context for anomalies

### User Expectations

- Dashboard automatically updated on schedule
- Clear visual indicators (emojis, colors) for status
- Trends show direction and magnitude of change
- Key insights surfaced in executive summary
- Detailed sections available for drill-down
- Historical versions archived for reference

---

## Final Rule (Hard Stop)

If user requests dashboard update without data:

```
User: "Update the dashboard"

Agent: "Checking data sources...

⚠️ Cannot generate dashboard: No data found in Done folder

Required:
- Done folder must contain completed task files
- At least one completed task in the period
- Task files must have valid timestamps

Current status:
- Done folder: ./done/ ✓ (exists)
- Task files: 0 ❌ (no completed tasks found)
- Time period: Last 7 days

Options:
1. Complete some tasks and mark them done
2. Specify a different time period (e.g., last 30 days)
3. Import historical data from another source

Would you like me to:
- Show you how to mark tasks as done?
- Check a different time period?
- Create a sample dashboard template?"
```

Then wait for user choice.

---

## Integration with Other Skills

### Task Management Skills
- Read completed tasks from `/sp.implement` outputs
- Track task completion times and outcomes
- Aggregate task metrics by category

### Git Workflow Skills (`/sp.git.commit_pr`)
- Count commits in period
- Track deployment frequency
- Link dashboard metrics to git activity

### Planning Skills (`/sp.plan`, `/sp.tasks`)
- Compare planned vs actual progress
- Track milestone completion
- Highlight blocked tasks

### Prompt History (`/sp.phr`)
- Count agent interactions
- Track response times from PHR timestamps
- Summarize common request types

---

## Example: End-to-End Dashboard Generation

**Scenario:** Generate weekly dashboard on Monday morning

**Step 1: Period Definition**
```javascript
const period = {
  type: 'weekly',
  start: '2024-01-15T00:00:00Z',  // Monday
  end: '2024-01-21T23:59:59Z',     // Sunday
  label: 'Week of January 15, 2024',
  comparison: {
    start: '2024-01-08T00:00:00Z',
    end: '2024-01-14T23:59:59Z',
    label: 'last week'
  }
};
```

**Step 2: Data Collection**
```javascript
const data = {
  tasks: [
    { id: 'TASK-001', title: 'Implement login', completed_at: '2024-01-16T14:30:00Z', duration: 4.5 },
    { id: 'TASK-002', title: 'Fix bug in checkout', completed_at: '2024-01-17T10:15:00Z', duration: 2.0 },
    // ... 13 more tasks
  ],
  commits: 47,
  deployments: [
    { version: 'v2.1.0', timestamp: '2024-01-18T15:00:00Z', success: true },
    { version: 'v2.1.1', timestamp: '2024-01-19T16:30:00Z', success: true }
  ],
  revenue: 12500,
  expenses: 8200
};
```

**Step 3: Metric Calculation**
```javascript
const metrics = {
  counts: {
    tasks_completed: 15,      // vs 12 last week (+25%)
    commits: 47,               // vs 52 last week (-10%)
    deployments: 2,            // vs 1 last week (+100%)
    features_shipped: 3        // vs 2 last week (+50%)
  },
  time: {
    avg_response_time: 3.2,   // vs 4.5 last week (-29%)
    avg_task_duration: 3.8,   // vs 4.2 last week (-10%)
  },
  financial: {
    revenue: 12500,            // vs 11000 last week (+14%)
    expenses: 8200,            // vs 8500 last week (-4%)
    profit: 4300               // vs 2500 last week (+72%)
  },
  quality: {
    deployment_success: 100,   // vs 100 last week (0%)
    bug_rate: 0.67,            // vs 0.5 last week (+34%)
  }
};
```

**Step 4: Dashboard Generation**
```markdown
# Dashboard - Week of January 15, 2024

## Executive Summary

**Period:** January 15-21, 2024
**Generated:** 2024-01-22 09:00:00 UTC
**Status:** 🟢 Excellent

### Key Highlights

- ✅ **15** tasks completed (📈 +25% vs last week)
- 🚀 **2** deployments to production (100% success rate)
- 💰 **$12,500** revenue generated (📈 +14%)
- ⏱️ **3.2** hours average response time (📉 -29% improvement)
- 🎯 **90%** of milestones on track

### Overall Health: 🟢 Excellent

Strong performance across all key metrics. Response time improvement particularly notable.
Slight increase in bug rate warrants attention next week.

## Team Metrics

### Response Times

| Metric | Current | Previous | Trend |
|--------|---------|----------|-------|
| Avg Response Time | 3.2 hours | 4.5 hours | 📉 -29% |
| Median Response Time | 2.8 hours | 4.0 hours | 📉 -30% |

### Throughput

- **Tasks Completed:** 15 (📈 +3 vs last week)
- **Deployments:** 2 (📈 +1 vs last week)
- **Features Shipped:** 3

### Quality

- **Deployment Success:** 100% (target: 95%) ✅
- **Bug Rate:** 0.67 bugs per feature (📈 +0.17, target: <1.0) ⚠️

## Financial Metrics

- **Revenue:** $12,500 (📈 +14%)
- **Expenses:** $8,200 (📉 -4%)
- **Profit:** $4,300 (📈 +72%)

## Recent Activities

### Completed This Week

1. ✅ Implement user authentication system (4.5h)
2. ✅ Fix checkout bug affecting mobile users (2.0h)
3. ✅ Add analytics dashboard (6.0h)
4. ✅ Optimize database queries (3.5h)
5. ✅ Deploy v2.1.0 to production

[See all 15 completed tasks →]

## Deadlines

### Upcoming (Next 7 Days)

- **Jan 25**: Q1 Feature Release (Status: 🟢 On track)
- **Jan 27**: Client demo preparation (Status: 🟡 At risk - slides incomplete)

## Action Items

- [ ] Address bug rate increase (investigate root cause)
- [ ] Complete client demo slides by Jan 26
- [ ] Review Q1 roadmap priorities
```

**Step 5: Archive Previous Dashboard**
```bash
mv Dashboard.md archive/dashboards/Dashboard-2024-01-15.md
```

**Step 6: Write New Dashboard**
```bash
# Write new Dashboard.md with updated content
```

**Outcome:**
```
✅ DASHBOARD UPDATED

Generated: Weekly dashboard for Jan 15-21, 2024
Sections: 8 (Executive Summary, Team Metrics, Financial, Activities, Deadlines, Action Items, Risks, Trends)
Metrics: 12 key metrics tracked
Trends: 10 comparisons to previous week
Archived: Previous dashboard saved to archive/dashboards/Dashboard-2024-01-15.md

Dashboard location: ./Dashboard.md
```

---
