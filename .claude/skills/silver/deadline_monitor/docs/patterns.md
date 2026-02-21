# Deadline Monitor - Monitoring & Alerting Patterns

## Overview
This document describes common patterns for implementing deadline monitoring and alerting systems.

---

## Pattern 1: Time-Based Polling Monitor

### Use Case
Regularly check for upcoming and overdue deadlines at scheduled intervals.

### Implementation
```python
import schedule
import time
from datetime import datetime, timedelta

class TimeBasedMonitor:
    def __init__(self, check_interval_minutes=15):
        self.check_interval = check_interval_minutes
        self.monitor = DeadlineMonitor()
        
    def start_monitoring(self):
        # Schedule the monitoring function
        schedule.every(self.check_interval).minutes.do(self.check_deadlines)
        
        # Also run immediately
        self.check_deadlines()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def check_deadlines(self):
        """Check for upcoming and overdue deadlines."""
        try:
            notifications = self.monitor.run_monitoring_cycle()
            print(f"Checked deadlines, sent {len(notifications)} notifications")
        except Exception as e:
            print(f"Error during deadline check: {str(e)}")

# Usage
if __name__ == "__main__":
    monitor = TimeBasedMonitor(check_interval_minutes=10)
    monitor.start_monitoring()
```

### Benefits
- Simple to implement and understand
- Predictable resource usage
- Easy to configure check frequency

---

## Pattern 2: Event-Driven Monitor

### Use Case
Respond to deadline changes in real-time using webhooks or event streams.

### Implementation
```python
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)
monitor = DeadlineMonitor()

@app.route('/webhook/deadline-change', methods=['POST'])
def handle_deadline_change():
    """Handle incoming deadline change notifications."""
    try:
        task_data = request.json
        task = Task(
            id=task_data['id'],
            title=task_data['title'],
            deadline=datetime.fromisoformat(task_data['deadline']),
            assignee=task_data['assignee'],
            priority=task_data.get('priority', 'medium'),
            tags=task_data.get('tags', [])
        )
        
        # Process the specific task that changed
        notifications = monitor.process_task_notifications(task)
        
        return jsonify({
            "status": "processed",
            "notifications_sent": len(notifications)
        }), 200
    except Exception as e:
        print(f"Error processing deadline change: {str(e)}")
        return jsonify({"error": str(e)}), 500

def start_event_monitor():
    """Start the event-driven monitor in a separate thread."""
    app.run(host='0.0.0.0', port=5000, threaded=True)

# Alternative: Using a message queue
import pika
import json

def event_driven_queue_consumer():
    """Consume deadline change events from a message queue."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue='deadline_changes')
    
    def callback(ch, method, properties, body):
        task_data = json.loads(body)
        # Process the deadline change
        task = Task(
            id=task_data['id'],
            title=task_data['title'],
            deadline=datetime.fromisoformat(task_data['deadline']),
            assignee=task_data['assignee'],
            priority=task_data.get('priority', 'medium'),
            tags=task_data.get('tags', [])
        )
        
        monitor.process_task_notifications(task)
    
    channel.basic_consume(queue='deadline_changes', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
```

### Benefits
- Immediate response to deadline changes
- More efficient than constant polling
- Better for systems with low-frequency updates

---

## Pattern 3: Hybrid Monitor

### Use Case
Combine polling and event-driven approaches for comprehensive coverage.

