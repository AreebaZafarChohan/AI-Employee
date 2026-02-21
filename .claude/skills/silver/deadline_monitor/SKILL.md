# Deadline Monitor Skill

## Overview

**Skill Name:** `deadline_monitor`
**Domain:** `silver`
**Purpose:** Track task deadlines and send notifications or escalate if overdue to ensure timely completion of critical tasks and maintain project momentum.

**Core Capabilities:**
- Real-time monitoring of task deadlines across multiple systems
- Configurable notification schedules with multiple channels
- Automated escalation procedures for missed deadlines
- Timezone-aware scheduling and deadline calculations
- Integration with popular project management and communication tools

**When to Use:**
- Managing projects with tight deadlines
- Coordinating distributed teams across timezones
- Ensuring accountability for critical deliverables
- Automating routine deadline tracking tasks
- Maintaining visibility into project timelines

**When NOT to Use:**
- Projects with flexible or undefined timelines
- Personal tasks without formal deadline tracking
- Situations where manual tracking is more efficient
- Tasks without clear ownership or responsibility
- Emergency situations requiring immediate human intervention

## Impact Analysis

### Security Impact: LOW
- May access task and user information (requires appropriate permissions)
- Notification logs could contain sensitive project information
- Need to ensure privacy of deadline and task details
- Communication channel security considerations

### System Impact: MEDIUM
- Integration with task management systems required
- Regular polling or webhook processing for deadline updates
- Need for reliable scheduling and notification infrastructure
- Potential for cascading effects if monitoring system fails

### Operational Impact: HIGH
- Critical tasks may be delayed if notifications fail
- Incorrect escalation could cause confusion or panic
- Requires ongoing maintenance and monitoring
- Team adoption depends on reliability of notifications

### Business Impact: HIGH
- Improved project delivery predictability
- Reduced risk of missed deadlines
- Enhanced team accountability and visibility
- Potential cost savings from avoided delays

## Environment Variables

### Required Variables
```
DEADLINE_MONITOR_CHANNEL=slack  # Options: slack, email, teams, webhook
NOTIFICATION_SCHEDULE="*/15 * * * *"  # Cron schedule for checking deadlines
TASK_MANAGEMENT_API_URL=https://api.company.com/tasks
NOTIFICATION_LOG_PATH=/var/log/deadline_notifications.log
```

### Optional Variables
```
DEADLINE_DEBUG_MODE=false
DEADLINE_TIMEZONE=UTC
NOTIFICATION_LEAD_TIME=24h  # Send reminder this far in advance
ESCALATION_AFTER=48h        # Escalate if overdue by this amount
CRITICAL_TASK_TAGS=critical,urgent
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
EMAIL_SMTP_HOST=smtp.company.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=noreply@company.com
```

## Network and Authentication Implications

### Authentication Requirements
- OAuth 2.0 tokens for accessing task management APIs
- Service account credentials for automated monitoring
- JWT tokens for secure communication with notification systems
- Multi-factor authentication for administrative access

### Network Considerations
- Reliable connectivity to task management systems
- Latency considerations for real-time deadline monitoring
- Bandwidth for frequent API calls to update task status
- Fallback mechanisms when external systems are unavailable

### Integration Points
- Task management platforms (Jira, Asana, Trello)
- Communication platforms (Slack, Microsoft Teams, Discord)
- Email systems (SMTP servers)
- Calendar systems (Google Calendar, Outlook)

## Blueprints

