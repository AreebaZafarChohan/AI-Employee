#!/usr/bin/env python3
"""
AI Employee — Bronze Tier (All-in-One)

Ek file, poora pipeline. Continuously chalta hai:
  1. Inbox watch karta hai naye files ke liye
  2. Copy karta hai Needs_Action mein + metadata sidecar
  3. Plan banata hai Plans/ mein
  4. Original move karta hai Done/ mein
  5. Har action log karta hai Logs/ mein (JSON)
  6. Duplicate files dobara process nahi hoti

Usage:
    python3 ai_employee.py              # start (Ctrl+C to stop)
    python3 ai_employee.py --vault PATH # custom vault path

Drop any .md or .txt file into Inbox/ and watch the magic happen.
"""

import json
import shutil
import signal
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.utils.logger import log_action, set_default_logs_dir

# Parse --vault flag
vault_path = ROOT / "AI-Employee-Vault"
if "--vault" in sys.argv:
    idx = sys.argv.index("--vault")
    if idx + 1 < len(sys.argv):
        vault_path = Path(sys.argv[idx + 1]).resolve()

INBOX = vault_path / "Inbox"
NEEDS_ACTION = vault_path / "Needs_Action"
PLANS = vault_path / "Plans"
DONE = vault_path / "Done"
LOGS = vault_path / "Logs"
LEDGER = vault_path / ".processed_files.json"

FILE_PATTERNS = {".md", ".txt"}

# Ensure all folders exist
for folder in [INBOX, NEEDS_ACTION, PLANS, DONE, LOGS]:
    folder.mkdir(parents=True, exist_ok=True)

set_default_logs_dir(LOGS)


# ---------------------------------------------------------------------------
# Ledger — persistent duplicate guard
# ---------------------------------------------------------------------------

