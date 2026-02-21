# CEO Briefing Writer - Common Patterns

## Pattern 1: Weekly Executive Review

**Use Case:** Generate standard weekly briefing every Friday

**Implementation:**
```javascript
const { generateCEOBriefing } = require('./ceo_briefing_writer');

// Run every Friday at 4 PM
const briefing = await generateCEOBriefing({
  period: 'weekly',
  start_date: getStartOfWeek(),
  end_date: getEndOfWeek(),
  include_recommendations: true,
  confidence_level: 'high'
});

console.log(`Briefing generated: ${briefing.file_path}`);
```

**Expected Output:**
- File: `CEO_Briefing.md`
- Sections: 8 (Summary, Health, Goals, Financials, Highlights, Bottlenecks, Recommendations, Week Ahead)
- Previous briefing archived automatically

---

## Pattern 2: Board Meeting Preparation

**Use Case:** Generate comprehensive briefing for quarterly board meeting

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'quarterly',
  start_date: getStartOfQuarter(),
  end_date: getEndOfQuarter(),
  include_recommendations: true,
  include_detailed_financials: true,
  include_team_metrics: true,
  format: 'board_presentation',
  confidence_level: 'high'
});
```

**Customizations:**
- Extended financial section with unit economics
- Detailed goal progress with historical trends
- Strategic recommendations with ROI projections
- Risk assessment with mitigation plans

---

## Pattern 3: Crisis Management Briefing

**Use Case:** Generate rapid status assessment during critical situation

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'custom',
  start_date: incidentStartTime,
  end_date: new Date(),
  focus: 'crisis',
  include_recommendations: true,
  priority_filter: ['critical', 'high'],
  confidence_level: 'medium'  // Accept lower confidence for speed
});
```

**Characteristics:**
- Focus on critical bottlenecks only
- Immediate action recommendations
- Simplified metrics (only essential KPIs)
- Real-time data (no caching)

---

## Pattern 4: Investor Update

**Use Case:** Monthly update for investors with growth metrics

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'monthly',
  start_date: getStartOfMonth(),
  end_date: getEndOfMonth(),
  include_recommendations: false,  // Internal only
  include_detailed_financials: true,
  include_growth_metrics: true,
  format: 'investor_update',
  sections: [
    'executive_summary',
    'financial_performance',
    'growth_metrics',
    'key_milestones',
    'upcoming_focus'
  ]
});
```

**Investor-Specific Metrics:**
- MRR/ARR growth rate
- Customer acquisition metrics
- Burn multiple
- Runway
- Key milestones achieved

---

## Pattern 5: Automated Slack/Email Distribution

**Use Case:** Automatically send briefing to leadership team

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'weekly',
  start_date: getStartOfWeek(),
  end_date: getEndOfWeek(),
  include_recommendations: true
});

// Extract executive summary for Slack
const summary = extractExecutiveSummary(briefing);

await sendToSlack({
  channel: '#leadership',
  message: summary,
  attachment: briefing.file_path
});

// Send full briefing via email
await sendEmail({
  to: ['ceo@company.com', 'cfo@company.com', 'cto@company.com'],
  subject: `CEO Briefing - Week of ${formatDate(briefing.period.start)}`,
  body: briefing.markdown_content,
  attachments: [briefing.file_path]
});
```

---

## Pattern 6: Conditional Recommendations

**Use Case:** Only show recommendations when confidence is high

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'weekly',
  include_recommendations: true,
  recommendation_rules: {
    min_confidence: 0.8,
    min_data_points: 3,
    require_historical_comparison: true,
    categories: ['financial', 'strategic', 'operational']
  }
});
```

**Recommendation Filtering:**
- Only show recommendations with >80% confidence
- Require at least 3 data points supporting recommendation
- Must have historical data for comparison
- Filter by category relevance

---

## Pattern 7: Multi-Period Comparison

**Use Case:** Compare current week to previous weeks and targets

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'weekly',
  start_date: getStartOfWeek(),
  end_date: getEndOfWeek(),
  comparison_periods: [
    { label: 'Last Week', start: getStartOfWeek(-1), end: getEndOfWeek(-1) },
    { label: 'Last Month', start: getStartOfMonth(-1), end: getEndOfMonth(-1) },
    { label: 'Last Quarter', start: getStartOfQuarter(-1), end: getEndOfQuarter(-1) }
  ],
  include_trend_analysis: true
});
```

**Trend Indicators:**
- Week-over-week change
- Month-over-month change
- Quarter-over-quarter change
- Variance from target

---

## Pattern 8: Custom Bottleneck Rules

