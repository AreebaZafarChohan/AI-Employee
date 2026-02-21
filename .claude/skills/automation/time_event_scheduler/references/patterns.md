# Time Event Scheduler Patterns

This document describes design patterns, best practices, and architectural decisions for the Time Event Scheduler skill.

## Design Patterns

### 1. Cron-Based State Machine Pattern

**Problem:** Need deterministic, repeatable scheduling across system restarts.

**Solution:** Use cron expressions as declarative state definitions. System evaluates all active schedules on startup and at intervals.

**Implementation:**
```javascript
// Schedule file stores declarative state
{
  "id": "sched_001",
  "schedule": {
    "type": "cron",
    "expression": "0 9 * * 0"
  },
  "next_occurrence": "2025-02-09T09:00:00Z",
  "enabled": true
}

// Evaluator runs periodically (every minute)
function evaluateSchedules() {
  const now = Date.now();
  const activeSchedules = loadSchedules({ enabled: true });

  for (const schedule of activeSchedules) {
    if (schedule.next_occurrence <= now) {
      executeSchedule(schedule.id);
      schedule.next_occurrence = calculateNextOccurrence(schedule.cron_expression);
      saveSchedule(schedule);
    }
  }
}
```

**Benefits:**
- Survives system restarts
- No in-memory state required
- Easy to audit and debug

**Trade-offs:**
- 1-minute resolution (not millisecond-precise)
- Requires periodic evaluation loop

---

### 2. Template Substitution Pattern

**Problem:** Need dynamic content in scheduled tasks (dates, timestamps, variables).

**Solution:** Use template placeholders that are replaced at execution time.

**Implementation:**
```javascript
// Template definition
const template = {
  task_title: "Weekly Audit - {{date}}",
  task_description: "Audit for week ending {{date}}\nExecuted at {{timestamp}}"
};

// At execution time
function renderTemplate(template, context) {
  const rendered = {};
  for (const [key, value] of Object.entries(template)) {
    rendered[key] = value
      .replace(/{{date}}/g, context.date)
      .replace(/{{timestamp}}/g, context.timestamp)
      .replace(/{{month}}/g, context.month)
      .replace(/{{year}}/g, context.year)
      .replace(/{{quarter}}/g, context.quarter);
  }
  return rendered;
}

// Execution context
const context = {
  date: "2025-02-09",
  timestamp: "2025-02-09T09:00:00Z",
  month: "February",
  year: "2025",
  quarter: "Q1"
};

const rendered = renderTemplate(template, context);
// Output: { task_title: "Weekly Audit - 2025-02-09", ... }
```

**Supported Placeholders:**
- `{{date}}` - ISO date (YYYY-MM-DD)
- `{{timestamp}}` - ISO timestamp with timezone
- `{{month}}` - Full month name
- `{{year}}` - Four-digit year
- `{{quarter}}` - Quarter (Q1-Q4)
- `{{day_of_week}}` - Day name (Monday-Sunday)

**Benefits:**
- Flexible task content
- No code changes for new templates
- Easy to test

---

### 3. Action Chain Pattern

**Problem:** Scheduled events often require multiple actions (create task, send notification, update dashboard).

**Solution:** Define action chains that execute sequentially on schedule trigger.

**Implementation:**
```javascript
const schedule = {
  actions: [
    {
      type: "create_task",
      target: "Needs_Action/",
      agent: "lex"
    },
    {
      type: "trigger_skill",
      skill: "email_drafter",
      params: { recipient: "team@company.com" }
    },
    {
      type: "notify",
      target: "dashboard",
      message: "Weekly audit task created"
    }
  ]
};

// Executor runs actions in order
async function executeActions(schedule) {
  for (const action of schedule.actions) {
    try {
      switch (action.type) {
        case "create_task":
          await createTask(action);
          break;
        case "trigger_skill":
          await triggerSkill(action.skill, action.params);
          break;
        case "notify":
          await sendNotification(action.target, action.message);
          break;
        case "execute_script":
          await runScript(action.script, action.timeout_seconds);
          break;
        default:
          console.warn(`Unknown action type: ${action.type}`);
      }
    } catch (error) {
      console.error(`Action failed: ${action.type}`, error);
      // Continue with next action (fail-safe)
    }
  }
}
```

