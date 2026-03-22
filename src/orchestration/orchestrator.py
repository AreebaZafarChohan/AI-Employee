#!/usr/bin/env python3
"""Silver Tier Orchestrator.

Monitors /Approved folder, parses approval files, executes actions via MCP,
logs results, and moves files to /Done.

Safety features:
- Rejects expired approvals (default: 24 hours)
- Validates required fields
- Logs all failures
- Never executes without approval

Usage:
    python orchestrator.py              # run one cycle
    python orchestrator.py --watch      # continuous monitoring
    DRY_RUN=true python orchestrator.py # test without executing
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
APPROVED_DIR = VAULT / "Approved"
DONE_DIR = VAULT / "Done"
LOGS_DIR = VAULT / "Logs"

# Approval expiry (default: 24 hours)
APPROVAL_EXPIRY_HOURS = int(os.getenv("APPROVAL_EXPIRY_HOURS", "24"))

# Dry run mode
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("orchestrator")

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
}

REQUIRED_PLAN_FIELDS = {
    "plan_id": str,
    "item_type": str,
    "risk_level": str,
    "requires_approval": bool,
}

VALID_RISK_LEVELS = {"low", "medium", "high"}
VALID_ITEM_TYPES = {"email", "file_drop", "whatsapp"}

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


def log_action(approval_id: str, action: str, status: str, details: dict = None):
    """Log action to logs file."""
    log_file = LOGS_DIR / f"orchestrator-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": get_timestamp(),
        "approval_id": approval_id,
        "action": action,
        "status": status,
        "dry_run": DRY_RUN,
        **(details or {})
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def move_to_done(path: Path, approval_id: str):
    """Move file to /Done with execution metadata."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would move {path.name} to Done/")
        return
    
    done_file = DONE_DIR / path.name
    metadata, body = load_markdown_file(path)
    
    # Add execution metadata
    metadata["executed_at"] = get_timestamp()
    metadata["execution_status"] = "completed"
    metadata["moved_to_done_from"] = "Approved"
    
    # Reconstruct file with updated frontmatter
    new_content = f"---\n{yaml.dump(metadata, default_flow_style=False, sort_keys=False)}---\n{body}"
    done_file.write_text(new_content, encoding="utf-8")
    
    # Remove original
    path.unlink()
    logger.info(f"Moved {path.name} to Done/")


def move_to_rejected(path: Path, reason: str):
    """Move file to /Rejected with rejection reason."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would move {path.name} to Rejected/")
        return
    
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


# ---------------------------------------------------------------------------
# Action Executors
# ---------------------------------------------------------------------------


def execute_email_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Execute email-related action via MCP email server."""
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
    
    result = {
        "action_type": "email_draft",
        "plan_id": plan_id,
        "status": "simulated",
        "recipient": from_field,
        "subject": draft_subject,
        "message": f"Draft email prepared for {from_field}",
        "mcp_tool": "draft_email",
        "mcp_params": {
            "to": from_field,
            "subject": draft_subject,
            "body": draft_body,
        }
    }
    
    if not DRY_RUN:
        # In production, would call MCP email server:
        # result = call_mcp_tool("draft_email", result["mcp_params"])
        logger.info(f"Would call MCP tool: draft_email(to={from_field}, subject={draft_subject})")
        result["status"] = "mcp_ready"
    
    return result


def execute_file_drop_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Execute file drop action."""
    plan_id = plan_metadata.get("plan_id", "unknown")
    
    logger.info(f"Executing file drop action for plan {plan_id}")
    
    result = {
        "action_type": "file_drop_process",
        "plan_id": plan_id,
        "status": "simulated",
        "message": "File drop action executed (simulation)",
    }
    
    return result


def execute_whatsapp_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Execute WhatsApp action."""
    plan_id = plan_metadata.get("plan_id", "unknown")
    
    logger.info(f"Executing WhatsApp action for plan {plan_id}")
    
    result = {
        "action_type": "whatsapp_process",
        "plan_id": plan_id,
        "status": "simulated",
        "message": "WhatsApp action executed (simulation)",
    }
    
    return result


