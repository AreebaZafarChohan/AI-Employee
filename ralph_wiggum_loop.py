#!/usr/bin/env python3
"""
Ralph Wiggum Autonomous Reasoning Loop

Gold Tier core reasoning engine that implements the PERCEIVE → REASON → DECIDE → ACT → LEARN cycle.

For autonomous task execution (agent-driven), use:
    python ralph_loop.py --agent claude

Usage:
    python ralph_wiggum_loop.py              # run one cycle
    python ralph_wiggum_loop.py --continuous # run continuously
    DRY_RUN=true python ralph_wiggum_loop.py # log without executing
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from src.utils.logger import log_action
except ImportError:
    pass

# ============================================================================
# Configuration
# ============================================================================

VAULT_PATH = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
PLANS_DIR = VAULT_PATH / "Plans"
APPROVED_DIR = VAULT_PATH / "Approved"
DONE_DIR = VAULT_PATH / "Done"
LOGS_DIR = VAULT_PATH / "Logs"
KNOWLEDGE_DIR = VAULT_PATH / "Knowledge"

LOOP_INTERVAL = int(os.getenv("RALPH_LOOP_INTERVAL", "30"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

STATE_FILE = VAULT_PATH / ".ralph_loop_state.json"

# Logging setup
logger = logging.getLogger("ralph_wiggum_loop")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | ralph_wiggum_loop | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class LoopState:
    """State of the Ralph Wiggum loop."""
    last_cycle: str = ""
    cycle_count: int = 0
    pending_tasks: int = 0
    active_plans: int = 0
    errors_last_hour: int = 0
    total_processed: int = 0
    total_failed: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "LoopState":
        return cls(**data)


@dataclass
class PerceivedInput:
    """Input from PERCEIVE stage."""
    source: str
    content: str
    metadata: Dict
    timestamp: str
    domain: str = "business"
    priority: str = "medium"


@dataclass
class Analysis:
    """Output from REASON stage."""
    situation_summary: str
    key_factors: List[str]
    constraints: List[str]
    opportunities: List[str]
    risks: List[str]
    recommended_actions: List[str]


@dataclass
class Decision:
    """Output from DECIDE stage."""
    action: str
    reasoning: str
    confidence: float
    requires_approval: bool
    risk_level: str
    estimated_time: int
    dependencies: List[str]


@dataclass
class ActionResult:
    """Output from ACT stage."""
    success: bool
    result: Any
    execution_time_ms: int
    error: Optional[str] = None


# ============================================================================
# Ralph Wiggum Loop
# ============================================================================


class RalphWiggumLoop:
    """Autonomous reasoning loop for Gold Tier AI Employee."""
    
    def __init__(self):
        self.state = self._load_state()
        self.inputs_buffer: List[PerceivedInput] = []
        self.company_handbook = self._load_company_handbook()
        
    def _load_state(self) -> LoopState:
        """Load loop state from file."""
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                return LoopState.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return LoopState()
    
    def _save_state(self):
        """Save loop state to file."""
        self.state.last_cycle = get_timestamp()
        STATE_FILE.write_text(json.dumps(self.state.to_dict(), indent=2))
    
    def _load_company_handbook(self) -> str:
        """Load company handbook for reference."""
        handbook_path = KNOWLEDGE_DIR / "Company_Handbook.md"
        if handbook_path.exists():
            return handbook_path.read_text()
        return ""
    
    # =========================================================================
    # Stage 1: PERCEIVE
    # =========================================================================
    
    def perceive(self) -> List[PerceivedInput]:
        """
        PERCEIVE: Gather inputs from all sources.
        
        Sources:
        - Needs_Action/ folder (new tasks)
        - Gmail (new emails)
        - WhatsApp (new messages)
        - Social media (engagement)
        - Odoo (accounting events)
        - Schedule (reminders)
        """
        logger.info("=== STAGE 1: PERCEIVE ===")
        
        inputs = []
        
        # 1. Scan Needs_Action folder
        inputs.extend(self._scan_needs_action())
        
        # 2. Check for new emails (via ledger)
        inputs.extend(self._check_new_emails())
        
        # 3. Check for new WhatsApp messages
        inputs.extend(self._check_new_whatsapp())
        
        # 4. Check for social media engagement
        inputs.extend(self._check_social_engagement())
        
        # 5. Check for accounting alerts
        inputs.extend(self._check_accounting_alerts())
        
        # 6. Check schedule for reminders
        inputs.extend(self._check_schedule())
        
        self.inputs_buffer = inputs
        self.state.pending_tasks = len(inputs)
        
        logger.info(f"Perceived {len(inputs)} inputs")
        return inputs
    
    def _scan_needs_action(self) -> List[PerceivedInput]:
        """Scan Needs_Action folder for new items."""
        inputs = []
        
        if not NEEDS_ACTION_DIR.exists():
            return inputs
        
        for file_path in NEEDS_ACTION_DIR.glob("*.md"):
            if file_path.stem.endswith(".meta"):
                continue
            
            try:
                content = file_path.read_text()
                metadata = self._parse_frontmatter(content)
                
                inputs.append(PerceivedInput(
                    source="needs_action",
                    content=content,
                    metadata=metadata,
                    timestamp=get_timestamp(),
                    domain=metadata.get("domain", "business"),
                    priority=metadata.get("priority", "medium"),
                ))
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        
        return inputs
    
    def _check_new_emails(self) -> List[PerceivedInput]:
        """Check for new emails (placeholder - integrates with gmail_watcher)."""
        # This would integrate with Gmail watcher ledger
        return []
    
    def _check_new_whatsapp(self) -> List[PerceivedInput]:
        """Check for new WhatsApp messages (placeholder)."""
        return []
    
    def _check_social_engagement(self) -> List[PerceivedInput]:
        """Check for social media engagement (placeholder)."""
        return []
    
    def _check_accounting_alerts(self) -> List[PerceivedInput]:
        """Check for accounting alerts (placeholder - integrates with odoo_watcher)."""
        return []
    
    def _check_schedule(self) -> List[PerceivedInput]:
        """Check schedule for reminders (placeholder)."""
        return []
    
    # =========================================================================
    # Stage 2: REASON
    # =========================================================================
    
    def reason(self, inputs: List[PerceivedInput]) -> List[Analysis]:
        """
        REASON: Analyze inputs using AI reasoning.
        
        For each input:
        1. Understand the situation
        2. Identify key factors
        3. Recognize constraints
        4. Find opportunities
        5. Assess risks
        6. Recommend actions
        """
        logger.info("=== STAGE 2: REASON ===")
        
        analyses = []
        
        for input_item in inputs:
            try:
                analysis = self._analyze_input(input_item)
                analyses.append(analysis)
                logger.info(f"Analyzed: {input_item.source}")
            except Exception as e:
                logger.error(f"Error analyzing input: {e}")
                self.state.errors_last_hour += 1
        
        logger.info(f"Generated {len(analyses)} analyses")
        return analyses
    
    def _analyze_input(self, input_item: PerceivedInput) -> Analysis:
        """Analyze a single input using AI."""
        
        # Use Claude API for reasoning (if available)
        if CLAUDE_API_KEY:
            return self._ai_analyze(input_item)
        
        # Fallback: simple rule-based analysis
        return self._rule_based_analyze(input_item)
    
    def _ai_analyze(self, input_item: PerceivedInput) -> Analysis:
        """Analyze using Claude AI."""
        try:
            import httpx
            
            prompt = f"""You are Ralph Wiggum, an AI employee assistant.

