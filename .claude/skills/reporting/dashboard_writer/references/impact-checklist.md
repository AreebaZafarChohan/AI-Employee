# Dashboard Writer - Impact Checklist

This checklist ensures comprehensive dashboard generation and data accuracy.

---

## Pre-Generation Setup

### Data Source Configuration

- [ ] Done folder path configured: `DASHBOARD_DONE_FOLDER`
- [ ] Done folder exists and is readable
- [ ] At least one task file found in Done folder
- [ ] Task file format validated (YAML frontmatter or key-value)
- [ ] Timezone configured: `DASHBOARD_TIMEZONE`
- [ ] Period type selected: daily | weekly | monthly

### Output Configuration

- [ ] Dashboard.md path configured: `DASHBOARD_PATH`
- [ ] Dashboard path is writable
- [ ] Archive path configured: `DASHBOARD_ARCHIVE_PATH`
- [ ] Archive folder exists or can be created
- [ ] Previous dashboard backed up (if exists)

---

## Data Collection Checks

### Task Data

- [ ] Task files contain required fields:
  - [ ] `id` or identifier
  - [ ] `completed_at` timestamp
  - [ ] `title` or description
- [ ] Optional fields captured (if present):
  - [ ] `duration` (hours)
  - [ ] `response_time` (hours)
  - [ ] `revenue` (USD)
  - [ ] `cost` (USD)
  - [ ] `type` (feature, bug, etc.)
  - [ ] `status` (done, deployed, etc.)

### Git History (if applicable)

- [ ] Git repository detected
- [ ] Git log accessible
- [ ] Commits filtered by date range
- [ ] Commit messages parsed correctly
- [ ] Authors/contributors identified

### External APIs (if configured)

- [ ] API tokens configured and valid
- [ ] API endpoints accessible
- [ ] Rate limits considered
- [ ] Responses cached (if appropriate)
- [ ] Error handling for API failures

---

## Metric Calculation Checks

### Count Metrics

- [ ] Tasks completed count accurate
- [ ] Deployments counted
- [ ] Commits counted
- [ ] Issues resolved counted
- [ ] Features shipped identified
- [ ] Bugs fixed counted

### Time Metrics

- [ ] Average response time calculated
  - [ ] Missing values handled
  - [ ] Outliers identified
  - [ ] Median included for robustness
- [ ] Average task duration calculated
- [ ] Cycle time (start to completion) calculated
- [ ] Time metrics formatted (hours, days, etc.)

### Financial Metrics

- [ ] Revenue aggregated
- [ ] Expenses aggregated
- [ ] Profit calculated (revenue - expenses)
- [ ] Margin calculated (if revenue > 0)
- [ ] Budget tracking enabled (if configured)
- [ ] Currency formatting applied ($ symbols, commas)

### Quality Metrics

- [ ] Bug rate calculated (bugs per feature)
- [ ] Deployment success rate calculated
- [ ] Test coverage retrieved (if available)
- [ ] Rollback rate calculated (if applicable)

---

## Trend Analysis Checks

### Period Comparison

- [ ] Current period data complete
- [ ] Previous period data available
  - If not: Handle gracefully with "First period, no comparison"
- [ ] Trend direction calculated (up/down/same)
- [ ] Percent change calculated
- [ ] Change significance determined
- [ ] Trend emoji selected (📈/📉/➡️)

### Trend Interpretation

- [ ] "Higher is better" metrics identified:
  - [ ] Tasks completed
  - [ ] Revenue
  - [ ] Deployment success rate
- [ ] "Lower is better" metrics identified:
  - [ ] Response time
  - [ ] Bug rate
  - [ ] Expenses
- [ ] Emoji direction correct for metric type

---

## Dashboard Section Generation

### Executive Summary

- [ ] Period label formatted (e.g., "Week of January 15, 2024")
- [ ] Generation timestamp included
- [ ] Overall status indicator present (🟢/🟡/🔴)
- [ ] Key highlights listed (3-5 items)
- [ ] Health indicator with explanation

### Project Status (if applicable)

- [ ] Active projects listed
- [ ] Progress bars rendered
- [ ] Status emojis correct
- [ ] Owners identified
- [ ] Next milestones shown
- [ ] Blocked projects highlighted
- [ ] Recently completed projects listed

### Team Metrics

- [ ] Response time table formatted
- [ ] Throughput metrics included
- [ ] Quality metrics shown
- [ ] All metrics have trends (if available)
- [ ] Target values shown (if configured)
- [ ] Status indicators (✅/⚠️/❌) based on targets

### Financial Dashboard

- [ ] Revenue formatted with currency symbol
- [ ] Expenses formatted
- [ ] Profit/margin calculated
- [ ] Budget status table (if configured)
- [ ] Over-budget warning (if applicable)

### Deadlines & Milestones

- [ ] Upcoming deadlines listed (next 7 days)
- [ ] Overdue items highlighted
- [ ] Days until/overdue calculated
- [ ] Risk indicators shown
- [ ] Quarterly milestones included

### Recent Activities

- [ ] Completed tasks listed
- [ ] Deployments noted
- [ ] Major accomplishments highlighted
- [ ] Limit to reasonable count (e.g., top 10)
- [ ] Link to full list (if many items)

### Action Items (if configured)

- [ ] Next steps identified
- [ ] Pending approvals listed
- [ ] Decisions needed highlighted
- [ ] Assigned owners shown

---

## Formatting and Display Checks

### Markdown Syntax

