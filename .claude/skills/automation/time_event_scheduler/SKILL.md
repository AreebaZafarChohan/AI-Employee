---
name: time_event_scheduler
description: Plan, schedule, format prompts for periodic events (cron, weekly audits).
---

# Time Event Scheduler

## Purpose

This skill generates and manages scheduled periodic events for AI agents, including cron expressions, calendar events, and formatted prompts for recurring tasks. It handles timing specifications, converts natural language schedules into machine-readable formats, and creates event definitions that integrate with task management systems.

The skill is designed for autonomous agents that need to execute recurring tasks like weekly audits, daily briefings, monthly reports, or custom periodic workflows.

## When to Use This Skill

Use `time_event_scheduler` when:

- **Weekly audits**: Schedule recurring audit tasks (e.g., Sunday compliance checks)
- **Daily briefings**: Generate morning/evening briefing schedules
- **Monthly reports**: Schedule end-of-month reporting tasks
- **Custom intervals**: Create schedules for any periodic event (hourly, daily, weekly, monthly)
- **Multi-timezone coordination**: Schedule events across different timezones
- **Event reminders**: Set up reminder prompts before scheduled events
- **Recurring workflows**: Automate repetitive task execution patterns
- **Calendar integration**: Generate calendar event formats (iCal, Google Calendar)

Do NOT use this skill when:

- **One-time events**: Use task management directly for non-recurring tasks
- **Real-time triggers**: Use event-driven systems for immediate responses
- **Human scheduling**: Personal calendar management (not agent workflows)
- **System cron jobs**: Use native cron for OS-level scheduled tasks
- **Database scheduling**: Use database-native job schedulers (e.g., pg_cron)

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"
SCHEDULE_PATH="$VAULT_PATH/Schedules"          # Auto-created if missing
TIMEZONE_DEFAULT="UTC"                          # Default timezone for schedules

# Optional: Schedule configuration
SCHEDULE_FORMAT="cron"                          # cron | natural | iso8601
SCHEDULE_REMINDER_ADVANCE_MINUTES="15"          # Minutes before event to remind
SCHEDULE_MAX_OCCURRENCES="1000"                 # Safety limit for recurring events
SCHEDULE_AUDIT_DAY="Sunday"                     # Default day for weekly audits
SCHEDULE_BRIEFING_TIME="09:00"                  # Default time for daily briefings

# Optional: Calendar integration
CALENDAR_EXPORT_FORMAT="ical"                   # ical | google | outlook
CALENDAR_AUTO_EXPORT="true"                     # Auto-generate calendar files
CALENDAR_EXPORT_PATH="$VAULT_PATH/Calendars"    # Calendar export location

# Optional: Event execution
EVENT_EXECUTOR_AGENT="lex"                      # Agent responsible for executing scheduled events
EVENT_PRE_EXECUTION_BUFFER_MINUTES="5"          # Minutes to start task before scheduled time
EVENT_PARALLEL_EXECUTION_LIMIT="3"              # Max concurrent scheduled tasks

# Optional: Audit trail
SCHEDULE_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs/Schedules"
SCHEDULE_HISTORY_RETENTION_DAYS="90"            # Keep schedule history for 90 days
```

**Secrets Management:**

- No secrets required for basic scheduling
- Calendar integrations may need API keys (stored in .env, not in schedule files)
- Never log sensitive event details

**Variable Discovery Process:**
```bash
# Check schedule configuration
cat .env | grep SCHEDULE_

# Verify Schedules folder exists
test -d "$VAULT_PATH/Schedules" && echo "OK" || mkdir -p "$VAULT_PATH/Schedules"

# Count active schedules
find "$VAULT_PATH/Schedules" -name '*.schedule.json' | wc -l

# Show upcoming events (next 7 days)
find "$VAULT_PATH/Schedules" -name '*.schedule.json' -exec jq -r '.next_occurrence' {} \; | sort
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required for basic operation. Optional calendar integrations may use HTTPS (443).

**Dependency Topology:**

```
Time Event Scheduler
  ├── Vault State Manager (file writes to Schedules/)
  │   └── Filesystem (Schedules/ folder)
  ├── Task Lifecycle Manager (creates tasks from schedules)
  │   └── Needs_Action/ folder
  └── Optional: Calendar APIs
      ├── Google Calendar API (port 443, OAuth)
      ├── Microsoft Outlook API (port 443, OAuth)
      └── CalDAV servers (configurable port)
```

