# Dashboard Writer - Patterns

## Data Collection Patterns

### Pattern 1: File-Based Task Collection

**Use Case:** Read completed tasks from Done folder

**Implementation:**
```javascript
async function collectTasksFromDoneFolder(period) {
  const doneFolder = process.env.DASHBOARD_DONE_FOLDER || './done/';
  const files = await fs.readdir(doneFolder);

  const tasks = [];

  for (const file of files) {
    if (!file.endsWith('.task.md') && !file.endsWith('.prompt.md')) {
      continue;
    }

    const filePath = path.join(doneFolder, file);
    const content = await fs.readFile(filePath, 'utf-8');
    const task = parseTaskFile(content);

    // Filter by period
    if (task.completed_at >= period.start && task.completed_at <= period.end) {
      tasks.push(task);
    }
  }

  return tasks;
}

function parseTaskFile(content) {
  // Parse YAML frontmatter
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const yaml = require('js-yaml');
  const frontmatter = yaml.load(match[1]);

  return {
    id: frontmatter.id,
    title: frontmatter.title,
    completed_at: new Date(frontmatter.completed_at),
    started_at: new Date(frontmatter.started_at),
    duration: frontmatter.duration_hours || calculateDuration(
      frontmatter.started_at,
      frontmatter.completed_at
    ),
    type: frontmatter.type || 'task',
    outcome: frontmatter.outcome,
    revenue: frontmatter.revenue || 0,
    cost: frontmatter.cost || 0
  };
}
```

**When to Use:**
- Local file-based task management
- Markdown-based task tracking
- Simple project structures

**When NOT to Use:**
- External issue trackers (use API pattern instead)
- Real-time data needs (file scanning is slow)

---

### Pattern 2: Git History Collection

**Use Case:** Extract activity metrics from git commits

**Implementation:**
```javascript
async function collectGitHistory(period) {
  const { execSync } = require('child_process');

  const since = period.start.toISOString();
  const until = period.end.toISOString();

  const command = `git log --since="${since}" --until="${until}" ` +
                  `--pretty=format:"%H|%an|%ad|%s" --date=iso`;

  const output = execSync(command, { encoding: 'utf-8' });

  const commits = output.split('\n')
    .filter(line => line.trim())
    .map(line => {
      const [hash, author, date, message] = line.split('|');
      return {
        hash,
        author,
        date: new Date(date),
        message,
        type: classifyCommit(message)
      };
    });

  return commits;
}

function classifyCommit(message) {
  const msg = message.toLowerCase();

  if (msg.match(/^feat|^feature/)) return 'feature';
  if (msg.match(/^fix|^bug/)) return 'bugfix';
  if (msg.match(/^docs/)) return 'documentation';
  if (msg.match(/^test/)) return 'test';
  if (msg.match(/^refactor/)) return 'refactor';
  if (msg.match(/^chore/)) return 'chore';

  return 'other';
}
```

**When to Use:**
- Development activity tracking
- Commit frequency analysis
- Contributor statistics

**When NOT to Use:**
- Non-git projects
- When commit messages are inconsistent

---

### Pattern 3: API-Based Data Collection

**Use Case:** Fetch data from external issue trackers (GitHub, Jira)

**Implementation:**
```javascript
async function collectIssuesFromGitHub(period) {
  const { Octokit } = require('@octokit/rest');

  const octokit = new Octokit({
    auth: process.env.GITHUB_TOKEN
  });

  const since = period.start.toISOString();

  const { data: issues } = await octokit.issues.listForRepo({
    owner: 'your-org',
    repo: 'your-repo',
    state: 'closed',
    since,
    per_page: 100
  });

  return issues
    .filter(issue => {
      const closedAt = new Date(issue.closed_at);
      return closedAt >= period.start && closedAt <= period.end;
    })
    .map(issue => ({
      id: issue.number,
      title: issue.title,
      type: issue.labels.some(l => l.name === 'bug') ? 'bug' : 'feature',
      completed_at: new Date(issue.closed_at),
      assignee: issue.assignee?.login,
      labels: issue.labels.map(l => l.name)
    }));
}
```

**When to Use:**
- Team uses external issue tracker
- Need real-time data
- Multi-repository projects

**When NOT to Use:**
- No API access or token
- Rate limits too restrictive
- Local-only development

---

## Metric Calculation Patterns

### Pattern 4: Time-Based Aggregation

**Use Case:** Calculate averages, medians, percentiles for time metrics