**Use Case:** Define company-specific bottleneck detection rules

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'weekly',
  bottleneck_rules: [
    {
      name: 'runway_critical',
      condition: (data) => data.runway_months < 6,
      severity: 'critical',
      message: 'Runway below 6 months - immediate action required'
    },
    {
      name: 'hiring_behind',
      condition: (data) => data.hiring_progress < 0.5 && data.days_remaining < 30,
      severity: 'high',
      message: 'Hiring significantly behind target with limited time'
    },
    {
      name: 'revenue_stagnant',
      condition: (data) => data.revenue_growth < 5 && data.burn_rate > data.revenue,
      severity: 'high',
      message: 'Revenue growth stagnant while burning cash'
    }
  ]
});
```

---

## Pattern 9: Goal-Specific Briefing

**Use Case:** Focus briefing on specific strategic initiative

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'weekly',
  focus_goal: 'G1',  // Specific goal ID
  include_related_tasks: true,
  include_related_metrics: true,
  sections: [
    'goal_progress',
    'related_tasks',
    'blockers',
    'recommendations'
  ]
});
```

**Goal-Focused Sections:**
- Detailed progress breakdown
- All tasks contributing to goal
- Specific blockers affecting goal
- Recommendations to accelerate progress

---

## Pattern 10: Data Source Fallbacks

**Use Case:** Generate briefing even with incomplete data

**Implementation:**
```javascript
const briefing = await generateCEOBriefing({
  period: 'weekly',
  data_sources: {
    goals: { path: './goals/', required: true },
    tasks: { path: './done/', required: true },
    financials: { path: './financials/', required: false, fallback: 'previous_period' },
    issues: { path: './issues/', required: false, fallback: 'empty' }
  },
  allow_partial_data: true,
  mark_missing_sections: true
});
```

**Fallback Strategies:**
- Use previous period data if current unavailable
- Mark sections as "Data Unavailable"
- Generate partial briefing with warnings
- Suggest data sources to add

---

## Best Practices

### 1. Consistent Scheduling
Run briefing generation at the same time each week for consistency:
```bash
# Cron job: Every Friday at 4 PM
0 16 * * 5 /path/to/generate_ceo_briefing.sh
```

### 2. Archive Management
Keep historical briefings for trend analysis:
```javascript
// Archive with descriptive naming
const archivePath = `./archive/briefings/CEO_Briefing-${formatDate(period.start)}.md`;
await archiveBriefing(currentBriefing, archivePath);
```

### 3. Validation Before Distribution
Always validate briefing before sending:
```javascript
const validation = validateBriefing(briefing);
if (!validation.isValid) {
  console.error('Briefing validation failed:', validation.errors);
  // Fix issues before distributing
}
```

### 4. Sensitive Data Handling
Redact sensitive information for different audiences:
```javascript
const publicBriefing = redactSensitiveData(briefing, {
  remove: ['detailed_financials', 'employee_names', 'customer_names'],
  aggregate: ['revenue', 'expenses']
});
```

### 5. Recommendation Review
Have human review high-impact recommendations:
```javascript
const briefing = await generateCEOBriefing({
  period: 'weekly',
  recommendation_review: {
    require_approval: ['financial', 'strategic'],
    auto_approve: ['operational'],
    approval_threshold: 'high_priority'
  }
});
```

---

## Anti-Patterns to Avoid

### ❌ Generating Without Data Validation
```javascript
// WRONG: Generate without checking data availability
const briefing = await generateCEOBriefing({ period: 'weekly' });

// CORRECT: Validate data sources first
const dataSources = await validateDataSources();
if (!dataSources.isValid) {
  console.error('Missing required data:', dataSources.missing);
  return;
}
const briefing = await generateCEOBriefing({ period: 'weekly' });
```

### ❌ Overloading with Details
```javascript
// WRONG: Include every metric and task
const briefing = await generateCEOBriefing({
  include_all_tasks: true,
  include_all_metrics: true,
  detail_level: 'maximum'
});

// CORRECT: Focus on executive-level insights
const briefing = await generateCEOBriefing({
  top_tasks: 5,
  key_metrics_only: true,
  detail_level: 'executive'
});
```

### ❌ Ignoring Trends
```javascript
// WRONG: Show only current period data
const briefing = await generateCEOBriefing({
  period: 'weekly',
  include_comparison: false
});

// CORRECT: Always include trend analysis
const briefing = await generateCEOBriefing({
  period: 'weekly',
  include_comparison: true,
  comparison_periods: ['last_week', 'last_month']
});
```