**Action Types:**
- `create_task` - Write task file to vault
- `trigger_skill` - Invoke another skill
- `notify` - Send notification (dashboard, email, Slack)
- `execute_script` - Run shell script
- `custom` - Custom action handler

**Benefits:**
- Composable workflows
- Easy to extend
- Fail-safe execution (one failure doesn't break chain)

---

### 4. Timezone Normalization Pattern

**Problem:** Different schedules use different timezones, but system needs consistent internal representation.

**Solution:** Store all timestamps in UTC, convert to local timezone only for display.

**Implementation:**
```javascript
// Schedule definition (user's timezone)
const schedule = {
  schedule: {
    expression: "0 9 * * 0",
    timezone: "America/New_York"  // User input
  }
};

// Internal storage (always UTC)
function saveSchedule(schedule) {
  const utcOccurrence = convertToUTC(
    schedule.next_occurrence,
    schedule.timezone
  );
  schedule.next_occurrence_utc = utcOccurrence;
  writeFile(schedule);
}

// Display (convert back to user's timezone)
function displaySchedule(schedule) {
  const localTime = convertFromUTC(
    schedule.next_occurrence_utc,
    schedule.timezone
  );
  return {
    ...schedule,
    next_occurrence_local: localTime
  };
}

// Helper functions
function convertToUTC(time, timezone) {
  return new Date(time).toISOString();
}

function convertFromUTC(utcTime, timezone) {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(new Date(utcTime));
}
```

**Benefits:**
- Consistent internal representation
- Avoids timezone confusion
- Handles DST transitions automatically

---

### 5. Reminder Offset Pattern

**Problem:** Users need warnings before scheduled events (e.g., 15 minutes before).

**Solution:** Create shadow schedules that trigger before main event.

**Implementation:**
```javascript
// Main schedule
const mainSchedule = {
  id: "sched_001",
  name: "Weekly Audit",
  schedule: {
    expression: "0 9 * * 0",
    timezone: "UTC"
  },
  reminder: {
    enabled: true,
    minutes_before: 15,
    message: "Weekly audit starts in 15 minutes"
  }
};

// System creates shadow reminder schedule
const reminderSchedule = {
  id: "sched_001_reminder",
  name: "Weekly Audit Reminder",
  schedule: {
    expression: "45 8 * * 0",  // 15 minutes before 9:00
    timezone: "UTC"
  },
  parent_schedule: "sched_001",
  action: "send_reminder"
};

// At reminder time
function handleReminder(reminderSchedule) {
  const parent = loadSchedule(reminderSchedule.parent_schedule);
  sendNotification({
    target: "dashboard",
    message: parent.reminder.message,
    type: "reminder",
    scheduled_for: parent.next_occurrence
  });
}
```

**Benefits:**
- Decoupled from main schedule
- Can have multiple reminders (1 week, 1 day, 1 hour)
- Easy to disable independently

---

### 6. Calendar Export Adapter Pattern

**Problem:** Different calendar systems use different formats (iCal, Google, Outlook).

**Solution:** Use adapter pattern to convert internal schedule format to various calendar formats.

**Implementation:**
```javascript
// Base calendar exporter
class CalendarExporter {
  constructor(schedules) {
    this.schedules = schedules;
  }

  export(format) {
    const adapter = this.getAdapter(format);
    return adapter.convert(this.schedules);
  }

  getAdapter(format) {
    switch (format) {
      case "ical":
        return new ICalAdapter();
      case "google":
        return new GoogleCalendarAdapter();
      case "outlook":
        return new OutlookAdapter();
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }
}

// iCal adapter
class ICalAdapter {
  convert(schedules) {
    let ical = "BEGIN:VCALENDAR\nVERSION:2.0\n";
    for (const schedule of schedules) {
      ical += this.convertEvent(schedule);
    }
    ical += "END:VCALENDAR";
    return ical;
  }

  convertEvent(schedule) {
    const rrule = this.cronToRRule(schedule.cron_expression);
    return `BEGIN:VEVENT
UID:${schedule.id}@ai-employee.local
DTSTART:${this.formatDate(schedule.next_occurrence)}
SUMMARY:${schedule.name}
RRULE:${rrule}
END:VEVENT\n`;
  }

  cronToRRule(cron) {
    // Convert cron to RRULE format
    // Example: "0 9 * * 0" -> "FREQ=WEEKLY;BYDAY=SU"
  }

  formatDate(date) {
    return date.replace(/[-:]/g, '').split('.')[0] + 'Z';
  }
}

// Usage
const exporter = new CalendarExporter(schedules);
const icalFile = exporter.export("ical");
const googleFile = exporter.export("google");
```

**Benefits:**
- Easy to add new formats
- Keeps conversion logic separate
- Testable adapters

---

### 7. Safe Execution Wrapper Pattern

**Problem:** Scheduled tasks may fail, hang, or cause errors.

**Solution:** Wrap execution in safety mechanisms (timeout, retry, error handling).

**Implementation:**
```javascript
async function safeExecute(schedule) {
  const startTime = Date.now();
  const timeout = schedule.timeout_seconds * 1000 || 300000; // Default 5 minutes

  try {
    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error("Execution timeout")), timeout);
    });

    // Create execution promise
    const executionPromise = executeSchedule(schedule);

    // Race promises
    const result = await Promise.race([executionPromise, timeoutPromise]);

    // Log success
    logExecution({
      schedule_id: schedule.id,
      status: "success",
      duration_ms: Date.now() - startTime,
      result
    });

    return result;
  } catch (error) {
    // Log failure
    logExecution({
      schedule_id: schedule.id,
      status: "failed",
      duration_ms: Date.now() - startTime,
      error: error.message
    });

    // Retry logic
    if (schedule.retry_on_failure && schedule.retry_count < 3) {
      schedule.retry_count++;
      await sleep(1000 * Math.pow(2, schedule.retry_count)); // Exponential backoff
      return safeExecute(schedule);
    }

    throw error;
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

**Safety Features:**
- Timeout protection
- Exponential backoff retry
- Error logging
- Duration tracking

---

### 8. Natural Language Parser Pattern

**Problem:** Cron syntax is difficult for humans.

**Solution:** Parse natural language into cron expressions.

**Implementation:**
```javascript
function parseNaturalLanguage(text) {
  text = text.toLowerCase().trim();

  // Daily patterns
  if (text.match(/every day at (\d+)(am|pm)/)) {
    const [_, hour, period] = text.match(/every day at (\d+)(am|pm)/);
    const cronHour = period === "pm" ? parseInt(hour) + 12 : hour;
    return `0 ${cronHour} * * *`;
  }

  // Weekly patterns
  if (text.match(/every (monday|tuesday|wednesday|thursday|friday|saturday|sunday) at (\d+)(am|pm)/)) {
    const days = { sunday: 0, monday: 1, tuesday: 2, wednesday: 3, thursday: 4, friday: 5, saturday: 6 };
    const [_, day, hour, period] = text.match(/every (\w+) at (\d+)(am|pm)/);
    const cronHour = period === "pm" ? parseInt(hour) + 12 : hour;
    return `0 ${cronHour} * * ${days[day]}`;
  }

  // Interval patterns
  if (text.match(/every (\d+) hours/)) {
    const [_, hours] = text.match(/every (\d+) hours/);
    return `0 */${hours} * * *`;
  }

  // Weekday pattern
  if (text.match(/every weekday at (\d+)(am|pm)/)) {
    const [_, hour, period] = text.match(/every weekday at (\d+)(am|pm)/);
    const cronHour = period === "pm" ? parseInt(hour) + 12 : hour;
    return `0 ${cronHour} * * 1-5`;
  }

  throw new Error(`Cannot parse: ${text}`);
}

// Tests
console.assert(parseNaturalLanguage("every day at 9am") === "0 9 * * *");
console.assert(parseNaturalLanguage("every sunday at 5pm") === "0 17 * * 0");
console.assert(parseNaturalLanguage("every 4 hours") === "0 */4 * * *");
console.assert(parseNaturalLanguage("every weekday at 8am") === "0 8 * * 1-5");
```

**Supported Patterns:**
- "every day at [time]"
- "every [day] at [time]"
- "every [N] hours"
- "every weekday at [time]"

---

## Best Practices

### 1. Always Validate Cron Expressions

```javascript
function validateCron(expression) {
  const parts = expression.split(/\s+/);
  if (parts.length < 5 || parts.length > 6) {
    throw new Error("Cron must have 5 or 6 fields");
  }

  // Validate each field
  const ranges = [
    { min: 0, max: 59, name: "minute" },
    { min: 0, max: 23, name: "hour" },
    { min: 1, max: 31, name: "day" },
    { min: 1, max: 12, name: "month" },
    { min: 0, max: 6, name: "weekday" }
  ];

  for (let i = 0; i < 5; i++) {
    if (!isValidCronField(parts[i], ranges[i])) {
      throw new Error(`Invalid ${ranges[i].name}: ${parts[i]}`);
    }
  }
}
```

### 2. Use UTC for Storage, Local for Display

```javascript
// Store in UTC
schedule.next_occurrence_utc = "2025-02-09T09:00:00Z";

// Display in user's timezone
schedule.next_occurrence_local = "2025-02-09 04:00:00 EST";
```

### 3. Limit Max Occurrences

```javascript
if (schedule.execution_count >= schedule.max_occurrences) {
  schedule.enabled = false;
  logEvent("Schedule reached max occurrences, disabled");
}
```

### 4. Log All Executions

```javascript
logExecution({
  schedule_id: schedule.id,
  timestamp: new Date().toISOString(),
  status: "success",
  duration_ms: 1234,
  agent: "lex"
});
```

### 5. Handle DST Transitions

```javascript
function calculateNextOccurrence(cron, timezone) {
  const next = cronParser.next(cron);
  // Check if DST transition occurred
  if (isDSTTransition(next, timezone)) {
    adjustForDST(next, timezone);
  }
  return next;
}
```

---

## Anti-Patterns (Avoid These)

### ❌ Hardcoding Timezones
```javascript
// BAD
const schedule = { cron: "0 9 * * *", timezone: "America/New_York" };

// GOOD
const schedule = {
  cron: "0 9 * * *",
  timezone: process.env.TIMEZONE_DEFAULT || "UTC"
};
```

### ❌ Missing Error Handling
```javascript
// BAD
function executeSchedule(id) {
  const schedule = loadSchedule(id);
  createTask(schedule.prompt_template);
}

// GOOD
async function executeSchedule(id) {
  try {
    const schedule = loadSchedule(id);
    await createTask(schedule.prompt_template);
    logSuccess(id);
  } catch (error) {
    logError(id, error);
    notifyAdmin(error);
  }
}
```

### ❌ Blocking Execution
```javascript
// BAD (blocks other schedules)
function evaluateSchedules() {
  schedules.forEach(s => executeSchedule(s));
}

// GOOD (parallel execution)
async function evaluateSchedules() {
  const promises = schedules.map(s => executeSchedule(s));
  await Promise.all(promises);
}
```

### ❌ No Timeout Protection
```javascript
// BAD (can hang forever)
await runTask();

// GOOD (timeout after 5 minutes)
await Promise.race([
  runTask(),
  sleep(300000).then(() => { throw new Error("Timeout"); })
]);
```

---

## Performance Considerations

### Schedule Evaluation Frequency

- Evaluate every 1 minute (good balance)
- Avoid evaluating every second (too frequent)
- Avoid evaluating every 5+ minutes (too coarse)

### File System Optimization

```javascript
// Use file caching to avoid repeated reads
const scheduleCache = new Map();

function loadSchedule(id, useCache = true) {
  if (useCache && scheduleCache.has(id)) {
    return scheduleCache.get(id);
  }
  const schedule = JSON.parse(readFile(`Schedules/${id}.json`));
  scheduleCache.set(id, schedule);
  return schedule;
}

// Invalidate cache on write
function saveSchedule(schedule) {
  writeFile(`Schedules/${schedule.id}.json`, JSON.stringify(schedule));
  scheduleCache.delete(schedule.id);
}
```

### Parallel Execution

```javascript
// Execute schedules in parallel (with limit)
const PARALLEL_LIMIT = 3;

async function executeSchedulesParallel(schedules) {
  const chunks = chunkArray(schedules, PARALLEL_LIMIT);
  for (const chunk of chunks) {
    await Promise.all(chunk.map(s => executeSchedule(s)));
  }
}
```

---

## Summary

Key patterns for time event scheduling:

1. **Cron-Based State Machine** - Declarative, persistent scheduling
2. **Template Substitution** - Dynamic content generation
3. **Action Chains** - Composable workflows
4. **Timezone Normalization** - Consistent UTC storage
5. **Reminder Offset** - Pre-event notifications
6. **Calendar Export Adapter** - Multi-format support
7. **Safe Execution Wrapper** - Error handling and timeouts
8. **Natural Language Parser** - User-friendly input

Always validate inputs, log executions, handle errors, and test timezone edge cases.
