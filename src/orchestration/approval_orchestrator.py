#!/usr/bin/env python3
"""Approval Orchestrator — Silver Tier.

Monitors /Approved folder, parses approval files, executes actions via MCP servers,
logs results to audit trail, and moves files to /Done or /Quarantine.

Safety features:
- Rejects expired approvals (default: 24 hours)
- Validates required fields and schemas
- Retry wrapper with exponential backoff
- Failure quarantine folder for problematic files
- Comprehensive audit logging
- Never executes without proper approval

Usage:
    python approval_orchestrator.py              # run one cycle
    python approval_orchestrator.py --watch      # continuous monitoring
    DRY_RUN=true python approval_orchestrator.py # test without executing

Environment Variables:
    APPROVAL_EXPIRY_HOURS: Max age of approval (default: 24)
    MAX_RETRIES: Max retry attempts (default: 3)
    RETRY_DELAY_SECONDS: Base delay between retries (default: 5)
    DRY_RUN: Test mode (default: false)
    LOG_LEVEL: Logging level (default: INFO)
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
import fcntl
import hashlib
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Thread

import yaml
import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
APPROVED_DIR = VAULT / "Approved"
DONE_DIR = VAULT / "Done"
LOGS_DIR = VAULT / "Logs"
QUARANTINE_DIR = VAULT / "Quarantine"
AUDIT_DIR = VAULT / "Audit"

# Approval expiry (default: 24 hours)
APPROVAL_EXPIRY_HOURS = int(os.getenv("APPROVAL_EXPIRY_HOURS", "24"))

# Retry configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "5"))

# Dry run mode (can be overridden by CLI)
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
MCP_TIMEOUT_SECONDS = int(os.getenv("MCP_TIMEOUT_SECONDS", "30"))

# Concurrent processing
MAX_CONCURRENT_EXECUTIONS = int(os.getenv("MAX_CONCURRENT_EXECUTIONS", "3"))

# Auto-approve low-risk items
AUTO_APPROVE_LOW_RISK = os.getenv("AUTO_APPROVE_LOW_RISK", "false").lower() == "true"
PENDING_APPROVAL_DIR = VAULT / "Pending_Approval"

# Webhook notifications
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("approval_orchestrator")

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

REQUIRED_APPROVAL_FIELDS = {
    "approval_id": str,
    "plan_file": str,
    "source_file": str,
    "risk_level": str,
    "requested_at": str,
    "status": str,
    "action_type": str,  # send_email, publish_post, reply_whatsapp
}

REQUIRED_PLAN_FIELDS = {
    "plan_id": str,
    "item_type": str,
    "risk_level": str,
    "requires_approval": bool,
}

VALID_RISK_LEVELS = {"low", "medium", "high"}
VALID_ACTION_TYPES = {"send_email", "publish_post", "reply_whatsapp"}
VALID_ITEM_TYPES = {"email", "file_drop", "whatsapp", "linkedin_post", "social_post"}

# ---------------------------------------------------------------------------
# Retry Wrapper
# ---------------------------------------------------------------------------


def retry_with_backoff(
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_DELAY_SECONDS,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> Callable:
    """Decorator for retry with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds between retries.
        exceptions: Tuple of exceptions to catch and retry.
        logger: Optional logger for retry events.

    Returns:
        Decorated function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        if logger:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                                f"Retrying in {delay:.1f}s..."
                            )
                        time.sleep(delay)
                    else:
                        if logger:
                            logger.error(
                                f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                            )
            raise last_exception
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (metadata, body)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        metadata = yaml.safe_load(match.group(1))
        return metadata or {}, match.group(2)
    except yaml.YAMLError as e:
        logger.error(f"YAML parse error: {e}")
        return {}, content


