# Dashboard Writer - Gotchas

Common pitfalls, edge cases, and known issues when generating dashboards.

---

## Data Collection Gotchas

### Issue 1: Empty Done Folder

**Problem:** No completed tasks in the period

**Example:**
```javascript
const tasks = await collectTasksFromDoneFolder(period);
// tasks.length === 0
```

**Why It's a Problem:**
- Dashboard shows zeros for all metrics
- Trends cannot be calculated (division by zero)
- Looks like system is broken

**Mitigation:**
```javascript
function generateDashboard(data, period) {
  if (data.tasks.length === 0) {
    return `# Dashboard - ${period.label}

⚠️ **No data available for this period**

Possible reasons:
- No tasks completed in ${period.label}
- Done folder empty or misconfigured
- Date range outside of available data

Try:
- Check a different time period
- Verify DASHBOARD_DONE_FOLDER path
- Ensure tasks are being marked as done

Last updated: ${new Date().toISOString()}`;
  }

  // Normal dashboard generation
  return generateFullDashboard(data, period);
}
```

---

### Issue 2: Inconsistent Task File Format

**Problem:** Task files don't follow expected structure

**Example:**
```markdown
<!-- Some files have YAML frontmatter -->
---
id: TASK-001
completed_at: 2024-01-15
---

<!-- Others don't -->
TASK-001: Implement login feature
Completed: Jan 15, 2024
```

**Why It's a Problem:**
- Parser fails on files without frontmatter
- Dates in different formats can't be parsed
- Missing fields cause errors

**Mitigation:**
```javascript
function parseTaskFile(content) {
  try {
    // Try YAML frontmatter first
    const yamlMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (yamlMatch) {
      return parseYAMLTask(yamlMatch[1]);
    }

    // Fallback: Try simple key-value format
    return parseSimpleTask(content);
  } catch (err) {
    console.warn('Failed to parse task file:', err);
    return null;  // Skip invalid files
  }
}

function parseSimpleTask(content) {
  const lines = content.split('\n');
  const task = {};

  for (const line of lines) {
    if (line.match(/^id:|^ID:/i)) {
      task.id = line.split(':')[1].trim();
    }
    if (line.match(/^completed:|^Completed:/i)) {
      task.completed_at = new Date(line.split(':')[1].trim());
    }
    // ... more field parsing
  }

  // Validate required fields
  if (!task.id || !task.completed_at) {
    throw new Error('Missing required fields: id, completed_at');
  }

  return task;
}
```

---

### Issue 3: Timezone Confusion

**Problem:** Tasks completed at different timezones cause date boundary issues

**Example:**
```javascript
// Task completed at 11:00 PM PST (Pacific)
completed_at: "2024-01-15T23:00:00-08:00"

// Converted to UTC: 7:00 AM next day
completed_at: "2024-01-16T07:00:00Z"

// If period is Jan 15 (UTC), this task is excluded
```

**Why It's a Problem:**
- Tasks "disappear" from expected period
- Counts don't match user expectations
- Inconsistent daily/weekly boundaries

**Mitigation:**
```javascript
function collectTasks(period, timezone = 'UTC') {
  const { zonedTimeToUtc, utcToZonedTime } = require('date-fns-tz');

  // Convert period boundaries to specified timezone
  const periodStart = zonedTimeToUtc(period.start, timezone);
  const periodEnd = zonedTimeToUtc(period.end, timezone);

  const tasks = await collectAllTasks();

  return tasks.filter(task => {
    const completedAt = new Date(task.completed_at);
    return completedAt >= periodStart && completedAt <= periodEnd;
  });
}

// Usage
const tasks = await collectTasks(period, 'America/Los_Angeles');
```

**Best Practice:**
- Store all timestamps in UTC
- Convert to user timezone only for display
- Document timezone in dashboard header

---

## Metric Calculation Gotchas

### Issue 4: Division by Zero

**Problem:** Calculating averages or rates with no data

**Example:**
```javascript
const avgResponseTime = sum(responseTimes) / responseTimes.length;
// NaN if responseTimes.length === 0

const bugRate = bugCount / featureCount;
// Infinity if featureCount === 0
```