### Blueprint 1: Deadline Monitoring Script (Bash)
```bash
#!/usr/bin/env bash
# deadline-monitor.sh
# Monitors task deadlines and sends notifications for upcoming or overdue tasks

set -euo pipefail

# Configuration
CHANNEL="${DEADLINE_MONITOR_CHANNEL:-slack}"
TASK_API="${TASK_MANAGEMENT_API_URL:-https://api.company.com/tasks}"
LOG_PATH="${NOTIFICATION_LOG_PATH:-/tmp/deadline_notifications.log}"
DEBUG="${DEADLINE_DEBUG_MODE:-false}"
TIMEZONE="${DEADLINE_TIMEZONE:-UTC}"
LEAD_TIME="${NOTIFICATION_LEAD_TIME:-24h}"
ESCALATION_DELAY="${ESCALATION_AFTER:-48h}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_notification() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local user=$(whoami)
    
    echo "{\"timestamp\":\"${timestamp}\",\"level\":\"${level}\",\"user\":\"${user}\",\"message\":\"${message}\"}" >> "${LOG_PATH}"
}

# Convert ISO date to epoch for comparison
iso_to_epoch() {
    local iso_date="$1"
    # Remove timezone info and convert to epoch
    date -d "${iso_date%.*}" +%s 2>/dev/null || date -jf "%Y-%m-%dT%H:%M:%S" "${iso_date%.*}" +%s
}

# Fetch tasks with deadlines
fetch_deadline_tasks() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Fetching tasks from $TASK_API"
    fi
    
    # In a real implementation, this would call the API
    # curl -H "Authorization: Bearer $TOKEN" "$TASK_API?status=active"
    
    # Mock data for demonstration
    cat << 'EOF'
[
  {
    "id": "task1",
    "title": "Complete project proposal",
    "description": "Draft and submit the quarterly project proposal",
    "assignee": "alice.johnson",
    "deadline": "2026-02-08T10:00:00Z",
    "priority": "high",
    "tags": ["proposal", "critical"]
  },
  {
    "id": "task2",
    "title": "Code review",
    "description": "Review PR #1234 for the login feature",
    "assignee": "bob.smith",
    "deadline": "2026-02-06T15:00:00Z",
    "priority": "medium",
    "tags": ["review", "frontend"]
  },
  {
    "id": "task3",
    "title": "Client presentation",
    "description": "Prepare slides for client meeting",
    "assignee": "carol.davis",
    "deadline": "2026-02-05T09:00:00Z",
    "priority": "high",
    "tags": ["presentation", "client-facing"]
  }
]
EOF
}

# Send notification based on configured channel
send_notification() {
    local task_id="$1"
    local task_title="$2"
    local assignee="$3"
    local deadline="$4"
    local status="$5"  # upcoming, overdue, critical_overdue
    local message="$6"
    
    case "$CHANNEL" in
        "slack")
            # In a real implementation, this would send to Slack webhook
            # curl -X POST -H 'Content-Type: application/json' \
            #   -d "{\"text\":\"$message\"}" "$SLACK_WEBHOOK_URL"
            echo "📤 Slack: $message"
            ;;
        "email")
            # In a real implementation, this would send an email
            # mail -s "Task Deadline Alert" "$assignee@company.com" <<< "$message"
            echo "📧 Email: $message"
            ;;
        "teams")
            # In a real implementation, this would send to Teams webhook
            echo "💬 Teams: $message"
            ;;
        "webhook")
            # In a real implementation, this would send to custom webhook
            echo "🔗 Webhook: $message"
            ;;
        *)
            echo "❌ Unknown notification channel: $CHANNEL"
            return 1
            ;;
    esac
    
    log_notification "INFO" "Notification sent for task $task_id ($status): $message"
}

# Calculate time difference in hours
time_diff_hours() {
    local start="$1"
    local end="$2"
    local start_epoch=$(iso_to_epoch "$start")
    local end_epoch=$(iso_to_epoch "$end")
    echo $(( (end_epoch - start_epoch) / 3600 ))
}

# Process tasks and send notifications
process_tasks() {
    local tasks_json="$1"
    local current_time_iso=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local current_epoch=$(iso_to_epoch "$current_time_iso")
    
    local num_tasks=$(echo "$tasks_json" | jq 'length')
    
    for ((i=0; i<num_tasks; i++)); do
        local task=$(echo "$tasks_json" | jq ".[$i]")
        local task_id=$(echo "$task" | jq -r '.id')
        local task_title=$(echo "$task" | jq -r '.title')
        local assignee=$(echo "$task" | jq -r '.assignee')
        local deadline=$(echo "$task" | jq -r '.deadline')
        local priority=$(echo "$task" | jq -r '.priority')
        local tags=$(echo "$task" | jq -r '.tags | join(", ")')
        
        local deadline_epoch=$(iso_to_epoch "$deadline")
        local hours_until_deadline=$(( (deadline_epoch - current_epoch) / 3600 ))
        
        if [[ "$DEBUG" == "true" ]]; then
            echo "Debug: Task $task_id - Hours until deadline: $hours_until_deadline"
        fi
        
        # Determine notification type based on time until deadline
        if [[ $hours_until_deadline -lt 0 ]]; then
            # Task is overdue
            local overdue_hours=$(( -1 * hours_until_deadline ))
            local message="🚨 OVERDUE TASK ALERT 🚨\nTask: $task_title (ID: $task_id)\nAssignee: $assignee\nWas due: $deadline\nOverdue by: $overdue_hours hours\nPriority: $priority\nTags: $tags"
            
            if [[ $overdue_hours -ge 48 ]]; then
                # Critical overdue - escalate
                send_notification "$task_id" "$task_title" "$assignee" "$deadline" "critical_overdue" "$message"
            else
                # Regular overdue
                send_notification "$task_id" "$task_title" "$assignee" "$deadline" "overdue" "$message"
            fi
        elif [[ $hours_until_deadline -le 24 ]]; then
            # Task due within 24 hours
            local message="⏰ UPCOMING DEADLINE ⏰\nTask: $task_title (ID: $task_id)\nAssignee: $assignee\nDue: $deadline\nHours remaining: $hours_until_deadline\nPriority: $priority\nTags: $tags"
            send_notification "$task_id" "$task_title" "$assignee" "$deadline" "upcoming" "$message"
        fi
    done
}

# Main execution
main() {
    echo "👀 Starting deadline monitoring process..."
    echo "Channel: $CHANNEL"
    echo "Timezone: $TIMEZONE"
    
    # Fetch tasks with deadlines
    local tasks_data
    tasks_data=$(fetch_deadline_tasks)
    
    # Process tasks and send notifications
    process_tasks "$tasks_data"
    
    echo "✅ Deadline monitoring process completed!"
}

main "$@"
```