def load_markdown_file(path: Path) -> tuple[dict, str]:
    """Load markdown file and parse frontmatter."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_frontmatter(content)


def validate_approval(metadata: dict, path: Path) -> list[str]:
    """Validate approval file has all required fields."""
    errors = []

    # Check required fields
    for field, field_type in REQUIRED_APPROVAL_FIELDS.items():
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(metadata[field], field_type):
            errors.append(f"Field {field} has wrong type (expected {field_type.__name__})")

    # Validate risk_level
    if metadata.get("risk_level") and metadata["risk_level"] not in VALID_RISK_LEVELS:
        errors.append(f"Invalid risk_level: {metadata['risk_level']} (must be {VALID_RISK_LEVELS})")

    # Validate action_type
    if metadata.get("action_type") and metadata["action_type"] not in VALID_ACTION_TYPES:
        errors.append(f"Invalid action_type: {metadata['action_type']} (must be {VALID_ACTION_TYPES})")

    # Check expiry
    if "requested_at" in metadata:
        try:
            requested_at = datetime.fromisoformat(metadata["requested_at"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - requested_at).total_seconds() / 3600
            if age_hours > APPROVAL_EXPIRY_HOURS:
                errors.append(f"Approval expired: {age_hours:.1f} hours old (max: {APPROVAL_EXPIRY_HOURS})")
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid requested_at format: {e}")

    return errors


def validate_plan(metadata: dict) -> list[str]:
    """Validate plan file has all required fields."""
    errors = []

    # Check required fields
    for field, field_type in REQUIRED_PLAN_FIELDS.items():
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(metadata[field], field_type):
            errors.append(f"Field {field} has wrong type (expected {field_type.__name__})")

    # Validate risk_level
    if metadata.get("risk_level") and metadata["risk_level"] not in VALID_RISK_LEVELS:
        errors.append(f"Invalid risk_level: {metadata['risk_level']}")

    # Validate item_type
    if metadata.get("item_type") and metadata["item_type"] not in VALID_ITEM_TYPES:
        errors.append(f"Invalid item_type: {metadata['item_type']} (must be {VALID_ITEM_TYPES})")

    return errors


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_audit_log(audit_entry: dict, logs_dir: Path = AUDIT_DIR) -> Path:
    """Write audit log entry to daily audit file with file locking.

    Args:
        audit_entry: Dictionary containing audit information.
        logs_dir: Directory for audit logs.

    Returns:
        Path to the audit log file.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_file = logs_dir / f"audit-{today}.json"

    # Ensure entry has required fields
    if "timestamp" not in audit_entry:
        audit_entry["timestamp"] = get_timestamp()
    if "orchestrator" not in audit_entry:
        audit_entry["orchestrator"] = "approval_orchestrator"

    # Sanitize credentials before writing
    audit_entry = json.loads(sanitize_credentials(json.dumps(audit_entry, default=str)))

    # Append with file locking
    with open(audit_file, "a+", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX)

            # Read existing entries
            fh.seek(0)
            raw = fh.read().strip()
            if raw:
                try:
                    entries = json.loads(raw)
                except json.JSONDecodeError:
                    entries = []
            else:
                entries = []

            entries.append(audit_entry)

            # Rewrite the whole file
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps(entries, indent=2, ensure_ascii=False))
            fh.write("\n")
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)

    logger.debug(f"Audit entry written to: {audit_file}")
    return audit_file


def log_action(
    approval_id: str,
    action: str,
    status: str,
    details: dict = None,
    logs_dir: Path = LOGS_DIR,
) -> Path:
    """Log action to daily log file."""
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / f"orchestrator-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"

    log_entry = {
        "timestamp": get_timestamp(),
        "approval_id": approval_id,
        "action": action,
        "status": status,
        "dry_run": DRY_RUN,
        **(details or {})
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(sanitize_credentials(json.dumps(log_entry)) + "\n")

    return log_file


def move_to_done(path: Path, approval_id: str, execution_result: dict) -> Path:
    """Move file to /Done with execution metadata."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would move {path.name} to Done/")
        return DONE_DIR / path.name

    DONE_DIR.mkdir(parents=True, exist_ok=True)

    done_file = DONE_DIR / path.name
    metadata, body = load_markdown_file(path)

    # Add execution metadata
    metadata["executed_at"] = get_timestamp()
    metadata["execution_status"] = "completed"
    metadata["moved_to_done_from"] = "Approved"
    if execution_result:
        metadata["execution_result"] = execution_result

    # Reconstruct file with updated frontmatter
    new_content = f"---\n{yaml.dump(metadata, default_flow_style=False, sort_keys=False)}---\n{body}"
    done_file.write_text(new_content, encoding="utf-8")

    # Remove original
    path.unlink()
    logger.info(f"Moved {path.name} to Done/")

    return done_file


def move_to_quarantine(path: Path, reason: str, error_details: dict = None) -> Path:
    """Move file to /Quarantine with failure reason."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would move {path.name} to Quarantine/")
        return QUARANTINE_DIR / path.name

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    quarantine_file = QUARANTINE_DIR / path.name
    metadata, body = load_markdown_file(path)

    # Add quarantine metadata
    metadata["quarantined_at"] = get_timestamp()
    metadata["quarantine_reason"] = reason
    metadata["status"] = "quarantined"
    if error_details:
        metadata["error_details"] = error_details

    # Reconstruct file
    new_content = f"---\n{yaml.dump(metadata, default_flow_style=False, sort_keys=False)}---\n{body}"
    quarantine_file.write_text(new_content, encoding="utf-8")

    # Remove original
    path.unlink()
    logger.warning(f"Quarantined {path.name}: {reason}")

    return quarantine_file