**Why It's a Problem:**
- NaN or Infinity displayed in dashboard
- Breaks trend calculations
- Confusing to users

**Mitigation:**
```javascript
function safeAverage(values, defaultValue = 0) {
  if (!values || values.length === 0) return defaultValue;
  return sum(values) / values.length;
}

function safeRatio(numerator, denominator, defaultValue = 0) {
  if (denominator === 0) return defaultValue;
  return numerator / denominator;
}

// Or indicate no data:
function safeAverage(values) {
  if (!values || values.length === 0) return 'N/A';
  return (sum(values) / values.length).toFixed(2);
}
```

---

### Issue 5: Outliers Skewing Averages

**Problem:** Single extreme value distorts average

**Example:**
```javascript
const responseTimes = [2, 3, 2.5, 3, 120];  // One outlier
const avg = average(responseTimes);  // 26.1 hours (misleading)
```

**Why It's a Problem:**
- Average doesn't represent typical performance
- Hides actual performance trends
- One-time incident affects long-term metrics

**Mitigation:**
```javascript
function calculateRobustTimeMetrics(values) {
  if (values.length === 0) return { avg: 'N/A', median: 'N/A' };

  // Remove outliers (beyond 2 standard deviations)
  const mean = average(values);
  const stdDev = standardDeviation(values);
  const filtered = values.filter(v =>
    Math.abs(v - mean) <= 2 * stdDev
  );

  return {
    avg: average(filtered),
    median: median(values),  // Median is robust to outliers
    p95: percentile(values, 95),
    outliers: values.length - filtered.length
  };
}

function standardDeviation(values) {
  const avg = average(values);
  const squareDiffs = values.map(v => Math.pow(v - avg, 2));
  return Math.sqrt(average(squareDiffs));
}
```

**Display Strategy:**
```markdown
**Response Time:**
- Median: 2.8 hours (typical)
- Average: 26.1 hours (includes 1 outlier)
- 95th percentile: 3.5 hours
```

---

### Issue 6: Missing Previous Period Data

**Problem:** First-time dashboard has no comparison data

**Example:**
```javascript
const current = calculateMetrics(currentData);
const previous = calculateMetrics(previousData);  // Empty
const trends = calculateTrends(current, previous);
// All trends show "N/A" or misleading percentages
```

**Why It's a Problem:**
- Can't show trends on first run
- Percentage changes are meaningless (division by zero)
- Dashboard looks incomplete

**Mitigation:**
```javascript
function calculateTrends(current, previous) {
  if (!previous || Object.keys(previous).length === 0) {
    return {
      available: false,
      message: 'No previous period data available for comparison'
    };
  }

  // Normal trend calculation
  return {
    available: true,
    data: computeTrendData(current, previous)
  };
}

function renderMetric(metric, trend) {
  if (!trend.available) {
    return `**${metric.name}:** ${metric.value} (first period, no comparison)`;
  }

  return `**${metric.name}:** ${metric.value} (${trend.emoji} ${trend.change}% vs last period)`;
}
```

---

## Date and Time Gotchas

### Issue 7: Week Start Day Confusion

**Problem:** Different teams/regions start weeks on different days

**Example:**
```javascript
// US: Week starts Sunday
// ISO: Week starts Monday

const weekStart = startOfWeek(new Date());  // Which is it?
```

**Why It's a Problem:**
- Weekly metrics include wrong days
- Comparisons to "last week" are off
- Team expectations mismatch

**Mitigation:**
```javascript
// Always specify weekStartsOn option
const weekStart = startOfWeek(new Date(), { weekStartsOn: 1 }); // Monday

// Or make it configurable
const WEEK_STARTS_ON = parseInt(process.env.WEEK_STARTS_ON || '1');
// 0 = Sunday, 1 = Monday, etc.

function getPeriod(type) {
  if (type === 'weekly') {
    return {
      start: startOfWeek(new Date(), { weekStartsOn: WEEK_STARTS_ON }),
      end: new Date()
    };
  }
  // ...
}
```

