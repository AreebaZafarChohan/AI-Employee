#!/usr/bin/env python3
"""LinkedIn Sales Post Engine — Silver Tier Skill.

Reads Business_Goals.md, revenue summary, and recent completed tasks,
then generates an engaging LinkedIn sales post draft saved to
/Pending_Approval/ for human review.

Constraints:
  - Never auto-publishes
  - Always saves as draft with requires_approval: true
  - Max 180 words
  - Focus on business value with CTA

Usage:
    python linkedin_sales_post_engine.py
    DRY_RUN=true python linkedin_sales_post_engine.py
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
PENDING_APPROVAL = VAULT / "Pending_Approval"
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
logger = logging.getLogger("linkedin_sales_post_engine")

# Post constraints
MAX_WORDS = 180

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def read_business_goals() -> list[str]:
    """Read business goals from Company_Handbook.md."""
    handbook_path = VAULT / "Company_Handbook.md"
    if not handbook_path.exists():
        return []

    content = handbook_path.read_text(encoding="utf-8")
    goals = []

    in_goals_section = False
    for line in content.split("\n"):
        if "##" in line and any(word in line.lower() for word in ["goal", "objective", "mission", "vision"]):
            in_goals_section = True
            continue
        if in_goals_section:
            if line.startswith("##"):
                in_goals_section = False
            elif line.strip().startswith("-"):
                goal = line.strip()[1:].strip()
                if len(goal) > 10:  # Skip very short items
                    goals.append(goal)

    return goals[:5]  # Max 5 goals


def read_revenue_summary() -> dict:
    """Read revenue/financial summary from Dashboard or accounting files."""
    summary = {
        "highlights": [],
        "metrics": {},
    }

    # Try Dashboard.md first
    dashboard_path = VAULT / "Dashboard.md"
    if dashboard_path.exists():
        metadata, body = load_markdown_file(dashboard_path)

        # Look for revenue mentions
        for line in body.split("\n"):
            line_lower = line.lower()
            if any(word in line_lower for word in ["revenue", "growth", "sales", "profit", "income"]):
                # Extract metric if present
                if ":" in line:
                    key, _, value = line.partition(":")
                    summary["metrics"][key.strip()] = value.strip()
                else:
                    summary["highlights"].append(line.strip())

    # Try accounting files
    accounting_dir = VAULT / "Accounting"
    if accounting_dir.exists():
        for md_file in accounting_dir.glob("*.md"):
            metadata, body = load_markdown_file(md_file)
            if "amount" in metadata:
                summary["highlights"].append(f"Transaction: ${metadata['amount']}")

    return summary


def read_completed_tasks(limit: int = 5) -> list[dict]:
    """Read last N completed tasks from /Done."""
    tasks = []

    if not DONE_DIR.exists():
        return tasks

    # Get all markdown files sorted by modification time
    md_files = sorted(
        [f for f in DONE_DIR.glob("*.md") if f.name != ".gitkeep"],
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    for md_file in md_files[:limit]:
        metadata, body = load_markdown_file(md_file)

        # Skip if file is too old or not a task
        if metadata.get("type") == "daily_briefing":
            continue

        tasks.append({
            "file": md_file.name,
            "title": md_file.stem.replace("-", " ").title(),
            "metadata": metadata,
            "body": body.strip()[:200],  # First 200 chars
        })

    return tasks


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def truncate_to_word_limit(text: str, max_words: int) -> str:
    """Truncate text to max words, preserving sentence boundaries."""
    words = text.split()
    if len(words) <= max_words:
        return text

    # Truncate and try to end at sentence boundary
    truncated = " ".join(words[:max_words])
    last_period = truncated.rfind(".")
    if last_period > len(truncated) * 0.7:  # If period is in last 30%
        return truncated[:last_period + 1]

    return truncated


def generate_post(business_goals: list[str], revenue: dict, tasks: list[dict]) -> str:
    """Generate LinkedIn sales post."""
    logger.info(f"Generating post with {len(business_goals)} goals, {len(revenue['highlights'])} revenue hints, {len(tasks)} tasks")

    # Build post sections
    sections = []

    # Hook (1-2 lines)
    hooks = [
        "🚀 Exciting progress this week!",
        "💼 Another week, another milestone!",
        "✨ Proud of what we've accomplished!",
        "🎯 Driving results for our clients!",
    ]
    sections.append(hooks[min(len(tasks) % len(hooks), len(hooks) - 1)])
    sections.append("")

    # Wins section (based on completed tasks)
    if tasks:
        win_count = min(3, len(tasks))
        sections.append(f"✅ {win_count} key wins this week:")
        sections.append("")
        for i, task in enumerate(tasks[:win_count], 1):
            # Create bullet point from task title
            title = task["title"][:60]
            sections.append(f"   • {title}")
        sections.append("")

    # Revenue/business value section
    if revenue["highlights"] or revenue["metrics"]:
        sections.append("📈 Business momentum continues...")
        sections.append("")
        if revenue["metrics"]:
            for key, value in list(revenue["metrics"].items())[:2]:
                sections.append(f"   • {key}: {value}")
        elif revenue["highlights"]:
            sections.append(f"   • {revenue['highlights'][0][:80]}")
        sections.append("")

    # Goals alignment
    if business_goals:
        sections.append(f"🎯 Focused on: {business_goals[0][:70]}")
        sections.append("")

    # Call-to-action
    ctas = [
        "💬 Let's connect if you're looking to drive similar results!",
        "📩 DM me to explore how we can help your business grow!",
        "🤝 Open to partnerships and collaborations!",
        "🔗 Reach out if you'd like to learn more!",
    ]
    sections.append(ctas[min(len(business_goals) % len(ctas), len(ctas) - 1)])
    sections.append("")

    # Hashtags
    sections.append("#BusinessGrowth #Success #Partnership #Innovation")

    # Join and trim to word limit
    post = "\n".join(sections)
    word_count = count_words(post)

    if word_count > MAX_WORDS:
        logger.warning(f"Post exceeds word limit ({word_count} > {MAX_WORDS}), truncating...")
        post = truncate_to_word_limit(post, MAX_WORDS)
        word_count = count_words(post)

    logger.info(f"Generated post: {word_count} words")
    return post


def create_approval_file(post: str) -> Optional[Path]:
    """Create approval request file in /Pending_Approval."""
    post_id = datetime.now().strftime("%Y%m%d")
    filename = f"LINKEDIN_POST_{post_id}.md"
    filepath = PENDING_APPROVAL / filename

    frontmatter = {
        "type": "social_post",
        "platform": "linkedin",
        "action": "publish",
        "requires_approval": True,
        "risk_level": "medium",
        "generated_at": get_timestamp(),
        "word_count": count_words(post),
        "status": "pending_approval",
    }

    content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip()}
---

# LinkedIn Sales Post Draft

**Platform:** LinkedIn
**Generated:** {get_timestamp()}
**Word Count:** {count_words(post)}
**Status:** Pending Approval

---

{post}

---

## Approval Required

⚠️ **Do NOT publish without human review**

This is an AI-generated draft. Please review for:
- Accuracy of claims and metrics
- Tone and brand alignment
- Appropriate timing
- CTA relevance

## Action Required

- [ ] Review post content
- [ ] Edit if needed
- [ ] **Approve** → Move to `/Approved` for publishing
- [ ] **Reject** → Move to `/Rejected` with feedback
"""

    if not DRY_RUN:
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Created approval request: {filename}")
    else:
        logger.info(f"[DRY_RUN] Would create: {filename}")
        logger.info("---")
        logger.info(content[:500])
        logger.info("...")

    log_generation(filename, "success" if not DRY_RUN else "dry_run", word_count=count_words(post))
    return filepath


def log_generation(filename: str, status: str, **details) -> None:
    """Log generation to daily log file."""
    log_file = LOGS_DIR / f"linkedin-sales-post-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": get_timestamp(),
        "filename": filename,
        "status": status,
        "dry_run": DRY_RUN,
        **details
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    logger.info(f"Starting LinkedIn Sales Post Engine (DRY_RUN={DRY_RUN})")

    # Read data sources
    logger.info("Reading data sources...")
    business_goals = read_business_goals()
    revenue = read_revenue_summary()
    tasks = read_completed_tasks(limit=5)

    logger.info(f"Loaded: {len(business_goals)} goals, {len(revenue['highlights'])} revenue hints, {len(tasks)} tasks")

    if not business_goals and not tasks:
        logger.warning("No business goals or tasks found. Post may be generic.")

    # Generate post
    post = generate_post(business_goals, revenue, tasks)

    # Create approval file
    filepath = create_approval_file(post)

    if filepath:
        logger.info(f"Post saved to: {filepath}")
        logger.info(f"Word count: {count_words(post)}")
        logger.info("Status: Pending approval (requires human review)")
    else:
        logger.error("Failed to create approval file")
        return 1

    logger.info("LinkedIn Sales Post Engine complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