### Blueprint 2: Deadline Monitoring Engine (Python)
```python
#!/usr/bin/env python3
"""
deadline_monitor.py
Track task deadlines and send notifications or escalate if overdue
"""

import os
import json
import requests
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import pytz
from tzlocal import get_localzone


@dataclass
class Task:
    """Represents a task with a deadline."""
    id: str
    title: str
    description: str
    assignee: str
    deadline: datetime
    priority: str  # 'low', 'medium', 'high', 'critical'
    tags: List[str]
    project: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Notification:
    """Represents a notification sent for a task."""
    task_id: str
    notification_type: str  # 'reminder', 'overdue', 'escalation'
    recipient: str
    sent_at: datetime
    message: str
    channel: str


class DeadlineMonitor:
    """
    Monitors task deadlines and sends notifications or escalations when needed.
    
    This class handles tracking deadlines, sending reminders, and escalating
    overdue tasks according to configured rules.
    """
    
    def __init__(self):
        """Initialize the deadline monitor with configuration."""
        self.notification_channel = os.getenv('DEADLINE_MONITOR_CHANNEL', 'slack')
        self.timezone = pytz.timezone(os.getenv('DEADLINE_TIMEZONE', 'UTC'))
        self.reminder_lead_time = self._parse_duration(os.getenv('NOTIFICATION_LEAD_TIME', '24h'))
        self.escalation_after = self._parse_duration(os.getenv('ESCALATION_AFTER', '48h'))
        self.critical_tags = set(tag.strip() for tag in os.getenv('CRITICAL_TASK_TAGS', 'critical,urgent').split(','))
        
        # Configure logging
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for notification tracking."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create file handler for notification log
        log_path = os.getenv('NOTIFICATION_LOG_PATH', '/tmp/deadline_notifications.log')
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _parse_duration(self, duration_str: str) -> timedelta:
        """
        Parse duration string like '24h', '3d', '1w' into timedelta.
        
        Args:
            duration_str: Duration string (e.g., '24h', '3d', '1w')
            
        Returns:
            timedelta object representing the duration
        """
        if duration_str.endswith('h'):
            return timedelta(hours=int(duration_str[:-1]))
        elif duration_str.endswith('d'):
            return timedelta(days=int(duration_str[:-1]))
        elif duration_str.endswith('w'):
            return timedelta(weeks=int(duration_str[:-1]))
        elif duration_str.endswith('m'):
            return timedelta(minutes=int(duration_str[:-1]))
        else:
            # Default to hours if no unit specified
            return timedelta(hours=int(duration_str))
    
    def fetch_tasks_with_deadlines(self) -> List[Task]:
        """
        Fetch tasks with deadlines from the configured API.
        
        Returns:
            List of Task objects
        """
        # In a real implementation, this would fetch from an API
        # api_url = os.getenv('TASK_MANAGEMENT_API_URL', 'https://api.company.com/tasks')
        # headers = {'Authorization': f'Bearer {get_token()}'}
        # params = {'status': 'active', 'has_deadline': 'true'}
        # response = requests.get(api_url, headers=headers, params=params)
        # tasks_data = response.json()
        
        # For this example, we'll return mock data
        now = datetime.now(self.timezone)
        mock_tasks = [
            {
                "id": "task1",
                "title": "Complete project proposal",
                "description": "Draft and submit the quarterly project proposal",
                "assignee": "alice.johnson",
                "deadline": (now + timedelta(hours=12)).isoformat(),
                "priority": "high",
                "tags": ["proposal", "critical"]
            },
            {
                "id": "task2",
                "title": "Code review",
                "description": "Review PR #1234 for the login feature",
                "assignee": "bob.smith",
                "deadline": (now - timedelta(hours=2)).isoformat(),  # Overdue
                "priority": "medium",
                "tags": ["review", "frontend"]
            },
            {
                "id": "task3",
                "title": "Client presentation",
                "description": "Prepare slides for client meeting",
                "assignee": "carol.davis",
                "deadline": (now + timedelta(days=2)).isoformat(),
                "priority": "high",
                "tags": ["presentation", "client-facing"]
            },
            {
                "id": "task4",
                "title": "Security audit",
                "description": "Perform quarterly security audit",
                "assignee": "dave.wilson",
                "deadline": (now - timedelta(days=3)).isoformat(),  # Critically overdue
                "priority": "critical",
                "tags": ["security", "audit"]
            }
        ]
        
        tasks = []
        for task_data in mock_tasks:
            task = Task(
                id=task_data["id"],
                title=task_data["title"],
                description=task_data["description"],
                assignee=task_data["assignee"],
                deadline=datetime.fromisoformat(task_data["deadline"].replace('Z', '+00:00')),
                priority=task_data["priority"],
                tags=task_data["tags"]
            )
            tasks.append(task)
        
        return tasks
    
    def is_task_critical(self, task: Task) -> bool:
        """
        Determine if a task is critical based on tags or priority.
        
        Args:
            task: The task to evaluate
            
        Returns:
            True if the task is critical, False otherwise
        """
        return task.priority == 'critical' or bool(self.critical_tags.intersection(task.tags))
    
    def get_notification_recipients(self, task: Task) -> List[str]:
        """
        Determine notification recipients for a task.
        
        Args:
            task: The task requiring notification
            
        Returns:
            List of recipient identifiers (emails, usernames, etc.)
        """
        recipients = [task.assignee]
        
        # Add project manager or supervisor for critical tasks
        if self.is_task_critical(task):
            # In a real implementation, this would look up the project manager
            # recipients.append(get_project_manager(task.project))
            pass
        
        # Add team lead for overdue tasks
        if datetime.now(self.timezone) > task.deadline:
            # In a real implementation, this would look up the team lead
            # recipients.append(get_team_lead(task.assignee))
            pass
        
        return recipients
    
    def format_notification_message(self, task: Task, notification_type: str) -> str:
        """
        Format a notification message for a task.
        
        Args:
            task: The task to notify about
            notification_type: Type of notification ('reminder', 'overdue', 'escalation')
            
        Returns:
            Formatted notification message
        """
        deadline_str = task.deadline.strftime("%Y-%m-%d %H:%M %Z")
        now = datetime.now(self.timezone)
        
        if notification_type == 'reminder':
            hours_left = int((task.deadline - now).total_seconds() // 3600)
            return (
                f"⏰ UPCOMING DEADLINE ⏰\n"
                f"Task: {task.title} (ID: {task.id})\n"
                f"Assignee: {task.assignee}\n"
                f"Due: {deadline_str}\n"
                f"Hours remaining: {hours_left}\n"
                f"Priority: {task.priority}\n"
                f"Tags: {', '.join(task.tags)}"
            )
        elif notification_type == 'overdue':
            overdue_hours = int((now - task.deadline).total_seconds() // 3600)
            return (
                f"🚨 OVERDUE TASK ALERT 🚨\n"
                f"Task: {task.title} (ID: {task.id})\n"
                f"Assignee: {task.assignee}\n"
                f"Was due: {deadline_str}\n"
                f"Overdue by: {overdue_hours} hours\n"
                f"Priority: {task.priority}\n"
                f"Tags: {', '.join(task.tags)}"
            )
        elif notification_type == 'escalation':
            overdue_hours = int((now - task.deadline).total_seconds() // 3600)
            return (
                f"🚨 CRITICAL OVERDUE TASK - ESCALATION REQUIRED 🚨\n"
                f"Task: {task.title} (ID: {task.id})\n"
                f"Assignee: {task.assignee}\n"
                f"Was due: {deadline_str}\n"
                f"Overdue by: {overdue_hours} hours\n"
                f"Priority: {task.priority}\n"
                f"Tags: {', '.join(task.tags)}\n"
                f"Immediate action required!"
            )
        else:
            return f"Task Update: {task.title} (ID: {task.id})"
    
    def send_notification(self, task: Task, notification_type: str, recipient: str) -> bool:
        """
        Send a notification about a task to a recipient.
        
        Args:
            task: The task to notify about
            notification_type: Type of notification
            recipient: Recipient identifier
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        message = self.format_notification_message(task, notification_type)
        
        try:
            if self.notification_channel == 'slack':
                return self._send_slack_notification(message, recipient)
            elif self.notification_channel == 'email':
                return self._send_email_notification(message, recipient)
            elif self.notification_channel == 'teams':
                return self._send_teams_notification(message, recipient)
            elif self.notification_channel == 'webhook':
                return self._send_webhook_notification(message, recipient)
            else:
                self.logger.error(f"Unknown notification channel: {self.notification_channel}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to send notification for task {task.id}: {str(e)}")
            return False
    
    def _send_slack_notification(self, message: str, recipient: str) -> bool:
        """Send notification via Slack."""
        # In a real implementation:
        # webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        # payload = {"text": message}
        # response = requests.post(webhook_url, json=payload)
        # return response.status_code == 200
        
        # For demo purposes:
        print(f"📤 Slack: {message}")
        return True
    
    def _send_email_notification(self, message: str, recipient: str) -> bool:
        """Send notification via email."""
        # In a real implementation:
        smtp_host = os.getenv('EMAIL_SMTP_HOST', 'localhost')
        smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        email_from = os.getenv('EMAIL_FROM', 'noreply@example.com')
        
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = f"{recipient}@company.com"
        msg['Subject'] = f"Task Deadline Alert: {message.split(chr(10))[0].replace('⏰ ', '').replace('🚨 ', '')}"
        
        msg.attach(MIMEText(message.replace('\n', '<br>'), 'html'))
        
        try:
            # For demo purposes, just log instead of sending
            self.logger.info(f"Email prepared for {recipient}@company.com: {message.split(chr(10))[0]}")
            # Uncomment for real implementation:
            # server = smtplib.SMTP(smtp_host, smtp_port)
            # server.starttls()
            # server.login(username, password)
            # server.send_message(msg)
            # server.quit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def _send_teams_notification(self, message: str, recipient: str) -> bool:
        """Send notification via Microsoft Teams."""
        # In a real implementation, this would use Teams webhook
        print(f"💬 Teams: {message}")
        return True
    
    def _send_webhook_notification(self, message: str, recipient: str) -> bool:
        """Send notification via custom webhook."""
        # In a real implementation, this would call a custom webhook
        print(f"🔗 Webhook: {message}")
        return True
    
    def process_task_notifications(self, task: Task) -> List[Notification]:
        """
        Process notifications for a single task based on its deadline.
        
        Args:
            task: The task to process
            
        Returns:
            List of notifications sent
        """
        now = datetime.now(self.timezone)
        notifications = []
        
        # Calculate time differences
        time_until_deadline = task.deadline - now
        time_since_deadline = now - task.deadline
        
        # Determine what notifications to send
        notification_actions = []
        
        # Check for upcoming deadline reminder
        if timedelta(0) < time_until_deadline <= self.reminder_lead_time:
            notification_actions.append(('reminder', 'Reminder before deadline'))
        
        # Check for overdue task
        elif time_since_deadline > timedelta(0):
            if time_since_deadline <= self.escalation_after:
                notification_actions.append(('overdue', 'Overdue task notification'))
            else:
                notification_actions.append(('escalation', 'Escalation for critically overdue task'))
        
        # Send notifications for each action
        for notification_type, description in notification_actions:
            recipients = self.get_notification_recipients(task)
            
            for recipient in recipients:
                success = self.send_notification(task, notification_type, recipient)
                
                if success:
                    notification = Notification(
                        task_id=task.id,
                        notification_type=notification_type,
                        recipient=recipient,
                        sent_at=now,
                        message=self.format_notification_message(task, notification_type),
                        channel=self.notification_channel
                    )
                    notifications.append(notification)
                    
                    self.logger.info(f"Notification sent for task {task.id} to {recipient} via {self.notification_channel}: {description}")
                else:
                    self.logger.warning(f"Failed to send notification for task {task.id} to {recipient}")
        
        return notifications
    
    def run_monitoring_cycle(self) -> List[Notification]:
        """
        Run a complete monitoring cycle: fetch tasks and send appropriate notifications.
        
        Returns:
            List of notifications sent during this cycle
        """
        self.logger.info("Starting deadline monitoring cycle")
        
        # Fetch tasks with deadlines
        tasks = self.fetch_tasks_with_deadlines()
        
        if not tasks:
            self.logger.info("No tasks with deadlines found")
            return []
        
        all_notifications = []
        
        # Process each task
        for task in tasks:
            notifications = self.process_task_notifications(task)
            all_notifications.extend(notifications)
        
        # Log summary
        summary = {
            'total_tasks': len(tasks),
            'notifications_sent': len(all_notifications),
            'breakdown': {
                'reminder': len([n for n in all_notifications if n.notification_type == 'reminder']),
                'overdue': len([n for n in all_notifications if n.notification_type == 'overdue']),
                'escalation': len([n for n in all_notifications if n.notification_type == 'escalation'])
            }
        }
        
        self.logger.info(f"Monitoring cycle completed: {summary}")
        
        return all_notifications


def main():
    """Example usage of the DeadlineMonitor."""
    import sys
    
    # Initialize monitor
    monitor = DeadlineMonitor()
    
    # Run monitoring cycle
    notifications = monitor.run_monitoring_cycle()
    
    # Print summary
    print(f"\n📊 Monitoring Cycle Summary:")
    print(f"Total tasks monitored: {len(set(n.task_id for n in notifications))}")
    print(f"Notifications sent: {len(notifications)}")
    
    breakdown = {
        'reminder': len([n for n in notifications if n.notification_type == 'reminder']),
        'overdue': len([n for n in notifications if n.notification_type == 'overdue']),
        'escalation': len([n for n in notifications if n.notification_type == 'escalation'])
    }
    
    print(f"  - Reminders: {breakdown['reminder']}")
    print(f"  - Overdue alerts: {breakdown['overdue']}")
    print(f"  - Escalations: {breakdown['escalation']}")


if __name__ == "__main__":
    main()
```

