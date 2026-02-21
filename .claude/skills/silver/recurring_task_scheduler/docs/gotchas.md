# Recurring Task Scheduler - Gotchas and Troubleshooting

## Overview
This document highlights common issues, anti-patterns, and troubleshooting tips related to the Recurring Task Scheduler skill. Understanding these gotchas will help you avoid common pitfalls and resolve issues more effectively.

## Common Gotchas

### 1. Timezone Confusion
**Problem**: Scheduled tasks running at unexpected times due to timezone misconfiguration.
**Solution**: Always explicitly specify timezones in your schedule definitions. Use consistent timezone settings across all configurations.

**Example of bad practice**:
```json
{
  "id": "daily_task",
  "schedule": {
    "type": "cron",
    "expression": "0 9 * * *"  // What timezone is this?
  }
}
```

**Better approach**:
```json
{
  "id": "daily_task",
  "schedule": {
    "type": "cron",
    "expression": "0 9 * * *",
    "timezone": "America/New_York"
  }
}
```

### 2. Overlapping Task Executions
**Problem**: Long-running tasks starting before previous instances have completed.
**Solution**: Implement task locks or ensure tasks complete faster than their scheduled interval.

**Mitigation strategies**:
- Use file or database locks to prevent concurrent execution
- Monitor task duration and adjust scheduling frequency accordingly
- Implement queue-based execution for tasks that may run long

### 3. Daylight Saving Time Issues
**Problem**: Tasks not running as expected during daylight saving transitions.
**Solution**: Use UTC for scheduling when possible, or use timezone-aware scheduling libraries that handle DST transitions.

### 4. System Clock Drift
**Problem**: Scheduled tasks not running at precise times due to system clock drift.
**Solution**: Ensure your system uses NTP (Network Time Protocol) to maintain accurate time.

### 5. Accumulation of Missed Executions
**Problem**: When the scheduler is down, many tasks may try to execute at once when it restarts.
**Solution**: Implement an `on_missed_cycle` policy in your task definitions to handle missed executions appropriately.

## Anti-Patterns to Avoid

### 1. Hardcoded Schedules in Code
**Anti-Pattern**: Embedding schedule information directly in application code.
```python
# DON'T DO THIS
import time
if time.localtime().tm_hour == 2 and time.localtime().tm_min == 0:
    run_backup()
```

**Better Approach**: Define all schedules in configuration files (e.g., `task-schedule-rules.json`).

### 2. Scheduling Too Frequently
**Anti-Pattern**: Setting very short intervals that overwhelm the system.
```json
{
  "id": "check_status",
  "schedule": {
    "type": "interval",
    "unit": "seconds",
    "frequency": 1  // Every second - likely too frequent
  }
}
```

**Better Approach**: Evaluate if real-time event-driven approaches might be more appropriate than polling.

### 3. Neglecting Failure Scenarios
**Anti-Pattern**: Not considering what happens when tasks fail repeatedly.
**Better Approach**: Implement exponential backoff for retries and alerting for persistent failures.

### 4. Resource Starvation
**Anti-Pattern**: Scheduling multiple resource-intensive tasks to run simultaneously.
**Better Approach**: Stagger resource-heavy tasks or implement resource allocation controls.

### 5. Missing Audit Trail
**Anti-Pattern**: Not logging task execution details.
**Better Approach**: Ensure all task starts, successes, and failures are logged with sufficient detail for debugging.

## Troubleshooting Tips

### 1. Debugging Schedule Issues
- Check the system timezone: `date` or `timedatectl status`
- Verify your cron expression with online validators
- Enable debug logging to see exact execution times
- Check for DST transitions that might affect scheduling

### 2. Diagnosing Performance Problems
- Monitor system resources during scheduled task execution
- Log task execution times to identify slow tasks
- Check for resource contention between simultaneous tasks
- Review the scheduler's internal queue length

### 3. Resolving Dependency Issues
- Verify that all required services are running before scheduled tasks start
- Implement proper health checks before executing dependent tasks
- Use connection pooling appropriately for database-dependent tasks
- Check network connectivity to external services

### 4. Handling Missed Executions
- Implement proper catch-up policies based on task type
- For time-sensitive tasks, skip missed executions
- For accumulating tasks, run missed executions sequentially
- Log missed executions for monitoring and alerting

## Common Error Messages and Solutions

### "Task execution took too long"
**Cause**: Task exceeded its configured timeout.
**Solution**: Increase the timeout value or optimize the task to complete faster.

### "Failed to acquire execution lock"
**Cause**: Previous instance of the task is still running.
**Solution**: Check if the task is stuck, or reduce the scheduling frequency.

### "Scheduler is overloaded"
**Cause**: Too many tasks scheduled simultaneously.
**Solution**: Distribute tasks across different times or implement queuing.

### "Configuration file not found"
**Cause**: Missing or incorrectly referenced configuration file.
**Solution**: Verify file paths and permissions for configuration files.

### "Permission denied when executing task"
**Cause**: Insufficient permissions for the task to run.
**Solution**: Grant appropriate permissions or run the scheduler under a more privileged account.

## Best Practices for Avoiding Gotchas

1. **Always test schedules** in a non-production environment first
2. **Log everything** related to task execution for debugging
3. **Monitor execution times** to detect performance degradation
4. **Set appropriate timeouts** for all tasks to prevent hanging
5. **Implement alerting** for failed or missed executions
6. **Document all scheduled tasks** with their purpose and dependencies
7. **Regularly review** scheduled tasks for relevance and performance
8. **Use consistent naming** for easy identification of tasks
9. **Plan for scalability** as the number of scheduled tasks grows
10. **Keep tasks idempotent** so repeated execution doesn't cause issues

## Conclusion

Understanding these gotchas and following the recommended practices will help you implement robust and reliable recurring task scheduling. Regular review and monitoring of your scheduled tasks will help identify and address issues before they become problematic.