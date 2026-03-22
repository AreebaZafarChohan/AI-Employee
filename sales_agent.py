#!/usr/bin/env python3
"""AI Sales Agent - Full Pipeline: Lead Discovery, Scoring, DM, Meetings, Invoices."""

import os
import sys
import json
import argparse
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from src.utils.ai_client import AIClient

logger = logging.getLogger("sales_agent")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./AI-Employee-Vault"))
PROSPECTS_DIR = VAULT_PATH / "Business" / "Clients" / "prospects"
SALES_DIR = VAULT_PATH / "Business" / "Sales"
INVOICES_DIR = VAULT_PATH / "Accounting" / "Invoices"
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL_DIR = VAULT_PATH / "Pending_Approval"

PIPELINE_STAGES = ["new", "contacted", "responded", "meeting", "closed_won", "closed_lost"]


class SalesAgent:
    """Core sales engine managing the full lead-to-revenue pipeline."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.ai = AIClient()
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [PROSPECTS_DIR, SALES_DIR, INVOICES_DIR, NEEDS_ACTION_DIR, PENDING_APPROVAL_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    # ── Lead Discovery ──────────────────────────────────────────────

    def discover_leads(self, keywords: list[str], max_results: int = 20) -> list[dict]:
        """Discover leads via LinkedIn search (Playwright scraping)."""
        logger.info("Discovering leads for keywords: %s", keywords)

        leads = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                li_email = os.getenv("LINKEDIN_EMAIL", "")
                li_pass = os.getenv("LINKEDIN_PASSWORD", "")

                if li_email and li_pass and not self.dry_run:
                    page.goto("https://www.linkedin.com/login")
                    page.fill("#username", li_email)
                    page.fill("#password", li_pass)
                    page.click('[data-litms-control-urn="login-submit"]')
                    page.wait_for_load_state("networkidle")

                for kw in keywords:
                    search_url = f"https://www.linkedin.com/search/results/people/?keywords={kw}"
                    if self.dry_run:
                        logger.info("[DRY RUN] Would search: %s", search_url)
                        # Generate mock leads for dry run
                        leads.extend(self._generate_mock_leads(kw, min(5, max_results)))
                        continue

                    page.goto(search_url)
                    page.wait_for_load_state("networkidle")

                    cards = page.query_selector_all(".entity-result__item")
                    for card in cards[:max_results]:
                        try:
                            name_el = card.query_selector(".entity-result__title-text a span[aria-hidden='true']")
                            headline_el = card.query_selector(".entity-result__primary-subtitle")
                            link_el = card.query_selector(".entity-result__title-text a")

                            name = name_el.inner_text().strip() if name_el else "Unknown"
                            headline = headline_el.inner_text().strip() if headline_el else ""
                            profile_url = link_el.get_attribute("href") if link_el else ""

                            title, company = self._parse_headline(headline)

                            lead = {
                                "name": name,
                                "title": title,
                                "company": company,
                                "headline": headline,
                                "linkedin_url": profile_url,
                                "source": f"search:{kw}",
                                "discovered_at": datetime.now().isoformat(),
                            }
                            leads.append(lead)
                        except Exception as e:
                            logger.debug("Failed to parse card: %s", e)

                browser.close()
        except ImportError:
            logger.warning("Playwright not installed, using mock leads")
            for kw in keywords:
                leads.extend(self._generate_mock_leads(kw, min(5, max_results)))
        except Exception as e:
            logger.error("Lead discovery error: %s", e)
            for kw in keywords:
                leads.extend(self._generate_mock_leads(kw, min(5, max_results)))

        # Score and save leads
        saved = []
        for lead in leads:
            lead["score"] = self.ai.score_lead(lead)
            lead["stage"] = "new"
            lead["id"] = self._lead_id(lead)
            self._save_lead(lead)
            saved.append(lead)
            logger.info("Lead: %s (%s) - Score: %d", lead["name"], lead["company"], lead["score"])

        self._update_pipeline()
        return saved

    def _generate_mock_leads(self, keyword: str, count: int) -> list[dict]:
        mock_companies = ["TechFlow AI", "DataVerse Inc", "CloudPeak Solutions", "Neural Labs", "AutoScale Corp"]
        mock_titles = ["CEO", "CTO", "VP Engineering", "Head of Product", "Director of Operations"]
        mock_names = ["Alex Rivera", "Jordan Chen", "Taylor Brooks", "Morgan Patel", "Casey Williams"]
        leads = []
        for i in range(min(count, len(mock_names))):
            leads.append({
                "name": mock_names[i],
                "title": mock_titles[i],
                "company": mock_companies[i],
                "headline": f"{mock_titles[i]} at {mock_companies[i]}",
                "linkedin_url": f"https://linkedin.com/in/{mock_names[i].lower().replace(' ', '-')}",
                "source": f"search:{keyword}",
                "discovered_at": datetime.now().isoformat(),
            })
        return leads

    def _parse_headline(self, headline: str) -> tuple[str, str]:
        parts = headline.split(" at ", 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        parts = headline.split(" | ", 1)
        return parts[0].strip(), parts[1].strip() if len(parts) == 2 else ""

    def _lead_id(self, lead: dict) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", lead["name"].lower()).strip("-")
        return f"lead-{slug}"

    # ── Lead Management ─────────────────────────────────────────────

    def _save_lead(self, lead: dict):
        path = PROSPECTS_DIR / f"{lead['id']}.md"
        content = f"""---