### Blueprint 3: Escalation Rules Configuration (JSON)
```json
{
  "version": "1.0.0",
  "last_updated": "2026-02-06T00:00:00Z",
  "monitoring_rules": {
    "default_reminder_schedule": {
      "before_deadline": "24h",
      "repeat_interval": "6h",
      "max_reminders": 3
    },
    "escalation_tiers": [
      {
        "tier": 1,
        "condition": "deadline_passed",
        "delay": "1h",
        "recipients": ["assignee"],
        "message_template": "REMINDER_OVERDUE"
      },
      {
        "tier": 2,
        "condition": "overdue_for", 
        "delay": "24h",
        "recipients": ["assignee", "manager"],
        "message_template": "ESCALATION_LEVEL_1"
      },
      {
        "tier": 3,
        "condition": "critically_overdue",
        "delay": "72h",
        "recipients": ["assignee", "manager", "director"],
        "message_template": "ESCALATION_LEVEL_2"
      }
    ],
    "critical_conditions": [
      {
        "field": "priority",
        "operator": "==",
        "value": "critical",
        "escalation_delay": "12h"
      },
      {
        "field": "tags",
        "operator": "contains",
        "value": "security",
        "escalation_delay": "6h"
      },
      {
        "field": "project",
        "operator": "==",
        "value": "customer-facing",
        "escalation_delay": "18h"
      }
    ],
    "notification_templates": {
      "REMINDER_UPCOMING": {
        "subject": "Upcoming Task Deadline: {{task_title}}",
        "body": "This is a reminder that task '{{task_title}}' (ID: {{task_id}}) is due soon.\n\nDue Date: {{deadline}}\nAssignee: {{assignee}}\nPriority: {{priority}}\n\nPlease ensure timely completion."
      },
      "REMINDER_OVERDUE": {
        "subject": "OVERDUE TASK: {{task_title}}",
        "body": "ALERT: Task '{{task_title}}' (ID: {{task_id}}) is now overdue.\n\nOriginal Due Date: {{deadline}}\nAssignee: {{assignee}}\nPriority: {{priority}}\n\nImmediate action required!"
      },
      "ESCALATION_LEVEL_1": {
        "subject": "ESCALATED: Overdue Task {{task_title}}",
        "body": "ESCALATION: Task '{{task_title}}' (ID: {{task_id}}) remains overdue.\n\nOriginal Due Date: {{deadline}}\nDays Overdue: {{days_overdue}}\nAssignee: {{assignee}}\nPriority: {{priority}}\n\nManagement attention required."
      },
      "ESCALATION_LEVEL_2": {
        "subject": "CRITICAL ESCALATION: Severely Overdue Task {{task_title}}",
        "body": "CRITICAL ESCALATION: Task '{{task_title}}' (ID: {{task_id}}) is severely overdue.\n\nOriginal Due Date: {{deadline}}\nDays Overdue: {{days_overdue}}\nAssignee: {{assignee}}\nPriority: {{priority}}\n\nImmediate executive attention required!"
      }
    },
    "channel_preferences": {
      "default": "slack",
      "by_priority": {
        "critical": ["email", "sms"],
        "high": ["slack", "email"],
        "medium": "slack",
        "low": "digest_email"
      },
      "by_recipient_role": {
        "assignee": "direct_channel",
        "manager": "email",
        "director": "email_summary"
      }
    }
  },
  "metadata": {
    "created_by": "Deadline Monitoring System",
    "reviewed_by": "Operations Team",
    "next_review_date": "2026-05-06T00:00:00Z"
  }
}
```

