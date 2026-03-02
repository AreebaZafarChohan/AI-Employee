#!/usr/bin/env python3
"""Monday CEO Briefing Generator — Silver Tier Skill.

Reads Company_Handbook.md, completed tasks from /Done (last 7 days),
accounting files, and pending approvals, then generates a comprehensive
weekly CEO briefing saved to /Briefings/YYYY-MM-DD_Monday.md and updates Dashboard.

Usage:
    python monday_ceo_briefing.py              # generate briefing
    DRY_RUN=true python monday_ceo_briefing.py # preview only
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
ACCOUNTING_DIR = VAULT / "Accounting"
PENDING_APPROVAL_DIR = VAULT / "Pending_Approval"

LOOKBACK_DAYS = int(os.getenv("BRIEFING_LOOKBACK_DAYS", "7"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("monday_ceo_briefing")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args():
    """Parse command-line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Monday CEO Briefing Generator")
    parser.add_argument("--dry-run", action="store_true", help="Preview mode (no file writes)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
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
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_cutoff() -> datetime:
    """Get datetime for N days ago."""
    return datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)


def log_generation(briefing_id: str, status: str, details: dict = None):
    log_file = LOGS_DIR / f"monday-ceo-briefing-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "timestamp": get_timestamp(),
        "briefing_id": briefing_id,
        "status": status,
        "dry_run": DRY_RUN,
        **(details or {}),
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


def read_completed_tasks() -> list[dict]:
    """Read completed tasks from /Done folder in last N days."""
    tasks = []
    cutoff = get_cutoff()

    if not DONE_DIR.exists():
        return tasks

    for md_file in DONE_DIR.glob("*.md"):
        if md_file.name == ".gitkeep":
            continue

        metadata, body = load_markdown_file(md_file)
        completed_at = None

        for field in ["completed_at", "executed_at", "created_at", "received_at"]:
            if field in metadata:
                try:
                    ts = metadata[field].replace("Z", "+00:00")
                    completed_at = datetime.fromisoformat(ts)
                    break
                except (ValueError, TypeError):
                    pass

        if not completed_at:
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime, tz=timezone.utc)
                completed_at = mtime
            except (OSError, ValueError):
                completed_at = cutoff

        if completed_at and completed_at >= cutoff:
            tasks.append({
                "file": md_file.name,
                "title": md_file.stem,
                "metadata": metadata,
                "body": body.strip()[:500],
                "completed_at": completed_at.isoformat(),
            })

    tasks.sort(key=lambda x: x["completed_at"], reverse=True)
    return tasks


def read_accounting_data() -> dict:
    """Read accounting/financial data from Accounting/ and Done/ invoices."""
    accounting = {
        "transactions": [],
        "pending_payments": [],
        "revenue_hints": [],
        "subscriptions": [],
    }

    search_dirs = []
    if ACCOUNTING_DIR.exists():
        search_dirs.append(ACCOUNTING_DIR)

    for search_dir in search_dirs:
        for file_path in search_dir.glob("*.md"):
            metadata, body = load_markdown_file(file_path)

            if "amount" in metadata or "payment" in metadata.get("type", "").lower():
                accounting["transactions"].append({
                    "file": file_path.name,
                    "metadata": metadata,
                })

            if any(word in body.lower() for word in ["$", "revenue", "payment", "invoice", "paid"]):
                accounting["revenue_hints"].append({
                    "file": file_path.name,
                    "snippet": body[:200],
                })

            # Detect subscriptions
            if any(word in body.lower() for word in ["subscription", "recurring", "monthly", "annual"]):
                accounting["subscriptions"].append({
                    "file": file_path.name,
                    "metadata": metadata,
                    "snippet": body[:200],
                })

    # Also scan Done/ for invoice-related completions in the window
    if DONE_DIR.exists():
        cutoff = get_cutoff()
        for md_file in DONE_DIR.glob("*.md"):
            if any(kw in md_file.name.lower() for kw in ["invoice", "payment", "receipt"]):
                metadata, body = load_markdown_file(md_file)
                completed_at = None
                for field in ["completed_at", "executed_at", "created_at"]:
                    if field in metadata:
                        try:
                            ts = metadata[field].replace("Z", "+00:00")
                            completed_at = datetime.fromisoformat(ts)
                            break
                        except (ValueError, TypeError):
                            pass
                if not completed_at:
                    try:
                        completed_at = datetime.fromtimestamp(md_file.stat().st_mtime, tz=timezone.utc)
                    except (OSError, ValueError):
                        completed_at = cutoff

                if completed_at >= cutoff:
                    if any(word in body.lower() for word in ["$", "amount", "payment", "revenue"]):
                        accounting["revenue_hints"].append({
                            "file": md_file.name,
                            "snippet": body[:200],
                        })

    return accounting