name: {lead['name']}
company: {lead.get('company', '')}
title: {lead.get('title', '')}
linkedin_url: {lead.get('linkedin_url', '')}
score: {lead.get('score', 0)}
stage: {lead.get('stage', 'new')}
source: {lead.get('source', '')}
discovered_at: {lead.get('discovered_at', datetime.now().isoformat())}
last_action: {datetime.now().isoformat()}
---

# {lead['name']}

**{lead.get('title', '')}** at **{lead.get('company', '')}**

- Score: {lead.get('score', 0)}/100
- Stage: {lead.get('stage', 'new')}
- Source: {lead.get('source', '')}

## Interaction History

"""
        path.write_text(content, encoding="utf-8")

    def get_lead(self, lead_id: str) -> Optional[dict]:
        path = PROSPECTS_DIR / f"{lead_id}.md"
        if not path.exists():
            return None
        return self._parse_lead_file(path)

    def get_all_leads(self, stage: Optional[str] = None) -> list[dict]:
        leads = []
        if not PROSPECTS_DIR.exists():
            return leads
        for f in PROSPECTS_DIR.glob("lead-*.md"):
            lead = self._parse_lead_file(f)
            if lead and (stage is None or lead.get("stage") == stage):
                leads.append(lead)
        leads.sort(key=lambda x: x.get("score", 0), reverse=True)
        return leads

    def _parse_lead_file(self, path: Path) -> Optional[dict]:
        try:
            content = path.read_text(encoding="utf-8")
            match = re.search(r"---\n(.*?)\n---", content, re.DOTALL)
            if not match:
                return None
            meta = {}
            for line in match.group(1).split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip()
            meta["id"] = path.stem
            if "score" in meta:
                meta["score"] = int(meta["score"])
            # Extract interaction history
            hist_section = content.split("## Interaction History")
            meta["history"] = hist_section[1].strip() if len(hist_section) > 1 else ""
            return meta
        except Exception:
            return None

    def update_lead_stage(self, lead_id: str, new_stage: str):
        path = PROSPECTS_DIR / f"{lead_id}.md"
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8")
        content = re.sub(r"stage: \w+", f"stage: {new_stage}", content)
        content = re.sub(r"last_action: .*", f"last_action: {datetime.now().isoformat()}", content)
        path.write_text(content, encoding="utf-8")
        self._update_pipeline()

    def _append_history(self, lead_id: str, entry: str):
        path = PROSPECTS_DIR / f"{lead_id}.md"
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        content += f"\n- **{timestamp}**: {entry}"
        path.write_text(content, encoding="utf-8")

    # ── DM Generation ───────────────────────────────────────────────

    def generate_dm(self, lead_id: str, context: str = "") -> Optional[str]:
        lead = self.get_lead(lead_id)
        if not lead:
            logger.error("Lead not found: %s", lead_id)
            return None

        dm_text = self.ai.generate_dm(lead, context)
        logger.info("Generated DM for %s: %s", lead["name"], dm_text[:80])

        # Save to Pending_Approval for human review
        approval_path = PENDING_APPROVAL_DIR / f"dm-{lead_id}.md"
        approval_content = f"""---
type: send_linkedin_dm
lead_id: {lead_id}
lead_name: {lead.get('name', '')}
risk_level: high
created_at: {datetime.now().isoformat()}
status: pending
---

# LinkedIn DM Draft

**To:** {lead.get('name', '')} ({lead.get('title', '')} at {lead.get('company', '')})
**LinkedIn:** {lead.get('linkedin_url', '')}

## Message

{dm_text}

## Context

