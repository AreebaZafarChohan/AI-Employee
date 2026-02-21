---
name: ceo_briefing_writer
description: Compose a weekly CEO briefing from goals, tasks done, and finances. Summarize tasks, revenue, bottlenecks, and provide proactive suggestions based on rules.
---

# CEO Briefing Writer

## Purpose

This skill generates executive-level weekly briefings for CEOs and senior leadership. It aggregates data from goals, completed tasks, financial metrics, and operational status to produce concise, actionable reports that highlight progress, identify bottlenecks, and provide strategic recommendations.

It prevents:
- Information overload from scattered data sources
- Missing critical business insights
- Delayed awareness of bottlenecks and risks
- Lack of strategic recommendations
- Manual report compilation overhead

---

## When to Use This Skill

This skill MUST be invoked when:

- **Weekly executive review** - Generate end-of-week CEO briefing
- **Board meeting preparation** - Prepare executive summary for board presentations
- **Strategic planning sessions** - Provide current state overview before planning
- **Investor updates** - Compile progress and financial metrics for investors
- **Quarterly business reviews** - Summarize quarter-to-date performance
- **Crisis management** - Generate rapid status assessment during critical situations

If this skill is NOT applied → executives lack consolidated view of business health and miss early warning signals.

---

## Overview

### Core Responsibilities

1. **Goal Tracking**: Read organizational goals and measure progress against targets
2. **Task Aggregation**: Summarize completed tasks, features shipped, and deliverables
3. **Financial Analysis**: Compile revenue, expenses, burn rate, and runway metrics
4. **Bottleneck Identification**: Detect blockers, delays, and resource constraints
5. **Strategic Recommendations**: Provide proactive suggestions based on business rules
6. **Trend Analysis**: Compare current period to previous periods and targets

### Briefing Sections

A complete CEO briefing includes:

1. **Executive Summary**: 3-5 bullet points of most critical information
2. **Business Health Score**: Overall health indicator with key metrics
3. **Goals & Progress**: Status of strategic objectives and OKRs
4. **Financial Performance**: Revenue, expenses, runway, and key financial ratios
5. **Operational Highlights**: Major accomplishments and completed initiatives
6. **Bottlenecks & Risks**: Critical blockers and risk factors requiring attention
7. **Strategic Recommendations**: Proactive suggestions for leadership action
8. **Week Ahead**: Upcoming milestones, decisions needed, and focus areas

---

## Impact Analysis Workflow

### 1. Data Source Discovery

Before briefing generation, the skill MUST:

**Locate Data Sources:**
```bash
# Goals and objectives
find . -type f -name "goals.md" -o -name "objectives.md" -o -name "okrs.md"

# Completed tasks
find . -type d -iname "done" -o -type d -iname "completed"

# Financial data
find . -type f -name "financials.json" -o -name "revenue.json" -o -name "budget.md"

# Common locations:
# - ./goals/
# - ./done/
# - ./financials/
# - ./vault/Goals/
# - ./vault/Financials/
```

**Identify Data Formats:**
```yaml
data_sources:
  goals:
    paths: ["./goals/", "./vault/Goals/"]
    formats: ["*.goals.md", "*.okr.md", "objectives.md"]
    fields: ["goal_id", "title", "target", "current", "status", "owner"]

  completed_tasks:
    paths: ["./done/", "./tasks/done/"]
    formats: ["*.task.md", "*.prompt.md"]
    fields: ["id", "title", "completed_at", "outcome", "impact"]

  financials:
    paths: ["./financials/", "./vault/Financials/"]
    formats: ["*.json", "*.csv", "financials.md"]
    fields: ["revenue", "expenses", "burn_rate", "runway_months", "arr", "mrr"]

  bottlenecks:
    paths: ["./tasks/", "./issues/"]
    formats: ["*.blocked.md", "*.issue.md"]
    fields: ["blocker_id", "title", "blocked_since", "impact", "owner"]
```

### 2. Metric Calculation

