# CEO Briefing Writer

Generate executive-level weekly briefings that summarize goals, tasks, finances, and provide strategic recommendations.

## Quick Start

```bash
# Set up data sources
export CEO_BRIEFING_GOALS_PATH="./goals/"
export CEO_BRIEFING_DONE_PATH="./done/"
export CEO_BRIEFING_FINANCIALS_PATH="./financials/"

# Generate weekly briefing
/ceo_briefing_writer
```

## What It Does

The CEO Briefing Writer automatically compiles a comprehensive executive briefing that includes:

- **Executive Summary**: 3-5 most critical highlights
- **Business Health Score**: Quantitative assessment across financial, operational, and team dimensions
- **Goals & Progress**: Status of strategic objectives with at-risk flagging
- **Financial Performance**: Revenue, expenses, runway, and unit economics
- **Operational Highlights**: Key accomplishments and metrics
- **Bottlenecks & Risks**: Critical issues requiring attention
- **Strategic Recommendations**: Data-driven suggestions for leadership action
- **Week Ahead**: Upcoming milestones and decisions needed

## Why Use This Skill

### Before This Skill
- ⏰ 2-4 hours to manually compile weekly briefing
- 📊 Data scattered across multiple sources
- 🔍 Bottlenecks discovered too late
- 🤔 Recommendations based on intuition, not data
- 📉 Inconsistent reporting format

### After This Skill
- ⚡ 5 minutes to generate comprehensive briefing
- 📈 All data automatically aggregated
- 🚨 Early warning system for bottlenecks
- 🎯 Data-driven strategic recommendations
- 📋 Consistent, professional format

## Installation

1. **Copy environment variables:**
   ```bash
   cp .claude/skills/reporting/ceo_briefing_writer/assets/.env.example .env
   ```

2. **Configure data sources:**
   ```bash
   # Edit .env file
   CEO_BRIEFING_GOALS_PATH="./goals/"
   CEO_BRIEFING_DONE_PATH="./done/"
   CEO_BRIEFING_FINANCIALS_PATH="./financials/"
   ```

3. **Create required folders:**
   ```bash
   mkdir -p goals done financials archive/briefings
   ```

4. **Test generation:**
   ```bash
   /ceo_briefing_writer
   ```

## Data Source Requirements

### Goals Folder
Location: `./goals/` (configurable)

Expected format:
```yaml
---
id: G1
title: Launch mobile app
target: 100
current: 85
status: on_track
owner: Jane Doe
deadline: 2025-03-31
---
```

### Done Folder
Location: `./done/` (configurable)

Expected format: Task files with completion metadata
```yaml
---
id: TASK-001
title: Implement payment system
completed_at: 2025-02-01T14:30:00Z
impact: high
outcome: Successfully deployed to production
---
```

### Financials Folder
Location: `./financials/` (configurable)

Expected format (JSON):
```json
{
  "period": "2025-02",
  "mrr": 87500,
  "arr": 1050000,
  "burn_rate": 150000,
  "cash_balance": 2100000,
  "runway_months": 14,
  "cac": 500,
  "ltv": 2000
}
```

Or Markdown:
```markdown
# Financials - February 2025

- MRR: $87,500
- ARR: $1,050,000
- Burn Rate: $150,000/month
- Cash Balance: $2,100,000
- Runway: 14 months
```

## Configuration

### Basic Configuration
```bash
# Minimum required
CEO_BRIEFING_GOALS_PATH="./goals/"
CEO_BRIEFING_DONE_PATH="./done/"
CEO_BRIEFING_FINANCIALS_PATH="./financials/"
```

### Advanced Configuration
```bash
# Thresholds
CEO_BRIEFING_RUNWAY_WARNING="12"  # Warn when runway < 12 months
CEO_BRIEFING_REVENUE_TARGET_MONTHLY="100000"  # Monthly target
CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.7"  # Flag goals < 70% progress

# Recommendations
CEO_BRIEFING_ENABLE_RECOMMENDATIONS="true"
CEO_BRIEFING_MAX_RECOMMENDATIONS="5"

# Output
CEO_BRIEFING_OUTPUT_PATH="./CEO_Briefing.md"
CEO_BRIEFING_ARCHIVE_PATH="./archive/briefings/"
```

## Usage Examples

### Weekly Briefing (Standard)
```bash
# Generate briefing for current week
/ceo_briefing_writer

# Output: CEO_Briefing.md
# Previous briefing archived automatically
```

### Monthly Briefing
```bash
# Configure for monthly period
export CEO_BRIEFING_PERIOD="monthly"
/ceo_briefing_writer
```

### Custom Period
```bash
# Generate briefing for specific date range
/ceo_briefing_writer --start-date 2025-01-01 --end-date 2025-01-31
```

### With Custom Thresholds
```bash
# Adjust thresholds for early-stage startup
export CEO_BRIEFING_RUNWAY_WARNING="6"  # More aggressive
export CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.5"  # More lenient
/ceo_briefing_writer
```

## Output Structure

The generated briefing includes:

