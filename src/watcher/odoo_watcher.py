#!/usr/bin/env python3
"""
Gold Tier Odoo Watcher

Monitors Odoo for accounting events:
- Unpaid invoices
- Overdue payments
- Large expenses
- Low balance alerts

Creates markdown files in Needs_Action/ for required actions.

Usage:
    python odoo_watcher.py              # run one poll cycle
    python odoo_watcher.py --watch      # continuous monitoring
    DRY_RUN=true python odoo_watcher.py # log without writing files
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, use system env vars

# Add project root to path
# __file__ is in src/watcher, so root is two levels up
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import httpx
from src.utils.logger import log_action
from src.utils.cross_dedup import CrossSourceDedup

# Initialize deduplication
_cross_dedup = CrossSourceDedup()

# ============================================================================
# Configuration
# ============================================================================

VAULT_PATH = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
LOGS_DIR = VAULT_PATH / "Logs"
ACCOUNTING_DIR = VAULT_PATH / "Accounting"

POLL_INTERVAL = int(os.getenv("ODOO_POLL_INTERVAL", "300"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Odoo configuration
ODOO_CONFIG = {
    "url": os.getenv("ODOO_URL", "http://localhost:8069"),
    "db": os.getenv("ODOO_DB", "odoo"),
    "username": os.getenv("ODOO_USERNAME", "admin"),
    "password": os.getenv("ODOO_PASSWORD", "admin"),
}

# Alert thresholds
THRESHOLDS = {
    "overdue_days_warning": int(os.getenv("ODOO_OVERDUE_DAYS_WARNING", "7")),
    "overdue_days_critical": int(os.getenv("ODOO_OVERDUE_DAYS_CRITICAL", "30")),
    "expense_warning": float(os.getenv("ODOO_EXPENSE_WARNING", "1000")),
    "expense_critical": float(os.getenv("ODOO_EXPENSE_CRITICAL", "5000")),
    "balance_warning": float(os.getenv("ODOO_BALANCE_WARNING", "10000")),
    "balance_critical": float(os.getenv("ODOO_BALANCE_CRITICAL", "5000")),
}

# Logging setup
logger = logging.getLogger("odoo_watcher")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | odoo_watcher | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# Odoo JSON-RPC Client
# ============================================================================


class OdooClient:
    """Simple Odoo JSON-RPC client."""
    
    def __init__(self, config: Dict):
        self.url = config["url"]
        self.db = config["db"]
        self.username = config["username"]
        self.password = config["password"]
        self.uid = None
        self.timeout = 30
    
    def authenticate(self) -> Optional[int]:
        """Authenticate with Odoo."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.db, self.username, self.password, {}]
                }
            }
            
            response = httpx.post(
                f"{self.url}/jsonrpc",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(result["error"].get("message", "Unknown error"))
            
            self.uid = result.get("result")
            return self.uid
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def execute(self, model: str, method: str, args: List = None, kwargs: Dict = None):
        """Execute Odoo method."""
        if not self.uid:
            if not self.authenticate():
                raise Exception("Not authenticated")
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [self.db, self.uid, self.password, model, method, args or []],
                    "kwargs": kwargs or {}
                }
            }
            
            response = httpx.post(
                f"{self.url}/jsonrpc",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(result["error"].get("message", "Unknown error"))
            
            return result.get("result")
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise
    
    def search_read(self, model: str, domain: List, fields: List = None, limit: int = 80):
        """Search and read records."""
        return self.execute(model, "search_read", [domain], {"fields": fields or [], "limit": limit})


# ============================================================================
# Alert Generators
# ============================================================================


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


import requests

def notify_backend(filename: str, metadata: dict = None):
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
    try:
        requests.post(f"{backend_url}/events/new", json={
            "source": "odoo_watcher",
            "file": filename,
            "metadata": metadata or {}
        }, timeout=5)
    except:
        pass

def create_overdue_invoice_alert(invoice: Dict, days_overdue: int) -> Optional[Path]:
    """Create alert for overdue invoice."""
    
    invoice_id = invoice.get("id")
    
    # Check if already processed
    if hasattr(_cross_dedup, 'is_processed') and _cross_dedup.is_processed(f"odoo:invoice:{invoice_id}"):
        return None
    
    # Determine risk level
    risk_level = "high" if days_overdue >= THRESHOLDS["overdue_days_critical"] else "medium"
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"accounting-overdue-invoice-{invoice_id}-{timestamp}.md"
    file_path = NEEDS_ACTION_DIR / filename
    
    markdown_content = f"""---
type: accounting_alert
source: odoo_watcher
alert_type: overdue_invoice
invoice_id: {invoice.get('name', 'N/A')}
partner: "{invoice.get('partner_name', 'Unknown')}"
partner_id: {invoice.get('partner_id', 0)}
amount: {invoice.get('amount_residual', 0):.2f}
currency: {invoice.get('currency', 'USD')}
due_date: "{invoice.get('due_date', 'N/A')}"
days_overdue: {days_overdue}
created_at: "{get_timestamp()}"
domain: business
risk_level: {risk_level}
requires_approval: true
---

# Overdue Invoice Alert

**Invoice:** {invoice.get('name', 'N/A')}  
**Client:** {invoice.get('partner_name', 'Unknown')}  
**Amount:** ${invoice.get('amount_residual', 0):.2f}  
**Due Date:** {invoice.get('due_date', 'N/A')}  
**Days Overdue:** {days_overdue}

---

## Recommended Actions

1. **Immediate:** Send payment reminder email
2. **Follow-up:** Call client if no response in 3 days
3. **Escalation:** Consider collections if > 60 days

---

## Quick Actions

- [ ] Send payment reminder email
- [ ] Create follow-up task
- [ ] Call client
- [ ] Escalate to collections
"""
    
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would create: {filename}")
        return None
    
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    file_path.write_text(markdown_content, encoding="utf-8")
    
    log_action("overdue_invoice_alert", filename, {
        "invoice_id": invoice_id,
        "partner": invoice.get('partner_name'),
        "amount": invoice.get('amount_residual'),
        "days_overdue": days_overdue,
    })
    
    if hasattr(_cross_dedup, 'mark_processed'):
        _cross_dedup.mark_processed(f"odoo:invoice:{invoice_id}")
    
    logger.info(f"Created overdue invoice alert: {filename}")
    
    # Notify backend
    notify_backend(filename, {"invoice_id": invoice_id, "amount": invoice.get('amount_residual')})
    
    return file_path


def create_large_expense_alert(expense: Dict) -> Optional[Path]:
    """Create alert for large expense."""
    
    expense_id = expense.get("id")
    amount = expense.get("amount", 0)
    
    # Check if already processed
    if hasattr(_cross_dedup, 'is_processed') and _cross_dedup.is_processed(f"odoo:expense:{expense_id}"):
        return None
    
    # Determine risk level
    risk_level = "high" if amount >= THRESHOLDS["expense_critical"] else "medium"
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"accounting-large-expense-{expense_id}-{timestamp}.md"
    file_path = NEEDS_ACTION_DIR / filename
    
    threshold = THRESHOLDS["expense_critical"] if risk_level == "high" else THRESHOLDS["expense_warning"]
    
    markdown_content = f"""---
type: accounting_alert
source: odoo_watcher
alert_type: large_expense
expense_id: {expense.get('name', 'N/A')}
vendor: "{expense.get('vendor_name', 'Unknown')}"
amount: {amount:.2f}
currency: {expense.get('currency', 'USD')}
category: "{expense.get('category', 'N/A')}"
created_at: "{get_timestamp()}"
domain: business
risk_level: {risk_level}
requires_approval: true
threshold_exceeded: {threshold:.2f}
---

# Large Expense Alert

**Expense:** {expense.get('name', 'N/A')}  
**Vendor:** {expense.get('vendor_name', 'Unknown')}  
**Amount:** ${amount:.2f}  
**Category:** {expense.get('category', 'N/A')}  
**Threshold:** ${threshold:.2f}

---

## Approval Required

This expense exceeds the ${threshold:.2f} threshold and requires human approval.

---

## Actions

- [ ] Review and approve
- [ ] Reject expense
- [ ] Request more information
"""
    
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would create: {filename}")
        return None
    
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    file_path.write_text(markdown_content, encoding="utf-8")
    
    log_action("large_expense_alert", filename, {
        "expense_id": expense_id,
        "vendor": expense.get('vendor_name'),
        "amount": amount,
    })
    
    if hasattr(_cross_dedup, 'mark_processed'):
        _cross_dedup.mark_processed(f"odoo:expense:{expense_id}")
    
    logger.info(f"Created large expense alert: {filename}")
    
    # Notify backend
    notify_backend(filename, {"expense_id": expense_id, "amount": amount})
    
    return file_path


# ============================================================================
# Polling Functions
# ============================================================================


def poll_unpaid_invoices(odoo: OdooClient) -> int:
    """Poll for unpaid invoices."""
    count = 0
    
    try:
        # Get unpaid invoices
        domain = [
            ("move_type", "in", ["out_invoice", "in_invoice"]),
            ("payment_state", "=", "not_paid"),
            ("state", "=", "posted")
        ]
        
        invoices = odoo.search_read(
            "account.move",
            domain,
            ["id", "name", "partner_id", "invoice_date", "invoice_date_due", 
             "amount_total", "amount_residual", "currency_id", "move_type"],
            limit=50
        )
        
        today = datetime.now().date()
        
        for invoice in invoices:
            if not invoice.get("invoice_date_due"):
                continue
            
            due_date = datetime.strptime(invoice["invoice_date_due"], "%Y-%m-%d").date()
            days_overdue = (today - due_date).days
            
            # Only alert if overdue
            if days_overdue >= THRESHOLDS["overdue_days_warning"]:
                invoice_data = {
                    "id": invoice["id"],
                    "name": invoice["name"],
                    "partner_id": invoice["partner_id"][0] if invoice.get("partner_id") else 0,
                    "partner_name": invoice["partner_id"][1] if invoice.get("partner_id") else "Unknown",
                    "due_date": invoice["invoice_date_due"],
                    "amount_residual": invoice["amount_residual"],
                    "currency": invoice["currency_id"][1] if invoice.get("currency_id") else "USD",
                }
                
                if create_overdue_invoice_alert(invoice_data, days_overdue):
                    count += 1
        
        logger.info(f"Found {count} overdue invoices")
        
    except Exception as e:
        logger.error(f"Error polling unpaid invoices: {e}")
    
    return count


def poll_large_expenses(odoo: OdooClient) -> int:
    """Poll for large expenses."""
    count = 0
    
    try:
        # Get vendor bills from last 7 days
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        domain = [
            ("move_type", "=", "in_invoice"),
            ("invoice_date", ">=", seven_days_ago),
            ("state", "=", "posted")
        ]
        
        expenses = odoo.search_read(
            "account.move",
            domain,
            ["id", "name", "partner_id", "amount_total", "currency_id"],
            limit=50
        )
        
        for expense in expenses:
            amount = expense.get("amount_total", 0)
            
            if amount >= THRESHOLDS["expense_warning"]:
                expense_data = {
                    "id": expense["id"],
                    "name": expense["name"],
                    "vendor_id": expense["partner_id"][0] if expense.get("partner_id") else 0,
                    "vendor_name": expense["partner_id"][1] if expense.get("partner_id") else "Unknown",
                    "amount": amount,
                    "currency": expense["currency_id"][1] if expense.get("currency_id") else "USD",
                    "category": "Vendor Bill",
                }
                
                if create_large_expense_alert(expense_data):
                    count += 1
        
        logger.info(f"Found {count} large expenses")
        
    except Exception as e:
        logger.error(f"Error polling large expenses: {e}")
    
    return count


def run_single_poll() -> Dict:
    """Run a single poll cycle."""
    logger.info("Starting Odoo poll cycle...")
    
    results = {
        "overdue_invoices": 0,
        "large_expenses": 0,
    }
    
    # Check if Odoo is configured
    if not os.getenv("ODOO_URL"):
        logger.warning("Odoo not configured (ODOO_URL not set). Skipping poll.")
        return results
    
    # Initialize Odoo client
    odoo = OdooClient(ODOO_CONFIG)
    
    if not odoo.authenticate():
        logger.error("Failed to authenticate with Odoo. Skipping poll.")
        return results
    
    logger.info("Connected to Odoo successfully")
    
    # Run polls
    results["overdue_invoices"] = poll_unpaid_invoices(odoo)
    results["large_expenses"] = poll_large_expenses(odoo)
    
    total = sum(results.values())
    logger.info(f"Poll complete: {total} alerts created")
    
    return results


def run_watch_loop():
    """Run continuous watch loop."""
    logger.info("Starting Odoo Watcher...")
    logger.info(f"Odoo URL: {ODOO_CONFIG['url']}")
    logger.info(f"Odoo DB: {ODOO_CONFIG['db']}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    logger.info(f"Thresholds: {THRESHOLDS}")
    
    if DRY_RUN:
        logger.warning("DRY_RUN mode enabled - no files will be written")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.info(f"=== Poll Cycle {cycle_count} ===")
            
            results = run_single_poll()
            logger.info(f"Results: {results}")
            
            # Wait for next poll
            for _ in range(POLL_INTERVAL):
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")


# ============================================================================
# CLI
# ============================================================================


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Odoo Watcher")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run in continuous watch mode",
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
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ACCOUNTING_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.watch:
        run_watch_loop()
    else:
        run_single_poll()


if __name__ == "__main__":
    main()