### Implementation
```python
import threading
import time
from datetime import datetime, timedelta

class HybridMonitor:
    def __init__(self, polling_interval_minutes=30):
        self.polling_interval = polling_interval_minutes
        self.monitor = DeadlineMonitor()
        self.known_deadlines = {}  # Cache to track known deadlines
        self.lock = threading.Lock()
        
    def start_monitoring(self):
        """Start both polling and event processing."""
        # Start the polling thread
        polling_thread = threading.Thread(target=self.polling_worker)
        polling_thread.daemon = True
        polling_thread.start()
        
        # Start the event listener (could be webhook endpoint or queue consumer)
        event_thread = threading.Thread(target=self.event_listener)
        event_thread.daemon = True
        event_thread.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down hybrid monitor...")
    
    def polling_worker(self):
        """Regular polling to catch any missed events."""
        while True:
            try:
                self.catch_up_check()
                time.sleep(self.polling_interval * 60)  # Convert to seconds
            except Exception as e:
                print(f"Error in polling worker: {str(e)}")
    
    def catch_up_check(self):
        """Perform a comprehensive check to catch any missed deadlines."""
        with self.lock:
            all_tasks = self.monitor.fetch_tasks_with_deadlines()
            
            # Process each task to see if notifications are needed
            for task in all_tasks:
                # Update our cache
                self.known_deadlines[task.id] = task.deadline
                
                # Process notifications for this task
                self.monitor.process_task_notifications(task)
    
    def event_listener(self):
        """Listen for deadline change events."""
        # This could be a webhook endpoint or message queue consumer
        # For this example, we'll simulate receiving events
        import queue
        event_queue = queue.Queue()
        
        # Simulate adding events to queue
        # In real implementation, this would come from external system
        
        while True:
            try:
                # Wait for an event (with timeout to allow periodic checks)
                try:
                    task_data = event_queue.get(timeout=5)  # 5-second timeout
                    self.process_event(task_data)
                except queue.Empty:
                    # Timeout - continue loop
                    continue
            except Exception as e:
                print(f"Error in event listener: {str(e)}")
    
    def process_event(self, task_data):
        """Process a single deadline change event."""
        with self.lock:
            task = Task(
                id=task_data['id'],
                title=task_data['title'],
                deadline=datetime.fromisoformat(task_data['deadline']),
                assignee=task_data['assignee'],
                priority=task_data.get('priority', 'medium'),
                tags=task_data.get('tags', [])
            )
            
            # Process notifications for this specific task
            self.monitor.process_task_notifications(task)
            
            # Update our cache
            self.known_deadlines[task.id] = task.deadline
```

### Benefits
- Combines responsiveness of events with reliability of polling
- Catches any missed events through periodic checks
- Provides redundancy in case one method fails

---

## Pattern 4: Multi-Channel Notification System

### Use Case
Send notifications through multiple channels to ensure delivery.

### Implementation
```python
from abc import ABC, abstractmethod
import smtplib
from email.mime.text import MIMEText
import requests

class NotificationChannel(ABC):
    @abstractmethod
    def send(self, message: str, recipient: str) -> bool:
        pass

class SlackChannel(NotificationChannel):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, message: str, recipient: str) -> bool:
        payload = {
            "text": message,
            "channel": f"@{recipient}" if recipient.startswith('@') else recipient
        }
        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 200
        except Exception:
            return False

class EmailChannel(NotificationChannel):
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str, from_addr: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
    
    def send(self, message: str, recipient: str) -> bool:
        try:
            msg = MIMEText(message)
            msg['Subject'] = 'Task Deadline Alert'
            msg['From'] = self.from_addr
            msg['To'] = recipient
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception:
            return False

class MultiChannelNotifier:
    def __init__(self, channels: list[NotificationChannel]):
        self.channels = channels
    
    def send_notification(self, message: str, recipient: str, preferred_channels: list[str] = None) -> dict:
        """
        Send notification through multiple channels with fallback.
        
        Returns a dictionary with success status for each channel.
        """
        results = {}
        
        # If preferred channels specified, use them in order
        if preferred_channels:
            available_channels = [ch for ch in self.channels if ch.__class__.__name__.replace('Channel', '').lower() in preferred_channels]
        else:
            available_channels = self.channels
        
        for channel in available_channels:
            channel_name = channel.__class__.__name__.replace('Channel', '').lower()
            results[channel_name] = channel.send(message, recipient)
            
            # If successful, stop trying other channels (unless configured otherwise)
            if results[channel_name]:
                break
        
        return results

# Usage example
def setup_notifier():
    channels = [
        SlackChannel(os.getenv('SLACK_WEBHOOK_URL')),
        EmailChannel(
            os.getenv('EMAIL_SMTP_HOST'),
            int(os.getenv('EMAIL_SMTP_PORT', '587')),
            os.getenv('EMAIL_USERNAME'),
            os.getenv('EMAIL_PASSWORD'),
            os.getenv('EMAIL_FROM')
        )
    ]
    return MultiChannelNotifier(channels)
```