def move_to_rejected(path: Path, reason: str) -> Path:
    """Move file to /Rejected with rejection reason."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would move {path.name} to Rejected/")
        return (VAULT / "Rejected") / path.name

    rejected_dir = VAULT / "Rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)

    rejected_file = rejected_dir / path.name
    metadata, body = load_markdown_file(path)

    # Add rejection metadata
    metadata["rejected_at"] = get_timestamp()
    metadata["rejection_reason"] = reason
    metadata["status"] = "rejected"

    # Reconstruct file
    new_content = f"---\n{yaml.dump(metadata, default_flow_style=False, sort_keys=False)}---\n{body}"
    rejected_file.write_text(new_content, encoding="utf-8")

    # Remove original
    path.unlink()
    logger.warning(f"Rejected {path.name}: {reason}")

    return rejected_file


def send_webhook_notification(event_type: str, payload: dict) -> bool:
    """Send webhook notification on approval processing events.

    Args:
        event_type: Type of event (approval_completed, approval_failed, etc.)
        payload: Event payload data.

    Returns:
        True if notification sent successfully, False otherwise.
    """
    if not WEBHOOK_URL:
        logger.debug("No webhook URL configured, skipping notification")
        return False

    try:
        webhook_payload = {
            "event_type": event_type,
            "timestamp": get_timestamp(),
            "orchestrator": "approval_orchestrator",
            "vault": str(VAULT),
            **payload
        }

        with httpx.Client(timeout=10) as client:
            response = client.post(
                WEBHOOK_URL,
                json=webhook_payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(f"Webhook notification sent: {event_type}")
            return True
    except Exception as e:
        logger.warning(f"Webhook notification failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Credential Sanitization
# ---------------------------------------------------------------------------

_CREDENTIAL_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key\s*[=:]\s*)["\']?[\w\-]{20,}["\']?'), r'\1[REDACTED]'),
    (re.compile(r'(?i)(bearer\s+)[\w\-\.]{20,}'), r'\1[REDACTED]'),
    (re.compile(r'(?i)(password\s*[=:]\s*)["\']?[^\s"\']{6,}["\']?'), r'\1[REDACTED]'),
    (re.compile(r'(?i)(secret\s*[=:]\s*)["\']?[\w\-]{10,}["\']?'), r'\1[REDACTED]'),
    (re.compile(r'(?i)(token\s*[=:]\s*)["\']?[\w\-\.]{20,}["\']?'), r'\1[REDACTED]'),
]


def sanitize_credentials(text: str) -> str:
    """Replace API keys, tokens, passwords, secrets with [REDACTED]."""
    for pattern, replacement in _CREDENTIAL_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Auto-Approval for Low-Risk Items
# ---------------------------------------------------------------------------


def auto_approve_low_risk_items() -> int:
    """Scan Pending_Approval/ for low-risk items and move them to Approved/.

    Returns:
        Number of items auto-approved.
    """
    if not AUTO_APPROVE_LOW_RISK:
        return 0

    if not PENDING_APPROVAL_DIR.exists():
        return 0

    count = 0
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(PENDING_APPROVAL_DIR.glob("*.md")):
        try:
            metadata, body = load_markdown_file(path)
            if metadata.get("risk_level") == "low":
                dest = APPROVED_DIR / path.name
                shutil.move(str(path), str(dest))
                logger.info(f"Auto-approved low-risk item: {path.name}")
                write_audit_log({
                    "approval_id": path.stem,
                    "stage": "auto_approved",
                    "risk_level": "low",
                })
                count += 1
        except Exception as e:
            logger.warning(f"Could not auto-approve {path.name}: {e}")

    if count:
        logger.info(f"Auto-approved {count} low-risk item(s)")
    return count


# ---------------------------------------------------------------------------
# Resource Queue Executor (sequential per resource type, parallel across)
# ---------------------------------------------------------------------------


class ResourceQueueExecutor:
    """Execute approval actions sequentially per resource type (email/linkedin/whatsapp)
    but in parallel across different resource types."""

    RESOURCE_MAP = {
        "send_email": "email",
        "publish_post": "linkedin",
        "reply_whatsapp": "whatsapp",
    }

    def __init__(self):
        self._queues: dict[str, list[tuple[Path, dict, dict]]] = defaultdict(list)
        self._results: list[tuple[Path, bool, Exception | None]] = []

    def add(self, path: Path, approval_meta: dict, plan_meta: dict) -> None:
        resource = self.RESOURCE_MAP.get(approval_meta.get("action_type", ""), "other")
        self._queues[resource].append((path, approval_meta, plan_meta))

    def _process_queue(self, resource: str, items: list) -> list:
        results = []
        for path, approval_meta, plan_meta in items:
            try:
                success = process_approval_file(path)
                results.append((path, success, None))
            except Exception as e:
                logger.error(f"Queue error [{resource}] {path.name}: {e}")
                results.append((path, False, e))
        return results

    def execute_all(self) -> list[tuple[Path, bool, Exception | None]]:
        if not self._queues:
            return []

        with ThreadPoolExecutor(max_workers=len(self._queues)) as executor:
            futures = {
                executor.submit(self._process_queue, res, items): res
                for res, items in self._queues.items()
            }
            for future in as_completed(futures):
                self._results.extend(future.result())

        return self._results


# ---------------------------------------------------------------------------
# MCP Integration
# ---------------------------------------------------------------------------


def call_mcp_tool(tool_name: str, params: dict) -> dict:
    """Call MCP tool via MCP server.

    Args:
        tool_name: Name of MCP tool to call.
        params: Parameters for the tool.

    Returns:
        MCP tool response.
    """
    logger.info(f"Calling MCP tool: {tool_name} with params: {params}")

    if DRY_RUN:
        return {
            "status": "simulated",
            "tool": tool_name,
            "params": params,
            "message": f"[DRY_RUN] Would call MCP tool: {tool_name}",
        }

    # Call actual MCP server via HTTP
    try:
        with httpx.Client(timeout=MCP_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{MCP_SERVER_URL}/api/v1/tools/{tool_name}",
                json=params,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"MCP server HTTP error: {e}")
        raise RuntimeError(f"MCP server error: {e}")
    except Exception as e:
        logger.error(f"MCP server connection error: {e}")
        raise RuntimeError(f"Failed to connect to MCP server: {e}")


@retry_with_backoff(max_retries=MAX_RETRIES, base_delay=RETRY_DELAY_SECONDS, logger=logger)
def execute_email_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Execute email-related action via MCP email server.

    Args:
        plan_metadata: Plan file metadata.
        approval_metadata: Approval file metadata.

    Returns:
        Execution result.
    """
    plan_id = plan_metadata.get("plan_id", "unknown")
    source_file = plan_metadata.get("source_file", "")

    logger.info(f"Executing email action for plan {plan_id}")

    # Load source email from Done folder to get original content
    source_path = VAULT / "Done" / source_file
    if source_path.exists():
        email_metadata, email_body = load_markdown_file(source_path)
    else:
        email_metadata = {}
        email_body = ""

    # Extract recipient and subject
    from_field = email_metadata.get("from", "")
    subject = email_metadata.get("subject", "Re: Your Request")

    # Prepare draft email content
    draft_subject = f"Re: {subject}"
    draft_body = f"""Dear {from_field.split('<')[0].strip()},

Thank you for your email regarding {subject}.

We have received your request and are processing it. Our team will respond with the requested information shortly.

Best regards,
AI Employee
"""

    mcp_params = {
        "to": from_field,
        "subject": draft_subject,
        "body": draft_body,
    }

    result = call_mcp_tool("draft_email", mcp_params)

    result.update({
        "action_type": "email_draft",
        "plan_id": plan_id,
        "recipient": from_field,
        "subject": draft_subject,
    })

    return result