def read_pending_approvals() -> list[dict]:
    """Read pending approval items from Pending_Approval/ folder."""
    approvals = []
    if not PENDING_APPROVAL_DIR.exists():
        return approvals

    for md_file in PENDING_APPROVAL_DIR.glob("*.md"):
        if md_file.name == ".gitkeep":
            continue
        metadata, body = load_markdown_file(md_file)
        approvals.append({
            "file": md_file.name,
            "title": md_file.stem.replace("-", " ").title(),
            "metadata": metadata,
            "body": body.strip()[:300],
        })

    return approvals


# ---------------------------------------------------------------------------
# Briefing Sections
# ---------------------------------------------------------------------------


def generate_executive_summary(business_goals: list[str], tasks: list[dict]) -> str:
    lines = [
        "## 1. Executive Summary",
        "",
        f"**Report Period:** {LOOKBACK_DAYS}-day window ending {datetime.now().strftime('%Y-%m-%d')}",
        f"**Generated:** {get_timestamp()}",
        "",
    ]

    if business_goals:
        lines.append("### Active Goals")
        for i, goal in enumerate(business_goals[:5], 1):
            lines.append(f"{i}. {goal}")
        lines.append("")

    total_tasks = len(tasks)
    lines.append("### Week Activity")
    lines.append(f"- **Tasks Completed:** {total_tasks}")

    if total_tasks > 0:
        type_counts = {}
        for task in tasks:
            task_type = task["metadata"].get("type", "general")
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        if type_counts:
            lines.append("- **By Type:**")
            for task_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  - {task_type}: {count}")

    lines.append("")
    return "\n".join(lines)


def generate_revenue_summary(accounting: dict) -> str:
    lines = [
        "## 2. Revenue Summary",
        "",
    ]

    if accounting["transactions"]:
        lines.append("### Transactions This Week")
        for txn in accounting["transactions"][:10]:
            amount = txn["metadata"].get("amount", "N/A")
            lines.append(f"- **{txn['file']}**: ${amount}")
        lines.append("")
    else:
        lines.append("*No transactions recorded this week.*")
        lines.append("")

    if accounting["revenue_hints"]:
        lines.append("### Revenue Signals")
        for hint in accounting["revenue_hints"][:5]:
            lines.append(f"- **{hint['file']}**: {hint['snippet'][:100]}...")
        lines.append("")

    return "\n".join(lines)