def load_ledger() -> set:
    if not LEDGER.exists():
        return set()
    try:
        return set(json.loads(LEDGER.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return set()


def save_ledger(entries: set) -> None:
    LEDGER.write_text(json.dumps(sorted(entries), indent=2), encoding="utf-8")


processed = load_ledger()


# ---------------------------------------------------------------------------
# Step 1+2: Copy Inbox → Needs_Action + metadata sidecar
# ---------------------------------------------------------------------------

def copy_to_needs_action(file_path: Path) -> Path | None:
    """Copy file from Inbox to Needs_Action, create metadata sidecar."""
    name = file_path.name

    if name in processed:
        return None

    # Handle name collisions
    dest = NEEDS_ACTION / name
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = NEEDS_ACTION / f"{file_path.stem}_{ts}{file_path.suffix}"

    shutil.copy2(str(file_path), str(dest))

    # Metadata sidecar
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta_content = (
        "---\n"
        "type: file_drop\n"
        f'original_name: "{name}"\n'
        f'created_at: "{created_at}"\n'
        "status: pending\n"
        "---\n"
    )
    meta_path = NEEDS_ACTION / f"{dest.stem}.meta.md"
    meta_path.write_text(meta_content, encoding="utf-8")

    # Update ledger
    processed.add(name)
    save_ledger(processed)

    log_action("file_copied", name, "success")
    _print(f"  INBOX -> Needs_Action: {name}")
    return dest


# ---------------------------------------------------------------------------
# Step 3+4: Process Needs_Action → Plan + Done
# ---------------------------------------------------------------------------

def process_needs_action():
    """Process all unprocessed files in Needs_Action."""
    files = [
        f for f in sorted(NEEDS_ACTION.iterdir())
        if f.is_file()
        and f.suffix in FILE_PATTERNS
        and not f.name.startswith(".")
        and not f.stem.endswith(".meta")
    ]

    for f in files:
        try:
            _create_plan(f)
            _move_to_done(f)
        except Exception as e:
            _print(f"  ERROR processing {f.name}: {e}")
            log_action("process_error", f.name, f"error: {e}")


def _create_plan(file_path: Path) -> None:
    """Analyse content and write a plan file."""
    content = file_path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

    # Extract objective
    objective = file_path.stem.replace("-", " ").replace("_", " ").title()
    for line in lines:
        if line.startswith("# "):
            objective = line.lstrip("# ").strip()
            break

    # Extract steps
    steps = []
    for line in lines:
        stripped = line.lstrip("-*0123456789.) ")
        if line != stripped and stripped:
            steps.append(stripped)
    if not steps:
        steps = [
            f"Review content of {file_path.name}",
            "Identify required actions",
            "Execute per Company Handbook",
            "Verify completion",
        ]

    # Write plan
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    step_lines = "\n".join(f"- [ ] {s}" for s in steps)
    plan_content = (
        f'---\nsource: "{file_path.name}"\n'
        f'created_at: "{ts}"\nstatus: pending\n---\n\n'
        f"# Plan: {objective}\n\n"
        f"## Objective\n\n{objective}\n\n"
        f"## Steps\n\n{step_lines}\n\n"
        f"## Status\n\n**pending** — awaiting human review.\n"
    )

    plan_name = f"plan-{file_path.stem}.md"
    (PLANS / plan_name).write_text(plan_content, encoding="utf-8")
    log_action("plan_created", plan_name, "success")
    _print(f"  PLAN created: {plan_name}")


def _move_to_done(file_path: Path) -> None:
    """Move file and its sidecar to Done."""
    name = file_path.name

    dest = DONE / name
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = DONE / f"{file_path.stem}_{ts}{file_path.suffix}"

    shutil.move(str(file_path), str(dest))
    log_action("file_archived", name, "success")

    # Move sidecar too
    meta = NEEDS_ACTION / f"{file_path.stem}.meta.md"
    if meta.exists():
        shutil.move(str(meta), str(DONE / meta.name))

    _print(f"  DONE: {name} archived")


# ---------------------------------------------------------------------------
# Watchdog handler — triggers the full pipeline
# ---------------------------------------------------------------------------

class InboxHandler(FileSystemEventHandler):
    """When a new file lands in Inbox, run the full pipeline."""

    def __init__(self):
        super().__init__()
        self._handled: set = set()

    def _should_process(self, event) -> Path | None:
        """Check if this event should trigger processing."""
        if event.is_directory:
            return None
        fp = Path(event.src_path)
        if fp.suffix not in FILE_PATTERNS:
            return None
        if fp.name.startswith("."):
            return None
        if fp.stem.endswith(".meta"):
            return None
        return fp

    def on_created(self, event):
        fp = self._should_process(event)
        if not fp:
            return
        # Small delay to let file write finish
        time.sleep(0.5)
        self._run_pipeline(fp)

    def on_modified(self, event):
        fp = self._should_process(event)
        if not fp:
            return
        # For modified files (e.g. file updated while running),
        # process if not already handled in this batch
        self._run_pipeline(fp)

    def _run_pipeline(self, fp: Path):
        """Run full pipeline for a file — with dedup within same second."""
        # Prevent double-trigger (created + modified fire together)
        key = f"{fp.name}:{int(time.time())}"
        if key in self._handled:
            return
        self._handled.add(key)

        # Cleanup old keys (keep set small)
        cutoff = str(int(time.time()) - 5)
        self._handled = {k for k in self._handled if k.split(":")[1] >= cutoff}

        if not fp.exists():
            return

        _print(f"\n  New file detected: {fp.name}")

        # Full pipeline: copy → process → plan → done → log
        result = copy_to_needs_action(fp)
        if result:
            process_needs_action()
        else:
            _print(f"  Skipped (already processed): {fp.name}")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _print(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Process any existing files first
    _print("Checking for existing Inbox files...")
    existing = [
        f for f in sorted(INBOX.iterdir())
        if f.is_file() and f.suffix in FILE_PATTERNS and not f.name.startswith(".")
    ]
    new_count = 0
    for f in existing:
        if copy_to_needs_action(f):
            new_count += 1

    if new_count > 0:
        _print(f"Copied {new_count} existing file(s) to Needs_Action")
        process_needs_action()
    else:
        _print("No new files in Inbox")

    # Also process anything already sitting in Needs_Action
    process_needs_action()

    # Start live watcher
    handler = InboxHandler()
    observer = Observer()
    observer.schedule(handler, str(INBOX), recursive=False)
    observer.start()

    _print("")
    _print("=" * 50)
    _print("  AI EMPLOYEE — Bronze Tier — RUNNING")
    _print("=" * 50)
    _print(f"  Watching: {INBOX}")
    _print(f"  Plans:    {PLANS}")
    _print(f"  Done:     {DONE}")
    _print(f"  Logs:     {LOGS}")
    _print("=" * 50)
    _print("  Drop a .md or .txt file in Inbox/")
    _print("  Press Ctrl+C to stop")
    _print("=" * 50)
    _print("")

    try:
        while observer.is_alive():
            observer.join(3)

            # Safety net: poll Inbox every 3 seconds
            # (WSL2 filesystem events can be unreliable)
            for f in sorted(INBOX.iterdir()):
                if (
                    f.is_file()
                    and f.suffix in FILE_PATTERNS
                    and not f.name.startswith(".")
                    and f.name not in processed
                ):
                    _print(f"\n  Polled new file: {f.name}")
                    result = copy_to_needs_action(f)
                    if result:
                        process_needs_action()

    except KeyboardInterrupt:
        _print("\nShutting down...")
    finally:
        observer.stop()
        observer.join()
        _print("AI Employee stopped. Goodbye!")


if __name__ == "__main__":
    main()