- Lead Score: {lead.get('score', 0)}/100
- Stage: {lead.get('stage', 'new')}
"""
        if not self.dry_run:
            approval_path.write_text(approval_content, encoding="utf-8")
            self._append_history(lead_id, f"DM draft created → Pending Approval")
        else:
            logger.info("[DRY RUN] Would save DM to %s", approval_path)

        return dm_text

    def send_dm(self, lead_id: str, message: str) -> bool:
        """Send an approved DM via Playwright."""
        lead = self.get_lead(lead_id)
        if not lead:
            return False

        if self.dry_run:
            logger.info("[DRY RUN] Would send DM to %s", lead["name"])
            self.update_lead_stage(lead_id, "contacted")
            self._append_history(lead_id, "DM sent (dry run)")
            return True

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # Login and send message via LinkedIn messaging
                li_email = os.getenv("LINKEDIN_EMAIL", "")
                li_pass = os.getenv("LINKEDIN_PASSWORD", "")
                if not li_email or not li_pass:
                    logger.error("LinkedIn credentials not configured")
                    return False

                page.goto("https://www.linkedin.com/login")
                page.fill("#username", li_email)
                page.fill("#password", li_pass)
                page.click('[data-litms-control-urn="login-submit"]')
                page.wait_for_load_state("networkidle")

                profile_url = lead.get("linkedin_url", "")
                if profile_url:
                    page.goto(profile_url)
                    page.wait_for_load_state("networkidle")
                    msg_btn = page.query_selector('button:has-text("Message")')
                    if msg_btn:
                        msg_btn.click()
                        page.wait_for_selector(".msg-form__contenteditable")
                        page.fill(".msg-form__contenteditable", message)
                        send_btn = page.query_selector(".msg-form__send-button")
                        if send_btn:
                            send_btn.click()
                            logger.info("DM sent to %s", lead["name"])

                browser.close()
        except Exception as e:
            logger.error("Failed to send DM: %s", e)
            return False

        self.update_lead_stage(lead_id, "contacted")
        self._append_history(lead_id, f"DM sent: {message[:50]}...")
        return True

    # ── Meeting Scheduling ──────────────────────────────────────────

    def schedule_meeting(self, lead_id: str) -> Optional[str]:
        lead = self.get_lead(lead_id)
        if not lead:
            return None

        calendly_link = os.getenv("CALENDLY_LINK", "https://calendly.com/your-link")
        meeting_msg = f"Great to connect, {lead['name'].split()[0]}! Here's my calendar link to find a time that works: {calendly_link}"

        self.update_lead_stage(lead_id, "meeting")
        self._append_history(lead_id, f"Meeting link shared: {calendly_link}")

        # Create Needs_Action entry
        action_path = NEEDS_ACTION_DIR / f"meeting-{lead_id}.md"
        action_content = f"""---
type: meeting_scheduled
lead_id: {lead_id}
lead_name: {lead.get('name', '')}
created_at: {datetime.now().isoformat()}
---

# Meeting Scheduled: {lead.get('name', '')}

Calendly link sent to {lead.get('name', '')} ({lead.get('company', '')}).
Awaiting booking confirmation.
"""
        if not self.dry_run:
            action_path.write_text(action_content, encoding="utf-8")

        return meeting_msg

    # ── Invoice Generation ──────────────────────────────────────────

    def generate_invoice(self, lead_id: str, amount: float, description: str = "AI Automation Services") -> Optional[str]:
        lead = self.get_lead(lead_id)
        if not lead:
            return None

        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d')}-{lead_id[-4:]}"
        due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        invoice_path = INVOICES_DIR / f"{invoice_id}.md"
        invoice_content = f"""---
invoice_id: {invoice_id}
lead_id: {lead_id}
client_name: {lead.get('name', '')}
company: {lead.get('company', '')}
amount: {amount}
currency: USD
status: pending
issued_date: {datetime.now().strftime('%Y-%m-%d')}
due_date: {due_date}
description: {description}
---

# Invoice {invoice_id}

**Bill To:** {lead.get('name', '')}
**Company:** {lead.get('company', '')}
**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Due:** {due_date}

| Description | Amount |
|---|---|
| {description} | ${amount:,.2f} |

**Total: ${amount:,.2f} USD**

