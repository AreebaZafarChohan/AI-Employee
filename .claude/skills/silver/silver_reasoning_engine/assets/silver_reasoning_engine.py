#!/usr/bin/env python3
"""Silver Reasoning Engine.

Deep-reasons over every item in /Needs_Action:
  - Summarizes content
  - Identifies objective
  - Classifies domain (personal/business/finance/social)
  - Computes risk level (high/medium/low)
  - Computes confidence score (0-100)
  - Generates structured Plan in /Plans
  - Routes requires_approval items to /Pending_Approval
  - Logs all actions to /Logs

Constraints:
  - Never executes any external action
  - Only reads /Needs_Action, writes /Plans, /Pending_Approval, /Logs

Usage:
    python silver_reasoning_engine.py
    SRE_DRY_RUN=true python silver_reasoning_engine.py
    SRE_LOG_LEVEL=DEBUG python silver_reasoning_engine.py
"""

import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[5]   # project root
sys.path.insert(0, str(ROOT))

VAULT          = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION   = VAULT / "Needs_Action"
PLANS          = VAULT / "Plans"
PENDING        = VAULT / "Pending_Approval"
LOGS           = VAULT / "Logs"

DRY_RUN: bool  = os.getenv("SRE_DRY_RUN", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Risk keyword tables
# ---------------------------------------------------------------------------

HIGH_KEYWORDS = {
    "payment", "invoice", "wire", "transfer", "bank account",
    "new contact", "unknown sender", "credentials", "password",
    "legal", "lawsuit", "court", "breach", "overdue", "urgent",
    "critical", "emergency", "terminate", "fired",
}

MEDIUM_KEYWORDS = {
    "post", "publish", "linkedin", "twitter", "facebook",
    "email to", "outreach", "schedule", "meeting request",
    "announcement", "press release", "public", "external",
    "client", "vendor", "partner",
}

LOW_KEYWORDS = {
    "update", "status", "internal", "note", "reminder",
    "draft", "read", "review", "summary", "report", "log",
}

# Domain keyword tables
DOMAIN_KEYWORDS = {
    "finance":  {"invoice", "payment", "budget", "revenue", "expense", "tax",
                 "accounting", "bank", "money", "cost", "price", "fee", "salary"},
    "social":   {"linkedin", "twitter", "facebook", "instagram", "post",
                 "publish", "social media", "content", "announcement", "press"},
    "business": {"client", "project", "contract", "meeting", "vendor",
                 "partner", "proposal", "deliverable", "milestone", "team"},
    "personal": {"personal", "family", "health", "appointment", "reminder",
                 "grocery", "home", "car", "vacation", "birthday"},
}

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

def _build_logger() -> logging.Logger:
    level_name = os.getenv("SRE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("silver_reasoning_engine")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | silver_reasoning_engine | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    LOGS.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fh = logging.FileHandler(LOGS / f"silver-reasoning-engine-{today}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


log = _build_logger()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(text: str) -> str:
    """Convert text to URL-safe slug (max 40 chars)."""
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:40]


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        log.warning("Cannot read %s: %s", path, exc)
        return ""


def _extract_frontmatter(content: str) -> dict:
    """Extract simple YAML frontmatter key: value pairs."""
    meta: dict = {}
    if not content.startswith("---"):
        return meta
    end = content.find("---", 3)
    if end == -1:
        return meta
    block = content[3:end]
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta


def _extract_title(content: str, filename: str) -> str:
    """Best-effort title from frontmatter subject/title or first H1."""
    meta = _extract_frontmatter(content)
    for key in ("subject", "title", "name"):
        if meta.get(key):
            return meta[key]
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return filename.replace(".md", "").replace("-", " ").replace("_", " ").title()


def _body_text(content: str) -> str:
    """Strip frontmatter, return plain body."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].strip()
    return content.strip()

# ---------------------------------------------------------------------------
# Reasoning steps
# ---------------------------------------------------------------------------

def _summarize(title: str, body: str) -> str:
    """2–3 sentence summary from first meaningful paragraphs."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()]
    # Drop lines that are purely markdown headings or checklist items
    clean = []
    for p in paragraphs:
        lines = [l for l in p.splitlines()
                 if not l.strip().startswith("#")
                 and not l.strip().startswith("- [ ]")
                 and not l.strip().startswith("- [x]")]
        text = " ".join(lines).strip()
        if len(text) > 20:
            clean.append(text)
        if len(clean) >= 3:
            break

    if not clean:
        return f'Item titled "{title}" with no extractable body content.'

    summary_parts = clean[:2]
    summary = "  ".join(summary_parts)
    # Truncate to ~300 chars
    if len(summary) > 300:
        summary = summary[:297] + "..."
    return summary


def _identify_objective(title: str, body: str) -> str:
    """Single sentence: what action is ultimately being requested."""
    body_lower = body.lower()

    # Action verb patterns
    action_patterns = [
        (r"\bplease\s+([\w\s]{3,40})", "Requested action: {}"),
        (r"\bneed(s)?\s+to\s+([\w\s]{3,40})", "Needs to: {}"),
        (r"\bask(ing)?\s+(?:you\s+)?to\s+([\w\s]{3,40})", "Asking to: {}"),
        (r"\bcan\s+you\s+([\w\s]{3,40})", "Requesting: {}"),
        (r"\bshould\s+([\w\s]{3,40})", "Should: {}"),
    ]

    for pattern, template in action_patterns:
        m = re.search(pattern, body_lower)
        if m:
            verb_phrase = m.group(m.lastindex).strip().rstrip(".,;").capitalize()
            return template.format(verb_phrase) + "."

    # Fall back to title-based objective
    return f'Process and respond to: "{title}".'


def _classify_domain(title: str, body: str) -> str:
    """Classify into personal | business | finance | social."""
    text = (title + " " + body).lower()
    scores: dict[str, int] = {d: 0 for d in DOMAIN_KEYWORDS}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[domain] += 1

    best_domain = max(scores, key=lambda d: scores[d])
    if scores[best_domain] == 0:
        return "business"   # safe default
    return best_domain


def _score_risk(title: str, body: str) -> str:
    """Return high | medium | low."""
    text = (title + " " + body).lower()

    for kw in HIGH_KEYWORDS:
        if kw in text:
            log.debug("Risk HIGH triggered by keyword: %s", kw)
            return "high"

    for kw in MEDIUM_KEYWORDS:
        if kw in text:
            log.debug("Risk MEDIUM triggered by keyword: %s", kw)
            return "medium"

    return "low"


def _score_confidence(title: str, body: str, domain: str, risk: str) -> int:
    """Return confidence 0–100."""
    score = 0
    text = (title + " " + body).lower()
    words = body.split()

    # Clear subject/title
    if len(title) > 5 and title.lower() not in ("untitled", "no subject", ""):
        score += 20

    # Explicit action verb
    action_verbs = ["please", "need", "request", "ask", "send", "create",
                    "review", "approve", "schedule", "pay", "publish"]
    if any(v in text for v in action_verbs):
        score += 20

    # Domain keyword match ≥2
    domain_hits = sum(1 for kw in DOMAIN_KEYWORDS.get(domain, set()) if kw in text)
    if domain_hits >= 2:
        score += 20

    # Risk keywords unambiguous (at least one clear signal)
    all_risk_kw = HIGH_KEYWORDS | MEDIUM_KEYWORDS
    risk_hits = sum(1 for kw in all_risk_kw if kw in text)
    if risk_hits >= 1:
        score += 20

    # Body length > 50 words
    if len(words) > 50:
        score += 10

    # Single domain (no score tie at top)
    domain_scores = {d: sum(1 for kw in kws if kw in text)
                     for d, kws in DOMAIN_KEYWORDS.items()}
    top_scores = sorted(domain_scores.values(), reverse=True)
    if len(top_scores) >= 2 and top_scores[0] > top_scores[1]:
        score += 10

    return min(score, 100)


def _requires_approval(risk: str) -> bool:
    return risk in ("high", "medium")


def _proposed_mcp_actions(domain: str, risk: str, objective: str) -> list[dict]:
    """Generate a list of proposed MCP tool actions based on domain/risk."""
    actions: list[dict] = []

    if domain == "finance":
        actions.append({
            "tool": "accounting_audit",
            "input": "Verify financial details and amounts from the item",
            "note": "Human must approve before execution",
        })
        if risk == "high":
            actions.append({
                "tool": "approval_gatekeeper",
                "input": "Create approval request for financial transaction",
                "note": "Required before any payment action",
            })

    elif domain == "social":
        actions.append({
            "tool": "linkedin_post_generator",
            "input": "Generate draft post from item context",
            "note": "Draft only — human must approve before publish",
        })

    elif domain == "business":
        actions.append({
            "tool": "silver_process_engine",
            "input": "Route business task through standard workflow",
            "note": "Human must review plan before execution",
        })
        if risk == "high":
            actions.append({
                "tool": "approval_gatekeeper",
                "input": "Gate high-risk business action",
                "note": "Required before external communication",
            })

    elif domain == "personal":
        actions.append({
            "tool": "vault_state_manager",
            "input": "Log personal task and update dashboard",
            "note": "Low risk — can proceed after plan review",
        })

    # Always suggest logging
    actions.append({
        "tool": "audit_logger",
        "input": f"Log processing of: {objective[:60]}",
        "note": "Automatic — no approval needed",
    })

    return actions


# ---------------------------------------------------------------------------
# Plan + Approval file writers
# ---------------------------------------------------------------------------

def _write_plan(
    source_file: Path,
    title: str,
    summary: str,
    objective: str,
    domain: str,
    risk: str,
    confidence: int,
    mcp_actions: list[dict],
) -> Path:
    """Write plan file to /Plans and return its path."""
    short_id = uuid.uuid4().hex[:8]
    slug = _slug(title)
    plan_filename = f"{slug}-{short_id}-plan.md"
    plan_path = PLANS / plan_filename

    approval_flag = _requires_approval(risk)

    # Build step checklist based on domain
    base_steps = [
        "Review the item summary and verify accuracy",
        "Confirm the objective matches the requester's intent",
        "Validate domain classification is correct",
    ]
    domain_steps = {
        "finance": [
            "Verify all financial amounts and account details",
            "Cross-reference with accounting records",
            "Obtain approval from authorized approver",
            "Execute financial action only after written approval",
        ],
        "social": [
            "Review generated draft content for accuracy and tone",
            "Ensure content aligns with company voice guidelines",
            "Get approval from content owner",
            "Publish only after explicit human approval",
        ],
        "business": [
            "Identify all stakeholders involved",
            "Review any contracts or commitments referenced",
            "Confirm timeline and deadlines",
            "Communicate outcome to relevant parties",
        ],
        "personal": [
            "Acknowledge receipt of personal task",
            "Schedule or assign as appropriate",
            "Mark complete when resolved",
        ],
    }
    all_steps = base_steps + domain_steps.get(domain, [])
    steps_md = "\n".join(f"- [ ] {s}" for s in all_steps)

    # Build MCP actions block
    mcp_md_parts = []
    for a in mcp_actions:
        mcp_md_parts.append(
            f"- tool: `{a['tool']}`\n"
            f"  input: {a['input']}\n"
            f"  note: \"{a['note']}\""
        )
    mcp_md = "\n".join(mcp_md_parts) if mcp_md_parts else "- No external MCP actions required."

    content = f"""---
status: pending
risk_level: {risk}
confidence: {confidence}
requires_approval: {"true" if approval_flag else "false"}
domain: {domain}
created_at: "{_now_iso()}"
source_file: "{source_file.name}"
engine: silver_reasoning_engine
---

## Objective

{objective}

## Context

{summary}

## Step Checklist

{steps_md}

## Proposed MCP Actions

{mcp_md}
"""

    if not DRY_RUN:
        PLANS.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(content, encoding="utf-8")
        log.info("Plan written: %s", plan_path.relative_to(ROOT))
    else:
        log.info("[DRY-RUN] Would write plan: %s", plan_filename)

    return plan_path


def _write_approval_request(
    plan_path: Path,
    title: str,
    risk: str,
    confidence: int,
    domain: str,
    objective: str,
) -> Path:
    """Write approval request to /Pending_Approval and return its path."""
    short_id = uuid.uuid4().hex[:8]
    slug = _slug(title)
    approval_filename = f"{slug}-{short_id}-approval.md"
    approval_path = PENDING / approval_filename

    risk_reasons = {
        "high": (
            "This item contains keywords associated with financial transactions, "
            "unknown contacts, credentials, or legal matters. "
            "Human review is mandatory before any action is taken."
        ),
        "medium": (
            "This item involves external communication or public-facing content. "
            "Human review required to ensure appropriate tone and accuracy."
        ),
    }
    reason = risk_reasons.get(risk, "Risk level requires human review.")

    content = f"""---
type: approval_request
source_plan: "Plans/{plan_path.name}"
risk_level: {risk}
confidence: {confidence}
domain: {domain}
requested_at: "{_now_iso()}"
status: awaiting_approval
engine: silver_reasoning_engine
---

## Summary

{objective}

## Risk Reason

{reason}

## Confidence Note

This plan was generated with {confidence}% confidence.
{"High confidence — item context is clear." if confidence >= 70
 else "Moderate confidence — human should verify objective before approving."
 if confidence >= 40 else "Low confidence — item is ambiguous; careful review recommended."}

## Plan Reference

See: Plans/{plan_path.name}

## Approval Instructions

- Review the plan at the path above
- If approved: move this file to `/Approved/`
- If rejected: move this file to `/Rejected/` and add a note below

## Decision

> _Pending human review_
"""

    if not DRY_RUN:
        PENDING.mkdir(parents=True, exist_ok=True)
        approval_path.write_text(content, encoding="utf-8")
        log.info("Approval request written: %s", approval_path.relative_to(ROOT))
    else:
        log.info("[DRY-RUN] Would write approval: %s", approval_filename)

    return approval_path


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def process_item(item_path: Path) -> dict:
    """Reason over a single /Needs_Action item. Returns result dict."""
    log.info("Processing: %s", item_path.name)

    content = _read_file(item_path)
    body    = _body_text(content)
    title   = _extract_title(content, item_path.name)

    # --- Reasoning steps ---
    summary    = _summarize(title, body)
    objective  = _identify_objective(title, body)
    domain     = _classify_domain(title, body)
    risk       = _score_risk(title, body)
    confidence = _score_confidence(title, body, domain, risk)
    approval   = _requires_approval(risk)
    mcp_actions = _proposed_mcp_actions(domain, risk, objective)

    log.info(
        "  → domain=%-10s risk=%-8s confidence=%3d%%  approval=%s",
        domain, risk, confidence, approval,
    )
    log.debug("  summary:   %s", summary[:80])
    log.debug("  objective: %s", objective)

    # --- Write plan ---
    plan_path = _write_plan(
        source_file=item_path,
        title=title,
        summary=summary,
        objective=objective,
        domain=domain,
        risk=risk,
        confidence=confidence,
        mcp_actions=mcp_actions,
    )

    # --- Write approval request if needed ---
    approval_path = None
    if approval:
        approval_path = _write_approval_request(
            plan_path=plan_path,
            title=title,
            risk=risk,
            confidence=confidence,
            domain=domain,
            objective=objective,
        )

    return {
        "item":         item_path.name,
        "title":        title,
        "domain":       domain,
        "risk":         risk,
        "confidence":   confidence,
        "requires_approval": approval,
        "plan":         str(plan_path),
        "approval":     str(approval_path) if approval_path else None,
    }


def run() -> None:
    log.info("=" * 60)
    log.info("Silver Reasoning Engine — start")
    log.info("Vault:    %s", VAULT)
    log.info("DRY_RUN:  %s", DRY_RUN)
    log.info("=" * 60)

    if not NEEDS_ACTION.exists():
        log.warning("Needs_Action directory not found: %s", NEEDS_ACTION)
        return

    items = sorted(NEEDS_ACTION.glob("*.md"))
    if not items:
        log.info("No items in /Needs_Action — nothing to process.")
        return

    log.info("Found %d item(s) to process.", len(items))

    results = []
    errors  = []

    for item_path in items:
        try:
            result = process_item(item_path)
            results.append(result)
        except Exception as exc:
            log.error("Failed to process %s: %s", item_path.name, exc, exc_info=True)
            errors.append(item_path.name)

    # --- Summary ---
    log.info("")
    log.info("=" * 60)
    log.info("Silver Reasoning Engine — summary")
    log.info("  Processed : %d", len(results))
    log.info("  Errors    : %d", len(errors))
    log.info("  High risk : %d", sum(1 for r in results if r["risk"] == "high"))
    log.info("  Medium    : %d", sum(1 for r in results if r["risk"] == "medium"))
    log.info("  Low       : %d", sum(1 for r in results if r["risk"] == "low"))
    log.info("  Approvals : %d", sum(1 for r in results if r["requires_approval"]))
    log.info("  Avg conf  : %d%%",
             int(sum(r["confidence"] for r in results) / len(results)) if results else 0)
    log.info("=" * 60)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    run()
