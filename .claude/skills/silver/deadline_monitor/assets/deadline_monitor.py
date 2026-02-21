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