## Pre-Deployment Validation Checklist

### Configuration Validation
- [ ] Verify DEADLINE_MONITOR_CHANNEL is set to a valid option
- [ ] Confirm TASK_MANAGEMENT_API_URL is accessible
- [ ] Check NOTIFICATION_LOG_PATH directory is writable
- [ ] Validate all required environment variables are set
- [ ] Test API connectivity to task management system

### Security Validation
- [ ] Ensure API tokens have appropriate scopes
- [ ] Verify authentication mechanisms for API calls
- [ ] Confirm sensitive data is not logged inappropriately
- [ ] Test access controls for notification data
- [ ] Validate encryption of communication channels

### Functional Validation
- [ ] Test notification sending with sample tasks
- [ ] Verify all notification channels work correctly
- [ ] Confirm timezone handling works as expected
- [ ] Test escalation procedures with overdue tasks
- [ ] Validate critical task identification works

### Performance Validation
- [ ] Measure monitoring cycle performance with realistic data
- [ ] Test notification sending rate limits
- [ ] Verify system handles peak notification loads
- [ ] Confirm monitoring doesn't impact task management systems
- [ ] Test failover mechanisms if applicable

### Operational Validation
- [ ] Verify monitoring and alerting for system failures
- [ ] Test backup and recovery procedures
- [ ] Confirm logging provides sufficient information for debugging
- [ ] Validate that notification scheduling works correctly
- [ ] Test rollback procedures for configuration changes

