# Recurring Task Scheduler - Patterns Guide

## Overview
This document outlines various patterns for defining and managing recurring tasks using the Recurring Task Scheduler skill. These patterns cover common use cases and best practices for scheduling automation.

## Recurrence Rule Patterns

### 1. Simple Interval-Based Scheduling
Use for tasks that need to run at regular intervals (e.g., every hour, daily, weekly).

Example:
```json
{
  "id": "hourly_report",
  "schedule": {
    "type": "interval",
    "unit": "hours",
    "frequency": 1
  }
}
```

### 2. Cron-Based Scheduling
Use for complex scheduling needs with specific day/time combinations.

Example:
```json
{
  "id": "weekly_cleanup",
  "schedule": {
    "type": "cron",
    "expression": "0 0 * * 0"  // Runs at midnight every Sunday
  }
}
```

### 3. Business Days Only
Schedule tasks to run only on weekdays, avoiding weekends.

Example:
```json
{
  "id": "daily_summary",
  "schedule": {
    "type": "cron",
    "expression": "0 9 * * 1-5"  // Runs at 9 AM Monday through Friday
  }
}
```

### 4. Monthly Scheduling
For tasks that need to run once per month on specific days.

Example:
```json
{
  "id": "monthly_billing",
  "schedule": {
    "type": "cron",
    "expression": "0 0 1 * *"  // Runs at midnight on the first of each month
  }
}
```

### 5. Seasonal or Date-Specific Scheduling
For tasks that run on specific dates or seasons.

Example:
```json
{
  "id": "yearly_audit",
  "schedule": {
    "type": "cron",
    "expression": "0 0 1 1 *"  // Runs at midnight on January 1st annually
  }
}
```

## Advanced Patterns

### 6. Dependent Task Chains
Create workflows where one task triggers another upon completion.

Example:
```json
{
  "id": "data_processing_pipeline",
  "dependencies": [],
  "schedule": {
    "type": "cron",
    "expression": "0 2 * * *"
  },
  "next_task": "report_generation"
},
{
  "id": "report_generation",
  "dependencies": ["data_processing_pipeline"],
  "schedule": {
    "type": "triggered"
  }
}
```

### 7. Load-Balanced Scheduling
Distribute tasks across multiple time slots to prevent system overload.

Example:
```json
{
  "id": "batch_job_cluster_1",
  "schedule": {
    "type": "cron",
    "expression": "0 */4 * * *"  // Runs every 4 hours starting at midnight
  }
},
{
  "id": "batch_job_cluster_2",
  "schedule": {
    "type": "cron",
    "expression": "20 */4 * * *"  // Runs every 4 hours starting at 00:20
  }
}
```

### 8. Conditional Scheduling
Run tasks based on specific conditions or system states.

Example:
```json
{
  "id": "cleanup_old_logs",
  "schedule": {
    "type": "interval",
    "unit": "days",
    "frequency": 1
  },
  "condition": {
    "type": "disk_usage",
    "threshold": 80,
    "action": "greater_than"
  }
}
```

### 9. Maintenance Windows
Schedule tasks during specific maintenance windows to minimize impact.

Example:
```json
{
  "id": "system_updates",
  "schedule": {
    "type": "cron",
    "expression": "0 2 * * 6"  // Runs at 2 AM every Saturday
  },
  "maintenance_window": {
    "start": "02:00",
    "end": "06:00"
  }
}
```

### 10. Adaptive Scheduling
Adjust scheduling frequency based on workload or demand.

Example:
```json
{
  "id": "monitoring_task",
  "schedule": {
    "type": "adaptive",
    "base_interval": 300,  // 5 minutes
    "min_interval": 60,    // 1 minute minimum
    "max_interval": 3600   // 1 hour maximum
  },
  "adaptation_criteria": {
    "metric": "queue_length",
    "increase_threshold": 100,
    "decrease_threshold": 10
  }
}
```

## Best Practices

1. **Timezone Awareness**: Always specify timezones for scheduled tasks to avoid confusion across different regions.

2. **Resource Allocation**: Consider system resources when scheduling multiple tasks simultaneously to prevent performance issues.

3. **Monitoring**: Implement monitoring for scheduled tasks to detect failures or delays promptly.

4. **Testing**: Test scheduling rules in a non-production environment before applying them to critical systems.

5. **Documentation**: Clearly document the purpose and expected behavior of each scheduled task.

6. **Graceful Degradation**: Design tasks to handle failures gracefully and avoid cascading failures in dependent systems.

## Conclusion

These patterns provide a foundation for implementing robust and efficient recurring task scheduling in your systems. Choose the appropriate pattern based on your specific requirements and always consider the impact on system resources and overall reliability.