**Topology Notes:**
- Primary operation: local file-based scheduling
- Optional external integrations via calendar APIs
- No database dependencies
- Stateless operation (schedules stored as JSON files)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as read-write volume: `-v /host/vault:/vault:rw`
- Ensure `Schedules/` folder is writable
- No network access required for basic operation
- Optional: expose calendar API endpoints if needed

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for filesystem access (local only)
- Agent authorization: all agents can read schedules, only lex/orch can create/modify
- Calendar APIs require OAuth 2.0 tokens (if enabled)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Schedule tampering** | Validate all cron expressions before saving |
| **Timezone attacks** | Validate timezone identifiers against IANA database |
| **Runaway schedules** | Enforce max occurrences limit |
| **Resource exhaustion** | Limit concurrent scheduled task execution |
| **Prompt injection** | Sanitize event descriptions and prompts |
| **Calendar API abuse** | Rate-limit API calls, use exponential backoff |

**Validation Rules:**

Before creating any schedule:
```javascript
function validateSchedule(schedule) {
  // Required fields check
  if (!schedule.name || !schedule.cron_expression) {
    throw new Error("Schedule name and cron expression are required");
  }

  // Validate cron expression (5-6 fields)
  const cronRegex = /^(\S+\s+){4,5}\S+$/;
  if (!cronRegex.test(schedule.cron_expression)) {
    throw new Error("Invalid cron expression format");
  }

  // Validate timezone
  const validTimezones = Intl.supportedValuesOf('timeZone');
  if (schedule.timezone && !validTimezones.includes(schedule.timezone)) {
    throw new Error(`Invalid timezone: ${schedule.timezone}`);
  }

  // Check max occurrences
  if (schedule.max_occurrences > 1000) {
    throw new Error("Max occurrences cannot exceed 1000");
  }

  return true;
}
```

---

## Usage Patterns

### Pattern 1: Weekly Sunday Audit

**Use Case:** Schedule a weekly compliance audit every Sunday at 9:00 AM UTC

**Input:**
```javascript
const { createSchedule } = require('./time_event_scheduler');

const auditSchedule = await createSchedule({
  name: "Weekly Compliance Audit",
  description: "Automated compliance check for all active workflows",
  schedule: {
    type: "cron",
    expression: "0 9 * * 0",  // Every Sunday at 9:00 AM
    timezone: "UTC"
  },
  event_type: "audit",
  prompt_template: {
    task_title: "Weekly Compliance Audit - {{date}}",
    task_description: `Execute comprehensive compliance audit:

    1. Review all active workflows in Needs_Action/
    2. Check for stale tasks (>7 days old)
    3. Validate all task metadata is complete
    4. Check for policy violations
    5. Generate audit report`,
    task_priority: "high",
    task_assignee: "lex",
    task_tags: ["audit", "compliance", "weekly"]
  },
  actions: [
    {
      type: "create_task",
      target: "Needs_Action/",
      agent: "lex"
    },
    {
      type: "notify",
      target: "dashboard",
      message: "Weekly audit task created"
    }
  ],
  metadata: {
    created_by: "admin",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true
  }
});

// Output: Schedule created at Schedules/weekly-compliance-audit.schedule.json
console.log(`Schedule ID: ${auditSchedule.id}`);
console.log(`Next occurrence: ${auditSchedule.next_occurrence}`);
```

**Output File** (`Schedules/weekly-compliance-audit.schedule.json`):
```json
{
  "id": "sched_001",
  "name": "Weekly Compliance Audit",
  "description": "Automated compliance check for all active workflows",
  "schedule": {
    "type": "cron",
    "expression": "0 9 * * 0",
    "timezone": "UTC",
    "human_readable": "Every Sunday at 9:00 AM UTC"
  },
  "event_type": "audit",
  "prompt_template": {
    "task_title": "Weekly Compliance Audit - {{date}}",
    "task_description": "Execute comprehensive compliance audit:\n\n1. Review all active workflows in Needs_Action/\n2. Check for stale tasks (>7 days old)\n3. Validate all task metadata is complete\n4. Check for policy violations\n5. Generate audit report",
    "task_priority": "high",
    "task_assignee": "lex",
    "task_tags": ["audit", "compliance", "weekly"]
  },
  "actions": [
    {
      "type": "create_task",
      "target": "Needs_Action/",
      "agent": "lex"
    },
    {
      "type": "notify",
      "target": "dashboard",
      "message": "Weekly audit task created"
    }
  ],
  "next_occurrence": "2025-02-09T09:00:00Z",
  "last_executed": null,
  "execution_count": 0,
  "max_occurrences": null,
  "enabled": true,
  "metadata": {
    "created_by": "admin",
    "created_at": "2025-02-04T10:00:00Z",
    "updated_at": "2025-02-04T10:00:00Z"
  }
}
```