- [ ] Headers use correct level (#, ##, ###)
- [ ] Tables formatted properly (pipes aligned)
- [ ] Lists use consistent markers (-, *, 1.)
- [ ] Links formatted: `[text](url)`
- [ ] Code blocks use triple backticks when needed

### Visual Elements

- [ ] Emojis render correctly:
  - [ ] Status: ✅ 🔄 ⏳ ❌
  - [ ] Trends: 📈 📉 ➡️
  - [ ] Health: 🟢 🟡 🔴
  - [ ] Warnings: ⚠️
- [ ] Progress bars render:
  - [ ] Unicode: ████████░░ 80%
  - [ ] Or ASCII fallback: [========--] 80%
- [ ] Tables have separators

### Number Formatting

- [ ] Large numbers have commas: 1,250,000
- [ ] Currency has symbol: $12,500
- [ ] Percentages have % sign: 45.3%
- [ ] Decimals limited: 4.23 (not 4.2333333)
- [ ] "N/A" shown for missing data (not 0 or undefined)

---

## Data Integrity Validation

### Completeness

- [ ] No required sections missing
- [ ] All metrics have values (or "N/A")
- [ ] No "undefined" or "null" in output
- [ ] No "NaN" or "Infinity" in calculations

### Accuracy

- [ ] Date ranges correct (start/end)
- [ ] No duplicate tasks counted
- [ ] Time periods don't overlap
- [ ] Timezone conversions accurate
- [ ] Rounding appropriate (not too precise)

### Consistency

- [ ] Metric definitions consistent across periods
- [ ] Units labeled (hours, days, USD, %)
- [ ] Date formats consistent
- [ ] Naming conventions followed

---

## Archive and Backup

### Previous Dashboard

- [ ] Previous Dashboard.md exists (if not first run)
- [ ] Previous version archived before overwrite
- [ ] Archive filename includes date: `Dashboard-2024-01-15.md`
- [ ] Archive folder organized (by year/month if many)

### Metadata

- [ ] Dashboard includes generation timestamp
- [ ] Dashboard includes period covered
- [ ] Dashboard includes data source info (optional)
- [ ] Dashboard version tracked (optional)

---

## Performance Validation

### Generation Time

- [ ] Dashboard generation completes within acceptable time:
  - [ ] < 5 seconds for local files only
  - [ ] < 30 seconds with git history
  - [ ] < 2 minutes with external APIs
- [ ] Timeout configured for API calls
- [ ] Progress indicators for long operations (optional)

### Resource Usage

- [ ] Memory usage reasonable (< 500MB for typical dataset)
- [ ] File handles closed after reading
- [ ] No memory leaks in scheduled runs
- [ ] Caches cleared when appropriate

---

## Error Handling Checks

### Missing Data

- [ ] Empty Done folder handled gracefully
- [ ] Zero tasks in period shows helpful message
- [ ] Missing fields in tasks don't crash parser
- [ ] Missing previous period handled (first run)

### External Failures

- [ ] Git command failures handled (not a git repo)
- [ ] API failures handled (network, rate limit, auth)
- [ ] File system errors handled (permissions, disk full)
- [ ] Invalid dates handled

### Recovery

- [ ] Partial data still generates dashboard (degraded mode)
- [ ] Error messages clear and actionable
- [ ] Logs capture errors for debugging
- [ ] User notified of missing/incomplete data

---

## Integration Checks

### Skill Integration

- [ ] Works with `/sp.implement` outputs (task completion)
- [ ] Works with `/sp.phr` (prompt history records)
- [ ] Works with `/sp.git.commit_pr` (git activity)
- [ ] Standalone operation possible (doesn't require other skills)

### Notification Integration (optional)

- [ ] Slack webhook configured (if using)
- [ ] Email notification configured (if using)
- [ ] Notification message includes key highlights
- [ ] Link to Dashboard.md included

### Scheduled Execution (optional)

- [ ] Cron schedule configured correctly
- [ ] Runs at expected times
- [ ] Handles failures gracefully (retry or skip)
- [ ] Logs execution results

---

## Final Pre-Publish Checklist

Before writing Dashboard.md:

- [ ] All sections generated successfully
- [ ] No placeholder text remaining (`{{VARIABLE}}`)
- [ ] All calculations verified
- [ ] Formatting validated (Markdown lint if available)
- [ ] Previous dashboard archived
- [ ] Ready to write: YES / NO

**If NO:** Document blockers and retry after fixes.

---

## Post-Generation Validation

After writing Dashboard.md:

- [ ] File created successfully
- [ ] File size reasonable (not 0 bytes, not > 1MB)
- [ ] Markdown renders correctly (preview)
- [ ] All links work (if any)
- [ ] Readable by target audience
- [ ] Meets team's expectations

---

## Troubleshooting Quick Checks

If dashboard is empty/broken:

1. [ ] Check Done folder has files: `ls -la $DASHBOARD_DONE_FOLDER`
2. [ ] Check date range includes data: "Are tasks in this period?"
3. [ ] Check file parsing: "Can you parse task files?"
4. [ ] Check calculations: "Are divisions by zero happening?"
5. [ ] Check previous run: "Did it work before? What changed?"

If metrics look wrong:

1. [ ] Verify timezone setting
2. [ ] Check for duplicate counting
3. [ ] Validate date filtering
4. [ ] Check metric definitions (what does "response time" mean?)
5. [ ] Compare to manual count (sanity check)

If trends are missing:

1. [ ] Is this the first run? (no previous period data)
2. [ ] Is previous period empty? (zero tasks to compare)
3. [ ] Archive folder accessible? (previous dashboards)
4. [ ] Calculation error? (division by zero)

---

## Notes

- This checklist should be completed for EVERY dashboard generation
- Missing items indicate incomplete or risky dashboard
- Document any exceptions or deviations
- Update checklist as new issues are discovered
- Automate checks where possible (validation script)

---