**Implementation:**
```javascript
function calculateTimeMetrics(tasks) {
  const responseTimes = tasks
    .filter(t => t.response_time)
    .map(t => t.response_time);

  const durations = tasks
    .filter(t => t.duration)
    .map(t => t.duration);

  return {
    response_time: {
      avg: average(responseTimes),
      median: median(responseTimes),
      p50: percentile(responseTimes, 50),
      p95: percentile(responseTimes, 95),
      p99: percentile(responseTimes, 99),
      min: Math.min(...responseTimes),
      max: Math.max(...responseTimes)
    },
    task_duration: {
      avg: average(durations),
      median: median(durations),
      total: sum(durations)
    }
  };
}

function average(values) {
  if (values.length === 0) return 0;
  return sum(values) / values.length;
}

function median(values) {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

function percentile(values, p) {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index % 1;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

function sum(values) {
  return values.reduce((acc, val) => acc + val, 0);
}
```

**When to Use:**
- Response time tracking
- Task duration analysis
- SLA compliance monitoring

**When NOT to Use:**
- Simple count metrics (use Pattern 5)
- Non-numeric data

---

### Pattern 5: Count-Based Aggregation

**Use Case:** Count items by category, type, status

**Implementation:**
```javascript
function calculateCountMetrics(tasks) {
  const metrics = {
    total: tasks.length,
    by_type: {},
    by_status: {},
    by_priority: {}
  };

  // Group by type
  tasks.forEach(task => {
    metrics.by_type[task.type] = (metrics.by_type[task.type] || 0) + 1;
    metrics.by_status[task.status] = (metrics.by_status[task.status] || 0) + 1;
    metrics.by_priority[task.priority] = (metrics.by_priority[task.priority] || 0) + 1;
  });

  return metrics;
}

// More advanced: Group by multiple dimensions
function groupBy(items, key) {
  return items.reduce((acc, item) => {
    const group = item[key];
    acc[group] = acc[group] || [];
    acc[group].push(item);
    return acc;
  }, {});
}

// Example: Count bugs vs features
const byType = groupBy(tasks, 'type');
const bugCount = byType.bug?.length || 0;
const featureCount = byType.feature?.length || 0;
const bugRate = bugCount / (featureCount || 1);
```

**When to Use:**
- Task completion counts
- Category distributions
- Simple frequency analysis

**When NOT to Use:**
- Time-based calculations (use Pattern 4)
- Financial metrics (use Pattern 6)

---

### Pattern 6: Financial Aggregation

**Use Case:** Calculate revenue, expenses, profit, budgets

**Implementation:**
```javascript
function calculateFinancialMetrics(tasks, period) {
  const revenue = tasks
    .filter(t => t.revenue)
    .reduce((sum, t) => sum + t.revenue, 0);

  const expenses = tasks
    .filter(t => t.cost)
    .reduce((sum, t) => sum + t.cost, 0);

  const profit = revenue - expenses;
  const margin = revenue > 0 ? (profit / revenue) * 100 : 0;

  // Annualized metrics
  const daysInPeriod = (period.end - period.start) / (1000 * 60 * 60 * 24);
  const annualizedRevenue = (revenue / daysInPeriod) * 365;
  const annualizedExpenses = (expenses / daysInPeriod) * 365;

  // Budget tracking
  const budget = getBudget(period);
  const budgetUsed = (expenses / budget.total) * 100;
  const budgetRemaining = budget.total - expenses;
  const burnRate = expenses / (daysInPeriod / 30); // monthly

  return {
    revenue,
    expenses,
    profit,
    margin,
    annualized: {
      revenue: annualizedRevenue,
      expenses: annualizedExpenses
    },
    budget: {
      total: budget.total,
      used: expenses,
      remaining: budgetRemaining,
      percentUsed: budgetUsed
    },
    burnRate
  };
}
```

**When to Use:**
- Financial dashboard sections
- Budget tracking
- ROI calculations

**When NOT to Use:**
- Non-financial metrics
- When currency conversion needed (add conversion layer first)

---

## Trend Analysis Patterns

### Pattern 7: Period-over-Period Comparison

**Use Case:** Compare current period to previous period

