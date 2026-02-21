# Recurring Task Scheduler Skill

## Overview

**Skill Name:** `recurring_task_scheduler`
**Domain:** `silver`
**Purpose:** Automatically create and manage recurring tasks based on flexible scheduling rules, ensuring timely and consistent execution of automated jobs.

**Core Capabilities:**
-   Define recurring tasks with various scheduling rules (e-g-, cron expressions, fixed intervals).
-   Automatically trigger defined tasks at their scheduled times.
-   Manage and persist the state of each task, including the last run time and next scheduled run.
-   Provide strategies for handling missed cycles due to system downtime (e-g-, skip, run immediately).
-   Maintain a detailed audit log for all task executions, including start times, completion status, and errors.
-   Integrate with other skills or external systems to perform actions as part of a task.
-   Support for different timezones to ensure tasks run at the correct local time.

**When to Use:**
-   Automating routine maintenance jobs (e-g-, cleaning temporary files, rotating logs).
-   Scheduling regular report generation or data aggregation.
-   Triggering periodic data synchronization between systems.
-   Managing recurring business processes like sending out weekly newsletters or daily reminders.
-   Automating infrastructure tasks like daily backups or system health checks.

**When NOT to Use:**
-   For tasks that require immediate, on-demand execution rather than a schedule.
-   As a replacement for a full-featured enterprise job scheduler if complex dependency chains are needed (e-g-, task B can only run after task A succeeds). This skill focuses on time-based recurrence.
-   For high-frequency tasks where execution time is less than a few seconds, as the overhead of the scheduler might be too high.
-   If you need to manage distributed tasks across a cluster of machines without a central coordinator.

---

## Impact Analysis

### Governance & Compliance Impact: **HIGH**
-   **Task Consistency:** Ensures that critical compliance and maintenance tasks are executed consistently and on time.
-   **Auditability:** Provides a clear audit trail of when tasks were run, what their outcome was, and any errors encountered, which is often a requirement for compliance.
-   **Accountability:** Lack of logging can obscure accountability for automated processes.

### Operational Efficiency Impact: **CRITICAL**
-   **Automation:** Reduces manual effort required to perform repetitive tasks, freeing up personnel for more strategic work.
-   **Reliability:** Increases the reliability of routine operations by removing the potential for human error.
-   **Process Optimization:** Scheduled tasks can be set to run during off-peak hours to optimize resource usage.
-   **Proactive Maintenance:** Enables proactive system maintenance, preventing issues before they become critical.

### System Integration Impact: **HIGH**
-   **Dependency on Time:** The entire system is dependent on accurate timekeeping and timezone data.
-   **Task Dependencies:** While not a full dependency manager, poorly configured overlapping tasks can cause resource contention or race conditions.
-   **Failure Resilience:** The scheduler must be resilient to its own failures and the failures of the tasks it runs, with clear strategies for recovery and missed cycles.
-   **Configuration Management:** Maintaining a large number of complex scheduling rules can become challenging.

---

## Environment Variables

### Required Variables

```bash
# Task scheduling configuration
RECURRING_TASK_RULES_PATH="./config/task-schedule-rules.json" # Path to the JSON file defining recurring tasks and their schedules.
RECURRING_TASK_STATE_PATH="./state/task_state.json"         # Path to persist the current state of tasks (last run, next run).
RECURRING_TASK_AUDIT_LOG="./logs/task-audit.log"            # Path to the audit log for all task executions.

# Default settings
RECURRING_TASK_DEFAULT_TIMEZONE="UTC"                         # Default timezone for evaluating schedules if not specified in the rule.
```

### Optional Variables

```bash
# Integration with other systems for task actions
RECURRING_TASK_ACTION_API="http://localhost:8080/api/tasks" # An endpoint to call to execute a task's action.
RECURRING_TASK_API_AUTH_TOKEN="<secret_token>"              # Auth token for the action API.

# Performance & concurrency
RECURRING_TASK_POLLING_INTERVAL_SECONDS="60"                # How often the scheduler checks for tasks that are due.
RECURRING_TASK_MAX_CONCURRENT_JOBS="10"                     # Maximum number of tasks to run simultaneously.

# Debugging
RECURRING_TASK_DEBUG_MODE="false"                           # Enable verbose logging for easier troubleshooting.
```

---

## Network and Authentication Implications

### Local Execution Mode

**Primary Mode:** Rules and state are managed locally- Ideal for tasks that run scripts or commands on the same machine-

**Requirements:**
-   Read access to `RECURRING_TASK_RULES_PATH`.
-   Read/Write access to `RECURRING_TASK_STATE_PATH`.
-   Write access to `RECURRING_TASK_AUDIT_LOG`.
-   No network dependencies for core scheduling logic-

### Integrated Execution Mode

**For tasks that trigger actions in external systems via API calls:**

```bash
# Example: Triggering a data processing job in another service
RECURRING_TASK_ACTION_API="https://dataproc.example.com/api/jobs"
RECURRING_TASK_ACTION_AUTH_TYPE="bearer"
```