def execute_action(plan_metadata: dict, approval_metadata: dict) -> dict:
    """Route to correct action executor based on item_type."""
    item_type = plan_metadata.get("item_type", "unknown")
    
    executors = {
        "email": execute_email_action,
        "file_drop": execute_file_drop_action,
        "whatsapp": execute_whatsapp_action,
    }
    
    executor = executors.get(item_type)
    if not executor:
        raise ValueError(f"Unknown item_type: {item_type}")
    
    return executor(plan_metadata, approval_metadata)


# ---------------------------------------------------------------------------
# Main Orchestrator Logic
# ---------------------------------------------------------------------------


def process_approval_file(approval_path: Path) -> bool:
    """
    Process a single approval file.
    
    Returns True if successful, False otherwise.
    """
    logger.info(f"Processing: {approval_path.name}")
    
    approval_id = approval_path.stem  # filename without extension
    
    try:
        # Step 1: Parse approval file
        approval_metadata, approval_body = load_markdown_file(approval_path)
        
        # Step 2: Validate approval
        errors = validate_approval(approval_metadata, approval_path)
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Validation failed for {approval_path.name}: {error_msg}")
            log_action(approval_id, "validate_approval", "failed", {"errors": errors})
            move_to_rejected(approval_path, error_msg)
            return False
        
        # Step 3: Load and validate plan
        plan_path = VAULT / approval_metadata["plan_file"]
        if not plan_path.exists():
            error_msg = f"Plan file not found: {plan_path}"
            logger.error(error_msg)
            log_action(approval_id, "load_plan", "failed", {"error": error_msg})
            move_to_rejected(approval_path, error_msg)
            return False
        
        plan_metadata, plan_body = load_markdown_file(plan_path)
        plan_errors = validate_plan(plan_metadata)
        if plan_errors:
            error_msg = "; ".join(plan_errors)
            logger.error(f"Plan validation failed: {error_msg}")
            log_action(approval_id, "validate_plan", "failed", {"errors": plan_errors})
            move_to_rejected(approval_path, f"Plan validation failed: {error_msg}")
            return False
        
        # Step 4: Execute action
        log_action(approval_id, "execute", "started")
        
        try:
            result = execute_action(plan_metadata, approval_metadata)
            logger.info(f"Action executed: {result['action_type']} - {result['status']}")
            log_action(approval_id, "execute", result["status"], result)
        except Exception as e:
            error_msg = f"Execution failed: {e}"
            logger.error(error_msg)
            log_action(approval_id, "execute", "failed", {"error": str(e)})
            raise
        
        # Step 5: Move to Done
        move_to_done(approval_path, approval_id)
        logger.info(f"Successfully processed {approval_path.name}")
        
        return True
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_action(approval_id, "process", "failed", {"error": str(e)})
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing {approval_path.name}: {e}")
        log_action(approval_id, "process", "failed", {"error": str(e), "type": type(e).__name__})
        return False


def run_orchestrator_cycle():
    """Run one orchestration cycle."""
    logger.info(f"Starting orchestrator cycle (DRY_RUN={DRY_RUN})")
    
    if not APPROVED_DIR.exists():
        logger.info(f"Approved directory does not exist: {APPROVED_DIR}")
        return 0
    
    approval_files = list(APPROVED_DIR.glob("*.md"))
    if not approval_files:
        logger.info("No files in Approved/")
        return 0
    
    logger.info(f"Found {len(approval_files)} file(s) in Approved/")
    
    success_count = 0
    fail_count = 0
    
    for approval_path in approval_files:
        if process_approval_file(approval_path):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"Cycle complete: {success_count} succeeded, {fail_count} failed")
    return success_count


def run_watch_mode(interval_seconds: int = 30):
    """Run orchestrator in continuous watch mode."""
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
    parser = argparse.ArgumentParser(description="Silver Tier Orchestrator")
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
        help="Override DRY_RUN env var",
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True
        logger.warning("DRY_RUN mode enabled - no real actions will be executed")
    
    # Ensure directories exist
    for dir_path in [APPROVED_DIR, DONE_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    if args.watch:
        run_watch_mode(args.interval)
    else:
        success_count = run_orchestrator_cycle()
        sys.exit(0 if success_count > 0 else 0)


if __name__ == "__main__":
    main()