def generate_bottlenecks(tasks: list[dict], business_goals: list[str]) -> str:
    lines = [
        "## 3. Bottlenecks & Blockers",
        "",
    ]

    bottlenecks = []

    high_priority = [t for t in tasks if t["metadata"].get("priority") == "high"]
    if high_priority:
        bottlenecks.append(f"- **High Priority Items:** {len(high_priority)} tasks marked high priority")

    pending_in_tasks = [t for t in tasks if t["metadata"].get("requires_approval") or t["metadata"].get("status") == "pending"]
    if pending_in_tasks:
        bottlenecks.append(f"- **Stuck on Approval:** {len(pending_in_tasks)} completed items had pending status")

    if business_goals and len(tasks) < len(business_goals):
        bottlenecks.append(f"- **Goal Progress Gap:** Only {len(tasks)} tasks completed vs {len(business_goals)} active goals this week")

    # Check for days with zero activity
    if tasks:
        task_dates = set()
        for t in tasks:
            try:
                task_dates.add(t["completed_at"][:10])
            except (KeyError, TypeError):
                pass
        idle_days = LOOKBACK_DAYS - len(task_dates)
        if idle_days > 2:
            bottlenecks.append(f"- **Idle Days:** {idle_days} days with no completed tasks this week")

    if bottlenecks:
        lines.extend(bottlenecks)
    else:
        lines.append("*No significant bottlenecks identified.*")

    lines.append("")
    return "\n".join(lines)


def generate_subscription_audit(accounting: dict) -> str:
    lines = [
        "## 4. Subscription Audit",
        "",
    ]

    if accounting["subscriptions"]:
        lines.append("### Recurring Payments / Subscriptions Detected")
        for sub in accounting["subscriptions"][:10]:
            amount = sub["metadata"].get("amount", "N/A")
            name = sub["file"].replace(".md", "").replace("-", " ").title()
            lines.append(f"- **{name}**: ${amount}" if amount != "N/A" else f"- **{name}**: See file for details")
        lines.append("")
    else:
        lines.append("*No subscription or recurring payment files detected in Accounting/.*")
        lines.append("")

    return "\n".join(lines)


def generate_suggestions(tasks: list[dict], business_goals: list[str], pending_approvals: list[dict]) -> str:
    lines = [
        "## 5. Suggestions & Next Steps",
        "",
    ]

    suggestions = []
    suggestions.append("1. **Review Pending Approvals** — Clear the approval queue to unblock downstream work")

    if business_goals:
        suggestions.append(f"2. **Align with Goals** — Map this week's {len(tasks)} tasks against {len(business_goals)} active goals to identify gaps")

    email_tasks = [t for t in tasks if t["metadata"].get("type") == "email"]
    if email_tasks:
        suggestions.append(f"3. **Follow up on Emails** — {len(email_tasks)} emails processed this week may need responses")

    if len(tasks) < 3:
        suggestions.append("4. **Investigate Low Output** — Fewer than 3 tasks completed this week; check for blockers or resource issues")
    elif len(tasks) >= 10:
        suggestions.append("4. **Capacity Check** — High task volume ({} tasks); ensure quality is maintained".format(len(tasks)))

    if pending_approvals:
        suggestions.append(f"5. **Approval Backlog** — {len(pending_approvals)} items in Pending_Approval/ need CEO attention")

    lines.extend(suggestions)
    lines.append("")
    return "\n".join(lines)


def generate_pending_approvals_section(pending_approvals: list[dict]) -> str:
    lines = [
        "## 6. Pending Approvals Overview",
        "",
    ]

    if not pending_approvals:
        lines.append("*No items pending approval.*")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"**Total Pending:** {len(pending_approvals)}")
    lines.append("")

    for item in pending_approvals[:15]:
        priority = item["metadata"].get("priority", "normal")
        item_type = item["metadata"].get("type", "unknown")
        lines.append(f"- **{item['title']}** — Type: {item_type}, Priority: {priority}")
        lines.append(f"  - Source: `{item['file']}`")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full Briefing
# ---------------------------------------------------------------------------