**Status:** Pending Payment
"""
        if not self.dry_run:
            invoice_path.write_text(invoice_content, encoding="utf-8")
            self._append_history(lead_id, f"Invoice {invoice_id} generated: ${amount:,.2f}")
        else:
            logger.info("[DRY RUN] Would create invoice at %s", invoice_path)

        return invoice_id

    def get_invoices(self) -> list[dict]:
        invoices = []
        if not INVOICES_DIR.exists():
            return invoices
        for f in INVOICES_DIR.glob("INV-*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                match = re.search(r"---\n(.*?)\n---", content, re.DOTALL)
                if match:
                    meta = {}
                    for line in match.group(1).split("\n"):
                        if ":" in line:
                            key, val = line.split(":", 1)
                            meta[key.strip()] = val.strip()
                    if "amount" in meta:
                        meta["amount"] = float(meta["amount"])
                    invoices.append(meta)
            except Exception:
                pass
        return invoices

    def update_payment_status(self, invoice_id: str, status: str):
        path = INVOICES_DIR / f"{invoice_id}.md"
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8")
        content = re.sub(r"status: \w+", f"status: {status}", content)
        path.write_text(content, encoding="utf-8")

    # ── Pipeline Dashboard ──────────────────────────────────────────

    def _update_pipeline(self):
        leads = self.get_all_leads()
        by_stage = {}
        for s in PIPELINE_STAGES:
            by_stage[s] = [l for l in leads if l.get("stage") == s]

        invoices = self.get_invoices()
        total_revenue = sum(float(inv.get("amount", 0)) for inv in invoices if inv.get("status") == "paid")
        pending_revenue = sum(float(inv.get("amount", 0)) for inv in invoices if inv.get("status") == "pending")

        pipeline_content = f"""---
updated_at: {datetime.now().isoformat()}
total_leads: {len(leads)}
total_revenue: {total_revenue}
pending_revenue: {pending_revenue}
---

# Sales Pipeline

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Funnel

| Stage | Count | Avg Score |
|---|---|---|
"""
        for stage in PIPELINE_STAGES:
            stage_leads = by_stage.get(stage, [])
            avg_score = sum(l.get("score", 0) for l in stage_leads) / max(len(stage_leads), 1)
            pipeline_content += f"| {stage} | {len(stage_leads)} | {avg_score:.0f} |\n"

        pipeline_content += f"""
## Revenue

- **Closed Revenue:** ${total_revenue:,.2f}
- **Pending Invoices:** ${pending_revenue:,.2f}
- **Pipeline Value:** ${pending_revenue + total_revenue:,.2f}

## Conversion Rates

"""
        if by_stage.get("new"):
            contacted = len(by_stage.get("contacted", []))
            pipeline_content += f"- New → Contacted: {contacted}/{len(by_stage['new'])+contacted} ({contacted/(len(by_stage['new'])+contacted)*100:.0f}%)\n" if (len(by_stage['new'])+contacted) > 0 else ""

        SALES_DIR.mkdir(parents=True, exist_ok=True)
        (SALES_DIR / "pipeline.md").write_text(pipeline_content, encoding="utf-8")

    def get_pipeline_stats(self) -> dict:
        leads = self.get_all_leads()
        invoices = self.get_invoices()
        by_stage = {}
        for s in PIPELINE_STAGES:
            by_stage[s] = len([l for l in leads if l.get("stage") == s])

        return {
            "total_leads": len(leads),
            "by_stage": by_stage,
            "total_revenue": sum(float(i.get("amount", 0)) for i in invoices if i.get("status") == "paid"),
            "pending_revenue": sum(float(i.get("amount", 0)) for i in invoices if i.get("status") == "pending"),
            "avg_score": sum(l.get("score", 0) for l in leads) / max(len(leads), 1),
            "invoices_count": len(invoices),
        }


def main():
    parser = argparse.ArgumentParser(description="AI Sales Agent")
    parser.add_argument("--discover", action="store_true", help="Discover new leads")
    parser.add_argument("--keywords", type=str, default="AI,SaaS", help="Search keywords (comma-separated)")
    parser.add_argument("--generate-dm", action="store_true", help="Generate DM for a lead")
    parser.add_argument("--invoice", action="store_true", help="Generate invoice for a lead")
    parser.add_argument("--lead", type=str, help="Lead ID for targeted actions")
    parser.add_argument("--amount", type=float, default=5000, help="Invoice amount")
    parser.add_argument("--pipeline", action="store_true", help="Show pipeline stats")
    parser.add_argument("--dry-run", action="store_true", help="Run without real actions")
    args = parser.parse_args()

    agent = SalesAgent(dry_run=args.dry_run)

    if args.discover:
        keywords = [k.strip() for k in args.keywords.split(",")]
        leads = agent.discover_leads(keywords)
        print(f"\nDiscovered {len(leads)} leads:")
        for l in leads:
            print(f"  - {l['name']} ({l['company']}) - Score: {l['score']}")

    elif args.generate_dm:
        if not args.lead:
            print("Error: --lead required")
            sys.exit(1)
        dm = agent.generate_dm(args.lead)
        if dm:
            print(f"\nGenerated DM:\n{dm}")

    elif args.invoice:
        if not args.lead:
            print("Error: --lead required")
            sys.exit(1)
        inv_id = agent.generate_invoice(args.lead, args.amount)
        if inv_id:
            print(f"\nInvoice created: {inv_id}")

    elif args.pipeline:
        stats = agent.get_pipeline_stats()
        print(json.dumps(stats, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