@retry_with_backoff(max_retries=MAX_RETRIES, base_delay=RETRY_DELAY_SECONDS, logger=logger)
def execute_publish_post_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Execute publish post action via social MCP server.

    Args:
        plan_metadata: Plan file metadata.
        approval_metadata: Approval file metadata.

    Returns:
        Execution result.
    """
    plan_id = plan_metadata.get("plan_id", "unknown")
    platform = approval_metadata.get("platform", plan_metadata.get("platform", "linkedin")).lower()

    logger.info(f"Executing publish post action for {platform} (plan {plan_id})")

    # Load post content from approval metadata or source
    post_content = approval_metadata.get("post_content", "")
    if not post_content:
        # Try to load from the actual file body
        source_file = approval_metadata.get("filename", "")
        if source_file:
            source_path = APPROVED_DIR / source_file
            if source_path.exists():
                _, post_content = load_markdown_file(source_path)

    tool_map = {
        "linkedin": "publish_linkedin_post",
        "twitter": "publish_twitter_post",
        "facebook": "publish_facebook_post",
        "instagram": "publish_instagram_post"
    }

    tool_name = tool_map.get(platform, "publish_linkedin_post")

    mcp_params = {
        "content": post_content,
        "platform": platform,
        "scheduled_at": plan_metadata.get("scheduled_at", None),
    }

    result = call_mcp_tool(tool_name, mcp_params)

    result.update({
        "action_type": "publish_post",
        "plan_id": plan_id,
        "platform": platform,
        "content_length": len(post_content),
    })

    return result


@retry_with_backoff(max_retries=MAX_RETRIES, base_delay=RETRY_DELAY_SECONDS, logger=logger)
def execute_whatsapp_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Execute WhatsApp action via MCP WhatsApp server.

    Args:
        plan_metadata: Plan file metadata.
        approval_metadata: Approval file metadata.

    Returns:
        Execution result.
    """
    plan_id = plan_metadata.get("plan_id", "unknown")

    logger.info(f"Executing WhatsApp action for plan {plan_id}")

    # Load message content
    message_content = plan_metadata.get("message_content", "")
    recipient = plan_metadata.get("recipient", "")

    if not message_content:
        # Try to load from source file
        source_file = plan_metadata.get("source_file", "")
        if source_file:
            source_path = VAULT / "Done" / source_file
            if source_path.exists():
                _, message_content = load_markdown_file(source_path)

    mcp_params = {
        "recipient": recipient,
        "message": message_content,
    }

    result = call_mcp_tool("send_whatsapp_message", mcp_params)

    result.update({
        "action_type": "reply_whatsapp",
        "plan_id": plan_id,
        "recipient": recipient,
        "message_length": len(message_content),
    })

    return result


