#!/usr/bin/env python3
"""Silver Tier WhatsApp Watcher.

Uses Playwright (async) with a persistent browser context to monitor WhatsApp
Web for unread chats. Every unread message is captured and a structured
markdown file is written to AI-Employee-Vault/Needs_Action/.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
import urllib.request
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ... rest of imports and config ...
# (I will provide the full file but with the updated functions)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.utils.logger import log_action, set_default_logs_dir
from src.utils.cross_dedup import CrossSourceDedup

_cross_dedup = CrossSourceDedup()

VAULT_PATH = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL_DIR = VAULT_PATH / "Pending_Approval"
APPROVED_DIR = VAULT_PATH / "Approved"
REJECTED_DIR = VAULT_PATH / "Rejected"
LOGS_DIR = VAULT_PATH / "Logs"

WA_PROFILE_DIR = Path(os.getenv("WA_PROFILE_DIR", ROOT / ".whatsapp_profile")).resolve()
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
DRY_RUN: bool = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")
WA_HEADLESS: bool = os.getenv("WA_HEADLESS", "false").lower() in ("true", "1", "yes")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

# ... (skipped boilerplate) ...

def _notify_backend_event(filename: str, metadata: dict | None = None) -> None:
    """Notify the backend API of a new event."""
    if DRY_RUN:
        return
    try:
        url = f"{BACKEND_API_URL}/events/new"
        payload = {
            "source": "whatsapp_watcher",
            "file": filename,
            "metadata": metadata or {},
        }
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            logging.info(f"Backend notified: {filename}")
    except Exception as exc:
        logging.debug("Backend event notification failed (non-critical): %s", exc)

def _write_needs_action(sender: str, message: str, timestamp: str, risk: str) -> Path:
    slug = re.sub(r"[^\w\s-]", "", sender.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-") or "unknown"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"whatsapp-{slug[:40]}-{ts}.md"
    
    dest = NEEDS_ACTION_DIR / filename
    
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = (
        "---\n"
        "type: whatsapp\n"
        f'sender: "{sender}"\n'
        f'message: "{message.replace(chr(10), " ")}"\n'
        f'received: "{timestamp}"\n'
        f"risk_level: {risk}\n"
        f'created_at: "{now_iso}"\n'
        "---\n\n"
        f"# WhatsApp: {sender}\n\n{message}"
    )

    if not DRY_RUN:
        NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        _notify_backend_event(filename, {"sender": sender, "risk_level": risk})
    
    return dest

# ... (rest of the file remains similar in spirit) ...