**Business Health Metrics:**
```yaml
health_metrics:
  financial_health:
    description: "Financial sustainability score"
    inputs: ["runway_months", "burn_rate", "revenue_growth"]
    calculation: |
      if runway_months > 18: score += 30
      elif runway_months > 12: score += 20
      elif runway_months > 6: score += 10
      else: score += 0

      if revenue_growth > 20%: score += 30
      elif revenue_growth > 10%: score += 20
      elif revenue_growth > 0%: score += 10
      else: score += 0

      if burn_rate_trend == "decreasing": score += 20
      elif burn_rate_trend == "stable": score += 10
      else: score += 0

    thresholds:
      excellent: ">= 70"
      good: ">= 50"
      fair: ">= 30"
      poor: "< 30"

  operational_health:
    description: "Execution and delivery score"
    inputs: ["goals_on_track", "tasks_completed", "deployment_success"]
    calculation: |
      score = (goals_on_track_percent * 0.4) +
              (tasks_completion_rate * 0.3) +
              (deployment_success_rate * 0.3)

    thresholds:
      excellent: ">= 80"
      good: ">= 65"
      fair: ">= 50"
      poor: "< 50"

  team_health:
    description: "Team capacity and morale score"
    inputs: ["response_time", "throughput", "quality_metrics"]
    calculation: |
      if avg_response_time < target: score += 30
      if throughput >= target: score += 40
      if bug_rate < threshold: score += 30

    thresholds:
      excellent: ">= 80"
      good: ">= 60"
      fair: ">= 40"
      poor: "< 40"
```

**Goal Progress Tracking:**
```yaml
goal_metrics:
  okr_completion:
    description: "Percentage of OKRs on track"
    calculation: "count(okrs_on_track) / count(total_okrs) * 100"

  goal_velocity:
    description: "Rate of goal completion"
    calculation: "goals_completed_this_period / weeks_in_period"

  at_risk_goals:
    description: "Goals at risk of missing target"
    criteria:
      - "current_progress < (target_progress * 0.8)"
      - "days_remaining < 30 AND progress < 70%"
      - "blocked_for > 7 days"
```

**Financial Metrics:**
```yaml
financial_metrics:
  revenue:
    mrr: "Monthly Recurring Revenue"
    arr: "Annual Recurring Revenue (MRR * 12)"
    growth_rate: "(current_mrr - previous_mrr) / previous_mrr * 100"

  expenses:
    burn_rate: "Monthly cash burn"
    runway: "cash_balance / burn_rate"
    burn_multiple: "burn_rate / net_new_arr"

  efficiency:
    cac: "Customer Acquisition Cost"
    ltv: "Lifetime Value"
    ltv_cac_ratio: "ltv / cac"
    magic_number: "net_new_arr / sales_marketing_spend"
```

### 3. Bottleneck Detection Rules

**Automatic Bottleneck Detection:**
```javascript
function detectBottlenecks(data) {
  const bottlenecks = [];

  // Financial bottlenecks
  if (data.runway_months < 6) {
    bottlenecks.push({
      type: "financial",
      severity: "critical",
      title: "Runway below 6 months",
      impact: "Business continuity at risk",
      recommendation: "Immediate fundraising or cost reduction required"
    });
  }

  if (data.burn_rate_trend === "increasing" && data.revenue_growth < 10) {
    bottlenecks.push({
      type: "financial",
      severity: "high",
      title: "Burn rate increasing without revenue growth",
      impact: "Runway decreasing faster than planned",
      recommendation: "Review expense structure and revenue acceleration plans"
    });
  }

  // Operational bottlenecks
  if (data.blocked_tasks > 5) {
    bottlenecks.push({
      type: "operational",
      severity: "high",
      title: `${data.blocked_tasks} tasks blocked`,
      impact: "Delivery velocity impacted",
      recommendation: "Unblock critical path items immediately"
    });
  }

  if (data.goals_at_risk > 3) {
    bottlenecks.push({
      type: "strategic",
      severity: "high",
      title: `${data.goals_at_risk} goals at risk`,
      impact: "Quarterly objectives may be missed",
      recommendation: "Reprioritize resources or adjust targets"
    });
  }

  // Team bottlenecks
  if (data.avg_response_time > data.target_response_time * 2) {
    bottlenecks.push({
      type: "team",
      severity: "medium",
      title: "Response time degraded",
      impact: "Customer satisfaction and team efficiency affected",
      recommendation: "Review team capacity and workload distribution"
    });
  }

  return bottlenecks.sort((a, b) =>
    severityScore(b.severity) - severityScore(a.severity)
  );
}
```

### 4. Strategic Recommendation Engine

