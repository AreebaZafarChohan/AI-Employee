# CEO Briefing Writer - Common Gotchas

## 1. Timezone Mismatches

**Problem:** Week boundaries calculated in wrong timezone

**Symptom:**
```
Expected: Week of Jan 27 - Feb 2
Actual: Week of Jan 26 - Feb 1 (off by one day)
```

**Cause:**
```javascript
// WRONG: Uses system timezone
const startOfWeek = new Date().setDate(date.getDate() - date.getDay());

// CORRECT: Use configured timezone
const startOfWeek = moment.tz(date, TIMEZONE).startOf('week');
```

**Fix:**
- Always use configured timezone from `CEO_BRIEFING_TIMEZONE`
- Explicitly convert all dates to target timezone
- Test with different timezone configurations

---

## 2. Missing Financial Data

**Problem:** Briefing fails when financial data unavailable

**Symptom:**
```
Error: Cannot read property 'mrr' of undefined
```

**Cause:**
```javascript
// WRONG: Assumes financial data always exists
const mrr = data.financials.mrr;

// CORRECT: Handle missing data gracefully
const mrr = data.financials?.mrr || 'N/A';
```

**Fix:**
```javascript
function getFinancialMetrics(data) {
  if (!data.financials) {
    return {
      mrr: 'N/A',
      arr: 'N/A',
      runway: 'N/A',
      note: 'Financial data unavailable for this period'
    };
  }
  return data.financials;
}
```

---

## 3. Division by Zero in Metrics

**Problem:** Calculating ratios with zero denominators

**Symptom:**
```
LTV:CAC Ratio: Infinity:1
Growth Rate: NaN%
```

**Cause:**
```javascript
// WRONG: No zero check
const ratio = ltv / cac;
const growth = (current - previous) / previous * 100;

// CORRECT: Handle zero denominators
const ratio = cac > 0 ? ltv / cac : 'N/A';
const growth = previous > 0 ? (current - previous) / previous * 100 : 'N/A';
```

**Fix:**
```javascript
function calculateRatio(numerator, denominator, label) {
  if (denominator === 0 || denominator === null || denominator === undefined) {
    return { value: 'N/A', note: `${label} unavailable (denominator is zero)` };
  }
  return { value: (numerator / denominator).toFixed(2), note: null };
}
```

---

## 4. Stale Cached Data

**Problem:** Briefing shows outdated metrics

**Symptom:**
```
Briefing shows revenue from last week instead of current week
```

**Cause:**
```javascript
// WRONG: Using cached data without timestamp check
const data = cache.get('financial_data');

// CORRECT: Validate cache freshness
const data = cache.get('financial_data');
if (!data || isCacheStale(data.timestamp, MAX_CACHE_AGE)) {
  data = await fetchFreshData();
  cache.set('financial_data', data);
}
```

**Fix:**
- Always check cache timestamp
- Set appropriate cache TTL (e.g., 1 hour for financial data)
- Force refresh for critical briefings

---

## 5. Incomplete Goal Data

**Problem:** Goals missing required fields

**Symptom:**
```
Goal progress shows "undefined%" or "NaN%"
```

**Cause:**
```yaml
# WRONG: Goal file missing target
---
id: G1
title: Launch mobile app
current: 85
# target: 100  <-- MISSING
---
```

**Fix:**
```javascript
function validateGoal(goal) {
  const required = ['id', 'title', 'target', 'current'];
  const missing = required.filter(field => !goal[field]);

  if (missing.length > 0) {
    console.warn(`Goal ${goal.id} missing fields: ${missing.join(', ')}`);
    return {
      ...goal,
      target: goal.target || 100,
      current: goal.current || 0,
      status: 'incomplete_data'
    };
  }

  return goal;
}
```

---

## 6. Bottleneck Detection False Positives

**Problem:** Too many bottlenecks flagged, causing alert fatigue

**Symptom:**
```
Bottlenecks: 15 critical issues
(Most are not actually critical)
```

**Cause:**
```javascript
// WRONG: Too sensitive thresholds
if (data.runway_months < 18) {
  bottlenecks.push({ severity: 'critical', ... });
}

// CORRECT: Appropriate thresholds
if (data.runway_months < 6) {
  bottlenecks.push({ severity: 'critical', ... });
} else if (data.runway_months < 12) {
  bottlenecks.push({ severity: 'medium', ... });
}
```

**Fix:**
- Calibrate thresholds based on company stage
- Use severity levels appropriately (critical = immediate action required)
- Limit critical bottlenecks to top 3-5 issues

---

## 7. Recommendation Overload

**Problem:** Too many recommendations, unclear priorities

**Symptom:**
```
Strategic Recommendations: 12 items
(CEO doesn't know where to focus)
```

**Cause:**
```javascript
// WRONG: Include all possible recommendations
const recommendations = generateAllRecommendations(data);

// CORRECT: Prioritize and limit
const recommendations = generateAllRecommendations(data)
  .sort((a, b) => priorityScore(b) - priorityScore(a))
  .slice(0, 5);  // Top 5 only
```

