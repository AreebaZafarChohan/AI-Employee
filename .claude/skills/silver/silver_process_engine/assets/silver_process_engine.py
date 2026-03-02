#!/usr/bin/env python3
"""Silver Process Engine.

Scans /Needs_Action, classifies each item, generates structured Plans,
creates approval requests for medium/high risk, logs actions, and moves
processed items to /Done.

Constraints:
  - Never executes real-world actions
  - Only prepares structured outputs

Usage:
    python silver_process_engine.py
    SILVER_PE_DRY_RUN=true python silver_process_engine.py
    SILVER_PE_LOG_LEVEL=DEBUG python silver_process_engine.py
"""

import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Vault paths (resolved relative to project root)
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[5]   # project root (.claude/skills/silver/silver_process_engine/assets/)
sys.path.insert(0, str(ROOT))

VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION = VAULT / "Needs_Action"
PLANS = VAULT / "Plans"
PENDING_APPROVAL = VAULT / "Pending_Approval"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"

DRY_RUN: bool = os.getenv("SILVER_PE_DRY_RUN", "false").lower() in ("true", "1", "yes")

# Keywords that escalate risk level by one step
RISK_KEYWORDS = {
    "urgent", "legal", "lawsuit", "court",
    "payment", "invoice", "overdue",
    "password", "credentials", "breach",
    "terminate", "fired", "layoff",
    "critical", "emergency", "asap",
}

# Financial threshold for high risk
FINANCIAL_HIGH_THRESHOLD = 100.0  # $100

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

def _build_logger() -> logging.Logger:
    level_name = os.getenv("SILVER_PE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("silver_process_engine")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | silver_process_engine | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    LOGS.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fh = logging.FileHandler(LOGS / f"silver-process-engine-{today}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


logger = _build_logger()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id() -> str:
    return str(uuid.uuid4())[:8]


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:50] or "item"


def _read_frontmatter(text: str) -> dict:
    """Parse simple key: value YAML frontmatter."""
    meta: dict = {}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    if end == -1:
        return meta
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_type(filename: str, meta: dict) -> str:
    """Determine item type from frontmatter or filename."""
    if "type" in meta:
        t = meta["type"].lower()
        if t in ("email", "whatsapp", "file_drop"):
            return t
    name = filename.lower()
    if "email" in name:
        return "email"
    if "whatsapp" in name:
        return "whatsapp"
    return "file_drop"


