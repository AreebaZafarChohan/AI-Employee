#!/usr/bin/env python3
"""Daily Briefing Generator — Silver Tier Skill.

Reads Business_Goals.md, completed tasks from /Done (last 24h),
and accounting files, then generates a comprehensive daily briefing
saved to /Briefings/YYYY-MM-DD_Daily.md and updates Dashboard.

Usage:
    python daily_briefing_generator.py              # generate briefing
    DRY_RUN=true python daily_briefing_generator.py # preview only
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
BRIEFINGS_DIR = VAULT / "Briefings"
LOGS_DIR = VAULT / "Logs"
DONE_DIR = VAULT / "Done"

# Dry run mode
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("daily_briefing")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args():
    """Parse command-line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Daily Briefing Generator")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode (no file writes)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()

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
    except yaml.YAMLError:
        return {}, content


def load_markdown_file(path: Path) -> tuple[dict, str]:
    """Load markdown file and parse frontmatter."""
    if not path.exists():
        return {}, ""
    content = path.read_text(encoding="utf-8")
    return parse_frontmatter(content)


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_yesterday() -> datetime:
    """Get datetime for 24 hours ago."""
    return datetime.now(timezone.utc) - timedelta(days=1)


def log_generation(briefing_id: str, status: str, details: dict = None):
    """Log briefing generation to logs file."""
    log_file = LOGS_DIR / f"daily-briefing-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": get_timestamp(),
        "briefing_id": briefing_id,
        "status": status,
        "dry_run": DRY_RUN,
        **(details or {})
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


# ---------------------------------------------------------------------------
# Data Sources
# ---------------------------------------------------------------------------


def read_business_goals() -> list[str]:
    """Read business goals from Company_Handbook.md."""
    handbook_path = VAULT / "Company_Handbook.md"
    if not handbook_path.exists():
        return []

    content = handbook_path.read_text(encoding="utf-8")
    goals = []

    # Extract goals from various sections
    in_goals_section = False
    for line in content.split("\n"):
        if "##" in line and ("Goal" in line or "Objective" in line or "Mission" in line):
            in_goals_section = True
            continue
        if in_goals_section:
            if line.startswith("##"):
                in_goals_section = False
            elif line.strip().startswith("-"):
                goals.append(line.strip()[1:].strip())

    return goals


def read_completed_tasks(hours: int = 24) -> list[dict]:
    """Read completed tasks from /Done folder in last N hours."""
    tasks = []
    cutoff = get_yesterday()

    if not DONE_DIR.exists():
        return tasks

    for md_file in DONE_DIR.glob("*.md"):
        if md_file.name == ".gitkeep":
            continue

        metadata, body = load_markdown_file(md_file)

        # Try to get completion time from various sources
        completed_at = None

        # Check frontmatter timestamps
        for field in ["completed_at", "executed_at", "created_at", "received_at"]:
            if field in metadata:
                try:
                    ts = metadata[field].replace("Z", "+00:00")
                    completed_at = datetime.fromisoformat(ts)
                    break
                except (ValueError, TypeError):
                    pass

        # Fall back to file modification time
        if not completed_at:
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime, tz=timezone.utc)
                completed_at = mtime
            except (OSError, ValueError):
                completed_at = cutoff  # Include if we can't determine

        # Include if within time window
        if completed_at and completed_at >= cutoff:
            tasks.append({
                "file": md_file.name,
                "title": md_file.stem,
                "metadata": metadata,
                "body": body.strip()[:500],  # First 500 chars
                "completed_at": completed_at.isoformat(),
            })

    # Sort by completion time (most recent first)
    tasks.sort(key=lambda x: x["completed_at"], reverse=True)
    return tasks


def read_accounting_data() -> dict:
    """Read accounting/financial data if available."""
    accounting = {
        "transactions": [],
        "pending_payments": [],
        "revenue_hints": [],
    }

    # Look for accounting files
    accounting_files = list((VAULT / "Accounting").glob("*.md")) if (VAULT / "Accounting").exists() else []
    accounting_files += list(VAULT.glob("*.md"))

    for file_path in accounting_files:
        if "account" in file_path.name.lower() or "invoice" in file_path.name.lower() or "payment" in file_path.name.lower():
            metadata, body = load_markdown_file(file_path)

            # Extract financial information
            if "amount" in metadata or "payment" in metadata.get("type", "").lower():
                accounting["transactions"].append({
                    "file": file_path.name,
                    "metadata": metadata,
                })

            # Look for revenue mentions in body
            if any(word in body.lower() for word in ["$", "revenue", "payment", "invoice", "paid"]):
                accounting["revenue_hints"].append({
                    "file": file_path.name,
                    "snippet": body[:200],
                })

    return accounting


