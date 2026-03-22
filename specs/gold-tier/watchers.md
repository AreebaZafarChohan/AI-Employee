# Gold Tier Watchers Specification

This document defines all watchers (sensors) required for Gold Tier operation.

## Watchers Overview

Watchers are Python services that monitor external systems for changes and create markdown files in `Needs_Action/` for processing.

| # | Watcher Name | Domain | Poll Interval | Status |
|---|--------------|--------|---------------|--------|
| 1 | Gmail Watcher | Communication | 60s | Existing (extend) |
| 2 | WhatsApp Watcher | Communication | 60s | Existing (extend) |
| 3 | Social Media Watcher | Social Media | 300s | New |
| 4 | Odoo Watcher | Accounting | 300s | New |
| 5 | Folder Watcher | File System | Event-driven | Existing |
| 6 | Schedule Watcher | Task Scheduling | 60s | New |

---

## Watcher 1: Gmail Watcher

**Path:** `gmail_watcher.py`  
**Status:** Existing (extend for Gold Tier)  
**Poll Interval:** 60 seconds

### Functionality

- Polls Gmail for unread important emails
- Filters by labels and importance
- Creates markdown files in `Needs_Action/`
- Marks processed emails as read
- Cross-domain deduplication

### Email Processing Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Gmail API  │────▶│  Filter &    │────▶│  Create Markdown│
│  (Unread)   │     │  Categorize  │     │  in Needs_Action│
└─────────────┘     └──────────────┘     └─────────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │  Mark as     │
                     │  Read        │
                     └──────────────┘
```

### Email Categorization

| Category | Label | Action |
|----------|-------|--------|
| **Client Inquiry** | Important | Create task |
| **Invoice** | Finance | Create accounting task |
| **Meeting Request** | Calendar | Create calendar event |
| **Newsletter** | Marketing | Archive |
| **Spam** | Spam | Ignore |

### Markdown File Template

```markdown
---
type: email
source: gmail
message_id: <gmail-message-id>
from: "Name <email@example.com>"
to: "you@example.com"
subject: "Email Subject"
received_at: "2026-03-06T10:30:00Z"
domain: business
risk_level: low
requires_approval: false
labels: ["important", "client"]
---

## Email Content

{email-body}

---

## Suggested Actions

- [ ] Reply to email
- [ ] Create follow-up task
- [ ] Archive email
```

### Configuration

```python
GMAIL_CONFIG = {
    "credentials_file": os.getenv("GMAIL_CREDENTIALS_FILE"),
    "token_file": os.getenv("GMAIL_TOKEN_FILE"),
    "poll_interval": int(os.getenv("GMAIL_POLL_INTERVAL", "60")),
    "max_results": int(os.getenv("GMAIL_MAX_RESULTS", "20")),
    "labels_filter": ["IMPORTANT"],
    "exclude_labels": ["SPAM", "TRASH"],
}
```

---

## Watcher 2: WhatsApp Watcher

**Path:** `whatsapp_watcher.py`  
**Status:** Existing (extend for Gold Tier)  
**Poll Interval:** 60 seconds

### Functionality

- Monitors WhatsApp Web via Playwright
- Detects new messages with keyword triggers
- Creates markdown files in `Needs_Action/`
- Supports auto-reply for low-risk messages
- Cross-domain deduplication

### Keyword Triggers

| Keyword | Risk Level | Action |
|---------|------------|--------|
| invoice | medium | Create accounting task |
| payment | high | Create payment task |
| urgent | high | Immediate notification |
| project | low | Create project task |
| proposal | medium | Create proposal task |

### Markdown File Template

```markdown
---
type: whatsapp
source: whatsapp
chat_id: <chat-id>
contact: "+1234567890"
contact_name: "Contact Name"
message: "Message content"
received_at: "2026-03-06T10:30:00Z"
domain: business
risk_level: medium
requires_approval: true
trigger_keyword: "invoice"
---