## Anti-Patterns

### Anti-Pattern 1: Missing Notifications
**Problem:** Notifications fail silently or are not sent when deadlines are approached or passed.
**Risk:** Missed deadlines without awareness, leading to project delays.
**Solution:** Implement comprehensive error handling and monitoring for notification failures.

**Wrong:**
```python
# Bad: No error handling for notification failures
def send_reminder(task):
    # Send notification without checking success
    send_slack_message(task.assignee, f"Task {task.title} is due soon!")
```

**Correct:**
```python
# Good: Comprehensive error handling and monitoring
def send_reminder(task):
    try:
        success = send_slack_message(task.assignee, f"Task {task.title} is due soon!")
        if not success:
            log_error(f"Failed to send reminder for task {task.id}")
            # Try alternate channel
            send_email(task.assignee, f"Task {task.title} is due soon!")
    except Exception as e:
        log_error(f"Error sending reminder for task {task.id}: {str(e)}")
        # Implement fallback notification method
        schedule_retry_notification(task, delay_minutes=30)
```

### Anti-Pattern 2: Ignoring Timezones
**Problem:** Deadline calculations don't account for different timezones of team members.
**Risk:** Notifications sent at inappropriate times or deadlines calculated incorrectly.
**Solution:** Implement timezone-aware scheduling and deadline calculations.