### Pattern 2: Monday Morning Briefing

**Use Case:** Daily briefing every Monday at 8:00 AM in user's timezone

**Input:**
```javascript
const briefingSchedule = await createSchedule({
  name: "Monday Morning Briefing",
  description: "Weekly summary of tasks and priorities",
  schedule: {
    type: "cron",
    expression: "0 8 * * 1",  // Every Monday at 8:00 AM
    timezone: "America/New_York"
  },
  event_type: "briefing",
  prompt_template: {
    task_title: "Monday Briefing - Week of {{date}}",
    task_description: `Generate weekly briefing:

    1. Summarize last week's completed tasks
    2. List this week's priorities
    3. Identify blockers and risks
    4. Highlight pending approvals
    5. Send briefing email to stakeholders`,
    task_priority: "high",
    task_assignee: "lex",
    task_tags: ["briefing", "weekly", "communication"]
  },
  actions: [
    {
      type: "create_task",
      target: "Needs_Action/",
      agent: "lex"
    },
    {
      type: "trigger_skill",
      skill: "email_drafter",
      params: {
        recipient_type: "stakeholders",
        tone: "formal"
      }
    }
  ],
  reminder: {
    enabled: true,
    minutes_before: 15,
    message: "Monday briefing will be generated in 15 minutes"
  },
  metadata: {
    created_by: "admin",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true
  }
});
```

### Pattern 3: Custom Interval Schedule

**Use Case:** Run performance metrics collection every 4 hours

**Input:**
```javascript
const metricsSchedule = await createSchedule({
  name: "Performance Metrics Collection",
  description: "Collect and aggregate performance metrics",
  schedule: {
    type: "cron",
    expression: "0 */4 * * *",  // Every 4 hours
    timezone: "UTC"
  },
  event_type: "metrics",
  prompt_template: {
    task_title: "Collect Performance Metrics - {{timestamp}}",
    task_description: `Collect system performance metrics:

    1. Query task completion rates
    2. Measure average task duration
    3. Calculate agent utilization
    4. Detect performance anomalies
    5. Update dashboard`,
    task_priority: "medium",
    task_assignee: "orch",
    task_tags: ["metrics", "monitoring", "performance"]
  },
  actions: [
    {
      type: "execute_script",
      script: "scripts/collect_metrics.sh",
      timeout_seconds: 300
    }
  ],
  max_occurrences: 1000,
  metadata: {
    created_by: "system",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true
  }
});
```

### Pattern 4: Calendar Event Export

**Use Case:** Generate iCal file for all scheduled events

**Input:**
```javascript
const { exportToCalendar } = require('./time_event_scheduler');

const calendarExport = await exportToCalendar({
  schedules: [auditSchedule.id, briefingSchedule.id, metricsSchedule.id],
  format: "ical",
  output_path: "$VAULT_PATH/Calendars/ai-agent-schedules.ics",
  options: {
    include_past_events: false,
    days_ahead: 30,  // Next 30 days only
    include_reminders: true
  }
});

console.log(`Calendar exported: ${calendarExport.file_path}`);
console.log(`Events included: ${calendarExport.event_count}`);
```

**Output File** (`Calendars/ai-agent-schedules.ics`):
```ical
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Employee//Time Event Scheduler//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH

BEGIN:VEVENT
UID:sched_001@ai-employee.local
DTSTAMP:20250204T100000Z
DTSTART:20250209T090000Z
SUMMARY:Weekly Compliance Audit
DESCRIPTION:Automated compliance check for all active workflows
RRULE:FREQ=WEEKLY;BYDAY=SU
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Weekly audit task will be created in 15 minutes
END:VALARM
END:VEVENT

BEGIN:VEVENT
UID:sched_002@ai-employee.local
DTSTAMP:20250204T100000Z
DTSTART:20250210T130000Z
SUMMARY:Monday Morning Briefing
DESCRIPTION:Weekly summary of tasks and priorities
RRULE:FREQ=WEEKLY;BYDAY=MO
TZID:America/New_York
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Monday briefing will be generated in 15 minutes
END:VALARM
END:VEVENT

BEGIN:VEVENT
UID:sched_003@ai-employee.local
DTSTAMP:20250204T100000Z
DTSTART:20250204T100000Z
SUMMARY:Performance Metrics Collection
DESCRIPTION:Collect and aggregate performance metrics
RRULE:FREQ=HOURLY;INTERVAL=4;COUNT=1000
END:VEVENT

END:VCALENDAR
```