**Rule-Based Recommendations:**
```javascript
function generateRecommendations(data, bottlenecks) {
  const recommendations = [];

  // Financial recommendations
  if (data.runway_months < 12 && data.revenue_growth > 20) {
    recommendations.push({
      category: "financial",
      priority: "high",
      title: "Consider raising capital from position of strength",
      rationale: "Strong revenue growth + runway below 12 months",
      action: "Initiate fundraising conversations with investors",
      expected_outcome: "Extend runway to 24+ months, fuel growth"
    });
  }

  if (data.ltv_cac_ratio > 3 && data.magic_number > 0.75) {
    recommendations.push({
      category: "growth",
      priority: "high",
      title: "Accelerate customer acquisition",
      rationale: "Strong unit economics indicate scalable growth model",
      action: "Increase sales & marketing spend by 30-50%",
      expected_outcome: "Faster revenue growth with healthy payback"
    });
  }

  // Operational recommendations
  if (data.deployment_frequency < 1 && data.bug_rate > 1.5) {
    recommendations.push({
      category: "operational",
      priority: "medium",
      title: "Improve deployment pipeline and quality",
      rationale: "Low deployment frequency + high bug rate",
      action: "Invest in CI/CD automation and testing infrastructure",
      expected_outcome: "Faster delivery with fewer production issues"
    });
  }

  // Strategic recommendations
  if (data.goals_completed_rate > 90 && data.team_capacity > 80) {
    recommendations.push({
      category: "strategic",
      priority: "medium",
      title: "Set more ambitious goals or expand team",
      rationale: "Consistently exceeding targets with high capacity utilization",
      action: "Either increase goal targets by 20% or hire 2-3 additional team members",
      expected_outcome: "Maintain growth momentum without team burnout"
    });
  }

  return recommendations.sort((a, b) =>
    priorityScore(b.priority) - priorityScore(a.priority)
  );
}
```

---

## Environment Variable Strategy

**Runtime Variables:**
```yaml
# Data source paths
CEO_BRIEFING_GOALS_PATH: "{{GOALS_FOLDER_PATH}}"
CEO_BRIEFING_DONE_PATH: "{{DONE_FOLDER_PATH}}"
CEO_BRIEFING_FINANCIALS_PATH: "{{FINANCIALS_FOLDER_PATH}}"
CEO_BRIEFING_ISSUES_PATH: "{{ISSUES_FOLDER_PATH}}"

# Output configuration
CEO_BRIEFING_OUTPUT_PATH: "{{OUTPUT_FILE_PATH}}"
CEO_BRIEFING_ARCHIVE_PATH: "{{ARCHIVE_PATH}}"

# Period configuration
CEO_BRIEFING_PERIOD: "{{weekly|monthly|quarterly}}"
CEO_BRIEFING_TIMEZONE: "{{TIMEZONE}}"

# Thresholds and targets
CEO_BRIEFING_RUNWAY_WARNING: "{{MONTHS}}"
CEO_BRIEFING_REVENUE_TARGET: "{{TARGET_USD}}"
CEO_BRIEFING_BURN_RATE_BUDGET: "{{BUDGET_USD}}"

# Recommendation rules
CEO_BRIEFING_ENABLE_RECOMMENDATIONS: "{{true|false}}"
CEO_BRIEFING_RECOMMENDATION_CONFIDENCE: "{{high|medium|low}}"
```

**Default Values:**
```yaml
CEO_BRIEFING_GOALS_PATH: "./goals/"
CEO_BRIEFING_DONE_PATH: "./done/"
CEO_BRIEFING_FINANCIALS_PATH: "./financials/"
CEO_BRIEFING_OUTPUT_PATH: "./CEO_Briefing.md"
CEO_BRIEFING_ARCHIVE_PATH: "./archive/briefings/"
CEO_BRIEFING_PERIOD: "weekly"
CEO_BRIEFING_TIMEZONE: "UTC"
CEO_BRIEFING_RUNWAY_WARNING: "12"
CEO_BRIEFING_ENABLE_RECOMMENDATIONS: "true"
CEO_BRIEFING_RECOMMENDATION_CONFIDENCE: "high"
```

---

## Briefing Template Structure