def generate_full_briefing() -> str:
    logger.info("Reading data sources (7-day window)...")

    business_goals = read_business_goals()
    completed_tasks = read_completed_tasks()
    accounting = read_accounting_data()
    pending_approvals = read_pending_approvals()

    logger.info(
        f"Loaded: {len(business_goals)} goals, {len(completed_tasks)} tasks, "
        f"{len(accounting['transactions'])} transactions, {len(pending_approvals)} pending approvals"
    )

    today = datetime.now().strftime("%Y-%m-%d")
    sections = [
        "---",
        f"briefing_id: {datetime.now().strftime('%Y%m%d')}_weekly",
        f'generated_at: "{get_timestamp()}"',
        "type: monday_ceo_briefing",
        f"period: {LOOKBACK_DAYS}d",
        f"lookback_days: {LOOKBACK_DAYS}",
        "---",
        "",
        f"# Monday CEO Briefing — {today}",
        "",
        generate_executive_summary(business_goals, completed_tasks),
        generate_revenue_summary(accounting),
        generate_bottlenecks(completed_tasks, business_goals),
        generate_subscription_audit(accounting),
        generate_suggestions(completed_tasks, business_goals, pending_approvals),
        generate_pending_approvals_section(pending_approvals),
        "---",
        "*Generated by AI Employee Monday CEO Briefing Generator*",
    ]

    return "\n".join(sections)


def update_dashboard(briefing_file: Path):
    """Update Dashboard.md with briefing link under Weekly Briefings section."""
    dashboard_path = VAULT / "Dashboard.md"

    if not dashboard_path.exists():
        logger.warning("Dashboard.md not found, skipping update")
        return

    metadata, body = load_markdown_file(dashboard_path)

    briefing_link = f"[[{briefing_file.name}]]"
    if briefing_link in body:
        logger.info("Briefing link already exists in Dashboard.md")
        return

    section_marker = "## Weekly Briefings"
    if section_marker not in body:
        new_section = f"\n{section_marker}\n\n- {briefing_link}\n\n"
        if "## Quick Links" in body:
            body = body.replace("## Quick Links", new_section + "## Quick Links")
        elif "## Daily Briefings" in body:
            body = body.replace("## Daily Briefings", new_section + "## Daily Briefings")
        else:
            body += new_section
    else:
        lines = body.split("\n")
        new_body = []
        for line in lines:
            new_body.append(line)
            if line.startswith(section_marker):
                new_body.append(f"\n- {briefing_link}")
        body = "\n".join(new_body)

    if metadata:
        new_content = f"---\n{yaml.dump(metadata, default_flow_style=False, sort_keys=False)}---\n{body}"
    else:
        new_content = body

    if not DRY_RUN:
        dashboard_path.write_text(new_content, encoding="utf-8")
        logger.info("Dashboard.md updated with weekly briefing link")
    else:
        logger.info("[DRY_RUN] Would update Dashboard.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    args = parse_args()

    global DRY_RUN
    if args.dry_run:
        DRY_RUN = True
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting Monday CEO briefing generation (DRY_RUN={DRY_RUN}, lookback={LOOKBACK_DAYS}d)")

    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    briefing_content = generate_full_briefing()

    briefing_filename = f"{datetime.now().strftime('%Y-%m-%d')}_Monday.md"
    briefing_path = BRIEFINGS_DIR / briefing_filename

    if not DRY_RUN:
        briefing_path.write_text(briefing_content, encoding="utf-8")
        logger.info(f"Briefing saved to: {briefing_path}")
    else:
        logger.info(f"[DRY_RUN] Would save to: {briefing_path}")
        logger.info("---")
        logger.info("Briefing preview:")
        for line in briefing_content.split("\n")[:30]:
            logger.info(f"  {line}")
        logger.info("  ...")
        logger.info("---")

    if not DRY_RUN:
        update_dashboard(briefing_path)

    log_generation(
        briefing_id=datetime.now().strftime("%Y%m%d") + "_weekly",
        status="success" if not DRY_RUN else "dry_run",
        details={
            "briefing_file": str(briefing_path),
            "goals_read": len(read_business_goals()),
            "tasks_read": len(read_completed_tasks()),
            "pending_approvals": len(read_pending_approvals()),
        },
    )

    logger.info("Monday CEO briefing generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
