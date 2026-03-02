#!/usr/bin/env python3
"""LinkedIn Post Generator — Silver Tier Skill.

Reads Business_Goals.md, recent completed tasks, and revenue highlights,
then generates a professional LinkedIn post draft saved to /Social/.

Constraints:
  - Never publishes automatically
  - Always saves as draft with requires_approval: true
  - Max 200 words per post

Usage:
    python linkedin_post_generator.py
    LINKEDIN_DRY_RUN=true python linkedin_post_generator.py
"""

import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
SOCIAL = VAULT / "Social"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"

HANDBOOK = VAULT / "Company_Handbook.md"
DASHBOARD = VAULT / "Dashboard.md"

DRY_RUN: bool = os.getenv("LINKEDIN_DRY_RUN", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

def _build_logger() -> logging.Logger:
    level = getattr(logging, os.getenv("LINKEDIN_LOG_LEVEL", "INFO").upper(), logging.INFO)
    logger = logging.getLogger("linkedin_post_generator")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | linkedin_post_generator | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    LOGS.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fh = logging.FileHandler(LOGS / f"linkedin-post-{today}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


logger = _build_logger()

# ---------------------------------------------------------------------------
# Context gathering
# ---------------------------------------------------------------------------

def _read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_business_goals(handbook_text: str) -> list[str]:
    """Pull goal/objective lines from Company_Handbook or any goals file."""
    goals = []
    in_goals = False
    for line in handbook_text.splitlines():
        lower = line.lower()
        if any(kw in lower for kw in ("goal", "objective", "mission", "vision", "focus")):
            in_goals = True
        if in_goals and line.strip().startswith(("- ", "* ", "•")):
            goal = line.strip().lstrip("-*• ").strip()
            if goal:
                goals.append(goal)
        if in_goals and line.startswith("#") and "goal" not in lower:
            in_goals = False
    return goals[:5]


def _read_recent_completed(done_dir: Path, limit: int = 6) -> list[dict]:
    """Return the most recently modified .md files from /Done (excluding meta files)."""
    if not done_dir.exists():
        return []
    files = sorted(
        [f for f in done_dir.glob("*.md") if ".meta" not in f.name],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:limit]

    items = []
    for f in files:
        text = _read_file_safe(f)
        # Extract title from first heading or filename
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem.replace("-", " ").title()
        # Extract first bullet as summary
        bullet_match = re.search(r"^[-*]\s+(.+)$", text, re.MULTILINE)
        summary = bullet_match.group(1).strip() if bullet_match else ""
        items.append({"title": title, "summary": summary, "file": f.name})
    return items


def _extract_revenue_highlights(handbook_text: str, dashboard_text: str) -> list[str]:
    """Pull revenue/metric mentions from available vault files."""
    highlights = []
    combined = handbook_text + "\n" + dashboard_text
    for line in combined.splitlines():
        lower = line.lower()
        if any(kw in lower for kw in ("revenue", "growth", "client", "mrr", "arr", "profit", "sales", "deal")):
            clean = line.strip().lstrip("-*•# ").strip()
            if clean and len(clean) > 10:
                highlights.append(clean)
    return highlights[:3]

# ---------------------------------------------------------------------------
# Post generation
# ---------------------------------------------------------------------------

def _word_count(text: str) -> int:
    return len(text.split())


def _trim_to_word_limit(text: str, limit: int = 200) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    # Trim to limit, ending on a sentence boundary if possible
    trimmed = " ".join(words[:limit])
    last_period = max(trimmed.rfind("."), trimmed.rfind("!"), trimmed.rfind("?"))
    if last_period > len(trimmed) * 0.6:
        return trimmed[: last_period + 1]
    return trimmed + "…"


def generate_post(
    goals: list[str],
    completed: list[dict],
    revenue: list[str],
) -> str:
    """Build the LinkedIn post body text (≤200 words)."""
    now = datetime.now(timezone.utc)
    month = now.strftime("%B %Y")

    # --- Hook ---
    if completed:
        first = completed[0]["title"]
        hook = f"Big things happening this {month}."
    else:
        hook = f"Reflecting on a productive {month}."

    # --- Body: recent wins ---
    wins_lines = []
    for item in completed[:3]:
        wins_lines.append(f"✅ {item['title']}")

    wins_block = "\n".join(wins_lines) if wins_lines else ""

    # --- Revenue / growth signal ---
    revenue_line = ""
    if revenue:
        revenue_line = f"\n\n{revenue[0]}"

    # --- Goals / mission signal ---
    goal_line = ""
    if goals:
        goal_line = f"\n\nOur focus: {goals[0].lower().rstrip('.')}."

    # --- CTA ---
    cta = "\n\nIf you're building something meaningful and need a team that executes — let's connect."

    # --- Assemble ---
    body = (
        f"{hook}\n\n"
        f"Here's what we shipped recently:\n\n"
        f"{wins_block}"
        f"{revenue_line}"
        f"{goal_line}"
        f"{cta}"
    )

    return _trim_to_word_limit(body, 200)

# ---------------------------------------------------------------------------
# Draft file rendering
# ---------------------------------------------------------------------------

def render_draft(post_body: str, context: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    word_count = _word_count(post_body)

    frontmatter = (
        "---\n"
        "type: social_post\n"
        "platform: LinkedIn\n"
        "status: draft\n"
        "requires_approval: true\n"
        f'generated_at: "{now}"\n'
        f"word_count: {word_count}\n"
        "published: false\n"
        "---\n"
    )

    sources_md = ""
    if context.get("goals"):
        sources_md += f"\n**Goals read from:** Company_Handbook.md\n"
    if context.get("completed"):
        files = ", ".join(f"`{i['file']}`" for i in context["completed"][:3])
        sources_md += f"**Recent tasks read from:** {files}\n"
    if context.get("revenue"):
        sources_md += f"**Revenue context:** {context['revenue'][0]}\n"

    body = (
        f"# LinkedIn Draft — {today}\n\n"
        "## Draft Post\n\n"
        "---\n\n"
        f"{post_body}\n\n"
        "---\n\n"
        f"**Word count:** {word_count} / 200\n\n"
        "## Approval Required\n\n"
        "- [ ] Review post content and tone\n"
        "- [ ] Edit if needed\n"
        "- [ ] **Approve** → publish manually on LinkedIn\n"
        "- [ ] **Reject** → delete or revise\n\n"
        "## Context Sources\n"
        f"{sources_md}\n"
        "> ⚠️ This draft was auto-generated. Do NOT publish without human review.\n"
    )

    return frontmatter + "\n" + body

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    try:
        from src.utils.logger import log_action, set_default_logs_dir
        set_default_logs_dir(LOGS)
        _log = log_action
    except ImportError:
        def _log(action: str, target: str, detail: str) -> None:
            logger.debug("log_action | %s | %s | %s", action, target, detail)

    if DRY_RUN:
        logger.info("=== DRY RUN MODE — no files will be written ===")

    logger.info("Reading context from vault…")

    handbook_text = _read_file_safe(HANDBOOK)
    dashboard_text = _read_file_safe(DASHBOARD)

    goals = _extract_business_goals(handbook_text)
    completed = _read_recent_completed(DONE)
    revenue = _extract_revenue_highlights(handbook_text, dashboard_text)

    logger.info(
        "Context loaded — goals=%d, completed_tasks=%d, revenue_hints=%d",
        len(goals), len(completed), len(revenue),
    )

    post_body = generate_post(goals, completed, revenue)
    word_count = _word_count(post_body)
    logger.info("Post generated — %d words", word_count)

    # Build draft filename
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"LinkedIn_Draft_{today}.md"
    draft_path = SOCIAL / filename

    context = {"goals": goals, "completed": completed, "revenue": revenue}
    draft_content = render_draft(post_body, context)

    if not DRY_RUN:
        SOCIAL.mkdir(parents=True, exist_ok=True)
        # Handle same-day collision
        if draft_path.exists():
            ts = datetime.now(timezone.utc).strftime("%H%M%S")
            draft_path = SOCIAL / f"LinkedIn_Draft_{today}_{ts}.md"
        draft_path.write_text(draft_content, encoding="utf-8")

    logger.info(
        "[%s] Draft saved: %s", "DRY" if DRY_RUN else "OK", draft_path.name
    )
    _log("linkedin_draft_created", draft_path.name, f"words={word_count} | requires_approval=true")

    print(f"\n{'='*60}")
    print(f"  LinkedIn Draft: {draft_path.name}")
    print(f"  Words: {word_count}/200")
    print(f"  Saved to: Social/{draft_path.name}")
    print(f"  Requires approval: YES")
    print(f"{'='*60}\n")
    print(post_body)
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    run()
