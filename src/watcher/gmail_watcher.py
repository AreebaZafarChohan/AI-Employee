#!/usr/bin/env python3
"""Gold Tier Gmail Watcher.
Inherits from BaseWatcher and implements Gmail-specific polling.
"""

import os
import sys
import re
from pathlib import Path
from typing import Any, Dict, Optional

# Bootstrap
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.watcher.base_watcher import BaseWatcher
from src.utils.cross_dedup import CrossSourceDedup

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: Optional[Path] = None):
        super().__init__("gmail_watcher", vault_path)
        self.dedup = CrossSourceDedup()
        self.ledger_file = self.vault_path / ".gmail_processed.json"
        self.ledger = self._load_ledger()
        self.service = self._build_service()

    def _load_ledger(self) -> set:
        if self.ledger_file.exists():
            try:
                import json
                return set(json.loads(self.ledger_file.read_text()))
            except:
                return set()
        return set()

    def _save_ledger(self):
        if not self.dry_run:
            import json
            self.ledger_file.write_text(json.dumps(list(self.ledger)))

    def _build_service(self):
        # Implementation of Gmail API build
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        token_file = self.root / "token.json"
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file))
            return build("gmail", "v1", credentials=creds)
        return None

    def poll(self) -> Dict[str, Any]:
        if not self.service:
            self.logger.error("Gmail service not initialized.")
            return {"error": "no_service"}

        summary = {"processed": 0, "skipped": 0, "errors": 0}
        
        try:
            query = "is:unread (is:important OR is:starred)"
            results = self.service.users().messages().list(userId="me", q=query, maxResults=10).execute()
            messages = results.get("messages", [])

            for msg_stub in messages:
                msg_id = msg_stub["id"]
                if msg_id in self.ledger:
                    summary["skipped"] += 1
                    continue

                msg = self.service.users().messages().get(userId="me", id=msg_id).execute()
                snippet = msg.get("snippet", "")
                
                if self.dedup.is_duplicate(snippet, "gmail"):
                    summary["skipped"] += 1
                    continue

                # Extract headers
                headers = msg.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")

                task_data = {
                    "type": "email",
                    "subject": subject,
                    "from": sender,
                    "snippet": snippet,
                    "gmail_id": msg_id,
                    "thread_id": msg.get("threadId")
                }

                # Write to Needs_Action/emails/
                if self.write_to_needs_action("emails", subject, task_data):
                    self.ledger.add(msg_id)
                    summary["processed"] += 1
                else:
                    summary["errors"] += 1

            self._save_ledger()
            return summary

        except Exception as e:
            self.logger.error(f"Poll error: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()

    watcher = GmailWatcher()
    watcher.run(watch=args.watch)