**Authentication Patterns:**
-   **Bearer Token:** For modern REST APIs- The `RECURRING_TASK_API_AUTH_TOKEN` is sent in an `Authorization` header-
-   **API Key:** For simpler service-to-service authentication, potentially in a custom header-

### Network Patterns

**Pattern 1: Standalone (No Network)**
-   The scheduler and the tasks it runs (e-g-, local shell scripts) are all on the same machine- No external network calls are made-

**Pattern 2: Integrated (Network Required)**
-   The scheduler makes outbound API calls to `RECURRING_TASK_ACTION_API` to trigger task actions- Network failures can lead to task execution failures, which must be logged and potentially retried-

---

## Blueprints & Templates

### Template 1: Recurring Task Rules (JSON)

**File:** `assets/task-schedule-rules.json`

```json
{
  "version": "1.0",
  "tasks": [
    {
      "id": "daily-log-rotation",
      "name": "Daily Log Rotation",
      "description": "Rotates and compresses application logs every night at midnight.",
      "schedule": {
        "type": "cron",
        "value": "0 0 * * *",
        "timezone": "America/New_York"
      },
      "action": {
        "type": "local_script",
        "command": "/usr/local/bin/rotate_logs.sh --app-name api-server"
      },
      "on_missed_cycle": "run_immediately",
      "enabled": true
    },
    {
      "id": "hourly-health-check",
      "name": "Hourly System Health Check",
      "description": "Pings critical services and reports their status.",
      "schedule": {
        "type": "interval",
        "value": "1h"
      },
      "action": {
        "type": "api_call",
        "endpoint_id": "health_check_service",
        "payload": {
          "services": ["database", "cache", "auth-service"]
        }
      },
      "on_missed_cycle": "skip",
      "enabled": true
    },
    {
      "id": "weekly-report-generation",
      "name": "Weekly Sales Report Generation",
      "description": "Generates the sales report every Monday at 9 AM.",
      "schedule": {
        "type": "cron",
        "value": "0 9 * * 1",
        "timezone": "UTC"
      },
      "action": {
        "type": "skill_call",
        "skill_name": "reporting.sales_report_generator",
        "context": {
          "period": "weekly"
        }
      },
      "enabled": false
    }
  ],
  "endpoints": {
      "health_check_service": {
          "url": "https://monitor.example.com/api/health",
          "auth_token_env": "HEALTH_CHECK_API_TOKEN"
      }
  }
}
```

### Template 2: Python Task Scheduler Engine

**File:** `assets/task_scheduler.py`
*(A high-level conceptual implementation)*
```python
import os
import json
import time
from datetime import datetime
from croniter import croniter
import schedule

class RecurringTaskScheduler:
    def __init__(self):
        self.rules_path = os.getenv('RECURRING_TASK_RULES_PATH')
        self.state_path = os.getenv('RECURRING_TASK_STATE_PATH')
        self.audit_log_path = os.getenv('RECURRING_TASK_AUDIT_LOG')
        self.task_rules = self._load_rules()
        self.task_states = self._load_state()

    def _load_rules(self):
        # Load from self.rules_path
        pass

    def _load_state(self):
        # Load from self.state_path
        pass

    def _save_state(self):
        # Save to self.state_path
        pass
    
    def _audit_log(self, task_id, event, details):
        # Append to self.audit_log_path
        pass

    def _execute_task(self, task_config):
        # Execute the action (local_script, api_call, etc.)
        self._audit_log(task_config['id'], 'task_started', {})
        try:
            # ... execution logic ...
            self._audit_log(task_config['id'], 'task_succeeded', {})
        except Exception as e:
            self._audit_log(task_config['id'], 'task_failed', {'error': str(e)})

    def run_pending(self):
        now = datetime.now()
        for task in self.task_rules['tasks']:
            if not task['enabled']:
                continue
            
            state = self.task_states.get(task['id'], {})
            last_run = state.get('last_run_time')
            
            # Simplified logic for checking if a task is due
            is_due = False
            if task['schedule']['type'] == 'cron':
                # Use croniter to find next scheduled run
                base_time = last_run or now
                cron = croniter(task['schedule']['value'], base_time)
                next_run = cron.get_next(datetime)
                if now >= next_run:
                    is_due = True
            
            if is_due:
                self._execute_task(task)
                state['last_run_time'] = now.isoformat()
                self.task_states[task['id']] = state
        
        self._save_state()

def main():
    scheduler = RecurringTaskScheduler()
    polling_interval = int(os.getenv('RECURRING_TASK_POLLING_INTERVAL_SECONDS', 60))
    while True:
        scheduler.run_pending()
        time.sleep(polling_interval)

if __name__ == "__main__":
    main()
```

---

## Validation Checklist

### Pre-Deployment Checklist

-   [ ] **Scheduling Rules**
    -   [ ] All task definitions in `task-schedule-rules.json` have a unique `id`.
    -   [ ] Cron expressions are valid and have the correct number of fields.
    -   [ ] Interval values are in a recognizable format (e-g-, "1h", "30m").
    -   [ ] Timezones are valid IANA timezone names (e-g-, "UTC", "America/New_York").
    -   [ ] `on_missed_cycle` is set to a valid strategy (`skip` or `run_immediately`).

