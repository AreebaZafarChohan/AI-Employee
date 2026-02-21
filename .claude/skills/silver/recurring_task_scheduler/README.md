# Recurring Task Scheduler

## Overview
The Recurring Task Scheduler is a Claude Code skill that enables automated creation and management of recurring tasks with flexible scheduling rules. It provides a robust system for scheduling, executing, and monitoring tasks that need to run on a regular basis, with support for various recurrence patterns, dependencies, and audit logging.

## Key Features
- **Flexible Scheduling**: Define tasks with various recurrence patterns (cron-like expressions, intervals, custom rules)
- **State Management**: Tracks task execution history and handles missed cycles
- **Audit Trail**: Comprehensive logging of all task activities for compliance and debugging
- **Dependency Management**: Handle task dependencies and prevent overlapping executions
- **Failure Recovery**: Robust error handling and recovery mechanisms

## Quick Start

1. **Configure your tasks** in `task-schedule-rules.json`:
```json
{
  "tasks": [
    {
      "id": "daily_backup",
      "name": "Daily Database Backup",
      "schedule": "0 2 * * *",
      "command": "/scripts/backup.sh",
      "enabled": true,
      "timezone": "UTC"
    }
  ]
}
```

2. **Start the scheduler**:
```bash
python task_scheduler.py
```

3. **Monitor execution** in the audit log and state files.

## Documentation
- `SKILL.md` - Full specification and implementation details
- `docs/patterns.md` - Recurrence rule patterns and best practices
- `docs/impact-checklist.md` - Impact assessment for task scheduling
- `docs/gotchas.md` - Common pitfalls and troubleshooting

## Assets
- `task-schedule-rules.json` - Template for defining scheduled tasks
- `task_scheduler.py` - Core scheduler implementation
- `example-schedule-config.json` - Example configuration file
- `MANIFEST.md` - Skill manifest

## Anti-Patterns to Avoid
- Creating overlapping tasks that compete for resources
- Hardcoding schedules in application logic instead of using configuration
- Neglecting audit logs for task execution tracking
- Failing to handle missed cycles during system downtime

For detailed information on configuration options, recurrence patterns, and advanced features, refer to `SKILL.md`.