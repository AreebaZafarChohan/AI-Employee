# CEO Briefing Writer - Installation Guide

This guide walks you through setting up the CEO Briefing Writer skill from scratch.

---

## Prerequisites

- Claude Code Agent system installed
- Access to project goals, tasks, and financial data
- Write permissions to project directory

---

## Installation Steps

### Step 1: Verify Skill Installation

The skill should already be installed in your Claude Code skills directory:

```bash
ls -la .claude/skills/reporting/ceo_briefing_writer/
```

Expected output:
```
SKILL.md
README.md
EXAMPLES.md
INSTALLATION.md
assets/
  .env.example
  briefing-template.md
references/
  patterns.md
  gotchas.md
  impact-checklist.md
```

### Step 2: Configure Environment Variables

Copy the example environment file:

```bash
cp .claude/skills/reporting/ceo_briefing_writer/assets/.env.example .env
```

Edit `.env` and configure your data source paths:

```bash
# Required: Data source paths
CEO_BRIEFING_GOALS_PATH="./goals/"
CEO_BRIEFING_DONE_PATH="./done/"
CEO_BRIEFING_FINANCIALS_PATH="./financials/"

# Required: Output configuration
CEO_BRIEFING_OUTPUT_PATH="./CEO_Briefing.md"
CEO_BRIEFING_ARCHIVE_PATH="./archive/briefings/"

# Optional: Customize thresholds
CEO_BRIEFING_RUNWAY_WARNING="12"
CEO_BRIEFING_REVENUE_TARGET_MONTHLY="100000"
```

### Step 3: Create Required Directories

```bash
# Create data source directories
mkdir -p goals
mkdir -p done
mkdir -p financials

# Create output directories
mkdir -p archive/briefings

# Verify permissions
test -w goals && echo "✓ goals writable"
test -w done && echo "✓ done writable"
test -w financials && echo "✓ financials writable"
test -w archive/briefings && echo "✓ archive writable"
```

### Step 4: Set Up Data Sources

#### Goals Folder

Create a goals file with your strategic objectives:

```bash
cat > goals/q1-2025.goals.md << 'EOF'
---
id: G1
title: Launch MVP
target: 100
current: 0
status: in_progress
owner: Jane Doe
deadline: 2025-03-31
---

# Goal: Launch MVP

## Description
Complete and launch minimum viable product with core features.

## Success Criteria
- All core features implemented
- 95%+ test coverage
- Performance benchmarks met
- Security audit passed

## Progress Updates
- 2025-02-01: Project kickoff, architecture defined
EOF
```

#### Done Folder

Create a sample completed task:

```bash
cat > done/sample-task.md << 'EOF'
---
id: TASK-001
title: Set up development environment
completed_at: 2025-02-05T10:00:00Z
impact: medium
outcome: Development environment configured and documented
---

# Task: Set up development environment

## What Was Done
- Configured local development environment
- Set up CI/CD pipeline
- Created documentation

## Impact
Medium - Enables team to start development work

## Metrics
- Setup time: 4 hours
- Team members onboarded: 5
EOF
```

#### Financials Folder

Create a sample financial data file:

```bash
cat > financials/2025-02.json << 'EOF'
{
  "period": "2025-02",
  "mrr": 50000,
  "arr": 600000,
  "burn_rate": 75000,
  "cash_balance": 900000,
  "runway_months": 12,
  "cac": 500,
  "ltv": 2000,
  "expenses": {
    "salaries": 60000,
    "infrastructure": 8000,
    "tools": 7000
  }
}
EOF
```

### Step 5: Test Briefing Generation

Generate your first CEO briefing:

```bash
# Load environment variables
source .env

# Generate briefing
/ceo_briefing_writer
```

Expected output:
```
✅ CEO BRIEFING GENERATED

Period: Week of February 5, 2025
Health Score: XX/100
Goals On Track: X/X
Critical Bottlenecks: X
Recommendations: X

Briefing location: ./CEO_Briefing.md
```

### Step 6: Verify Output

Check the generated briefing:

```bash
# View briefing
cat CEO_Briefing.md

# Check file size (should be reasonable, < 500KB)
ls -lh CEO_Briefing.md

# Verify archive was created (if this isn't first run)
ls -la archive/briefings/
```

---

## Configuration Options

### Basic Configuration (Minimum Required)