-   [ ] **Actions**
    -   [ ] `local_script` commands point to existing and executable files.
    -   [ ] `api_call` endpoint IDs are defined in the `endpoints` section of the rules file.
    -   [ ] `skill_call` names correspond to available skills.

-   [ ] **Configuration**
    -   [ ] All required environment variables are set.
    -   [ ] File paths for rules, state, and logs are correct and writable by the scheduler process.
    -   [ ] The default timezone is set appropriately for the environment.

### Post-Deployment Validation

-   [ ] **Functional Testing**
    -   [ ] A simple cron-based task runs at its scheduled time.
    -   [ ] A simple interval-based task runs at the correct frequency.
    -   [ ] Disabled tasks (`"enabled": false`) do not run.
    -   [ ] The `last_run_time` in `task_state.json` is updated after a task completes.

-   [ ] **Failure & Recovery Testing**
    -   [ ] A failing task (e-g-, a script that exits with an error) is logged as "failed" in the audit log.
    -   [ ] Stop the scheduler, wait for a task's scheduled time to pass, and restart it. Verify that `on_missed_cycle` behavior is correctly implemented.

-   [ ] **Audit & State Management**
    -   [ ] Audit log correctly records `task_started`, `task_succeeded`, and `task_failed` events.
    -   [ ] State is correctly persisted and reloaded if the scheduler is restarted.

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Overlapping Tasks with Resource Contention

**Bad Example:**
-   Scheduling a CPU-intensive report generation task every 5 minutes.
-   Scheduling a full database backup to run at the same time as a high-traffic data import.

**Why It's Bad:**
-   Causes performance degradation and resource starvation.
-   Can lead to deadlocks or race conditions if tasks access the same resources.
-   Makes system performance unpredictable.

**Correct Approach:**
-   Stagger schedules for resource-intensive tasks to run during off-peak hours.
-   Use shorter, more frequent intervals for lightweight tasks and longer intervals for heavy tasks.
-   Implement locking mechanisms if multiple tasks might access a shared resource, although this is outside the scope of the scheduler itself.

### ❌ Anti-Pattern 2: Hardcoding Schedules in Application Logic

**Bad Example:**
```python
# A function in an application that checks the time to run a job
def maybe_run_nightly_job():
    now = datetime.now()
    if now.hour == 2 and now.minute == 0: # ❌ Schedule is hardcoded
        run_nightly_job()
```

**Why It's Bad:**
-   Inflexible: Requires a code change and deployment to alter the schedule.
-   Poor Visibility: Schedules are scattered throughout the codebase and difficult to manage centrally.
-   Prone to error, especially with timezone handling.

**Correct Approach:**
-   Define all schedules declaratively in `task-schedule-rules.json`.
-   The application code should only contain the logic for the task itself, not for when it should run.

### ❌ Anti-Pattern 3: Missing Audit Logs for Task Execution

**Bad Example:**
-   A task script that runs but produces no log output unless it fails.
-   A scheduler that does not record when a task started or whether it was successful.

**Why It's Bad:**
-   Impossible to verify if a task ran when it was supposed to.
-   Makes troubleshooting failures extremely difficult.
-   Fails to meet compliance requirements for audibility.

**Correct Approach:**
-   The scheduler MUST log the start, success, and failure of every task execution to the audit log.
-   Logs should include the task ID, timestamp, and any relevant output or error messages.

### ❌ Anti-Pattern 4: Ignoring Timezone Differences

**Bad Example:**
-   Setting a cron schedule for `0 9 * * 1` (9 AM on Monday) and assuming it will run at 9 AM for all users, regardless of their location.
-   Running the scheduler process in a server configured to UTC, but scheduling tasks based on local times without specifying a timezone.

**Why It's Bad:**
-   Tasks run at the wrong time, potentially causing business disruption (e-g-, a report is generated too early or too late).
-   Daylight Saving Time changes can cause tasks to run an hour off or be skipped entirely.

**Correct Approach:**
-   Always specify a timezone in the schedule definition (`"timezone": "America/New_York"`).
-   If no timezone is specified, the scheduler should use a clearly defined default (e-g-, `RECURRING_TASK_DEFAULT_TIMEZONE="UTC"`).
-   Use timezone-aware libraries for all date and time calculations.

### ❌ Anti-Pattern 5: Not Handling Skipped Cycles or Failures

**Bad Example:**
-   A scheduler that, upon restarting after downtime, does not check for tasks that should have run while it was down.
-   A task that fails but is never retried or flagged for manual intervention.

**Why It's Bad:**
-   Critical tasks may be skipped, leading to data inconsistencies or missed business processes.
-   Repeatedly failing tasks can go unnoticed, masking a deeper underlying problem.

**Correct Approach:**
-   Implement a clear strategy for missed cycles (`on_missed_cycle`), allowing operators to choose whether to skip or run the task immediately.
-   The scheduler should have a mechanism to detect and log missed runs upon startup.
-   Failed tasks should be clearly logged, and an alerting mechanism should be considered to notify operators of persistent failures.

---

**Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** Silver Team
