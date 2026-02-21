# Deadline Monitor Skill

**Domain:** `silver`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

This skill provides comprehensive deadline monitoring capabilities that track task deadlines and send notifications or escalate if overdue. It ensures timely completion of critical tasks and maintains project momentum through automated monitoring and alerting.

### Prerequisites
- Python 3.8+ (for Python components)
- Bash shell environment (for shell components)
- Access to task management APIs
- Appropriate authentication tokens for API access
- Notification channel access (Slack, email, etc.)

### Installation
1. Clone or copy the skill assets to your system
2. Ensure required environment variables are configured
3. Make scripts executable: `chmod +x *.sh`
4. Install Python dependencies if using the Python module

### Configuration
Set the required environment variables:
```bash
export DEADLINE_MONITOR_CHANNEL=slack  # Options: slack, email, teams, webhook
export NOTIFICATION_SCHEDULE="*/15 * * * *"  # Cron schedule for checking deadlines
export TASK_MANAGEMENT_API_URL=https://api.company.com/tasks
export NOTIFICATION_LOG_PATH=/var/log/deadline_notifications.log
```

## Core Components

### 1. Deadline Monitoring Script
The `deadline-monitor.sh` script provides command-line deadline monitoring functionality. It evaluates tasks based on deadlines and sends notifications through configured channels.

Usage:
```bash
./deadline-monitor.sh
```

### 2. Deadline Monitoring Engine
The `deadline_monitor.py` Python module offers programmatic access to advanced monitoring capabilities. It includes multiple notification channels, escalation procedures, and timezone-aware scheduling.

Usage:
```python
from deadline_monitor import DeadlineMonitor

monitor = DeadlineMonitor()
notifications = monitor.run_monitoring_cycle()
```

### 3. Escalation Rules Configuration
The `escalation-rules.json` file defines the rules and procedures for handling overdue tasks, including notification schedules and escalation tiers.

## Environment Variables

### Required Variables
- `DEADLINE_MONITOR_CHANNEL`: Notification channel to use (slack, email, teams, webhook)
- `NOTIFICATION_SCHEDULE`: Cron schedule for checking deadlines
- `TASK_MANAGEMENT_API_URL`: URL for task management API
- `NOTIFICATION_LOG_PATH`: Path for notification logs

### Optional Variables
- `DEADLINE_DEBUG_MODE`: Enable debug output (default: false)
- `DEADLINE_TIMEZONE`: Timezone for deadline calculations (default: UTC)
- `NOTIFICATION_LEAD_TIME`: Time before deadline to send reminder (default: 24h)
- `ESCALATION_AFTER`: Time after which to escalate overdue tasks (default: 48h)
- `CRITICAL_TASK_TAGS`: Comma-separated list of critical task tags (default: critical,urgent)
- `SLACK_WEBHOOK_URL`: Slack webhook URL for notifications
- `EMAIL_SMTP_HOST`: SMTP server host for email notifications
- `EMAIL_SMTP_PORT`: SMTP server port (default: 587)
- `EMAIL_FROM`: Sender email address

## Notification Channels

### Slack
Send notifications to Slack channels or users using webhook URLs.

### Email
Send notifications via email using SMTP configuration.

### Microsoft Teams
Send notifications to Teams channels using webhook URLs.

### Custom Webhook
Send notifications to any custom webhook endpoint.

## Escalation Procedures

The system implements a tiered escalation approach:

1. **Initial Reminder**: Sent when deadline approaches (configurable lead time)
2. **Overdue Notification**: Sent when deadline passes
3. **Escalation**: Sent after configurable time period for overdue tasks
4. **Critical Escalation**: Sent for severely overdue critical tasks

## Integration Examples

### Cron Job Integration
Add to crontab to run periodically:
```bash
# Check deadlines every 15 minutes
*/15 * * * * /path/to/deadline-monitor.sh
```

### CI/CD Pipeline Integration
Add to deployment pipeline to monitor deployment deadlines:
```bash
# After deployment, monitor for post-deployment tasks
python -c "from deadline_monitor import DeadlineMonitor; DeadlineMonitor().run_monitoring_cycle()"
```

## Best Practices

1. **Configure Appropriate Intervals**: Balance between timely notifications and system load
2. **Test Notification Channels**: Verify all configured channels work correctly
3. **Monitor System Performance**: Track resource usage and response times
4. **Review Escalation Rules**: Regularly update escalation procedures based on effectiveness
5. **Consider Time Zones**: Account for team members in different geographic locations
6. **Avoid Notification Fatigue**: Implement digest notifications for less critical items

## Troubleshooting

Refer to the `docs/gotchas.md` file for common issues and solutions.

For additional support, consult the integration patterns in `docs/patterns.md` and the impact checklist in `docs/impact-checklist.md`.