### Benefits
- Higher probability of notification delivery
- Allows preference for different channels based on urgency
- Provides fallback if primary channel fails

---

## Pattern 5: Intelligent Escalation System

### Use Case
Automatically escalate overdue tasks based on configurable rules.

### Implementation
```python
from datetime import datetime, timedelta
from enum import Enum

class EscalationLevel(Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    CRITICAL = 4

class EscalationRule:
    def __init__(self, level: EscalationLevel, delay: timedelta, recipients: list[str], message_template: str):
        self.level = level
        self.delay = delay
        self.recipients = recipients
        self.message_template = message_template

class EscalationManager:
    def __init__(self):
        self.rules = self._load_escalation_rules()
        self.sent_notifications = {}  # Track sent notifications to avoid duplicates
    
    def _load_escalation_rules(self) -> list[EscalationRule]:
        """Load escalation rules from configuration."""
        # In a real implementation, this would load from a config file or database
        return [
            EscalationRule(
                level=EscalationLevel.LEVEL_1,
                delay=timedelta(hours=1),
                recipients=["assignee"],
                message_template="REMINDER_OVERDUE"
            ),
            EscalationRule(
                level=EscalationLevel.LEVEL_2,
                delay=timedelta(hours=24),
                recipients=["assignee", "manager"],
                message_template="ESCALATION_LEVEL_1"
            ),
            EscalationRule(
                level=EscalationLevel.CRITICAL,
                delay=timedelta(hours=72),
                recipients=["assignee", "manager", "director"],
                message_template="ESCALATION_LEVEL_2"
            )
        ]
    
    def get_applicable_escalations(self, task: Task) -> list[EscalationRule]:
        """Get applicable escalation rules for a task."""
        now = datetime.now(task.deadline.tzinfo or pytz.UTC)
        time_overdue = now - task.deadline
        
        applicable = []
        for rule in self.rules:
            if time_overdue >= rule.delay:
                # Check if this escalation hasn't been sent yet
                escalation_key = f"{task.id}_{rule.level.name}"
                if escalation_key not in self.sent_notifications:
                    applicable.append(rule)
        
        return applicable
    
    def process_escalations(self, task: Task, notifier: MultiChannelNotifier):
        """Process applicable escalations for a task."""
        applicable_rules = self.get_applicable_escalations(task)
        
        for rule in applicable_rules:
            # Format the message using the template
            message = self.format_escalation_message(task, rule.message_template)
            
            # Send to all specified recipients
            for recipient in rule.recipients:
                # Resolve the actual recipient (e.g., get manager of assignee)
                actual_recipient = self.resolve_recipient(task, recipient)
                
                # Send notification
                results = notifier.send_notification(message, actual_recipient)
                
                # Log that this escalation was sent
                escalation_key = f"{task.id}_{rule.level.name}"
                self.sent_notifications[escalation_key] = {
                    'sent_at': datetime.now(),
                    'results': results
                }
                
                print(f"Sent {rule.level.name} escalation for task {task.id} to {actual_recipient}")
    
    def format_escalation_message(self, task: Task, template_name: str) -> str:
        """Format an escalation message using the specified template."""
        # In a real implementation, this would use a proper templating system
        templates = {
            "REMINDER_OVERDUE": f"🚨 OVERDUE TASK ALERT 🚨\nTask: {task.title} (ID: {task.id})\nAssignee: {task.assignee}\nWas due: {task.deadline}\nPriority: {task.priority}",
            "ESCALATION_LEVEL_1": f"🚨 ESCALATION: Overdue Task 🚨\nTask: {task.title} (ID: {task.id})\nAssignee: {task.assignee}\nWas due: {task.deadline}\nDays overdue: {(datetime.now() - task.deadline).days}\nPriority: {task.priority}",
            "ESCALATION_LEVEL_2": f"🚨 CRITICAL ESCALATION: Severely Overdue Task 🚨\nTask: {task.title} (ID: {task.id})\nAssignee: {task.assignee}\nWas due: {task.deadline}\nDays overdue: {(datetime.now() - task.deadline).days}\nPriority: {task.priority}\nImmediate executive attention required!"
        }
        
        return templates.get(template_name, f"Task {task.title} is overdue")
    
    def resolve_recipient(self, task: Task, recipient_spec: str) -> str:
        """Resolve a recipient specification to an actual contact."""
        if recipient_spec == "assignee":
            return task.assignee
        elif recipient_spec == "manager":
            # In a real implementation, this would look up the manager
            return f"manager_of_{task.assignee}"
        elif recipient_spec == "director":
            # In a real implementation, this would look up the director
            return "project_director"
        else:
            return recipient_spec  # Assume it's already a specific user
```