## WhatsApp Message

**From:** {contact_name} ({contact})  
**Received:** {received_at}

### Message Content

{message}

---

## Suggested Actions

- [ ] Reply to message
- [ ] Create invoice
- [ ] Forward to team
```

### Configuration

```python
WHATSAPP_CONFIG = {
    "profile_dir": os.getenv("WA_PROFILE_DIR"),
    "poll_interval": int(os.getenv("WA_POLL_INTERVAL", "60")),
    "headless": os.getenv("WA_HEADLESS", "false").lower() == "true",
    "keywords": ["invoice", "payment", "urgent", "project", "proposal"],
    "auto_reply": os.getenv("WA_AUTO_REPLY", "false").lower() == "true",
    "auto_reply_template": "Thank you for your message. We'll respond shortly.",
}
```

---

## Watcher 3: Social Media Watcher (NEW)

**Path:** `social_watcher.py`  
**Status:** New Implementation Required  
**Poll Interval:** 300 seconds (5 minutes)

### Functionality

- Monitors social media platforms for mentions, comments, messages
- Tracks engagement metrics
- Creates markdown files for responses needed
- Generates analytics reports

### Platforms Monitored

| Platform | API | Monitored Events |
|----------|-----|------------------|
| LinkedIn | API | Comments, Messages, Connection requests |
| Facebook | Graph API | Comments, Messages, Page mentions |
| Instagram | Graph API | Comments, DMs, Story mentions |
| Twitter | API v2 | Mentions, Replies, DMs |

### Social Media Processing Flow

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Social APIs │────▶│  Aggregate   │────▶│  Categorize     │
│  (All)       │     │  Events      │     │  by Priority    │
└──────────────┘     └──────────────┘     └─────────────────┘
                              │
                              ▼
                     ┌──────────────┐     ┌─────────────────┐
                     │  High        │────▶│  Create         │
                     │  Priority    │     │  Needs_Action   │
                     └──────────────┘     └─────────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │  Analytics   │
                     │  Update      │
                     └──────────────┘
```

### Event Categorization

| Event Type | Priority | Auto-Response | Approval Required |
|------------|----------|---------------|-------------------|
| Customer complaint | High | No | Yes |
| Sales inquiry | High | Yes (acknowledgment) | Yes |
| General comment | Medium | No | No |
| Spam | Low | No | No |
| Mention | Medium | No | No |

### Markdown File Template

```markdown
---
type: social_media
source: linkedin
platform: linkedin
post_id: <post-id>
author: "Author Name"
author_profile: "https://linkedin.com/in/author"
content: "Comment or message content"
event_type: comment
received_at: "2026-03-06T10:30:00Z"
domain: business
risk_level: medium
requires_approval: true
sentiment: positive
---

## Social Media Event

**Platform:** LinkedIn  
**Type:** Comment  
**Author:** {author}  
**Received:** {received_at}

### Content

{content}

### Original Post Context

{original-post-excerpt}

---

## Suggested Response

{ai-generated-response}

---

## Actions

- [ ] Approve and post response
- [ ] Edit response
- [ ] Ignore
- [ ] Escalate to human
```

### Configuration

```python
SOCIAL_CONFIG = {
    "poll_interval": int(os.getenv("SOCIAL_POLL_INTERVAL", "300")),
    "platforms": ["linkedin", "facebook", "instagram", "twitter"],
    "linkedin": {
        "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN"),
        "organization_id": os.getenv("LINKEDIN_ORG_ID"),
    },
    "facebook": {
        "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),
        "page_id": os.getenv("FACEBOOK_PAGE_ID"),
    },
    "instagram": {
        "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN"),
        "business_account_id": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"),
    },
    "twitter": {
        "bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
    },
    "auto_respond_keywords": ["thank", "great", "awesome"],
    "escalation_keywords": ["complaint", "angry", "refund", "sue"],
}
```