@retry_with_backoff(max_retries=MAX_RETRIES, base_delay=RETRY_DELAY_SECONDS, logger=logger)
def execute_odoo_invoice_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Execute Odoo invoice creation via MCP Odoo server."""
    plan_id = plan_metadata.get("plan_id", "unknown")
    recipient = approval_metadata.get("recipient", "Client")
    
    logger.info(f"Creating Odoo invoice for {recipient} (plan {plan_id})")
    
    mcp_params = {
        "partner_name": recipient,
        "amount": float(approval_metadata.get("amount", 0)),
        "description": approval_metadata.get("topic", "Services rendered")
    }
    
    result = call_mcp_tool("create_invoice", mcp_params)
    
    result.update({
        "action_type": "create_odoo_invoice",
        "plan_id": plan_id,
        "recipient": recipient
    })
    
    return result


def execute_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Route to correct action executor based on action_type.

    Args:
        plan_metadata: Plan file metadata.
        approval_metadata: Approval file metadata.

    Returns:
        Execution result.

    Raises:
        ValueError: If action_type is unknown.
    """
    action_type = approval_metadata.get("action_type", "unknown")

    executors = {
        "send_email": execute_email_action,
        "publish_post": execute_publish_post_action,
        "reply_whatsapp": execute_whatsapp_action,
        "create_odoo_invoice": execute_odoo_invoice_action,
    }

    executor = executors.get(action_type)
    if not executor:
        raise ValueError(f"Unknown action_type: {action_type}")

    return executor(plan_metadata, approval_metadata)