**Fix:**
- Limit to 3-5 recommendations maximum
- Prioritize by impact and urgency
- Group related recommendations

---

## 8. Inconsistent Date Formatting

**Problem:** Dates formatted differently across sections

**Symptom:**
```
Executive Summary: "Week of 2025-01-27"
Goals Section: "January 27, 2025"
Financials: "01/27/2025"
```

**Cause:**
```javascript
// WRONG: Different formatting in each section
const date1 = moment(date).format('YYYY-MM-DD');
const date2 = moment(date).format('MMMM DD, YYYY');
const date3 = moment(date).format('MM/DD/YYYY');

// CORRECT: Consistent formatting
const formatDate = (date) => moment(date).format('MMMM DD, YYYY');
```

**Fix:**
```javascript
// Define standard formats
const DATE_FORMATS = {
  display: 'MMMM DD, YYYY',
  short: 'MMM DD',
  iso: 'YYYY-MM-DD'
};

// Use consistently
const displayDate = moment(date).format(DATE_FORMATS.display);
```

---

## 9. Large File Sizes

**Problem:** Briefing file becomes too large with embedded data

**Symptom:**
```
CEO_Briefing.md: 5.2 MB
(Takes long to load, hard to read)
```

**Cause:**
```markdown
<!-- WRONG: Embedding all raw data -->
## All Completed Tasks (500 tasks)
[Full list of 500 tasks with details...]
```

**Fix:**
```markdown
<!-- CORRECT: Summary with links -->
## Top Accomplishments (5)
[Top 5 tasks]

[See all 500 completed tasks →](./archive/tasks/2025-01-27-completed.md)
```

---

## 10. Hardcoded Thresholds

**Problem:** Thresholds not configurable per company

**Symptom:**
```
Runway warning at 12 months (too conservative for some companies)
```

**Cause:**
```javascript
// WRONG: Hardcoded threshold
if (runway_months < 12) {
  addWarning('Low runway');
}

// CORRECT: Configurable threshold
const RUNWAY_WARNING = process.env.CEO_BRIEFING_RUNWAY_WARNING || 12;
if (runway_months < RUNWAY_WARNING) {
  addWarning('Low runway');
}
```

**Fix:**
- Make all thresholds configurable via environment variables
- Provide sensible defaults
- Document threshold recommendations by company stage

---

## 11. Missing Comparison Data

**Problem:** Cannot calculate trends without historical data

**Symptom:**
```
Revenue: $100K (trend: N/A)
```

**Cause:**
```javascript
// WRONG: Assumes previous period data exists
const trend = (current - previous) / previous * 100;

// CORRECT: Handle missing previous data
const trend = previous
  ? (current - previous) / previous * 100
  : 'N/A (no historical data)';
```

**Fix:**
```javascript
function calculateTrend(current, previous, label) {
  if (!previous || previous === 0) {
    return {
      value: 'N/A',
      note: `No ${label} data from previous period for comparison`
    };
  }

  const change = ((current - previous) / previous * 100).toFixed(1);
  return {
    value: `${change}%`,
    direction: change > 0 ? 'up' : change < 0 ? 'down' : 'flat',
    emoji: change > 0 ? '📈' : change < 0 ? '📉' : '➡️'
  };
}
```

---

## 12. Circular Dependencies

**Problem:** Recommendation engine depends on bottleneck detection which depends on recommendations

**Symptom:**
```
Stack overflow or infinite loop during briefing generation
```

**Cause:**
```javascript
// WRONG: Circular dependency
function detectBottlenecks(data) {
  const recommendations = generateRecommendations(data);
  // Use recommendations to detect bottlenecks
}

function generateRecommendations(data) {
  const bottlenecks = detectBottlenecks(data);
  // Use bottlenecks to generate recommendations
}
```

**Fix:**
```javascript
// CORRECT: Linear dependency flow
function generateBriefing(data) {
  // 1. Calculate metrics (no dependencies)
  const metrics = calculateMetrics(data);

  // 2. Detect bottlenecks (depends on metrics only)
  const bottlenecks = detectBottlenecks(metrics);

  // 3. Generate recommendations (depends on metrics and bottlenecks)
  const recommendations = generateRecommendations(metrics, bottlenecks);

  return { metrics, bottlenecks, recommendations };
}
```

---

## Testing Checklist

Before deploying, test these scenarios:

- [ ] Generate briefing with complete data
- [ ] Generate briefing with missing financial data
- [ ] Generate briefing with missing goals
- [ ] Generate briefing with zero values (revenue, tasks, etc.)
- [ ] Generate briefing for first week (no historical data)
- [ ] Generate briefing across timezone boundaries
- [ ] Generate briefing with 0 completed tasks
- [ ] Generate briefing with 100+ completed tasks
- [ ] Verify all dates formatted consistently
- [ ] Verify no division by zero errors
- [ ] Verify cache invalidation works
- [ ] Verify archive mechanism works
- [ ] Verify recommendation prioritization
- [ ] Verify bottleneck severity levels