CONTEXT:
Company Handbook excerpt:
{self.company_handbook[:2000] if self.company_handbook else "No handbook available."}

INPUT:
Source: {input_item.source}
Domain: {input_item.domain}
Priority: {input_item.priority}
Content: {input_item.content[:2000]}

TASK:
Analyze this input and provide:
1. Situation summary (1-2 sentences)
2. Key factors (bullet points)
3. Constraints (any limitations)
4. Opportunities (potential positive outcomes)
5. Risks (potential negative outcomes)
6. Recommended actions (specific, actionable steps)

Respond in JSON format:
{{
    "situation_summary": "...",
    "key_factors": ["...", "..."],
    "constraints": ["...", "..."],
    "opportunities": ["...", "..."],
    "risks": ["...", "..."],
    "recommended_actions": ["...", "..."]
}}
"""
            
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse AI response
            ai_content = result["content"][0]["text"]
            analysis_data = json.loads(ai_content)
            
            return Analysis(
                situation_summary=analysis_data.get("situation_summary", ""),
                key_factors=analysis_data.get("key_factors", []),
                constraints=analysis_data.get("constraints", []),
                opportunities=analysis_data.get("opportunities", []),
                risks=analysis_data.get("risks", []),
                recommended_actions=analysis_data.get("recommended_actions", []),
            )
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._rule_based_analyze(input_item)
    
    def _rule_based_analyze(self, input_item: PerceivedInput) -> Analysis:
        """Fallback rule-based analysis."""
        content_lower = input_item.content.lower()
        
        # Simple keyword-based analysis
        key_factors = []
        risks = []
        actions = []
        
        if "urgent" in content_lower:
            key_factors.append("Marked as urgent")
            risks.append("Time-sensitive")
            actions.append("Prioritize immediately")
        
        if "invoice" in content_lower or "payment" in content_lower:
            key_factors.append("Financial matter")
            actions.append("Review accounting records")
        
        if "client" in content_lower or "customer" in content_lower:
            key_factors.append("Client-related")
            opportunities.append("Client relationship building")
        
        return Analysis(
            situation_summary=f"New {input_item.source} item requiring attention",
            key_factors=key_factors or ["Standard task"],
            constraints=[],
            opportunities=[],
            risks=risks or [],
            recommended_actions=actions or ["Review and process"],
        )
    
    # =========================================================================
    # Stage 3: DECIDE
    # =========================================================================
    
    def decide(self, analyses: List[Analysis], inputs: List[PerceivedInput]) -> List[Decision]:
        """
        DECIDE: Make decisions based on analysis.
        
        For each analysis:
        1. Choose best action
        2. Determine if approval needed
        3. Assess risk level
        4. Estimate time
        """
        logger.info("=== STAGE 3: DECIDE ===")
        
        decisions = []
        
        for i, analysis in enumerate(analyses):
            try:
                decision = self._make_decision(analysis, inputs[i] if i < len(inputs) else None)
                decisions.append(decision)
                logger.info(f"Decision made: {decision.action}")
            except Exception as e:
                logger.error(f"Error making decision: {e}")
        
        logger.info(f"Made {len(decisions)} decisions")
        return decisions
    
    def _make_decision(self, analysis: Analysis, input_item: Optional[PerceivedInput]) -> Decision:
        """Make a decision based on analysis."""
        
        # Determine action type
        if "email" in (input_item.source if input_item else ""):
            action = "draft_email_response"
        elif "invoice" in str(analysis.key_factors).lower():
            action = "process_invoice"
        elif "social" in (input_item.source if input_item else ""):
            action = "respond_to_engagement"
        else:
            action = "create_task"
        
        # Determine approval requirement
        requires_approval = any(
            risk in str(analysis.risks).lower()
            for risk in ["high", "critical", "financial", "legal"]
        )
        
        # Determine risk level
        risk_level = "high" if requires_approval else "low"
        
        return Decision(
            action=action,
            reasoning=f"Based on analysis: {analysis.situation_summary}",
            confidence=0.8,
            requires_approval=requires_approval,
            risk_level=risk_level,
            estimated_time=15,  # minutes
            dependencies=[],
        )
    
    # =========================================================================
    # Stage 4: ACT
    # =========================================================================
    
    def act(self, decisions: List[Decision], inputs: List[PerceivedInput]) -> List[ActionResult]:
        """
        ACT: Execute decisions.
        
        For each decision:
        1. If approval required → move to Pending_Approval
        2. If low risk → execute directly
        3. Log all actions
        """
        logger.info("=== STAGE 4: ACT ===")
        
        results = []
        
        for decision in decisions:
            try:
                if decision.requires_approval:
                    result = self._request_approval(decision)
                else:
                    result = self._execute_action(decision)
                
                results.append(result)
                logger.info(f"Action result: {result.success}")
                
                if result.success:
                    self.state.total_processed += 1
                else:
                    self.state.total_failed += 1
                    
            except Exception as e:
                logger.error(f"Error executing action: {e}")
                self.state.total_failed += 1
                results.append(ActionResult(
                    success=False,
                    result=None,
                    execution_time_ms=0,
                    error=str(e)
                ))
        
        logger.info(f"Executed {len(results)} actions")
        return results
    
    def _request_approval(self, decision: Decision) -> ActionResult:
        """Move item to Pending_Approval folder."""
        
        start_time = time.time()
        
        # Create approval request file
        pending_dir = VAULT_PATH / "Pending_Approval"
        pending_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"approval-{decision.action}-{timestamp}.md"
        file_path = pending_dir / filename
        
        content = f"""---