---

## Cron Expression Reference

### Standard Cron Format (5 fields)
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

### Common Examples

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Daily at 9:00 AM | `0 9 * * *` | Every day at 9:00 AM |
| Hourly | `0 * * * *` | Every hour on the hour |
| Every 15 minutes | `*/15 * * * *` | Every 15 minutes |
| Weekly on Sunday 9 AM | `0 9 * * 0` | Every Sunday at 9:00 AM |
| Monthly on 1st, 9 AM | `0 9 1 * *` | First day of every month at 9:00 AM |
| Weekdays at 8 AM | `0 8 * * 1-5` | Monday-Friday at 8:00 AM |
| Every 4 hours | `0 */4 * * *` | Every 4 hours starting at midnight |
| Twice daily | `0 9,17 * * *` | 9:00 AM and 5:00 PM every day |

---

## Natural Language Parsing

The skill supports natural language schedule descriptions:

| Natural Language | Converted to Cron |
|------------------|-------------------|
| "every sunday at 9am" | `0 9 * * 0` |
| "daily at noon" | `0 12 * * *` |
| "every weekday at 8:30am" | `30 8 * * 1-5` |
| "first monday of the month" | `0 9 1-7 * 1` |
| "every 4 hours" | `0 */4 * * *` |
| "twice a day" | `0 9,21 * * *` |

---

## API Reference

### createSchedule(config)

Creates a new scheduled event.

**Parameters:**
- `name` (string, required): Schedule name
- `description` (string, optional): Schedule description
- `schedule` (object, required):
  - `type` (string): "cron" | "natural" | "interval"
  - `expression` (string): Cron expression or natural language
  - `timezone` (string): IANA timezone identifier
- `event_type` (string): "audit" | "briefing" | "report" | "metrics" | "custom"
- `prompt_template` (object): Template for generated tasks
- `actions` (array): Actions to execute on schedule
- `reminder` (object, optional): Reminder configuration
- `max_occurrences` (number, optional): Limit number of executions

**Returns:** Schedule object with ID and next occurrence

### updateSchedule(scheduleId, updates)

Updates an existing schedule.

### deleteSchedule(scheduleId)

Deletes a schedule (soft delete, archives to history).

### listSchedules(filters)

Lists all schedules matching filters.

### getNextOccurrences(scheduleId, count)

Gets next N occurrences for a schedule.

### executeSchedule(scheduleId)

Manually triggers a scheduled event.

### exportToCalendar(options)

Exports schedules to calendar format (iCal, Google, Outlook).

---

## Integration with Task Lifecycle

When a scheduled event triggers:

1. **Prompt Template Rendering**: Replace template variables ({{date}}, {{timestamp}})
2. **Task Creation**: Generate task JSON from template
3. **File Write**: Write task to `Needs_Action/` folder
4. **Notification**: Trigger dashboard update or email notification
5. **Execution Tracking**: Update schedule's `last_executed` and `execution_count`
6. **History Logging**: Record event in audit trail

---

## Acceptance Criteria

- [ ] Schedules support standard cron expressions (5-6 fields)
- [ ] Natural language parsing converts to valid cron
- [ ] Timezone-aware scheduling works across all IANA timezones
- [ ] Schedule validation prevents invalid expressions
- [ ] Calendar export generates valid iCal format
- [ ] Reminders trigger N minutes before event
- [ ] Max occurrences limit enforced
- [ ] Audit trail logs all schedule executions
- [ ] Agent authorization enforced (only lex/orch can create)
- [ ] No hardcoded secrets in schedule files

---

## Follow-ups and Risks

**Follow-ups:**
1. Add support for recurring event exceptions (skip holidays)
2. Implement schedule conflict detection (overlapping tasks)
3. Add schedule analytics (execution success rate, average duration)

**Risks:**
1. **Clock drift**: System time inconsistencies may cause missed executions (mitigation: NTP sync)
2. **Timezone database updates**: New timezones or DST changes require updates (mitigation: regular IANA updates)
3. **Schedule explosion**: Too many schedules may overload system (mitigation: enforce limits)

---

## Code References

- Schedule parsing: `.claude/skills/automation/time_event_scheduler/assets/cron-parser.js`
- Calendar export: `.claude/skills/automation/time_event_scheduler/assets/calendar-exporter.js`
- Validation: `.claude/skills/automation/time_event_scheduler/references/validation-rules.md`