def _extract_amount(content: str, meta: dict) -> float:
    """Extract financial amount from content or metadata."""
    # Check metadata first
    amount_str = meta.get("amount", "")
    if amount_str:
        try:
            return float(re.sub(r"[^\d.]", "", str(amount_str)))
        except (ValueError, TypeError):
            pass
    
    # Look for amount patterns in content: $100, USD 100, 100 dollars
    patterns = [
        r'\$[\d,]+\.?\d*',
        r'USD\s*[\d,]+\.?\d*',
        r'[\d,]+\.?\d*\s*dollars?',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                return float(re.sub(r'[^\d.]', '', match.group().replace('$', '').replace('USD', '').replace('dollars', '')))
            except (ValueError, TypeError):
                pass
    
    return 0.0


def _is_unknown_sender(meta: dict) -> bool:
    """Check if sender is unknown (not in internal domains)."""
    from_field = meta.get("from", "").lower()
    
    # Internal domains
    internal_domains = ["company.com", "internal", "localhost"]
    
    if not from_field:
        return True
    
    # Check if sender email is from internal domain
    for domain in internal_domains:
        if domain in from_field:
            return False
    
    return True


def _has_urgent_keywords(content: str) -> bool:
    """Check if content contains urgent/urgent keywords."""
    content_lower = content.lower()
    urgent_keywords = {"urgent", "asap", "immediately", "rush", "deadline", "today only"}
    return any(kw in content_lower for kw in urgent_keywords)


def classify_risk(item_type: str, meta: dict, content: str) -> tuple[str, int, dict]:
    """
    Assign risk level with scoring and confidence.
    
    Returns:
        tuple: (risk_level, confidence_score, risk_factors)
        - risk_level: 'low' | 'medium' | 'high'
        - confidence_score: 0-100
        - risk_factors: dict with scoring details
    """
    risk_factors = {
        "base_score": 0,
        "financial_score": 0,
        "sender_score": 0,
        "keyword_score": 0,
        "urgency_score": 0,
        "factors": [],
    }
    
    # Base score by item type
    if item_type == "email":
        risk_factors["base_score"] = 20
        risk_factors["factors"].append("email type (+20)")
    elif item_type == "file_drop":
        risk_factors["base_score"] = 30
        risk_factors["factors"].append("file_drop type (+30)")
    elif item_type == "whatsapp":
        risk_factors["base_score"] = 25
        risk_factors["factors"].append("whatsapp type (+25)")
    
    # Priority field scoring
    priority = meta.get("priority", "").lower()
    if priority == "high":
        risk_factors["base_score"] += 30
        risk_factors["factors"].append("high priority (+30)")
    elif priority == "medium":
        risk_factors["base_score"] += 20
        risk_factors["factors"].append("medium priority (+20)")
    elif priority == "low":
        risk_factors["base_score"] += 10
        risk_factors["factors"].append("low priority (+10)")
    
    # Rule 1: Financial amount > $100 → high risk
    amount = _extract_amount(content, meta)
    if amount > FINANCIAL_HIGH_THRESHOLD:
        risk_factors["financial_score"] = 50
        risk_factors["factors"].append(f"amount ${amount:.2f} > ${FINANCIAL_HIGH_THRESHOLD} (+50)")
    elif amount > 0:
        risk_factors["financial_score"] = 20
        risk_factors["factors"].append(f"amount ${amount:.2f} (+20)")
    
    # Rule 2: Unknown sender → medium risk
    if _is_unknown_sender(meta):
        risk_factors["sender_score"] = 25
        risk_factors["factors"].append("unknown sender (+25)")
    else:
        risk_factors["sender_score"] = 5
        risk_factors["factors"].append("known sender (+5)")
    
    # Rule 3: Urgent keywords → medium risk
    if _has_urgent_keywords(content):
        risk_factors["urgency_score"] = 25
        risk_factors["factors"].append("urgent keywords (+25)")
    
    # Rule 4: Risk keywords (legal, payment, etc.) → escalate
    content_lower = content.lower()
    if any(kw in content_lower for kw in RISK_KEYWORDS):
        risk_factors["keyword_score"] = 30
        risk_factors["factors"].append("risk keywords present (+30)")
    
    # Rule 5: Internal file drop → low risk
    if item_type == "file_drop" and not _is_unknown_sender(meta):
        risk_factors["base_score"] = max(0, risk_factors["base_score"] - 20)
        risk_factors["factors"].append("internal file_drop (-20)")
    
    # Calculate total score
    total_score = sum([
        risk_factors["base_score"],
        risk_factors["financial_score"],
        risk_factors["sender_score"],
        risk_factors["keyword_score"],
        risk_factors["urgency_score"],
    ])
    
    # Cap at 100
    total_score = min(100, total_score)
    
    # Determine risk level based on score
    if total_score >= 70:
        risk_level = "high"
    elif total_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Calculate confidence based on available data
    confidence_factors = 0
    if meta.get("from"):
        confidence_factors += 1
    if meta.get("priority"):
        confidence_factors += 1
    if amount > 0:
        confidence_factors += 1
    if content:
        confidence_factors += 1
    
    # Base confidence 60%, +10% per factor (max 100%)
    confidence_score = min(100, 60 + (confidence_factors * 10))
    
    risk_factors["total_score"] = total_score
    risk_factors["confidence_score"] = confidence_score
    
    return risk_level, confidence_score, risk_factors

# ---------------------------------------------------------------------------
# Plan rendering
# ---------------------------------------------------------------------------

_STEPS_BY_TYPE = {
    "email": [
        "Read and understand the full email content and sender intent.",
        "Identify any action items, deadlines, or required responses.",
        "Draft a response or delegate to the appropriate owner.",
        "Send response (requires approval if risk is medium/high).",
        "Archive the email after action is complete.",
    ],
    "whatsapp": [
        "Read and understand the WhatsApp message and context.",
        "Identify the sender's intent and urgency level.",
        "Prepare a response or escalate to appropriate owner.",
        "Reply to the message (requires approval if risk is medium/high).",
        "Archive the item after handling.",
    ],
    "file_drop": [
        "Review the dropped file content and metadata.",
        "Classify the file purpose (report, attachment, task, contract, etc.).",
        "Route to appropriate folder, owner, or workflow.",
        "Notify relevant stakeholders if required.",
        "Archive the item after routing.",
    ],
}


def render_plan(source_file: str, item_type: str, risk: str, meta: dict, snippet: str, 
                confidence: int = 80, risk_factors: dict = None) -> tuple[str, str]:
    """Return (filename, markdown_content) for the plan file."""
    plan_id = _short_id()
    now = _now_iso()
    requires_approval = risk in ("medium", "high")
    subject = meta.get("subject") or meta.get("filename") or source_file
    title = f"Process {item_type.title()}: {subject}"
    slug = _slug(subject)

    steps = _STEPS_BY_TYPE.get(item_type, _STEPS_BY_TYPE["file_drop"])
    steps_md = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
    
    # Build risk factors display
    risk_factors_md = ""
    if risk_factors:
        factors_list = "\n".join(f"  - {factor}" for factor in risk_factors.get("factors", []))
        risk_factors_md = f"\n**Risk Score:** {risk_factors.get('total_score', 0)}/100\n**Confidence:** {confidence}%\n\n**Factors:**\n{factors_list}\n"

    risk_note = {
        "high": f"High priority item — requires careful handling and explicit approval.{risk_factors_md}",
        "medium": f"Medium risk — human review recommended before execution.{risk_factors_md}",
        "low": f"Low risk — standard processing applies.{risk_factors_md}",
    }[risk]

    approval_line = (
        f"**Yes** — Risk level is **{risk.upper()}**. Human review required before any action."
        if requires_approval
        else "**No** — Low risk item. Can proceed directly to execution."
    )

    frontmatter = (
        "---\n"
        f"plan_id: {plan_id}\n"
        f"source_file: {source_file}\n"
        f"item_type: {item_type}\n"
        f"risk_level: {risk}\n"
        f"risk_score: {risk_factors.get('total_score', 0) if risk_factors else 0}\n"
        f"confidence_score: {confidence}\n"
        f"requires_approval: {str(requires_approval).lower()}\n"
        f"status: {'pending_approval' if requires_approval else 'ready_to_execute'}\n"
        f'created_at: "{now}"\n'
        "---\n"
    )

    body = (
        f"# Plan: {title}\n\n"
        f"## Objective\n"
        f"Process the incoming {item_type} item, determine the required action, "
        f"and prepare a structured, human-reviewable response plan.\n\n"
        f"## Context Summary\n"
        f"Item received from **{meta.get('from', 'unknown sender')}** "
        f"at `{meta.get('received_at', now)}`. "
        f"Type: `{item_type}`. Priority: `{meta.get('priority', 'unspecified')}`. "
        f"Source file: `{source_file}`.\n\n"
        f"## Risk Level\n"
        f"**{risk.upper()}** (Score: {risk_factors.get('total_score', 0) if risk_factors else 0}/100, Confidence: {confidence}%)\n\n"
        f"{risk_note}\n\n"
        f"## Steps\n{steps_md}\n\n"
        f"## Requires Approval?\n{approval_line}\n\n"
        f"## Source Excerpt\n"
        f"> {snippet[:400]}\n"
    )

    filename = f"{slug}-{plan_id}-plan.md"
    return filename, frontmatter + "\n" + body

# ---------------------------------------------------------------------------
# Approval request rendering
# ---------------------------------------------------------------------------

def render_approval(plan_filename: str, source_file: str, risk: str, meta: dict) -> tuple[str, str]:
    """Return (filename, markdown_content) for the approval request."""
    approval_id = _short_id()
    now = _now_iso()
    subject = meta.get("subject") or meta.get("filename") or source_file
    slug = _slug(subject)

    steps = _STEPS_BY_TYPE.get(
        meta.get("type", "file_drop").lower(), _STEPS_BY_TYPE["file_drop"]
    )
    steps_md = "\n".join(f"- {s}" for s in steps)

    frontmatter = (
        "---\n"
        f"approval_id: {approval_id}\n"
        f"plan_file: Plans/{plan_filename}\n"
        f"source_file: {source_file}\n"
        f"risk_level: {risk}\n"
        f'requested_at: "{now}"\n'
        "status: pending\n"
        "---\n"
    )

    body = (
        f"# Approval Request: {subject}\n\n"
        f"## Why Approval Is Required\n"
        f"Risk level is **{risk.upper()}**. "
        f"This item requires explicit human review before any action is taken.\n\n"
        f"## Proposed Plan Summary\n{steps_md}\n\n"
        f"## Action Required\n"
        f"- [ ] Review linked plan: `Plans/{plan_filename}`\n"
        f"- [ ] **Approve** → move this file to `/Approved`\n"
        f"- [ ] **Reject** → move this file to `/Rejected`\n"
    )

    filename = f"{slug}-{approval_id}-approval.md"
    return filename, frontmatter + "\n" + body

# ---------------------------------------------------------------------------
# Item processor
# ---------------------------------------------------------------------------

def process_item(item_path: Path) -> str:
    """Process one Needs_Action item. Returns outcome string."""
    text = item_path.read_text(encoding="utf-8")
    meta = _read_frontmatter(text)

    # Extract snippet from frontmatter or body
    snippet = meta.get("snippet", "")
    if not snippet:
        body_start = text.find("\n---\n", text.find("---") + 3)
        snippet = text[body_start + 5:].strip()[:400] if body_start != -1 else text[:400]

    item_type = classify_type(item_path.name, meta)
    risk, confidence, risk_factors = classify_risk(item_type, meta, text)
    requires_approval = risk in ("medium", "high")

    logger.info(
        "Item: %s | type=%s | risk=%s | confidence=%d%% | approval=%s",
        item_path.name, item_type, risk, confidence, requires_approval,
    )
    
    # Log risk factors for debugging
    if risk_factors.get("factors"):
        logger.debug("Risk factors: %s", " | ".join(risk_factors["factors"]))

    # --- Write plan ---
    plan_filename, plan_content = render_plan(
        item_path.name, item_type, risk, meta, snippet, confidence, risk_factors
    )
    plan_path = PLANS / plan_filename

    if not DRY_RUN:
        PLANS.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan_content, encoding="utf-8")
    logger.info("[%s] Plan created: %s", "DRY" if DRY_RUN else "OK", plan_filename)

    # --- Write approval request ---
    if requires_approval:
        approval_filename, approval_content = render_approval(
            plan_filename, item_path.name, risk, meta
        )
        approval_path = PENDING_APPROVAL / approval_filename
        if not DRY_RUN:
            PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
            approval_path.write_text(approval_content, encoding="utf-8")
        logger.info(
            "[%s] Approval request created: %s", "DRY" if DRY_RUN else "OK", approval_filename
        )

    # --- Move to Done ---
    done_path = DONE / item_path.name
    if not DRY_RUN:
        DONE.mkdir(parents=True, exist_ok=True)
        item_path.rename(done_path)
    logger.info("[%s] Moved to Done: %s", "DRY" if DRY_RUN else "OK", item_path.name)

    return f"type={item_type} | risk={risk} | confidence={confidence}% | plan={plan_filename}"

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run() -> None:
    try:
        from src.utils.logger import log_action, set_default_logs_dir
        set_default_logs_dir(LOGS)
        _log_action = log_action
    except ImportError:
        def _log_action(action: str, target: str, detail: str) -> None:
            logger.debug("log_action | %s | %s | %s", action, target, detail)

    if DRY_RUN:
        logger.info("=== DRY RUN MODE — no files will be written ===")

    items = sorted(NEEDS_ACTION.glob("*.md")) if NEEDS_ACTION.exists() else []
    if not items:
        logger.info("No items in Needs_Action. Nothing to process.")
        return

    logger.info("Found %d item(s) in Needs_Action.", len(items))
    processed = errors = 0

    for item in items:
        try:
            outcome = process_item(item)
            _log_action("process_engine", item.name, f"success | {outcome}")
            processed += 1
        except Exception as exc:
            logger.error("Failed: %s — %s", item.name, exc, exc_info=True)
            _log_action("process_engine_error", item.name, f"error: {exc}")
            errors += 1

    logger.info("Done — processed=%d, errors=%d", processed, errors)


if __name__ == "__main__":
    run()