action: {decision.action}
reasoning: {decision.reasoning}
risk_level: {decision.risk_level}
requires_approval: true
requested_at: {get_timestamp()}
status: pending
---

# Approval Required

**Action:** {decision.action}

**Reasoning:** {decision.reasoning}

**Risk Level:** {decision.risk_level}

---

## Actions

- [ ] Approve
- [ ] Reject
- [ ] Request more information
"""
        
        if not DRY_RUN:
            file_path.write_text(content)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        log_action("approval_requested", filename, {
            "action": decision.action,
            "risk_level": decision.risk_level,
        })
        
        return ActionResult(
            success=True,
            result=str(file_path),
            execution_time_ms=execution_time,
        )
    
    def _execute_action(self, decision: Decision) -> ActionResult:
        """Execute action directly (low-risk only)."""
        
        start_time = time.time()
        
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would execute: {decision.action}")
            return ActionResult(
                success=True,
                result="simulated",
                execution_time_ms=0,
            )
        
        # Placeholder for actual execution
        # In production, this would call appropriate MCP tools
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return ActionResult(
            success=True,
            result="executed",
            execution_time_ms=execution_time,
        )
    
    # =========================================================================
    # Stage 5: LEARN
    # =========================================================================
    
    def learn(self, results: List[ActionResult], decisions: List[Decision]):
        """
        LEARN: Update models based on outcomes.
        
        1. Log all results
        2. Update success/failure rates
        3. Identify patterns
        4. Save state
        """
        logger.info("=== STAGE 5: LEARN ===")
        
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        
        logger.info(f"Success: {success_count}, Failed: {failure_count}")
        
        # Save state
        self._save_state()
        
        # Log cycle summary
        logger.info(f"Cycle complete. Total processed: {self.state.total_processed}, "
                   f"Total failed: {self.state.total_failed}")
    
    # =========================================================================
    # Main Loop
    # =========================================================================
    
    def run_cycle(self):
        """Run one complete PERCEIVE → REASON → DECIDE → ACT → LEARN cycle."""
        
        logger.info("=" * 60)
        logger.info(f"Starting Cycle {self.state.cycle_count + 1}")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            # Stage 1: PERCEIVE
            inputs = self.perceive()
            
            # Stage 2: REASON
            analyses = self.reason(inputs)
            
            # Stage 3: DECIDE
            decisions = self.decide(analyses, inputs)
            
            # Stage 4: ACT
            results = self.act(decisions, inputs)
            
            # Stage 5: LEARN
            self.learn(results, decisions)
            
            # Update state
            self.state.cycle_count += 1
            
            elapsed = time.time() - start_time
            logger.info(f"Cycle completed in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"Cycle failed: {e}")
            self.state.errors_last_hour += 1
            self._save_state()
    
    def run_continuous(self):
        """Run the loop continuously until interrupted."""
        logger.info("Starting Ralph Wiggum Loop (continuous mode)")
        logger.info(f"Loop interval: {LOOP_INTERVAL}s")
        logger.info(f"Vault: {VAULT_PATH}")
        
        if DRY_RUN:
            logger.warning("DRY_RUN mode enabled - no actions will be executed")
        
        try:
            while True:
                self.run_cycle()
                
                # Wait for next cycle
                logger.info(f"Sleeping for {LOOP_INTERVAL}s...")
                for _ in range(LOOP_INTERVAL):
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self._save_state()


# ============================================================================
# Helper Functions
# ============================================================================


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_frontmatter(content: str) -> Dict:
    """Parse YAML frontmatter."""
    import re
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if match:
        try:
            import yaml
            return yaml.safe_load(match.group(1)) or {}
        except:
            return {}
    return {}


# ============================================================================
# CLI
# ============================================================================


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Ralph Wiggum Autonomous Reasoning Loop")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Ensure directories exist
    for folder in [NEEDS_ACTION_DIR, PLANS_DIR, APPROVED_DIR, DONE_DIR, LOGS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    
    # Create loop instance
    loop = RalphWiggumLoop()
    
    if args.continuous:
        loop.run_continuous()
    else:
        loop.run_cycle()


if __name__ == "__main__":
    main()