---

## Watcher 4: Odoo Watcher (NEW)

**Path:** `odoo_watcher.py`  
**Status:** New Implementation Required  
**Poll Interval:** 300 seconds (5 minutes)

### Functionality

- Monitors Odoo for accounting events
- Tracks unpaid invoices
- Alerts on overdue payments
- Creates accounting tasks in `Needs_Action/`

### Monitored Events

| Event | Trigger | Action |
|-------|---------|--------|
| Invoice created | New invoice | Log only |
| Invoice overdue | > due date | Create alert task |
| Payment received | Payment registered | Log and update |
| Low balance | Account balance < threshold | Create alert |
| Large expense | Expense > threshold | Create approval task |

### Odoo Processing Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Odoo API   │────▶│  Check       │────▶│  Create         │
│  (JSON-RPC) │     │  Thresholds  │     │  Alerts/Tasks   │
└─────────────┘     └──────────────┘     └─────────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │  Update      │
                     │  Dashboard   │
                     └──────────────┘
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Overdue invoices | > 7 days | > 30 days |
| Account balance | < $10,000 | < $5,000 |
| Single expense | > $1,000 | > $5,000 |
| Unpaid invoices count | > 10 | > 25 |

### Markdown File Template (Overdue Invoice)

```markdown
---
type: accounting_alert
source: odoo
alert_type: overdue_invoice
invoice_id: INV/2026/001
partner: "Client Name"
partner_id: 123
amount: 5000.00
currency: USD
due_date: "2026-02-06"
days_overdue: 28
created_at: "2026-03-06T10:30:00Z"
domain: business
risk_level: high
requires_approval: true
---

## Overdue Invoice Alert

**Invoice:** {invoice_id}  
**Client:** {partner}  
**Amount:** ${amount}  
**Due Date:** {due_date}  
**Days Overdue:** {days_overdue}

---

## Recommended Actions

1. **Immediate:** Send payment reminder email
2. **Follow-up:** Call client if no response in 3 days
3. **Escalation:** Consider collections if > 60 days

---

## Quick Actions

- [ ] Send payment reminder email
- [ ] Create follow-up task
- [ ] Call client
- [ ] Escalate to collections
```

### Markdown File Template (Large Expense)

```markdown
---
type: accounting_alert
source: odoo
alert_type: large_expense
expense_id: EXP/2026/045
vendor: "Vendor Name"
amount: 7500.00
currency: USD
category: "Office Equipment"
created_at: "2026-03-06T10:30:00Z"
domain: business
risk_level: high
requires_approval: true
threshold_exceeded: 5000
---

## Large Expense Alert

**Expense:** {expense_id}  
**Vendor:** {vendor}  
**Amount:** ${amount}  
**Category:** {category}  
**Threshold:** ${threshold_exceeded}

---

## Approval Required

This expense exceeds the ${threshold_exceeded} threshold and requires human approval.

---

## Actions

- [ ] Review and approve
- [ ] Reject expense
- [ ] Request more information
```

### Configuration

```python
ODOO_WATCHER_CONFIG = {
    "url": os.getenv("ODOO_URL"),
    "database": os.getenv("ODOO_DB"),
    "username": os.getenv("ODOO_USERNAME"),
    "password": os.getenv("ODOO_PASSWORD"),
    "poll_interval": int(os.getenv("ODOO_POLL_INTERVAL", "300")),
    "thresholds": {
        "overdue_days_warning": 7,
        "overdue_days_critical": 30,
        "expense_warning": 1000,
        "expense_critical": 5000,
        "balance_warning": 10000,
        "balance_critical": 5000,
    },
}
```

---

## Watcher 5: Folder Watcher

**Path:** `filesystem_watcher.py`  
**Status:** Existing  
**Trigger:** File system events

### Functionality

- Watches `Inbox/` folder for new files
- Triggers on file create/modify events
- Copies files to `Needs_Action/`
- Creates metadata sidecar