```bash
# Data sources
CEO_BRIEFING_GOALS_PATH="./goals/"
CEO_BRIEFING_DONE_PATH="./done/"
CEO_BRIEFING_FINANCIALS_PATH="./financials/"

# Output
CEO_BRIEFING_OUTPUT_PATH="./CEO_Briefing.md"
```

### Recommended Configuration

```bash
# Data sources
CEO_BRIEFING_GOALS_PATH="./goals/"
CEO_BRIEFING_DONE_PATH="./done/"
CEO_BRIEFING_FINANCIALS_PATH="./financials/"
CEO_BRIEFING_ISSUES_PATH="./issues/"

# Output
CEO_BRIEFING_OUTPUT_PATH="./CEO_Briefing.md"
CEO_BRIEFING_ARCHIVE_PATH="./archive/briefings/"

# Period
CEO_BRIEFING_PERIOD="weekly"
CEO_BRIEFING_TIMEZONE="America/New_York"

# Thresholds (adjust for your company stage)
CEO_BRIEFING_RUNWAY_WARNING="12"
CEO_BRIEFING_REVENUE_TARGET_MONTHLY="100000"
CEO_BRIEFING_BURN_RATE_BUDGET="150000"

# Recommendations
CEO_BRIEFING_ENABLE_RECOMMENDATIONS="true"
CEO_BRIEFING_MAX_RECOMMENDATIONS="5"
```

### Advanced Configuration

```bash
# All basic + recommended settings, plus:

# Health score weights (must sum to 1.0)
CEO_BRIEFING_FINANCIAL_WEIGHT="0.4"
CEO_BRIEFING_OPERATIONAL_WEIGHT="0.35"
CEO_BRIEFING_TEAM_WEIGHT="0.25"

# Bottleneck detection
CEO_BRIEFING_MAX_CRITICAL_BOTTLENECKS="3"
CEO_BRIEFING_BOTTLENECK_SENSITIVITY="medium"

# Formatting
CEO_BRIEFING_CURRENCY_SYMBOL="$"
CEO_BRIEFING_CURRENCY_LOCALE="en-US"
CEO_BRIEFING_DATE_FORMAT="MMMM DD, YYYY"
CEO_BRIEFING_USE_EMOJIS="true"

# Caching
CEO_BRIEFING_CACHE_ENABLED="true"
CEO_BRIEFING_CACHE_TTL="3600"

# Audit
CEO_BRIEFING_AUDIT_LOG_PATH="./logs/briefing_audit.log"
CEO_BRIEFING_LOG_LEVEL="info"
```

---

## Customization

### Customize Briefing Template

Edit the template to match your needs:

```bash
cp .claude/skills/reporting/ceo_briefing_writer/assets/briefing-template.md ./briefing-template-custom.md

# Edit template
nano briefing-template-custom.md

# Configure to use custom template
export CEO_BRIEFING_TEMPLATE_PATH="./briefing-template-custom.md"
```

### Adjust Thresholds by Company Stage

**Early-Stage Startup (Pre-Seed, Seed):**
```bash
CEO_BRIEFING_RUNWAY_WARNING="6"           # More aggressive
CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.5" # More lenient
CEO_BRIEFING_BOTTLENECK_SENSITIVITY="high" # Catch issues early
```

**Growth-Stage (Series A, B):**
```bash
CEO_BRIEFING_RUNWAY_WARNING="12"          # Standard
CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.7" # Moderate
CEO_BRIEFING_BOTTLENECK_SENSITIVITY="medium"
```

**Mature Company (Series C+, Public):**
```bash
CEO_BRIEFING_RUNWAY_WARNING="18"          # Conservative
CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.8" # Strict
CEO_BRIEFING_BOTTLENECK_SENSITIVITY="low" # Focus on critical only
```

**Bootstrapped/Profitable:**
```bash
CEO_BRIEFING_RUNWAY_WARNING="0"           # Not applicable
CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.75"
CEO_BRIEFING_ENABLE_RECOMMENDATIONS="true"
CEO_BRIEFING_RECOMMENDATION_CONFIDENCE="medium"
```

---

## Automation Setup

### Weekly Automated Briefing

Create a script to generate and distribute briefings:

```bash
cat > generate_weekly_briefing.sh << 'EOF'
#!/bin/bash

# Load environment
source .env

# Generate briefing
echo "Generating CEO briefing..."
/ceo_briefing_writer

# Check success
if [ $? -eq 0 ]; then
  echo "✅ Briefing generated successfully"

  # Optional: Send to Slack
  # curl -X POST $SLACK_WEBHOOK_URL -d @CEO_Briefing.md

  # Optional: Email to leadership
  # /email_drafter --template executive_update --attach CEO_Briefing.md
else
  echo "❌ Briefing generation failed"
  exit 1
fi
EOF

chmod +x generate_weekly_briefing.sh
```

### Schedule with Cron

```bash
# Edit crontab
crontab -e

# Add weekly briefing (every Friday at 4 PM)
0 16 * * 5 /path/to/generate_weekly_briefing.sh

# Or monthly briefing (first day of month at 9 AM)
0 9 1 * * /path/to/generate_monthly_briefing.sh
```

---

## Troubleshooting

### Issue: "Cannot find goals folder"

**Solution:**
```bash
# Check path configuration
echo $CEO_BRIEFING_GOALS_PATH

# Verify folder exists
ls -la $CEO_BRIEFING_GOALS_PATH

# Create if missing
mkdir -p $CEO_BRIEFING_GOALS_PATH
```

### Issue: "No data available for period"

**Solution:**
```bash
# Check if data files exist
ls -la done/
ls -la financials/

# Verify date range
# Data files should have timestamps within the briefing period

# Check file formats
cat done/sample-task.md  # Should have YAML frontmatter
```

### Issue: "Permission denied writing briefing"

**Solution:**
```bash
# Check write permissions
test -w . && echo "Current directory writable" || echo "Not writable"

# Check output path
test -w $(dirname $CEO_BRIEFING_OUTPUT_PATH) && echo "Output path writable" || echo "Not writable"

# Fix permissions
chmod u+w .
chmod u+w archive/briefings/
```

### Issue: "Metrics showing N/A"

**Solution:**
```bash
# Check data format
# Ensure JSON is valid
cat financials/2025-02.json | jq .

# Ensure YAML frontmatter is valid
head -n 10 goals/q1-2025.goals.md

# Check for missing required fields
# Goals need: id, title, target, current, status
# Tasks need: id, title, completed_at
# Financials need: mrr, burn_rate, runway_months
```

### Issue: "Timezone issues - wrong week boundaries"

**Solution:**
```bash
# Set timezone explicitly
export CEO_BRIEFING_TIMEZONE="America/New_York"

# Verify timezone
date
TZ=$CEO_BRIEFING_TIMEZONE date

# Test with explicit dates
/ceo_briefing_writer --start-date 2025-02-03 --end-date 2025-02-09
```

---

## Validation Checklist

After installation, verify:

- [ ] Environment variables configured
- [ ] Data source folders exist and are writable
- [ ] Sample data files created
- [ ] Briefing generates without errors
- [ ] Output file created at expected location
- [ ] Archive mechanism works (second run)
- [ ] All sections populated (no empty sections)
- [ ] Metrics calculated correctly
- [ ] Dates formatted correctly
- [ ] No placeholder variables ({{VARIABLE}}) in output

---

## Next Steps

1. **Populate Real Data**: Replace sample data with actual goals, tasks, and financials
2. **Calibrate Thresholds**: Adjust warning thresholds based on your company stage
3. **Set Up Automation**: Schedule weekly briefing generation
4. **Customize Template**: Modify template to match your reporting needs
5. **Integrate with Tools**: Connect to Slack, email, or other distribution channels

---

## Getting Help

- **Documentation**: See `SKILL.md` for detailed documentation
- **Examples**: See `EXAMPLES.md` for real-world usage examples
- **Common Issues**: See `references/gotchas.md` for troubleshooting
- **Patterns**: See `references/patterns.md` for advanced usage patterns

---

## Uninstallation

To remove the skill:

```bash
# Remove skill directory
rm -rf .claude/skills/reporting/ceo_briefing_writer/

# Remove generated files
rm -f CEO_Briefing.md
rm -rf archive/briefings/

# Remove environment variables
# Edit .env and remove CEO_BRIEFING_* variables
```

---

**Installation Complete!** 🎉

You're now ready to generate executive briefings. Run `/ceo_briefing_writer` to create your first briefing.