---

### Issue 8: Leap Seconds and DST Transitions

**Problem:** Time calculations break during daylight saving time changes

**Example:**
```javascript
// March 10, 2024: DST starts (spring forward)
// 2:00 AM -> 3:00 AM (1 hour lost)

const start = new Date('2024-03-10T00:00:00');
const end = new Date('2024-03-10T23:59:59');
const hours = (end - start) / (1000 * 60 * 60);
// 23 hours, not 24!
```

**Why It's a Problem:**
- Daily metrics calculated incorrectly
- Hour-by-hour analysis shows gaps
- Comparisons between days are off

**Mitigation:**
```javascript
// Use date-fns or similar library that handles DST
const { differenceInHours, differenceInDays } = require('date-fns');

const hours = differenceInHours(end, start);
// Correctly accounts for DST

// Or work in calendar days, not 24-hour periods
const days = differenceInDays(end, start);
```

---

## Display and Formatting Gotchas

### Issue 9: Unicode Rendering Issues

**Problem:** Progress bars and emojis don't render in all terminals

**Example:**
```
Progress: █████░░░░░ 50%
// Terminal shows: Progress: ?????????? 50%
```

**Why It's a Problem:**
- Dashboard looks broken
- Progress bars unreadable
- Emojis show as boxes

**Mitigation:**
```javascript
function createProgressBar(value, total, useUnicode = true) {
  if (!useUnicode || !supportsUnicode()) {
    // ASCII fallback
    const filled = Math.round((value / total) * 20);
    const bar = '='.repeat(filled) + '-'.repeat(20 - filled);
    return `[${bar}] ${(value / total * 100).toFixed(0)}%`;
  }

  // Unicode version
  const filled = Math.round((value / total) * 20);
  const bar = '█'.repeat(filled) + '░'.repeat(20 - filled);
  return `${bar} ${(value / total * 100).toFixed(0)}%`;
}

function supportsUnicode() {
  // Check if terminal supports Unicode
  return process.env.LANG?.includes('UTF') ||
         process.env.LC_ALL?.includes('UTF') ||
         process.stdout.isTTY;
}
```

---

### Issue 10: Number Formatting Inconsistencies

**Problem:** Numbers displayed without thousand separators or currency symbols

**Example:**
```
Revenue: 1250000  // Hard to read
Response time: 4.2333333  // Too many decimals
```

**Why It's a Problem:**
- Hard to parse large numbers quickly
- Looks unprofessional
- Inconsistent precision

**Mitigation:**
```javascript
function formatNumber(value, type = 'number') {
  if (value === null || value === undefined) return 'N/A';

  switch (type) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
      // $1,250,000

    case 'percent':
      return `${value.toFixed(1)}%`;
      // 45.3%

    case 'decimal':
      return value.toFixed(2);
      // 4.23

    case 'number':
    default:
      return new Intl.NumberFormat('en-US').format(value);
      // 1,250,000
  }
}
```

---

## Performance Gotchas

### Issue 11: Slow File System Operations

**Problem:** Reading thousands of files from Done folder takes minutes

**Example:**
```javascript
const files = await fs.readdir(doneFolder);  // 5000 files

for (const file of files) {
  const content = await fs.readFile(path.join(doneFolder, file));
  // 5000 individual file reads = slow
}
```

**Why It's a Problem:**
- Dashboard generation times out
- Blocks other operations
- User frustration

**Mitigation:**
```javascript
// Parallel file reading
async function collectTasksParallel(doneFolder, period) {
  const files = await fs.readdir(doneFolder);

  // Filter by date in filename (if possible)
  const relevantFiles = files.filter(f =>
    f.includes(period.start.getFullYear())
  );

  // Read files in parallel (batches of 50)
  const batchSize = 50;
  const tasks = [];

  for (let i = 0; i < relevantFiles.length; i += batchSize) {
    const batch = relevantFiles.slice(i, i + batchSize);
    const batchTasks = await Promise.all(
      batch.map(f => readAndParseTask(path.join(doneFolder, f)))
    );
    tasks.push(...batchTasks.filter(Boolean));
  }

  // Filter by actual date
  return tasks.filter(t =>
    t.completed_at >= period.start && t.completed_at <= period.end
  );
}
```