### Events Monitored

| Event | Action |
|-------|--------|
| File created | Copy to Needs_Action |
| File modified | Re-process if needed |
| File deleted | Log and ignore |

### Configuration

```python
FOLDER_WATCHER_CONFIG = {
    "watch_path": VAULT / "Inbox",
    "file_patterns": [".md", ".txt"],
    "exclude_patterns": [".*", "*.meta.md"],
    "debounce_seconds": 1,
}
```

---

## Watcher 6: Schedule Watcher (NEW)

**Path:** `schedule_watcher.py`  
**Status:** New Implementation Required  
**Poll Interval:** 60 seconds

### Functionality

- Monitors scheduled tasks and deadlines
- Creates reminder tasks before deadlines
- Generates daily task lists
- Triggers recurring tasks

### Schedule Types

| Type | Description | Example |
|------|-------------|---------|
| One-time | Single deadline | Project delivery |
| Recurring | Repeats on schedule | Weekly report |
| Relative | X days before event | Reminder 3 days before |
| Cron-based | Complex schedule | Every 2nd Monday |

### Schedule Processing Flow

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Schedules   │────▶│  Check       │────▶│  Create         │
│  Database    │     │  Deadlines   │     │  Reminders      │
└──────────────┘     └──────────────┘     └─────────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │  Update      │
                     │  Dashboard   │
                     └──────────────┘
```

### Reminder Timing

| Deadline | Reminder Before |
|----------|-----------------|
| High priority | 3 days, 1 day, 3 hours |
| Medium priority | 1 day, 3 hours |
| Low priority | 3 hours |

### Markdown File Template (Deadline Reminder)

```markdown
---
type: schedule_reminder
source: schedule_watcher
task_id: TASK-2026-001
task_name: "Submit quarterly report"
deadline: "2026-03-10T17:00:00Z"
priority: high
time_remaining: "3 days"
created_at: "2026-03-06T10:30:00Z"
domain: business
risk_level: medium
requires_approval: false
---

## Deadline Reminder

**Task:** {task_name}  
**Deadline:** {deadline}  
**Time Remaining:** {time_remaining}  
**Priority:** {priority}

---

## Task Details

{task-description}

---

## Actions

- [ ] Start working on task
- [ ] Delegate to team member
- [ ] Request extension
- [ ] Mark as complete
```

### Configuration

```python
SCHEDULE_WATCHER_CONFIG = {
    "poll_interval": int(os.getenv("SCHEDULE_POLL_INTERVAL", "60")),
    "schedules_file": VAULT / ".schedules.json",
    "reminder_lead_times": {
        "high": [3 * 86400, 86400, 3 * 3600],  # 3 days, 1 day, 3 hours
        "medium": [86400, 3 * 3600],           # 1 day, 3 hours
        "low": [3 * 3600],                      # 3 hours
    },
    "working_hours": {
        "start": 9,
        "end": 17,
        "timezone": "UTC",
    },
}
```

---

## Watcher Common Patterns

### Base Watcher Class

```python
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

