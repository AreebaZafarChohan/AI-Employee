#!/usr/bin/env python3
"""Bronze Tier Filesystem Watcher — entry point.

Monitors AI-Employee-Vault/Inbox/ for new files and copies them to
Needs_Action/ with metadata sidecars.

Usage:
    python filesystem_watcher.py              # live watch (Ctrl-C to stop)
    python filesystem_watcher.py --scan       # one-shot scan then exit
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.watcher.file_system_watcher import FileSystemWatcher  # noqa: E402


VAULT_PATH = Path(__file__).resolve().parent / "AI-Employee-Vault"


def main() -> None:
    parser = argparse.ArgumentParser(description="Bronze Tier Filesystem Watcher")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Run a single scan of Inbox/ then exit (no live watching).",
    )
    parser.add_argument(
        "--vault",
        type=str,
        default=str(VAULT_PATH),
        help=f"Path to the Obsidian vault (default: {VAULT_PATH}).",
    )
    args = parser.parse_args()

    watcher = FileSystemWatcher(vault_path=args.vault)

    if args.scan:
        result = watcher.scan_once()
        print(f"Scan complete: {result['found']} found, "
              f"{result['processed']} processed, "
              f"{result['skipped']} skipped, "
              f"{len(result['errors'])} errors")
        if result["errors"]:
            for err in result["errors"]:
                print(f"  ERROR: {err}")
    else:
        print(f"Watching: {watcher.inbox_path}")
        print("Press Ctrl-C to stop.\n")
        watcher.start(blocking=True)


if __name__ == "__main__":
    main()