### Executive Summary Template
```markdown
# CEO Briefing - Week of {{DATE}}

**Generated:** {{TIMESTAMP}}
**Period:** {{START_DATE}} to {{END_DATE}}
**Overall Status:** {{STATUS_EMOJI}} {{STATUS_TEXT}}

## Executive Summary

{{#each top_highlights}}
- {{emoji}} **{{title}}**: {{description}}
{{/each}}

---

## Business Health Score: {{HEALTH_SCORE}}/100

| Dimension | Score | Status | Trend |
|-----------|-------|--------|-------|
| Financial Health | {{financial_score}}/100 | {{status_emoji}} {{status}} | {{trend_emoji}} {{trend}} |
| Operational Health | {{operational_score}}/100 | {{status_emoji}} {{status}} | {{trend_emoji}} {{trend}} |
| Team Health | {{team_score}}/100 | {{status_emoji}} {{status}} | {{trend_emoji}} {{trend}} |

**Overall Assessment:** {{health_assessment}}

---

## Goals & Progress

### Strategic Objectives ({{goals_on_track}}/{{total_goals}} on track)

{{#each goals}}
#### {{goal_title}}
- **Target:** {{target}}
- **Current:** {{current}} ({{progress_percent}}%)
- **Status:** {{status_emoji}} {{status}}
- **Owner:** {{owner}}
{{#if at_risk}}
- ⚠️ **Risk:** {{risk_description}}
{{/if}}
{{/each}}

### At-Risk Goals ({{at_risk_count}})

{{#each at_risk_goals}}
- 🔴 **{{title}}**: {{progress}}% complete, {{days_remaining}} days remaining
  - **Blocker:** {{blocker}}
  - **Action needed:** {{action}}
{{/each}}

---

## Financial Performance

### Revenue
- **MRR:** ${{mrr}} ({{mrr_trend_emoji}} {{mrr_change}}% vs last period)
- **ARR:** ${{arr}}
- **Growth Rate:** {{growth_rate}}% MoM
- **Target:** ${{target}} ({{percent_to_target}}% achieved)

### Expenses & Runway
- **Monthly Burn:** ${{burn_rate}}
- **Runway:** {{runway_months}} months
- **Cash Balance:** ${{cash_balance}}
{{#if runway_warning}}
- ⚠️ **Warning:** Runway below {{warning_threshold}} months
{{/if}}

### Unit Economics
- **CAC:** ${{cac}}
- **LTV:** ${{ltv}}
- **LTV:CAC Ratio:** {{ltv_cac_ratio}}:1 (target: >3:1)
- **Magic Number:** {{magic_number}} (target: >0.75)

---

## Operational Highlights

### Completed This Week ({{tasks_completed}})

{{#each top_accomplishments}}
- ✅ **{{title}}** ({{impact}})
{{/each}}

### Key Metrics
- **Deployments:** {{deployments}} ({{deployment_success}}% success rate)
- **Features Shipped:** {{features_shipped}}
- **Bugs Fixed:** {{bugs_fixed}}
- **Customer Issues Resolved:** {{issues_resolved}}

---

## Bottlenecks & Risks

{{#if no_bottlenecks}}
✅ No critical bottlenecks identified this week.
{{else}}
### Critical Issues ({{critical_count}})

{{#each critical_bottlenecks}}
#### {{severity_emoji}} {{title}}
- **Type:** {{type}}
- **Impact:** {{impact}}
- **Duration:** {{duration}}
- **Recommendation:** {{recommendation}}
{{/each}}

### Medium Priority ({{medium_count}})

{{#each medium_bottlenecks}}
- ⚠️ **{{title}}**: {{impact}}
{{/each}}
{{/if}}

---

## Strategic Recommendations

{{#each recommendations}}
### {{priority_emoji}} {{title}}

**Category:** {{category}}
**Priority:** {{priority}}

**Rationale:** {{rationale}}

**Recommended Action:** {{action}}

**Expected Outcome:** {{expected_outcome}}

**Timeline:** {{timeline}}

---
{{/each}}

## Week Ahead

### Upcoming Milestones
{{#each upcoming_milestones}}
- **{{date}}**: {{milestone}} ({{status}})
{{/each}}

### Decisions Needed
{{#each decisions_needed}}
- [ ] **{{decision}}** (Owner: {{owner}}, Deadline: {{deadline}})
{{/each}}

### Focus Areas
{{#each focus_areas}}
- 🎯 {{area}}: {{description}}
{{/each}}

---

**Next Briefing:** {{next_briefing_date}}
```

---

## Key Guarantees

1. **Executive-Level Focus**: Concise, strategic insights without operational noise
2. **Data-Driven**: All metrics sourced from actual data, not assumptions
3. **Actionable Recommendations**: Specific, prioritized actions with expected outcomes
4. **Bottleneck Detection**: Automatic identification of critical blockers
5. **Trend Analysis**: Week-over-week and target comparison
6. **Business Health Score**: Quantitative overall health assessment
7. **Consistent Format**: Standardized structure for easy scanning
8. **Archive History**: Previous briefings preserved for trend analysis

---

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [ ] Goals folder exists and contains parseable goal files
- [ ] Done folder exists and contains completed task data
- [ ] Financial data available (or gracefully handled if missing)
- [ ] Output path is writable
- [ ] Date/time calculations accurate across timezones
- [ ] Business health score calculation correct
- [ ] All template variables resolved (no placeholders in output)

### Quality Checks (Skill Degraded If Failed)

- [ ] Executive summary contains 3-5 most critical points
- [ ] Recommendations are specific and actionable
- [ ] Bottlenecks prioritized by severity
- [ ] Financial metrics formatted consistently
- [ ] Trends show meaningful comparisons
- [ ] No duplicate information across sections