**Implementation:**
```javascript
function calculateTrends(current, previous) {
  const trends = {};

  for (const [key, value] of Object.entries(current)) {
    if (typeof value === 'number') {
      const prevValue = previous[key] || 0;
      const change = value - prevValue;
      const percentChange = prevValue > 0 ? (change / prevValue) * 100 : 0;

      trends[key] = {
        current: value,
        previous: prevValue,
        change,
        percentChange,
        direction: change > 0 ? 'up' : change < 0 ? 'down' : 'same',
        emoji: getTrendEmoji(change, key),
        formatted: formatTrend(change, percentChange, key)
      };
    } else if (typeof value === 'object') {
      // Recursive for nested metrics
      trends[key] = calculateTrends(value, previous[key] || {});
    }
  }

  return trends;
}

function getTrendEmoji(change, metricKey) {
  // Some metrics: higher is better (revenue, tasks completed)
  // Some metrics: lower is better (response time, bug rate)

  const lowerIsBetter = ['response_time', 'bug_rate', 'expenses', 'burnRate'];
  const isLowerBetter = lowerIsBetter.some(m => metricKey.includes(m));

  if (change === 0) return '➡️';

  if (isLowerBetter) {
    return change < 0 ? '📈' : '📉';  // Down is good, up is bad
  } else {
    return change > 0 ? '📈' : '📉';  // Up is good, down is bad
  }
}

function formatTrend(change, percentChange, key) {
  const sign = change > 0 ? '+' : '';
  const emoji = getTrendEmoji(change, key);

  return `${emoji} ${sign}${percentChange.toFixed(1)}%`;
}
```

**When to Use:**
- All time-series metrics
- Progress tracking
- Performance comparison

**When NOT to Use:**
- First-time dashboard (no previous period)
- Metrics that shouldn't be compared (e.g., unique counts)

---

### Pattern 8: Moving Average Smoothing

**Use Case:** Smooth noisy metrics over time

**Implementation:**
```javascript
function calculateMovingAverage(dataPoints, windowSize = 7) {
  const smoothed = [];

  for (let i = 0; i < dataPoints.length; i++) {
    const start = Math.max(0, i - windowSize + 1);
    const window = dataPoints.slice(start, i + 1);
    const avg = window.reduce((sum, val) => sum + val, 0) / window.length;
    smoothed.push(avg);
  }

  return smoothed;
}

// Example: Smooth daily task completion
const dailyCompletions = [5, 3, 8, 2, 6, 4, 7, 10, 3, 5];
const smoothed = calculateMovingAverage(dailyCompletions, 3); // 3-day MA

// Trend detection
function detectTrend(values) {
  const first = values.slice(0, Math.floor(values.length / 2));
  const second = values.slice(Math.floor(values.length / 2));

  const firstAvg = first.reduce((sum, val) => sum + val, 0) / first.length;
  const secondAvg = second.reduce((sum, val) => sum + val, 0) / second.length;

  if (secondAvg > firstAvg * 1.1) return 'increasing';
  if (secondAvg < firstAvg * 0.9) return 'decreasing';
  return 'stable';
}
```

**When to Use:**
- Noisy daily metrics
- Long-term trend analysis
- Reducing volatility in charts

**When NOT to Use:**
- Small datasets (< 7 data points)
- When precision is critical

---

## Dashboard Formatting Patterns

### Pattern 9: Progress Bar Visualization

**Use Case:** Visual representation of progress

**Implementation:**
```javascript
function createProgressBar(current, total, width = 20) {
  const percent = (current / total) * 100;
  const filled = Math.round((current / total) * width);
  const empty = width - filled;

  const bar = '█'.repeat(filled) + '░'.repeat(empty);

  return `${bar} ${percent.toFixed(0)}%`;
}

// Examples:
createProgressBar(7, 10);   // ██████████████░░░░░░ 70%
createProgressBar(3, 10);   // ██████░░░░░░░░░░░░░░ 30%
createProgressBar(10, 10);  // ████████████████████ 100%

// With color indicators
function createColoredProgressBar(current, total, thresholds = {}) {
  const percent = (current / total) * 100;
  const bar = createProgressBar(current, total);

  let emoji = '';
  if (percent >= (thresholds.excellent || 90)) emoji = '🟢';
  else if (percent >= (thresholds.good || 70)) emoji = '🟡';
  else emoji = '🔴';

  return `${emoji} ${bar}`;
}
```

**When to Use:**
- Milestone progress
- Budget usage
- Goal tracking

**When NOT to Use:**
- Terminal doesn't support Unicode
- Percentage is sufficient

---

### Pattern 10: Table Formatting

**Use Case:** Structured data display in Markdown