**Better: Use index file**
```javascript
// Maintain an index of completed tasks
{
  "2024-01": ["TASK-001.md", "TASK-002.md"],
  "2024-02": ["TASK-015.md", "TASK-020.md"]
}

// Only read files from relevant months
const month = format(period.start, 'yyyy-MM');
const files = index[month] || [];
```

---

### Issue 12: Memory Leaks in Long-Running Processes

**Problem:** Scheduled dashboard updates cause memory to grow

**Example:**
```javascript
// Global cache that never clears
const cache = {};

cron.schedule('0 17 * * *', async () => {
  const data = await collectData('daily');
  cache[new Date().toISOString()] = data;  // Grows forever
  await generateDashboard(data);
});
```

**Why It's a Problem:**
- Memory usage increases over time
- Eventually crashes (OOM)
- Affects other processes

**Mitigation:**
```javascript
// Use LRU cache with size limit
const LRU = require('lru-cache');

const cache = new LRU({
  max: 30,  // Keep last 30 days
  maxAge: 1000 * 60 * 60 * 24 * 30  // 30 days
});

cron.schedule('0 17 * * *', async () => {
  const data = await collectData('daily');
  cache.set(new Date().toISOString(), data);
  await generateDashboard(data);

  // Explicit cleanup
  global.gc?.();  // If --expose-gc flag set
});
```

---

## Integration Gotchas

### Issue 13: Git Command Failures

**Problem:** Git commands fail in non-git directories or with errors

**Example:**
```javascript
const output = execSync('git log --since="1 week ago"');
// Error: fatal: not a git repository
```

**Why It's a Problem:**
- Dashboard generation fails completely
- No fallback behavior
- Error messages unclear

**Mitigation:**
```javascript
function collectGitHistory(period) {
  try {
    // Check if in git repo
    execSync('git rev-parse --git-dir', { stdio: 'ignore' });

    const since = period.start.toISOString();
    const command = `git log --since="${since}" --pretty=format:"%H|%an|%ad|%s"`;

    const output = execSync(command, { encoding: 'utf-8' });
    return parseGitLog(output);
  } catch (err) {
    console.warn('Git history unavailable:', err.message);
    return [];  // Graceful degradation
  }
}
```

---

### Issue 14: API Rate Limiting

**Problem:** GitHub/Jira API calls hit rate limits

**Example:**
```javascript
// 60 requests per hour for unauthenticated
// 5000 requests per hour for authenticated

for (let i = 0; i < 100; i++) {
  await fetch(`https://api.github.com/repos/...`);
  // Rate limit exceeded after 60
}
```

**Why It's a Problem:**
- Dashboard generation fails mid-way
- Data incomplete
- API access blocked temporarily

**Mitigation:**
```javascript
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);

      if (response.status === 429) {
        // Rate limited
        const retryAfter = response.headers.get('Retry-After') || 60;
        console.warn(`Rate limited, waiting ${retryAfter}s`);
        await sleep(retryAfter * 1000);
        continue;
      }

      return response;
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      await sleep(1000 * Math.pow(2, i));  // Exponential backoff
    }
  }
}

// Cache API responses
const cache = new Map();

async function fetchIssues(period) {
  const cacheKey = `issues-${period.start}-${period.end}`;

  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }

  const issues = await fetchFromAPI(period);
  cache.set(cacheKey, issues);

  return issues;
}
```

---

## Summary: Top 5 Critical Gotchas

1. **Empty Data (Issue 1)**: Always handle zero tasks gracefully
2. **Timezone Confusion (Issue 3)**: Store UTC, display in user timezone
3. **Division by Zero (Issue 4)**: Use safe math functions with defaults
4. **Outliers (Issue 5)**: Use median/percentiles, not just averages
5. **Performance (Issue 11)**: Batch file operations, use parallel processing

---