def read_dashboard() -> tuple[dict, str]:
    """Read current Dashboard.md."""
    dashboard_path = VAULT / "Dashboard.md"
    if not dashboard_path.exists():
        return {}, ""
    return load_markdown_file(dashboard_path)


# ---------------------------------------------------------------------------
# Briefing Generation
# ---------------------------------------------------------------------------


def generate_executive_summary(business_goals: list[str], tasks: list[dict]) -> str:
    """Generate executive summary section."""
    lines = [
        "## Executive Summary",
        "",
        f"Generated: {get_timestamp()}",
        "",
    ]

    if business_goals:
        lines.append("### Active Goals")
        for i, goal in enumerate(business_goals[:5], 1):
            lines.append(f"{i}. {goal}")
        lines.append("")

    # Summary stats
    total_tasks = len(tasks)
    if total_tasks > 0:
        lines.append("### Today's Activity")
        lines.append(f"- **Tasks Completed:** {total_tasks}")

        # Count by type
        type_counts = {}
        for task in tasks:
            task_type = task["metadata"].get("type", "general")
            type_counts[task_type] = type_counts.get(task_type, 0) + 1

        if type_counts:
            lines.append("- **By Type:**")
            for task_type, count in type_counts.items():
                lines.append(f"  - {task_type}: {count}")

        lines.append("")

    return "\n".join(lines)


def generate_revenue_snapshot(accounting: dict) -> str:
    """Generate revenue snapshot section."""
    lines = [
        "## Revenue Snapshot",
        "",
    ]

    if accounting["transactions"]:
        lines.append("### Recent Transactions")
        for txn in accounting["transactions"][:5]:
            amount = txn["metadata"].get("amount", "N/A")
            lines.append(f"- {txn['file']}: ${amount}")
        lines.append("")
    else:
        lines.append("*No recent transactions recorded.*")
        lines.append("")

    if accounting["revenue_hints"]:
        lines.append("### Revenue Signals")
        for hint in accounting["revenue_hints"][:3]:
            lines.append(f"- {hint['file']}: {hint['snippet'][:100]}...")
        lines.append("")

    return "\n".join(lines)


def generate_task_summary(tasks: list[dict]) -> str:
    """Generate task summary section."""
    lines = [
        "## Task Summary",
        "",
    ]

    if not tasks:
        lines.append("*No tasks completed in the last 24 hours.*")
        lines.append("")
        return "\n".join(lines)

    for task in tasks[:10]:  # Limit to 10 tasks
        title = task["title"].replace("-", " ").title()
        completed = task["completed_at"][:10] if task["completed_at"] else "Unknown"

        lines.append(f"### {title}")
        lines.append(f"**Completed:** {completed}")
        lines.append(f"**Source:** `{task['file']}`")

        # Extract key info from body
        if task["body"]:
            # Get first few bullet points or lines
            preview_lines = task["body"].split("\n")[:5]
            for line in preview_lines:
                if line.strip():
                    lines.append(f"> {line.strip()}")

        lines.append("")

    return "\n".join(lines)


def generate_bottlenecks(tasks: list[dict], business_goals: list[str]) -> str:
    """Identify potential bottlenecks."""
    lines = [
        "## Bottlenecks & Blockers",
        "",
    ]

    bottlenecks = []

    # Check for high priority items
    high_priority = [t for t in tasks if t["metadata"].get("priority") == "high"]
    if high_priority:
        bottlenecks.append(f"- **High Priority Items:** {len(high_priority)} tasks marked high priority")

    # Check for items pending approval
    pending_approval = [t for t in tasks if t["metadata"].get("requires_approval") or t["metadata"].get("status") == "pending"]
    if pending_approval:
        bottlenecks.append(f"- **Pending Approval:** {len(pending_approval)} items awaiting approval")

    # Check goal alignment
    if business_goals and len(tasks) < len(business_goals):
        bottlenecks.append(f"- **Goal Progress:** Only {len(tasks)} tasks completed vs {len(business_goals)} active goals")

    if bottlenecks:
        lines.extend(bottlenecks)
    else:
        lines.append("*No significant bottlenecks identified.*")

    lines.append("")
    return "\n".join(lines)