class BaseWatcher(ABC):
    """Base class for all watchers."""
    
    def __init__(self, config: dict):
        self.config = config
        self.vault = Path(config.get("vault_path", "./AI-Employee-Vault"))
        self.needs_action = self.vault / "Needs_Action"
        self.logs = self.vault / "Logs"
        self.ledger_file = self.vault / f".{self.name}_processed.json"
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Watcher name for logging."""
        pass
    
    @abstractmethod
    async def poll(self) -> list:
        """Poll source for new items."""
        pass
    
    def create_needs_action_file(
        self,
        content: str,
        metadata: dict,
        filename: str = None
    ) -> Path:
        """Create markdown file in Needs_Action folder."""
        self.needs_action.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            filename = f"{self.name}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.md"
        
        frontmatter = self._format_frontmatter(metadata)
        file_path = self.needs_action / filename
        file_path.write_text(f"{frontmatter}\n{content}", encoding="utf-8")
        
        self._update_ledger(filename)
        self._log_action("file_created", filename)
        
        return file_path
    
    def _format_frontmatter(self, metadata: dict) -> str:
        """Format metadata as YAML frontmatter."""
        import yaml
        return f"---\n{yaml.dump(metadata, default_flow_style=False)}---"
    
    def _update_ledger(self, filename: str):
        """Update processed items ledger."""
        ledger = self._load_ledger()
        ledger.append(filename)
        self._save_ledger(ledger)
    
    def _load_ledger(self) -> list:
        """Load ledger from file."""
        import json
        if self.ledger_file.exists():
            return json.loads(self.ledger_file.read_text())
        return []
    
    def _save_ledger(self, ledger: list):
        """Save ledger to file."""
        import json
        self.ledger_file.write_text(json.dumps(ledger, indent=2))
    
    def _log_action(self, action: str, details: dict):
        """Log watcher action."""
        import json
        from datetime import datetime, timezone
        
        log_file = self.logs / f"{self.name}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
        self.logs.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "watcher": self.name,
            "action": action,
            **details
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

### Error Handling Pattern

```python
class WatcherError(Exception):
    """Base watcher error."""
    pass

class AuthenticationError(WatcherError):
    """Authentication failed."""
    pass

class RateLimitError(WatcherError):
    """API rate limit exceeded."""
    pass

class NetworkError(WatcherError):
    """Network connectivity issue."""
    pass

async def with_retry(func, max_retries=3, base_delay=2.0):
    """Retry wrapper with exponential backoff."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except (NetworkError, RateLimitError) as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All retries failed: {e}")
    raise last_error
```

### Health Check Pattern

```python
class WatcherHealth:
    """Health check for watchers."""
    
    def __init__(self, watcher):
        self.watcher = watcher
    
    async def check(self) -> dict:
        """Check watcher health."""
        try:
            await self.watcher.health_check()
            return {
                "status": "healthy",
                "watcher": self.watcher.name,
                "last_poll": self.watcher.last_poll_time,
                "items_processed": self.watcher.items_processed,
                "errors_last_hour": self.watcher.errors_last_hour,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "watcher": self.watcher.name,
                "error": str(e),
            }
```

---

## Watcher Startup

### Systemd Service Files

```ini
# /etc/systemd/system/gmail-watcher.service
[Unit]
Description=Gmail Watcher
After=network.target

[Service]
Type=simple
User=ai-employee
WorkingDirectory=/opt/ai-employee
ExecStart=/usr/bin/python3 gmail_watcher.py --watch
Restart=always
Environment=VAULT_PATH=/opt/ai-employee/AI-Employee-Vault

[Install]
WantedBy=multi-user.target
```

### Docker Compose (Optional)

```yaml
version: '3.8'

services:
  gmail-watcher:
    build: .
    command: python gmail_watcher.py --watch
    volumes:
      - ./AI-Employee-Vault:/app/AI-Employee-Vault
    env_file: .env
    restart: unless-stopped

  whatsapp-watcher:
    build: .
    command: python whatsapp_watcher.py --watch
    volumes:
      - ./AI-Employee-Vault:/app/AI-Employee-Vault
      - ./whatsapp-profile:/app/.whatsapp_profile
    env_file: .env
    restart: unless-stopped

  social-watcher:
    build: .
    command: python social_watcher.py --watch
    volumes:
      - ./AI-Employee-Vault:/app/AI-Employee-Vault
    env_file: .env
    restart: unless-stopped

  odoo-watcher:
    build: .
    command: python odoo_watcher.py --watch
    volumes:
      - ./AI-Employee-Vault:/app/AI-Employee-Vault
    env_file: .env
    restart: unless-stopped
```

---

**Document End**
