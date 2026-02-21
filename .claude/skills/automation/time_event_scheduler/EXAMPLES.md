# Time Event Scheduler Examples

This document provides comprehensive examples for using the Time Event Scheduler skill in various scenarios.

## Table of Contents

1. [Weekly Sunday Audit](#1-weekly-sunday-audit)
2. [Monday Morning Briefing](#2-monday-morning-briefing)
3. [Daily Standup Reminder](#3-daily-standup-reminder)
4. [Monthly Reporting](#4-monthly-reporting)
5. [Every 4 Hours Monitoring](#5-every-4-hours-monitoring)
6. [Multi-Timezone Team Meeting](#6-multi-timezone-team-meeting)
7. [Custom Event with Reminders](#7-custom-event-with-reminders)
8. [Calendar Export for Team](#8-calendar-export-for-team)
9. [Conditional Schedule (Weekdays Only)](#9-conditional-schedule-weekdays-only)
10. [Natural Language Scheduling](#10-natural-language-scheduling)

---

## 1. Weekly Sunday Audit

**Scenario:** Run a comprehensive compliance audit every Sunday at 9:00 AM UTC.

**Code:**
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
4. Check for policy violations in In_Progress/
5. Verify Pending_Approval/ tasks have proper documentation
6. Generate audit report with findings`,
    task_priority: "high",
    task_assignee: "lex",
    task_tags: ["audit", "compliance", "weekly", "automated"]
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
      message: "Weekly audit task created - review required by EOD"
    }
  ],
  reminder: {
    enabled: true,
    minutes_before: 30,
    message: "Weekly compliance audit will start in 30 minutes"
  },
  max_occurrences: 52,  // One year of weekly audits
  metadata: {
    created_by: "admin",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true,
    category: "compliance",
    criticality: "high"
  }
});

console.log(`Audit Schedule Created`);
console.log(`  ID: ${auditSchedule.id}`);
console.log(`  Next Run: ${auditSchedule.next_occurrence}`);
console.log(`  Human Readable: ${auditSchedule.schedule.human_readable}`);
```

**Expected Output:**
```
Audit Schedule Created
  ID: sched_001
  Next Run: 2025-02-09T09:00:00Z
  Human Readable: Every Sunday at 9:00 AM UTC
```

**Generated File:** `Schedules/weekly-compliance-audit.schedule.json`

---

## 2. Monday Morning Briefing

**Scenario:** Generate a weekly briefing every Monday at 8:00 AM Eastern Time.

**Code:**
```javascript
const briefingSchedule = await createSchedule({
  name: "Monday Morning Briefing",
  description: "Weekly summary of tasks, priorities, and blockers",
  schedule: {
    type: "cron",
    expression: "0 8 * * 1",  // Every Monday at 8:00 AM
    timezone: "America/New_York"
  },
  event_type: "briefing",
  prompt_template: {
    task_title: "Monday Briefing - Week of {{date}}",
    task_description: `Generate weekly briefing report:

**Last Week's Summary:**
1. Summarize all completed tasks from Done/
2. Calculate completion rate vs planned tasks
3. Identify any missed deadlines

**This Week's Priorities:**
1. List top 5 priority tasks from Plans/
2. Highlight any blocking dependencies
3. Identify resource bottlenecks

**Risks & Issues:**
1. Flag tasks stuck in In_Progress/ >3 days
2. Identify pending approvals >48 hours old
3. Note any policy violations from last audit

**Action Items:**
1. Send briefing email to stakeholders
2. Update project dashboard
3. Schedule follow-up meetings if needed`,
    task_priority: "high",
    task_assignee: "lex",
    task_tags: ["briefing", "weekly", "communication", "reporting"]
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
        tone: "formal",
        subject: "Weekly Briefing - {{date}}"
      }
    },
    {
      type: "trigger_skill",
      skill: "dashboard_writer",
      params: {
        update_type: "weekly_summary"
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
    enabled: true,
    category: "reporting",
    distribution_list: ["team@company.com", "management@company.com"]
  }
});
```

---

## 3. Daily Standup Reminder

**Scenario:** Daily standup reminder every weekday at 9:30 AM.

**Code:**
```javascript
const standupSchedule = await createSchedule({
  name: "Daily Standup Reminder",
  description: "Remind team about daily standup meeting",
  schedule: {
    type: "cron",
    expression: "30 9 * * 1-5",  // Weekdays at 9:30 AM
    timezone: "America/Los_Angeles"
  },
  event_type: "custom",
  prompt_template: {
    task_title: "Daily Standup - {{date}}",
    task_description: `Daily standup preparation:

**Prepare Updates:**
1. Yesterday's accomplishments
2. Today's planned work
3. Current blockers

**Meeting Logistics:**
- Time: 9:30 AM PST
- Duration: 15 minutes
- Location: Conference Room A / Zoom
- Required: All team members`,
    task_priority: "medium",
    task_assignee: "lex",
    task_tags: ["standup", "daily", "meeting", "reminder"]
  },
  actions: [
    {
      type: "notify",
      target: "slack",
      channel: "#daily-standup",
      message: "@channel Daily standup in 5 minutes!"
    },
    {
      type: "notify",
      target: "calendar",
      action: "send_reminder"
    }
  ],
  reminder: {
    enabled: true,
    minutes_before: 5,
    message: "Daily standup starts in 5 minutes"
  },
  metadata: {
    created_by: "scrum_master",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true,
    category: "meeting"
  }
});
```

---

## 4. Monthly Reporting

**Scenario:** Generate end-of-month report on the first day of each month.

**Code:**
```javascript
const monthlyReportSchedule = await createSchedule({
  name: "Monthly Performance Report",
  description: "Generate comprehensive monthly performance metrics",
  schedule: {
    type: "cron",
    expression: "0 9 1 * *",  // First day of month at 9:00 AM
    timezone: "UTC"
  },
  event_type: "report",
  prompt_template: {
    task_title: "Monthly Report - {{month}} {{year}}",
    task_description: `Generate monthly performance report:

**Metrics to Include:**
1. Total tasks completed vs planned
2. Average task completion time
3. Agent utilization rates (lex, orch, cex)
4. Task category breakdown
5. Approval turnaround times
6. Policy compliance score
7. Error rates and incident count

**Analysis:**
1. Identify performance trends
2. Compare to previous month
3. Highlight achievements
4. Note areas for improvement

**Deliverables:**
1. Generate PDF report
2. Update executive dashboard
3. Send to leadership team
4. Archive in Reports/ folder`,
    task_priority: "high",
    task_assignee: "lex",
    task_tags: ["report", "monthly", "metrics", "leadership"]
  },
  actions: [
    {
      type: "create_task",
      target: "Needs_Action/",
      agent: "lex"
    },
    {
      type: "execute_script",
      script: "scripts/generate_monthly_report.sh",
      timeout_seconds: 600
    },
    {
      type: "trigger_skill",
      skill: "email_drafter",
      params: {
        recipient_type: "leadership",
        tone: "formal",
        subject: "Monthly Performance Report - {{month}}"
      }
    }
  ],
  max_occurrences: 12,  // One year of monthly reports
  metadata: {
    created_by: "admin",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true,
    category: "reporting",
    report_type: "monthly_performance"
  }
});
```

---

## 5. Every 4 Hours Monitoring

**Scenario:** Collect performance metrics every 4 hours.

**Code:**
```javascript
const metricsSchedule = await createSchedule({
  name: "Performance Metrics Collection",
  description: "Collect and aggregate system performance metrics",
  schedule: {
    type: "cron",
    expression: "0 */4 * * *",  // Every 4 hours
    timezone: "UTC"
  },
  event_type: "metrics",
  prompt_template: {
    task_title: "Collect Metrics - {{timestamp}}",
    task_description: `Collect system performance metrics:

**Metrics to Collect:**
1. Task completion rates (last 4 hours)
2. Average task duration by category
3. Agent CPU/memory utilization
4. Queue lengths (Needs_Action, In_Progress, Pending_Approval)
5. Error rates and types
6. API response times

**Actions:**
1. Store metrics in time-series database
2. Update real-time dashboard
3. Check alerting thresholds
4. Detect anomalies`,
    task_priority: "medium",
    task_assignee: "orch",
    task_tags: ["metrics", "monitoring", "performance", "automated"]
  },
  actions: [
    {
      type: "execute_script",
      script: "scripts/collect_metrics.sh",
      timeout_seconds: 300
    },
    {
      type: "notify",
      target: "dashboard",
      message: "Metrics collection completed"
    }
  ],
  max_occurrences: 1000,  // ~5 months of data
  metadata: {
    created_by: "system",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true,
    category: "monitoring",
    retention_days: 90
  }
});
```

---

## 6. Multi-Timezone Team Meeting

**Scenario:** Schedule a weekly team meeting that accommodates multiple timezones.

**Code:**
```javascript
// Create schedules for different regional teams

// US Team (Pacific Time)
const usSchedule = await createSchedule({
  name: "Weekly Team Meeting - US",
  schedule: {
    type: "cron",
    expression: "0 10 * * 3",  // Wednesdays at 10:00 AM
    timezone: "America/Los_Angeles"
  },
  event_type: "custom",
  prompt_template: {
    task_title: "Team Meeting (US) - {{date}}",
    task_description: "Weekly sync for US-based team members",
    task_assignee: "lex",
    task_tags: ["meeting", "us-team", "weekly"]
  },
  metadata: {
    region: "US",
    local_time: "10:00 AM PST"
  }
});

// Europe Team (Central European Time)
const euSchedule = await createSchedule({
  name: "Weekly Team Meeting - EU",
  schedule: {
    type: "cron",
    expression: "0 15 * * 3",  // Wednesdays at 3:00 PM
    timezone: "Europe/Paris"
  },
  event_type: "custom",
  prompt_template: {
    task_title: "Team Meeting (EU) - {{date}}",
    task_description: "Weekly sync for Europe-based team members",
    task_assignee: "lex",
    task_tags: ["meeting", "eu-team", "weekly"]
  },
  metadata: {
    region: "Europe",
    local_time: "3:00 PM CET"
  }
});

// Asia-Pacific Team (Singapore Time)
const apacSchedule = await createSchedule({
  name: "Weekly Team Meeting - APAC",
  schedule: {
    type: "cron",
    expression: "0 9 * * 4",  // Thursdays at 9:00 AM
    timezone: "Asia/Singapore"
  },
  event_type: "custom",
  prompt_template: {
    task_title: "Team Meeting (APAC) - {{date}}",
    task_description: "Weekly sync for APAC-based team members",
    task_assignee: "lex",
    task_tags: ["meeting", "apac-team", "weekly"]
  },
  metadata: {
    region: "APAC",
    local_time: "9:00 AM SGT"
  }
});

console.log("Multi-timezone meetings scheduled:");
console.log(`  US: ${usSchedule.next_occurrence} (${usSchedule.schedule.timezone})`);
console.log(`  EU: ${euSchedule.next_occurrence} (${euSchedule.schedule.timezone})`);
console.log(`  APAC: ${apacSchedule.next_occurrence} (${apacSchedule.schedule.timezone})`);
```

---

## 7. Custom Event with Reminders

**Scenario:** Schedule a quarterly review with multiple reminders.

**Code:**
```javascript
const quarterlyReviewSchedule = await createSchedule({
  name: "Quarterly Business Review",
  description: "Comprehensive quarterly review of all business metrics",
  schedule: {
    type: "cron",
    expression: "0 9 1 1,4,7,10 *",  // Jan 1, Apr 1, Jul 1, Oct 1 at 9:00 AM
    timezone: "UTC"
  },
  event_type: "report",
  prompt_template: {
    task_title: "Q{{quarter}} Business Review - {{year}}",
    task_description: `Quarterly business review preparation:

**Data Collection:**
1. Gather all quarterly metrics
2. Compile financial reports
3. Analyze project outcomes
4. Review strategic goals

**Analysis:**
1. Quarter-over-quarter comparison
2. Year-over-year trends
3. Goal achievement assessment
4. Risk and opportunity identification

**Deliverables:**
1. Executive presentation deck
2. Detailed metrics report
3. Recommendations document
4. Next quarter planning`,
    task_priority: "critical",
    task_assignee: "lex",
    task_tags: ["quarterly", "review", "strategic", "leadership"]
  },
  actions: [
    {
      type: "create_task",
      target: "Needs_Action/",
      agent: "lex"
    }
  ],
  reminder: {
    enabled: true,
    minutes_before: 10080,  // 1 week before (7 days * 24 hours * 60 minutes)
    message: "Quarterly business review in 1 week - begin preparation"
  },
  metadata: {
    created_by: "admin",
    created_at: "2025-02-04T10:00:00Z",
    enabled: true,
    category: "strategic",
    reminders: [
      { days_before: 7, message: "QBR in 1 week" },
      { days_before: 3, message: "QBR in 3 days" },
      { days_before: 1, message: "QBR tomorrow" }
    ]
  }
});
```

---

## 8. Calendar Export for Team

**Scenario:** Export all team schedules to a shared calendar file.

**Code:**
```javascript
const { exportToCalendar } = require('./time_event_scheduler');

// First, get all schedules
const { listSchedules } = require('./time_event_scheduler');
const allSchedules = await listSchedules({ enabled: true });

// Export to iCal format
const calendarExport = await exportToCalendar({
  schedules: allSchedules.map(s => s.id),
  format: "ical",
  output_path: "$VAULT_PATH/Calendars/team-schedule.ics",
  options: {
    include_past_events: false,
    days_ahead: 90,  // Next 3 months
    include_reminders: true,
    calendar_name: "AI Employee Team Schedule",
    calendar_description: "Automated schedules for AI agent workflows",
    timezone: "UTC"
  }
});

console.log("Calendar Export Summary:");
console.log(`  File: ${calendarExport.file_path}`);
console.log(`  Events: ${calendarExport.event_count}`);
console.log(`  Date Range: ${calendarExport.start_date} to ${calendarExport.end_date}`);
console.log(`  Format: ${calendarExport.format}`);

// Also export to Google Calendar format
const googleExport = await exportToCalendar({
  schedules: allSchedules.map(s => s.id),
  format: "google",
  output_path: "$VAULT_PATH/Calendars/team-schedule-google.ics",
  options: {
    days_ahead: 90,
    include_reminders: true
  }
});

console.log(`\nGoogle Calendar file: ${googleExport.file_path}`);
console.log("Import instructions:");
console.log("  1. Open Google Calendar");
console.log("  2. Click Settings > Import & Export");
console.log("  3. Select the .ics file");
console.log("  4. Choose destination calendar");
```

---

## 9. Conditional Schedule (Weekdays Only)

**Scenario:** Daily task that only runs on weekdays, with different times for morning/afternoon.

**Code:**
```javascript
// Morning schedule (weekdays only)
const morningSchedule = await createSchedule({
  name: "Morning Task Review",
  schedule: {
    type: "cron",
    expression: "0 8 * * 1-5",  // Weekdays at 8:00 AM
    timezone: "America/New_York"
  },
  event_type: "custom",
  prompt_template: {
    task_title: "Morning Review - {{date}}",
    task_description: `Morning task review:

1. Review overnight automated task completions
2. Prioritize today's task list
3. Identify any urgent items
4. Assign tasks to agents`,
    task_assignee: "lex",
    task_tags: ["morning", "review", "daily", "weekdays"]
  }
});

// Afternoon schedule (weekdays only)
const afternoonSchedule = await createSchedule({
  name: "Afternoon Progress Check",
  schedule: {
    type: "cron",
    expression: "0 14 * * 1-5",  // Weekdays at 2:00 PM
    timezone: "America/New_York"
  },
  event_type: "custom",
  prompt_template: {
    task_title: "Afternoon Check - {{date}}",
    task_description: `Afternoon progress check:

1. Review task completion status
2. Check for blocked tasks
3. Reallocate resources if needed
4. Update stakeholders on progress`,
    task_assignee: "lex",
    task_tags: ["afternoon", "progress", "daily", "weekdays"]
  }
});

console.log("Weekday schedules created:");
console.log(`  Morning: ${morningSchedule.schedule.human_readable}`);
console.log(`  Afternoon: ${afternoonSchedule.schedule.human_readable}`);
```

---

## 10. Natural Language Scheduling

**Scenario:** Use natural language to create schedules without writing cron expressions.

**Code:**
```javascript
// Example 1: Daily at specific time
const dailySchedule = await createSchedule({
  name: "Daily Backup",
  schedule: {
    type: "natural",
    expression: "every day at 2am",
    timezone: "UTC"
  },
  event_type: "custom"
  // ... rest of config
});
// Converted to: 0 2 * * *

// Example 2: Weekly on specific day
const weeklySchedule = await createSchedule({
  name: "Weekly Report",
  schedule: {
    type: "natural",
    expression: "every friday at 5pm",
    timezone: "America/New_York"
  },
  event_type: "report"
  // ... rest of config
});
// Converted to: 0 17 * * 5

// Example 3: Multiple days
const meetingSchedule = await createSchedule({
  name: "Team Sync",
  schedule: {
    type: "natural",
    expression: "every monday, wednesday, friday at 10am",
    timezone: "America/Los_Angeles"
  },
  event_type: "custom"
  // ... rest of config
});
// Converted to: 0 10 * * 1,3,5

// Example 4: Every X hours
const monitoringSchedule = await createSchedule({
  name: "System Check",
  schedule: {
    type: "natural",
    expression: "every 6 hours",
    timezone: "UTC"
  },
  event_type: "metrics"
  // ... rest of config
});
// Converted to: 0 */6 * * *

// Example 5: Weekdays only
const businessSchedule = await createSchedule({
  name: "Business Hours Task",
  schedule: {
    type: "natural",
    expression: "every weekday at 9am",
    timezone: "America/Chicago"
  },
  event_type: "custom"
  // ... rest of config
});
// Converted to: 0 9 * * 1-5

console.log("Natural language schedules created:");
console.log(`  Daily: ${dailySchedule.schedule.expression}`);
console.log(`  Weekly: ${weeklySchedule.schedule.expression}`);
console.log(`  Multiple: ${meetingSchedule.schedule.expression}`);
console.log(`  Interval: ${monitoringSchedule.schedule.expression}`);
console.log(`  Weekdays: ${businessSchedule.schedule.expression}`);
```

---

## Complete Workflow Example

**Scenario:** Set up a complete workflow with multiple coordinated schedules.

**Code:**
```javascript
// 1. Daily morning briefing
const morningBriefing = await createSchedule({
  name: "Daily Morning Briefing",
  schedule: { type: "cron", expression: "0 8 * * 1-5", timezone: "UTC" },
  event_type: "briefing",
  prompt_template: {
    task_title: "Daily Briefing - {{date}}",
    task_description: "Generate daily status briefing",
    task_assignee: "lex"
  }
});

// 2. Weekly audit (Sunday)
const weeklyAudit = await createSchedule({
  name: "Weekly Compliance Audit",
  schedule: { type: "cron", expression: "0 9 * * 0", timezone: "UTC" },
  event_type: "audit",
  prompt_template: {
    task_title: "Weekly Audit - {{date}}",
    task_description: "Execute compliance audit",
    task_assignee: "lex"
  }
});

// 3. Monthly report (1st of month)
const monthlyReport = await createSchedule({
  name: "Monthly Performance Report",
  schedule: { type: "cron", expression: "0 9 1 * *", timezone: "UTC" },
  event_type: "report",
  prompt_template: {
    task_title: "Monthly Report - {{month}} {{year}}",
    task_description: "Generate monthly performance report",
    task_assignee: "lex"
  }
});

// 4. Hourly monitoring
const hourlyMonitoring = await createSchedule({
  name: "Hourly System Check",
  schedule: { type: "cron", expression: "0 * * * *", timezone: "UTC" },
  event_type: "metrics",
  prompt_template: {
    task_title: "System Check - {{timestamp}}",
    task_description: "Collect system metrics",
    task_assignee: "orch"
  }
});

// 5. Export all to calendar
const calendar = await exportToCalendar({
  schedules: [
    morningBriefing.id,
    weeklyAudit.id,
    monthlyReport.id,
    hourlyMonitoring.id
  ],
  format: "ical",
  output_path: "$VAULT_PATH/Calendars/complete-workflow.ics",
  options: {
    days_ahead: 30,
    include_reminders: true
  }
});

console.log("Complete workflow configured:");
console.log(`  Daily briefings: ${morningBriefing.id}`);
console.log(`  Weekly audits: ${weeklyAudit.id}`);
console.log(`  Monthly reports: ${monthlyReport.id}`);
console.log(`  Hourly monitoring: ${hourlyMonitoring.id}`);
console.log(`  Calendar exported: ${calendar.file_path}`);
```

---

## Testing and Validation

**Test a schedule without waiting for trigger:**

```javascript
const { executeSchedule, getNextOccurrences } = require('./time_event_scheduler');

// Test execution
await executeSchedule("sched_001");
console.log("Schedule executed successfully");

// View next 10 occurrences
const occurrences = await getNextOccurrences("sched_001", 10);
console.log("Next 10 occurrences:");
occurrences.forEach((time, i) => {
  console.log(`  ${i + 1}. ${time}`);
});
```

---

## Error Handling

**Handle schedule creation errors:**

```javascript
try {
  const schedule = await createSchedule({
    name: "Test Schedule",
    schedule: {
      type: "cron",
      expression: "0 9 * * 0",
      timezone: "Invalid/Timezone"  // This will fail validation
    },
    event_type: "custom"
  });
} catch (error) {
  console.error("Schedule creation failed:");
  console.error(`  Error: ${error.message}`);
  console.error(`  Details: ${error.details}`);

  if (error.code === "INVALID_TIMEZONE") {
    console.error("  Hint: Use valid IANA timezone (e.g., 'America/New_York')");
  } else if (error.code === "INVALID_CRON") {
    console.error("  Hint: Check cron expression syntax at https://crontab.guru/");
  }
}
```

---

## Summary

These examples demonstrate the flexibility and power of the Time Event Scheduler skill. Key takeaways:

1. **Cron expressions** provide precise scheduling control
2. **Natural language** makes scheduling intuitive
3. **Timezone support** enables global coordination
4. **Calendar export** facilitates team visibility
5. **Integration hooks** enable complex workflows
6. **Reminders** ensure timely preparation
7. **Validation** prevents configuration errors

For more information, see:
- [README.md](./README.md) - Full documentation
- [SKILL.md](./SKILL.md) - Detailed skill specification
- [references/patterns.md](./references/patterns.md) - Design patterns
- [references/gotchas.md](./references/gotchas.md) - Common pitfalls