# ---------------------------------------------------------------------------
# Main Orchestrator Logic
# ---------------------------------------------------------------------------


def process_approval_file(approval_path: Path) -> bool:
    """Process a single approval file.

    Args:
        approval_path: Path to approval file.

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Processing: {approval_path.name}")

    approval_id = approval_path.stem  # filename without extension
    audit_entry = {
        "approval_id": approval_id,
        "file": approval_path.name,
        "stage": "started",
        "timestamp": get_timestamp(),
    }

    try:
        # Step 1: Parse approval file
        approval_metadata, approval_body = load_markdown_file(approval_path)
        audit_entry["stage"] = "parsed"
        audit_entry["metadata"] = {
            "action_type": approval_metadata.get("action_type"),
            "risk_level": approval_metadata.get("risk_level"),
            "plan_file": approval_metadata.get("plan_file"),
        }

        # Step 2: Validate approval
        errors = validate_approval(approval_metadata, approval_path)
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Validation failed for {approval_path.name}: {error_msg}")
            log_action(approval_id, "validate_approval", "failed", {"errors": errors})
            audit_entry["stage"] = "validation_failed"
            audit_entry["error"] = error_msg
            write_audit_log(audit_entry)
            move_to_rejected(approval_path, error_msg)
            return False

        # Step 3: Load and validate plan
        plan_path = VAULT / approval_metadata["plan_file"]
        if not plan_path.exists():
            error_msg = f"Plan file not found: {plan_path}"
            logger.error(error_msg)
            log_action(approval_id, "load_plan", "failed", {"error": error_msg})
            audit_entry["stage"] = "plan_not_found"
            audit_entry["error"] = error_msg
            write_audit_log(audit_entry)
            move_to_rejected(approval_path, error_msg)
            return False

        plan_metadata, plan_body = load_markdown_file(plan_path)
        plan_errors = validate_plan(plan_metadata)
        if plan_errors:
            error_msg = "; ".join(plan_errors)
            logger.error(f"Plan validation failed: {error_msg}")
            log_action(approval_id, "validate_plan", "failed", {"errors": plan_errors})
            audit_entry["stage"] = "plan_validation_failed"
            audit_entry["error"] = error_msg
            write_audit_log(audit_entry)
            move_to_rejected(approval_path, f"Plan validation failed: {error_msg}")
            return False

        # Step 4: Execute action with retry wrapper
        log_action(approval_id, "execute", "started")
        audit_entry["stage"] = "executing"
        write_audit_log(audit_entry)

        try:
            result = execute_action(plan_metadata, approval_metadata)
            logger.info(f"Action executed: {result['action_type']} - {result['status']}")
            log_action(approval_id, "execute", result["status"], result)
            audit_entry["stage"] = "executed"
            audit_entry["result"] = {
                "status": result.get("status"),
                "action_type": result.get("action_type"),
                "tool": result.get("tool"),
            }
        except Exception as e:
            error_msg = f"Execution failed after retries: {e}"
            logger.error(error_msg)
            log_action(approval_id, "execute", "failed", {"error": str(e)})
            audit_entry["stage"] = "execution_failed"
            audit_entry["error"] = error_msg
            write_audit_log(audit_entry)
            # Move to quarantine for retry failures
            move_to_quarantine(
                approval_path,
                f"Execution failed after {MAX_RETRIES + 1} attempts",
                {"error": str(e), "error_type": type(e).__name__}
            )
            return False

        # Step 5: Move to Done
        done_path = move_to_done(approval_path, approval_id, result)
        logger.info(f"Successfully processed {approval_path.name}")
        audit_entry["stage"] = "completed"
        audit_entry["done_file"] = done_path.name
        write_audit_log(audit_entry)

        return True

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_action(approval_id, "process", "failed", {"error": str(e)})
        audit_entry["stage"] = "file_not_found"
        audit_entry["error"] = str(e)
        write_audit_log(audit_entry)
        move_to_quarantine(approval_path, f"File not found: {e}", {"error": str(e)})
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing {approval_path.name}: {e}")
        log_action(approval_id, "process", "failed", {"error": str(e), "type": type(e).__name__})
        audit_entry["stage"] = "unexpected_error"
        audit_entry["error"] = {"message": str(e), "type": type(e).__name__}
        write_audit_log(audit_entry)
        move_to_quarantine(
            approval_path,
            f"Unexpected error: {e}",
            {"error": str(e), "error_type": type(e).__name__}
        )
        return False


def run_orchestrator_cycle() -> int:
    """Run one orchestration cycle.

    Returns:
        Number of successfully processed files.
    """
    logger.info(f"Starting orchestrator cycle (DRY_RUN={DRY_RUN})")

    # Auto-approve low-risk items from Pending_Approval/
    auto_approve_low_risk_items()

    if not APPROVED_DIR.exists():
        logger.info(f"Approved directory does not exist: {APPROVED_DIR}")
        return 0

    approval_files = sorted(APPROVED_DIR.glob("*.md"))
    if not approval_files:
        logger.info("No files in Approved/")
        return 0

    logger.info(f"Found {len(approval_files)} file(s) in Approved/")

    # Process files using ResourceQueueExecutor (sequential per resource, parallel across)
    queue_executor = ResourceQueueExecutor()
    for path in approval_files:
        try:
            metadata, _ = load_markdown_file(path)
            queue_executor.add(path, metadata, {})
        except Exception:
            # If we can't parse, fall back to direct processing
            queue_executor.add(path, {"action_type": "unknown"}, {})

    results = queue_executor.execute_all()

    # Count results
    success_count = sum(1 for _, success, _ in results if success)
    fail_count = sum(1 for _, success, _ in results if not success and not _)
    quarantine_count = sum(
        1 for path, success, _ in results
        if not success and (QUARANTINE_DIR / path.name).exists()
    )

    logger.info(f"Cycle complete: {success_count} succeeded, {fail_count} failed, {quarantine_count} quarantined")

    # Write cycle summary to audit log
    write_audit_log({
        "approval_id": "cycle_summary",
        "stage": "cycle_complete",
        "summary": {
            "total_files": len(approval_files),
            "succeeded": success_count,
            "failed": fail_count,
            "quarantined": quarantine_count,
            "concurrent_workers": MAX_CONCURRENT_EXECUTIONS,
        }
    })

    # Send webhook notification
    if WEBHOOK_URL:
        send_webhook_notification("cycle_completed", {
            "total_files": len(approval_files),
            "succeeded": success_count,
            "failed": fail_count,
            "quarantined": quarantine_count,
        })

    return success_count


def run_watch_mode(interval_seconds: int = 30):
    """Run orchestrator in continuous watch mode.

    Args:
        interval_seconds: Polling interval in seconds.
    """
    logger.info(f"Starting watch mode (interval={interval_seconds}s)")

    try:
        while True:
            run_orchestrator_cycle()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("Watch mode stopped by user")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    global DRY_RUN, MAX_CONCURRENT_EXECUTIONS
    
    parser = argparse.ArgumentParser(description="Approval Orchestrator — Silver Tier")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run in continuous watch mode",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Watch mode interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Override DRY_RUN env var to enable test mode",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum concurrent workers (default: 3)",
    )

    args = parser.parse_args()

    if args.dry_run:
        DRY_RUN = True
        logger.warning("DRY_RUN mode enabled - no real actions will be executed")
    
    # Apply max workers override
    MAX_CONCURRENT_EXECUTIONS = args.max_workers

    # Ensure directories exist
    for dir_path in [APPROVED_DIR, DONE_DIR, LOGS_DIR, QUARANTINE_DIR, AUDIT_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Vault: {VAULT}")
    logger.info(f"Approved: {APPROVED_DIR}")
    logger.info(f"Done: {DONE_DIR}")
    logger.info(f"Quarantine: {QUARANTINE_DIR}")
    logger.info(f"Audit: {AUDIT_DIR}")
    logger.info(f"Expiry: {APPROVAL_EXPIRY_HOURS}h | Retries: {MAX_RETRIES} | Base Delay: {RETRY_DELAY_SECONDS}s")
    logger.info(f"Concurrent workers: {MAX_CONCURRENT_EXECUTIONS} | MCP Server: {MCP_SERVER_URL}")

    if args.watch:
        run_watch_mode(args.interval)
    else:
        success_count = run_orchestrator_cycle()
        sys.exit(0 if success_count > 0 else 0)


if __name__ == "__main__":
    main()
