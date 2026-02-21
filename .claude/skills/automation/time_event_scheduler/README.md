# Time Event Scheduler

## Overview

The **Time Event Scheduler** skill enables AI agents to create, manage, and execute periodic scheduled tasks. It converts natural language schedules into cron expressions, generates calendar events, and integrates with the task lifecycle system to automate recurring workflows.

## Quick Start

### 1. Installation

Ensure your environment has the required vault structure:

```bash
# Set up vault path
export VAULT_PATH="/absolute/path/to/vault"

# Create schedules folder
mkdir -p "$VAULT_PATH/Schedules"
mkdir -p "$VAULT_PATH/Calendars"
```

### 2. Basic Usage

Create a weekly Sunday audit schedule:

```javascript
const { createSchedule } = require('./time_event_scheduler');

const schedule = await createSchedule({
  name: "Weekly Compliance Audit",
  schedule: {
    type: "cron",
    expression: "0 9 * * 0",  // Every Sunday at 9:00 AM
    timezone: "UTC"
  },
  event_type: "audit",
  prompt_template: {
    task_title: "Weekly Audit - {{date}}",
    task_description: "Execute compliance audit for all workflows",
    task_assignee: "lex"
  }
});

console.log(`Next audit: ${schedule.next_occurrence}`);
```

### 3. Natural Language Scheduling

Use natural language instead of cron:

```javascript
const schedule = await createSchedule({
  name: "Daily Briefing",
  schedule: {
    type: "natural",
    expression: "every weekday at 9am",
    timezone: "America/New_York"
  },
  event_type: "briefing"
});

// Automatically converted to: 0 9 * * 1-5
```

## Features

### Cron Expression Support
- Standard 5-field cron syntax
- Extended 6-field syntax (with seconds)
- Special characters: `*`, `/`, `,`, `-`
- Natural language parsing

### Timezone Handling
- Full IANA timezone database support
- Automatic DST adjustments
- Multi-timezone event coordination

### Calendar Export
- iCal format (.ics files)
- Google Calendar compatible
- Microsoft Outlook compatible
- Configurable date ranges

### Task Integration
- Automatic task creation from templates
- Variable substitution ({{date}}, {{timestamp}})
- Integration with Needs_Action/ folder
- Agent assignment and prioritization

### Event Types
- **audit**: Compliance checks and system audits
- **briefing**: Status reports and summaries
- **report**: Scheduled reporting tasks
- **metrics**: Performance monitoring
- **custom**: User-defined event types

## Common Schedules

### Weekly Sunday Audit (9:00 AM UTC)
```javascript
{
  schedule: {
    type: "cron",
    expression: "0 9 * * 0",
    timezone: "UTC"
  }
}
```

### Monday Morning Briefing (8:00 AM Local)
```javascript
{
  schedule: {
    type: "natural",
    expression: "every monday at 8am",
    timezone: "America/New_York"
  }
}
```

### Every 4 Hours
```javascript
{
  schedule: {
    type: "cron",
    expression: "0 */4 * * *",
    timezone: "UTC"
  }
}
```

### First Day of Month (9:00 AM)
```javascript
{
  schedule: {
    type: "cron",
    expression: "0 9 1 * *",
    timezone: "UTC"
  }
}
```

### Weekdays Only (8:30 AM)
```javascript
{
  schedule: {
    type: "cron",
    expression: "30 8 * * 1-5",
    timezone: "UTC"
  }
}
```

## Environment Variables

```bash
# Required
VAULT_PATH="/path/to/vault"
SCHEDULE_PATH="$VAULT_PATH/Schedules"
TIMEZONE_DEFAULT="UTC"

# Optional
SCHEDULE_FORMAT="cron"                         # cron | natural | iso8601
SCHEDULE_REMINDER_ADVANCE_MINUTES="15"         # Reminder before event
SCHEDULE_MAX_OCCURRENCES="1000"                # Safety limit
CALENDAR_EXPORT_FORMAT="ical"                  # ical | google | outlook
EVENT_EXECUTOR_AGENT="lex"                     # Agent for execution
```

## API Reference

### createSchedule(config)

Creates a new scheduled event.

**Parameters:**
```typescript
{
  name: string;                    // Schedule name (required)
  description?: string;            // Schedule description
  schedule: {
    type: "cron" | "natural" | "interval";
    expression: string;            // Cron or natural language
    timezone: string;              // IANA timezone
  };
  event_type: "audit" | "briefing" | "report" | "metrics" | "custom";
  prompt_template: {
    task_title: string;
    task_description: string;
    task_priority?: "low" | "medium" | "high";
    task_assignee?: string;
    task_tags?: string[];
  };
  actions?: Array<{
    type: "create_task" | "notify" | "trigger_skill" | "execute_script";
    [key: string]: any;
  }>;
  reminder?: {
    enabled: boolean;
    minutes_before: number;
    message: string;
  };
  max_occurrences?: number;
  metadata?: {
    [key: string]: any;
  };
}
```

**Returns:**
```typescript
{
  id: string;
  name: string;
  schedule: { ... };
  next_occurrence: string;  // ISO 8601 timestamp
  enabled: boolean;
  // ... full schedule object
}
```

### updateSchedule(scheduleId, updates)