### Benefits
- Automated escalation reduces manual oversight
- Configurable rules adapt to different organizational needs
- Tracks escalations to prevent duplicate notifications

---

## Pattern 6: Digest Notification System

### Use Case
Batch multiple deadline notifications into periodic digests to reduce notification fatigue.

### Implementation
```python
from collections import defaultdict
from datetime import datetime, timedelta

class DigestNotificationSystem:
    def __init__(self, digest_frequency_hours=24):
        self.digest_frequency = timedelta(hours=digest_frequency_hours)
        self.pending_notifications = defaultdict(list)  # user -> list of notifications
        self.last_digest_sent = {}  # user -> datetime of last digest
    
    def add_notification(self, task: Task, notification_type: str, recipient: str):
        """Add a notification to the pending digest for a user."""
        message = self.format_digest_entry(task, notification_type)
        self.pending_notifications[recipient].append({
            'task_id': task.id,
            'message': message,
            'timestamp': datetime.now(),
            'type': notification_type
        })
    
    def format_digest_entry(self, task: Task, notification_type: str) -> str:
        """Format a single entry for the digest."""
        if notification_type == 'reminder':
            return f"⏰ REMINDER: {task.title} due {task.deadline.strftime('%Y-%m-%d %H:%M')}"
        elif notification_type == 'overdue':
            overdue_hours = int((datetime.now() - task.deadline).total_seconds() // 3600)
            return f"🚨 OVERDUE: {task.title} ({overdue_hours}h overdue)"
        else:
            return f"📋 {task.title} - {notification_type}"
    
    def should_send_digest(self, user: str) -> bool:
        """Check if it's time to send a digest to a user."""
        if user not in self.last_digest_sent:
            return True  # First time sending to this user
        
        time_since_last = datetime.now() - self.last_digest_sent[user]
        return time_since_last >= self.digest_frequency
    
    def prepare_digest(self, user: str) -> str:
        """Prepare the digest message for a user."""
        notifications = self.pending_notifications[user]
        
        if not notifications:
            return ""  # No notifications to send
        
        # Group notifications by type
        by_type = defaultdict(list)
        for note in notifications:
            by_type[note['type']].append(note)
        
        # Create digest header
        header = f"📅 Deadline Digest for {user}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Add sections for each notification type
        sections = []
        
        if 'overdue' in by_type:
            sections.append("🚨 OVERDUE TASKS 🚨\n" + 
                          "\n".join(f"• {note['message']}" for note in by_type['overdue']) + 
                          "\n")
        
        if 'reminder' in by_type:
            sections.append("⏰ UPCOMING DEADLINES ⏰\n" + 
                          "\n".join(f"• {note['message']}" for note in by_type['reminder']) + 
                          "\n")
        
        if 'other' in by_type:
            sections.append("📋 OTHER UPDATES 📋\n" + 
                          "\n".join(f"• {note['message']}" for note in by_type['other']) + 
                          "\n")
        
        return header + "\n".join(sections)
    
    def send_digest(self, user: str, notifier: MultiChannelNotifier) -> bool:
        """Send the digest to a user and clear pending notifications."""
        if not self.should_send_digest(user):
            return False
        
        digest_message = self.prepare_digest(user)
        
        if not digest_message.strip():
            # No notifications to send, update last sent time anyway
            self.last_digest_sent[user] = datetime.now()
            return True
        
        # Send via preferred channel (could be email for digests)
        results = notifier.send_notification(digest_message, user, preferred_channels=['email'])
        
        if any(results.values()):  # If any channel succeeded
            # Clear the user's pending notifications
            del self.pending_notifications[user]
            self.last_digest_sent[user] = datetime.now()
            return True
        
        return False
    
    def process_all_digests(self, notifier: MultiChannelNotifier):
        """Process and send digests for all users who need them."""
        users_to_notify = [user for user in self.pending_notifications.keys() 
                          if self.should_send_digest(user)]
        
        sent_count = 0
        for user in users_to_notify:
            if self.send_digest(user, notifier):
                sent_count += 1
        
        return sent_count
```