**Wrong:**
```python
# Bad: No timezone consideration
def is_overdue(task):
    return datetime.now() > task.deadline  # Assumes same timezone
```

**Correct:**
```python
# Good: Timezone-aware comparison
def is_overdue(task):
    local_tz = pytz.timezone(get_user_timezone(task.assignee))
    local_now = datetime.now(local_tz)
    task_deadline_local = task.deadline.astimezone(local_tz)
    return local_now > task_deadline_local
```

### Anti-Pattern 3: Hardcoded Escalation Paths
**Problem:** Escalation procedures are hardcoded rather than configurable.
**Risk:** Inflexible system that can't adapt to different organizational structures.
**Solution:** Implement configurable escalation rules with multiple tiers.

**Wrong:**
```python
# Bad: Hardcoded escalation
def escalate_task(task):
    if task.priority == "critical":
        notify_user("manager@company.com")
        notify_user("director@company.com")
    else:
        notify_user("manager@company.com")
```

**Correct:**
```python
# Good: Configurable escalation rules
def escalate_task(task):
    escalation_rules = load_escalation_rules()
    
    for tier in escalation_rules:
        if matches_condition(task, tier.condition):
            for recipient in tier.recipients:
                notify_user(resolve_recipient(task, recipient), 
                           format_message(tier.message_template, task))
```