---

## Anti-Patterns

### ❌ Information Overload
**Problem:** Too much detail obscures key insights

**Example:**
```markdown
<!-- WRONG: 50 tasks listed -->
Completed Tasks: [long list of every task]

<!-- CORRECT: Top highlights only -->
Top 5 Accomplishments:
1. Launched new payment system (revenue impact: +$50K/mo)
2. Closed Series A funding ($5M)
3. Shipped mobile app v2.0 (10K+ downloads in 3 days)
```

### ❌ Missing Context
**Problem:** Metrics without comparison are meaningless

**Example:**
```markdown
<!-- WRONG -->
Revenue: $100K

<!-- CORRECT -->
Revenue: $100K (+25% vs last week, 80% of monthly target)
```

### ❌ Vague Recommendations
**Problem:** Generic advice without specific actions

**Example:**
```markdown
<!-- WRONG -->
Recommendation: Improve sales performance

<!-- CORRECT -->
Recommendation: Hire 2 additional SDRs by end of Q1
Rationale: Current team at 120% capacity, pipeline growing 30% MoM
Expected Outcome: Increase qualified leads by 40%, close rate maintained
```

---

## Integration with Other Skills

### Upstream Skills
- `vault_state_manager` → Reads goals, tasks, financial data
- `task_lifecycle_manager` → Provides completed task metrics
- `dashboard_writer` → Shares operational metrics

### Downstream Skills
- `email_drafter` → Can draft email to send briefing to stakeholders
- `approval_request_creator` → May require approval for sensitive recommendations

---

## Final Rule (Hard Stop)

If user requests CEO briefing without sufficient data:

```
User: "Generate CEO briefing"

Agent: "Checking data sources...

⚠️ Cannot generate complete CEO briefing: Missing required data

Data Source Status:
- Goals folder: ./goals/ ✓ (3 goals found)
- Done folder: ./done/ ❌ (no completed tasks this week)
- Financials: ./financials/ ⚠️ (partial data - missing runway)

Minimum Requirements:
- At least 1 goal defined
- At least 1 completed task in period
- Basic financial data (revenue OR expenses)

Options:
1. Generate partial briefing with available data (will note missing sections)
2. Wait until more data is available
3. Manually provide missing data

Would you like me to:
- Generate partial briefing?
- Show you how to add missing data?
- Use sample data for demonstration?"
```

Then wait for user choice.

---

## Example: End-to-End Briefing Generation

**Scenario:** Generate weekly CEO briefing on Friday afternoon

**Step 1: Data Collection**
```javascript
const data = {
  period: {
    start: '2025-01-27',
    end: '2025-02-02',
    label: 'Week of January 27, 2025'
  },
  goals: [
    { id: 'G1', title: 'Launch mobile app', target: 100, current: 85, status: 'on_track' },
    { id: 'G2', title: 'Reach $100K MRR', target: 100000, current: 87500, status: 'on_track' },
    { id: 'G3', title: 'Hire 5 engineers', target: 5, current: 2, status: 'at_risk' }
  ],
  tasks_completed: 23,
  financials: {
    mrr: 87500,
    arr: 1050000,
    burn_rate: 150000,
    runway_months: 14,
    cash_balance: 2100000
  },
  bottlenecks: [
    { type: 'hiring', severity: 'high', title: 'Engineering hiring behind target' }
  ]
};
```

**Step 2: Calculate Health Score**
```javascript
const healthScore = {
  financial: 75,  // Good runway, strong growth
  operational: 82, // High completion rate
  team: 65,       // Hiring challenges
  overall: 74     // Good overall
};
```

**Step 3: Generate Recommendations**
```javascript
const recommendations = [
  {
    title: "Accelerate engineering hiring",
    priority: "high",
    rationale: "Only 2/5 engineers hired, blocking product roadmap",
    action: "Engage recruiting agency, increase referral bonuses to $5K",
    expected_outcome: "3 additional hires by end of Q1"
  }
];
```

**Step 4: Write Briefing**
```bash
# Archive previous briefing
mv CEO_Briefing.md archive/briefings/CEO_Briefing-2025-01-27.md

# Write new briefing
# (generated content written to CEO_Briefing.md)
```

**Outcome:**
```
✅ CEO BRIEFING GENERATED

Period: Week of January 27, 2025
Health Score: 74/100 (Good)
Goals On Track: 2/3
Critical Bottlenecks: 1
Recommendations: 3 (1 high priority)

Briefing location: ./CEO_Briefing.md
Previous briefing archived: ./archive/briefings/CEO_Briefing-2025-01-27.md
```

---