### Benefits
- Reduces notification fatigue by batching updates
- Provides comprehensive view of all deadlines at once
- More efficient for users managing multiple tasks

---

## Pattern 7: Critical Path Monitoring

### Use Case
Identify and prioritize monitoring for tasks that are on the critical path of projects.

### Implementation
```python
from dataclasses import dataclass
from typing import Set

@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""
    predecessor: str  # task ID
    successor: str    # task ID
    dependency_type: str = "finish_to_start"  # finish_to_start, start_to_start, etc.

class CriticalPathMonitor:
    def __init__(self):
        self.dependencies = {}  # task_id -> list of TaskDependency
        self.critical_tasks_cache = set()
        self.cache_timestamp = None
    
    def load_dependencies(self, project_id: str) -> dict:
        """Load task dependencies for a project."""
        # In a real implementation, this would fetch from a project management system
        # For this example, we'll return mock data
        return {
            "task1": [TaskDependency("task0", "task1")],
            "task2": [TaskDependency("task1", "task2")],
            "task3": [TaskDependency("task1", "task3")],
            "task4": [TaskDependency("task2", "task4"), TaskDependency("task3", "task4")]
        }
    
    def calculate_critical_path(self, project_id: str) -> Set[str]:
        """
        Calculate the critical path for a project using the Critical Path Method (CPM).
        
        Returns a set of task IDs that are on the critical path.
        """
        dependencies = self.load_dependencies(project_id)
        
        # For simplicity, we'll implement a basic version
        # In practice, you'd implement full CPM with forward and backward passes
        
        # Identify tasks with no predecessors (start tasks)
        all_tasks = set(dependencies.keys())
        all_successors = set(dep.successor for deps in dependencies.values() for dep in deps)
        start_tasks = all_tasks - all_successors
        
        # For this simplified example, we'll identify tasks that have the longest chain
        # leading to them (potential critical path candidates)
        critical_candidates = set(start_tasks)
        
        # In a real implementation, you would calculate ES, EF, LS, LF values
        # and identify tasks with zero slack (EF - ES = LF - LS = 0)
        
        return critical_candidates
    
    def is_on_critical_path(self, task_id: str, project_id: str) -> bool:
        """Check if a task is on the critical path."""
        # Check if we need to recalculate the critical path
        if (not self.critical_tasks_cache or 
            not self.cache_timestamp or 
            datetime.now() - self.cache_timestamp > timedelta(hours=1)):  # Cache for 1 hour
            
            self.critical_tasks_cache = self.calculate_critical_path(project_id)
            self.cache_timestamp = datetime.now()
        
        return task_id in self.critical_tasks_cache
    
    def get_priority_level(self, task: Task) -> str:
        """Get the priority level for monitoring a task."""
        if self.is_on_critical_path(task.id, task.project or "default_project"):
            return "critical"
        elif task.priority == "critical" or "critical" in task.tags:
            return "critical"
        elif task.priority == "high" or "important" in task.tags:
            return "high"
        else:
            return "normal"
    
    def get_monitoring_frequency(self, task: Task) -> timedelta:
        """Get how frequently to check a task based on its priority."""
        priority = self.get_priority_level(task)
        
        frequency_map = {
            "critical": timedelta(minutes=5),   # Check every 5 minutes
            "high": timedelta(minutes=15),      # Check every 15 minutes
            "normal": timedelta(hours=1)        # Check every hour
        }
        
        return frequency_map.get(priority, timedelta(hours=1))
```

### Benefits
- Focuses monitoring resources on most impactful tasks
- Identifies tasks whose delays affect overall project timeline
- Enables more aggressive notification for critical tasks