### Anti-Pattern 4: No Rate Limiting
**Problem:** System sends excessive notifications, especially for overdue tasks checked frequently.
**Risk:** Notification fatigue, system resource exhaustion, potential API rate limit violations.
**Solution:** Implement rate limiting and deduplication for notifications.

**Wrong:**
```python
# Bad: No rate limiting
def check_overdue_tasks():
    overdue_tasks = get_overdue_tasks()
    for task in overdue_tasks:
        send_overdue_notification(task)  # Could spam every check
```

**Correct:**
```python
# Good: Rate limiting and deduplication
def check_overdue_tasks():
    overdue_tasks = get_overdue_tasks()
    for task in overdue_tasks:
        # Check if notification was recently sent
        if not was_recently_notified(task.id, "overdue", hours=2):
            send_overdue_notification(task)
            record_notification_sent(task.id, "overdue")
```

### Anti-Pattern 5: Single Point of Failure
**Problem:** Notification system relies on a single channel that might fail.
**Risk:** Critical deadline notifications are missed if the primary channel is down.
**Solution:** Implement redundant notification channels with fallback mechanisms.

**Wrong:**
```python
# Bad: Single notification channel
def notify_task_status(task, status):
    if status == "overdue":
        send_slack_message(task.assignee, f"Task {task.title} is overdue!")
```

**Correct:**
```python
# Good: Multiple channels with fallback
def notify_task_status(task, status):
    notification_channels = get_preferred_channels(task)
    
    success = False
    for channel in notification_channels:
        try:
            if channel == "slack":
                success = send_slack_message(task.assignee, get_message(status, task))
            elif channel == "email":
                success = send_email(task.assignee, get_subject(status, task), get_message(status, task))
            
            if success:
                break  # Stop once successful
        except Exception as e:
            log_error(f"Failed to send via {channel}: {str(e)}")
            continue  # Try next channel
    
    if not success:
        log_error(f"All notification channels failed for task {task.id}")
        # Implement emergency notification procedure
```