Updates an existing schedule.

```javascript
await updateSchedule("sched_001", {
  enabled: false,  // Disable schedule
  schedule: {
    expression: "0 10 * * 0"  // Change time to 10:00 AM
  }
});
```

### deleteSchedule(scheduleId)

Deletes (archives) a schedule.

```javascript
await deleteSchedule("sched_001");
```

### listSchedules(filters)

Lists all schedules matching filters.

```javascript
const schedules = await listSchedules({
  event_type: "audit",
  enabled: true,
  agent: "lex"
});
```

### getNextOccurrences(scheduleId, count)

Gets next N occurrences for a schedule.

```javascript
const occurrences = await getNextOccurrences("sched_001", 10);
// Returns: ["2025-02-09T09:00:00Z", "2025-02-16T09:00:00Z", ...]
```

### executeSchedule(scheduleId)

Manually triggers a scheduled event.

```javascript
await executeSchedule("sched_001");
// Creates task immediately, bypasses schedule
```

### exportToCalendar(options)

Exports schedules to calendar format.

```javascript
await exportToCalendar({
  schedules: ["sched_001", "sched_002"],
  format: "ical",
  output_path: "$VAULT_PATH/Calendars/schedules.ics",
  options: {
    days_ahead: 30,
    include_reminders: true
  }
});
```

## Cron Expression Quick Reference

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

**Special Characters:**
- `*` : Any value
- `,` : Value list separator (1,15,30)
- `-` : Range of values (1-5)
- `/` : Step values (*/15 = every 15)

**Examples:**
- `0 9 * * *` : Daily at 9:00 AM
- `*/15 * * * *` : Every 15 minutes
- `0 9 * * 0` : Every Sunday at 9:00 AM
- `0 9 1 * *` : First day of month at 9:00 AM
- `0 9 * * 1-5` : Weekdays at 9:00 AM

## Workflow Integration

### Task Creation Flow

1. **Schedule Trigger**: Cron daemon evaluates schedules
2. **Template Rendering**: Replace {{date}}, {{timestamp}} variables
3. **Task Generation**: Create task JSON from prompt_template
4. **File Write**: Write to `Needs_Action/` folder
5. **Notification**: Update dashboard/send alerts
6. **Execution Tracking**: Update schedule metadata

### Agent Roles

- **lex (Local Executive Agent)**: Creates and manages schedules
- **orch (Orchestrator)**: Executes scheduled tasks
- **cex (Cloud Executive Agent)**: Plans complex recurring workflows
- **Watchers**: Cannot create schedules (read-only)

## Security

### Validation Rules

All schedules are validated before creation:

1. **Cron Expression**: Must match valid cron syntax
2. **Timezone**: Must be valid IANA timezone identifier
3. **Max Occurrences**: Cannot exceed 1000 (safety limit)
4. **Agent Authorization**: Only lex/orch can create schedules
5. **Prompt Sanitization**: Template variables are escaped

### Audit Trail

All schedule operations are logged:
- Schedule creation/update/deletion
- Execution timestamps
- Task creation events
- Errors and failures

Logs stored in: `$VAULT_PATH/Audit_Logs/Schedules/`

## Troubleshooting

### Schedule Not Triggering

1. Check if schedule is enabled:
   ```bash
   cat "$VAULT_PATH/Schedules/<schedule-file>.json" | jq '.enabled'
   ```

2. Verify cron expression:
   ```bash
   # Test cron expression online: https://crontab.guru/
   ```

3. Check timezone configuration:
   ```bash
   cat .env | grep TIMEZONE_DEFAULT
   ```

4. Review audit logs:
   ```bash
   tail -f "$VAULT_PATH/Audit_Logs/Schedules/schedule-executions.log"
   ```

### Invalid Cron Expression

Use the cron validation tool:
```bash
node .claude/skills/automation/time_event_scheduler/assets/validate-cron.js "0 9 * * 0"
# Output: Valid cron expression: Every Sunday at 9:00 AM
```

### Timezone Issues

List available timezones:
```bash
node -e "console.log(Intl.supportedValuesOf('timeZone'))"
```

### Missing Calendar Export

Verify calendar export path:
```bash
mkdir -p "$VAULT_PATH/Calendars"
ls -la "$VAULT_PATH/Calendars/"
```

## Examples

See [EXAMPLES.md](./EXAMPLES.md) for comprehensive usage examples including:
- Weekly compliance audits
- Daily briefings
- Multi-timezone coordination
- Calendar integrations
- Custom event types

## References

- [Cron Expression Syntax](https://en.wikipedia.org/wiki/Cron)
- [IANA Time Zone Database](https://www.iana.org/time-zones)
- [iCalendar Format (RFC 5545)](https://datatracker.ietf.org/doc/html/rfc5545)
- [patterns.md](./references/patterns.md) - Design patterns
- [gotchas.md](./references/gotchas.md) - Common pitfalls
- [impact-checklist.md](./references/impact-checklist.md) - Security checklist

## Support

For issues or questions:
1. Check [gotchas.md](./references/gotchas.md) for common problems
2. Review audit logs in `$VAULT_PATH/Audit_Logs/Schedules/`
3. Validate configuration with provided test scripts
4. Consult AGENTS.md for agent authorization rules