```markdown
# CEO Briefing - Week of [Date]

## Executive Summary
- 3-5 critical highlights

## Business Health Score: XX/100
- Financial Health: XX/100
- Operational Health: XX/100
- Team Health: XX/100

## Goals & Progress
- Strategic objectives status
- At-risk goals

## Financial Performance
- Revenue metrics
- Expenses & runway
- Unit economics

## Operational Highlights
- Top accomplishments
- Key metrics

## Bottlenecks & Risks
- Critical issues
- High/medium priority items

## Strategic Recommendations
- Data-driven suggestions
- Expected outcomes

## Week Ahead
- Upcoming milestones
- Decisions needed
- Focus areas
```

## Key Features

### 1. Business Health Score
Quantitative assessment (0-100) across three dimensions:
- **Financial Health**: Runway, revenue growth, burn rate
- **Operational Health**: Goal progress, task completion, deployment success
- **Team Health**: Response time, throughput, quality metrics

### 2. Automatic Bottleneck Detection
Identifies critical issues based on rules:
- Runway below threshold
- Goals at risk of missing targets
- Tasks blocked for extended periods
- Revenue growth stagnant
- Team capacity constraints

### 3. Strategic Recommendations
Data-driven suggestions with:
- Clear rationale
- Specific actions
- Expected outcomes
- Priority ranking

### 4. Trend Analysis
Compares current period to:
- Previous week/month/quarter
- Targets and goals
- Historical averages

## Troubleshooting

### Briefing Generation Fails

**Problem:** Error when generating briefing

**Solutions:**
```bash
# Check data sources exist
ls -la $CEO_BRIEFING_GOALS_PATH
ls -la $CEO_BRIEFING_DONE_PATH
ls -la $CEO_BRIEFING_FINANCIALS_PATH

# Verify permissions
test -w $CEO_BRIEFING_OUTPUT_PATH && echo "Writable" || echo "Not writable"

# Check logs
tail -f ./logs/briefing_audit.log
```

### Missing Data Sections

**Problem:** Some sections show "N/A" or are empty

**Solutions:**
- Ensure data files exist in configured folders
- Verify data format matches expected schema
- Check date ranges (data may be outside period)
- Review logs for parsing errors

### Incorrect Metrics

**Problem:** Metrics don't match manual calculations

**Solutions:**
- Verify timezone configuration matches company timezone
- Check date range boundaries (week start/end)
- Ensure no duplicate data entries
- Validate data source timestamps

### Too Many Bottlenecks

**Problem:** Briefing flags too many issues

**Solutions:**
```bash
# Adjust sensitivity
export CEO_BRIEFING_BOTTLENECK_SENSITIVITY="low"

# Increase thresholds
export CEO_BRIEFING_RUNWAY_WARNING="6"  # Only warn below 6 months
export CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.5"  # Only flag below 50%
```

## Best Practices

### 1. Consistent Scheduling
Generate briefings at the same time each week:
```bash
# Cron job: Every Friday at 4 PM
0 16 * * 5 /path/to/generate_briefing.sh
```

### 2. Data Quality
- Keep data sources up to date
- Use consistent formats
- Validate data before briefing generation
- Archive historical data for trends

### 3. Threshold Calibration
- Start with default thresholds
- Adjust based on company stage and feedback
- Review quarterly as company grows

### 4. Review Process
- Have executive team review first few briefings
- Collect feedback on relevance and accuracy
- Iterate on recommendation rules

### 5. Archive Management
- Keep historical briefings for trend analysis
- Implement cleanup policy (e.g., keep 1 year)
- Back up archives regularly

## Integration

### With Email Drafter
Automatically email briefing to leadership:
```bash
/ceo_briefing_writer
/email_drafter --template executive_update --attach CEO_Briefing.md
```

### With Dashboard Writer
Share metrics between skills:
```bash
# Dashboard writer can reference briefing metrics
export DASHBOARD_BRIEFING_PATH="./CEO_Briefing.md"
```

### With Slack
Post executive summary to Slack:
```bash
/ceo_briefing_writer
# Extract summary and post to #leadership channel
```

## FAQ

**Q: How long does it take to generate a briefing?**
A: Typically 5-30 seconds depending on data volume.

**Q: Can I customize the briefing format?**
A: Yes, edit `assets/briefing-template.md` to customize sections and layout.

**Q: What if I don't have financial data?**
A: The skill will generate a partial briefing and mark financial sections as "Data Unavailable".

**Q: Can I generate briefings for past periods?**
A: Yes, use `--start-date` and `--end-date` parameters to specify custom periods.

**Q: How are recommendations generated?**
A: Based on rule-based logic analyzing metrics, trends, and thresholds. See `SKILL.md` for details.

**Q: Can I disable recommendations?**
A: Yes, set `CEO_BRIEFING_ENABLE_RECOMMENDATIONS="false"`.

## Support

- **Documentation**: See `SKILL.md` for detailed documentation
- **Examples**: See `EXAMPLES.md` for concrete usage examples
- **Common Issues**: See `references/gotchas.md` for troubleshooting
- **Patterns**: See `references/patterns.md` for advanced usage

## Version History

- **v1.0.0** (2025-02-05): Initial release
  - Weekly/monthly/quarterly briefing generation
  - Business health score calculation
  - Automatic bottleneck detection
  - Strategic recommendation engine
  - Trend analysis and comparison
  - Archive management