**Implementation:**
```javascript
function createMarkdownTable(data, columns) {
  // Header
  const headers = columns.map(col => col.label).join(' | ');
  const separator = columns.map(col => '-'.repeat(col.width || 10)).join(' | ');

  // Rows
  const rows = data.map(row => {
    return columns.map(col => {
      const value = row[col.key];
      const formatted = col.format ? col.format(value) : value;
      return formatted;
    }).join(' | ');
  });

  return `| ${headers} |\n|${separator}|\n` + rows.map(r => `| ${r} |`).join('\n');
}

// Example:
const tasks = [
  { name: 'Login', status: 'done', progress: 100 },
  { name: 'Checkout', status: 'in_progress', progress: 60 },
  { name: 'Analytics', status: 'todo', progress: 0 }
];

const columns = [
  { key: 'name', label: 'Task', width: 15 },
  { key: 'status', label: 'Status', width: 12, format: formatStatus },
  { key: 'progress', label: 'Progress', width: 20, format: v => createProgressBar(v, 100) }
];

function formatStatus(status) {
  const emojis = {
    done: '✅',
    in_progress: '🔄',
    todo: '⏳'
  };
  return `${emojis[status] || ''} ${status}`;
}

console.log(createMarkdownTable(tasks, columns));
```

**Output:**
```markdown
| Task | Status | Progress |
|---------------|------------|------------------|
| Login | ✅ done | ████████████████████ 100% |
| Checkout | 🔄 in_progress | ████████████░░░░░░░░ 60% |
| Analytics | ⏳ todo | ░░░░░░░░░░░░░░░░░░░░ 0% |
```

**When to Use:**
- Structured data with multiple dimensions
- Comparisons across items
- Status reports

**When NOT to Use:**
- Single metric (use inline formatting)
- Very wide tables (hard to read in Markdown)

---

## Automation Patterns

### Pattern 11: Scheduled Dashboard Updates

**Use Case:** Automatically update dashboard at intervals

**Implementation:**
```javascript
const cron = require('node-cron');

// Daily at 5 PM
cron.schedule('0 17 * * *', async () => {
  console.log('Running daily dashboard update...');
  await updateDashboard('daily');
});

// Weekly on Monday at 9 AM
cron.schedule('0 9 * * 1', async () => {
  console.log('Running weekly dashboard update...');
  await updateDashboard('weekly');
});

// Monthly on 1st at 9 AM
cron.schedule('0 9 1 * *', async () => {
  console.log('Running monthly dashboard update...');
  await updateDashboard('monthly');
});

async function updateDashboard(period) {
  try {
    const data = await collectData(period);
    const metrics = calculateMetrics(data);
    const dashboard = generateDashboard(metrics, period);

    // Archive previous
    await archiveDashboard();

    // Write new
    await fs.writeFile('Dashboard.md', dashboard);

    console.log(`✅ Dashboard updated: ${period}`);

    // Optional: Send notification
    await notifyDashboardUpdate(period);
  } catch (err) {
    console.error('❌ Dashboard update failed:', err);
  }
}
```

**When to Use:**
- Regular status reporting
- Team needs consistent updates
- Automated workflows

**When NOT to Use:**
- Ad-hoc updates only
- Manual review required before publishing

---

### Pattern 12: Webhook Notification

**Use Case:** Notify team when dashboard updates

**Implementation:**
```javascript
async function notifyDashboardUpdate(period, metrics) {
  const webhook = process.env.SLACK_WEBHOOK_URL;

  const message = {
    text: `Dashboard updated: ${period}`,
    blocks: [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: `📊 Dashboard Update: ${period}`
        }
      },
      {
        type: 'section',
        fields: [
          {
            type: 'mrkdwn',
            text: `*Tasks Completed:*\n${metrics.counts.tasks_completed} ${metrics.trends.tasks_completed.emoji}`
          },
          {
            type: 'mrkdwn',
            text: `*Revenue:*\n$${metrics.financial.revenue.toLocaleString()} ${metrics.trends.revenue.emoji}`
          },
          {
            type: 'mrkdwn',
            text: `*Response Time:*\n${metrics.time.avg_response_time.toFixed(1)}h ${metrics.trends.response_time.emoji}`
          },
          {
            type: 'mrkdwn',
            text: `*Deployment Success:*\n${metrics.quality.deployment_success.toFixed(0)}%`
          }
        ]
      },
      {
        type: 'actions',
        elements: [
          {
            type: 'button',
            text: {
              type: 'plain_text',
              text: 'View Dashboard'
            },
            url: 'https://github.com/your-org/your-repo/blob/main/Dashboard.md'
          }
        ]
      }
    ]
  };

  await fetch(webhook, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(message)
  });
}
```

**When to Use:**
- Team collaboration tool integration
- Real-time status updates
- Alert on significant changes

**When NOT to Use:**
- No webhook available
- Dashboard contains sensitive info not for general audience

---
