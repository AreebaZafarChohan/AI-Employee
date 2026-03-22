#!/usr/bin/env python3
"""Gmail Actions script to mark messages as read."""

import sys
import os
import argparse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from gmail_watcher import _build_gmail_service, _with_retry

def mark_as_read(message_id: str):
    service = _build_gmail_service()
    print(f"Marking message {message_id} as read...")
    
    _with_retry(
        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": [message_id],
                "removeLabelIds": ["UNREAD"]
            }
        ).execute,
        label=f"mark_as_read:{message_id}"
    )
    print(f"Successfully marked {message_id} as read.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform actions on Gmail messages.")
    parser.add_argument("action", choices=["mark_as_read"], help="Action to perform")
    parser.add_argument("--message_id", required=True, help="Gmail message ID")
    
    args = parser.parse_args()
    
    if args.action == "mark_as_read":
        mark_as_read(args.message_id)