def generate_suggestions(tasks: list[dict], business_goals: list[str]) -> str:
    """Generate actionable suggestions."""
    lines = [
        "## Suggestions & Next Steps",
        "",
    ]

    suggestions = []

    # Suggest reviewing pending items
    suggestions.append("1. **Review Pending Items** — Check Needs_Action/ for items requiring attention")

    # Suggest goal alignment
    if business_goals:
        suggestions.append(f"2. **Align with Goals** — Ensure upcoming tasks support {len(business_goals)} active business goals")

    # Suggest processing emails
    email_tasks = [t for t in tasks if t["metadata"].get("type") == "email"]
    if email_tasks:
        suggestions.append(f"3. **Follow up on Emails** — {len(email_tasks)} emails processed today may need responses")

    # Suggest weekly review if many tasks completed
    if len(tasks) >= 5:
        suggestions.append("4. **Weekly Review** — High task volume suggests scheduling a weekly review")

    lines.extend(suggestions)
    lines.append("")

    return "\n".join(lines)


def generate_full_briefing() -> str:
    """Generate complete daily briefing."""
    logger.info("Reading data sources...")

    # Read all sources
    business_goals = read_business_goals()
    completed_tasks = read_completed_tasks(hours=24)
    accounting = read_accounting_data()

    logger.info(f"Loaded: {len(business_goals)} goals, {len(completed_tasks)} tasks, {len(accounting['transactions'])} transactions")

    # Generate sections
    sections = [
        "---",
        f"briefing_id: {datetime.now().strftime('%Y%m%d')}",
        f"generated_at: \"{get_timestamp()}\"",
        "type: daily_briefing",
        "period: 24h",
        "---",
        "",
        f"# Daily Briefing — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        generate_executive_summary(business_goals, completed_tasks),
        generate_revenue_snapshot(accounting),
        generate_task_summary(completed_tasks),
        generate_bottlenecks(completed_tasks, business_goals),
        generate_suggestions(completed_tasks, business_goals),
        "---",
        "*Generated by AI Employee Daily Briefing Generator*",
    ]

    return "\n".join(sections)


def update_dashboard(briefing_file: Path):
    """Update Dashboard.md with briefing summary."""
    dashboard_path = VAULT / "Dashboard.md"

    if not dashboard_path.exists():
        logger.warning("Dashboard.md not found, skipping update")
        return

    metadata, body = load_markdown_file(dashboard_path)

    # Check if link already exists
    briefing_link = f"[[{briefing_file.name}]]"
    if briefing_link in body:
        logger.info("Briefing link already exists in Dashboard.md")
        return

    # Find or create "Daily Briefings" section
    section_marker = "## Daily Briefings"
    if section_marker not in body:
        # Add new section before Quick Links
        new_section = f"\n{section_marker}\n\n- {briefing_link}\n\n"
        if "## Quick Links" in body:
            body = body.replace("## Quick Links", new_section + "## Quick Links")
        else:
            body += new_section
    else:
        # Add to existing section
        lines = body.split("\n")
        new_body = []
        for line in lines:
            new_body.append(line)
            if line.startswith(section_marker):
                # Add link after section header
                new_body.append(f"\n- {briefing_link}")
        body = "\n".join(new_body)

    # Reconstruct file
    if metadata:
        new_content = f"---\n{yaml.dump(metadata, default_flow_style=False, sort_keys=False)}---\n{body}"
    else:
        new_content = body

    if not DRY_RUN:
        dashboard_path.write_text(new_content, encoding="utf-8")
        logger.info("Dashboard.md updated")
    else:
        logger.info("[DRY_RUN] Would update Dashboard.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    args = parse_args()
    
    # Override DRY_RUN from command line
    global DRY_RUN
    if args.dry_run:
        DRY_RUN = True
    
    # Override LOG_LEVEL from command line
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting daily briefing generation (DRY_RUN={DRY_RUN})")

    # Ensure directories exist
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate briefing
    briefing_content = generate_full_briefing()

    # Save briefing
    briefing_filename = f"{datetime.now().strftime('%Y-%m-%d')}_Daily.md"
    briefing_path = BRIEFINGS_DIR / briefing_filename

    if not DRY_RUN:
        briefing_path.write_text(briefing_content, encoding="utf-8")
        logger.info(f"Briefing saved to: {briefing_path}")
    else:
        logger.info(f"[DRY_RUN] Would save to: {briefing_path}")
        logger.info("---")
        logger.info("Briefing preview:")
        for line in briefing_content.split("\n")[:20]:
            logger.info(f"  {line}")
        logger.info("  ...")
        logger.info("---")

    # Update Dashboard
    if not DRY_RUN:
        update_dashboard(briefing_path)

    # Log generation
    log_generation(
        briefing_id=datetime.now().strftime("%Y%m%d"),
        status="success" if not DRY_RUN else "dry_run",
        details={
            "briefing_file": str(briefing_path),
            "goals_read": len(read_business_goals()),
            "tasks_read": len(read_completed_tasks()),
        }
    )

    logger.info("Daily briefing generation complete")

    return 0


if __name__ == "__main__":
    sys.exit(main())
