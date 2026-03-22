#!/usr/bin/env python3
"""Process all files in Needs_Action → Plans + Done + Logs."""

import sys
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import logger
try:
    from src.utils.logger import log_action, set_default_logs_dir
except ImportError:
    # Fallback logger if src.utils not found
    def log_action(action, file, status):
        print(f"[{datetime.now()}] {action}: {file} ({status})")
    def set_default_logs_dir(path):
        pass

# Configuration
VAULT_DIR = Path("AI-Employee-Vault")
NEEDS_ACTION_DIR = VAULT_DIR / "Needs_Action"
PLANS_DIR = VAULT_DIR / "Plans"
DONE_DIR = VAULT_DIR / "Done"
LOGS_DIR = VAULT_DIR / "Logs"

def process_needs_action():
    """Scan and process files in Needs_Action."""
    count = 0
    # Ensure directories exist
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    set_default_logs_dir(LOGS_DIR)

    # Process files
    for f in sorted(NEEDS_ACTION_DIR.glob("*.md")):
        if f.name.startswith(".") or f.stem.endswith(".meta"):
            continue

        try:
            content = f.read_text(encoding="utf-8")
            lines = [l.strip() for l in content.splitlines() if l.strip()]

            obj = f.stem
            steps = []
            
            # Simple parsing logic (can be replaced with AI calls later)
            for l in lines:
                if l.startswith("# "):
                    obj = l.lstrip("# ")
                # Extract potential steps
                s = l.lstrip("-*0123456789.) ")
                if len(s) > 5 and l != s: 
                    steps.append(s)
            
            if not steps:
                steps = ["Review content", "Identify actions", "Execute", "Verify"]

            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            step_lines = "\n".join(f"- [ ] {s}" for s in steps)
            plan_content = (
                f'---\nsource: "{f.name}"\ncreated_at: "{ts}"\nstatus: pending\n---\n\n'
                f"# Plan: {obj}\n\n## Steps\n\n{step_lines}\n\n"
                f"## Status\n\n**pending**\n"
            )

            # Create Plan
            plan_file = PLANS_DIR / f"plan-{f.stem}.md"
            plan_file.write_text(plan_content, encoding="utf-8")
            log_action("plan_created", plan_file.name, "success")

            # Move Original to Done
            shutil.move(str(f), str(DONE_DIR / f.name))
            log_action("file_moved", f.name, "success")

            # Move Metadata if exists
            meta = NEEDS_ACTION_DIR / f"{f.stem}.meta.md"
            if meta.exists():
                shutil.move(str(meta), str(DONE_DIR / meta.name))

            count += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed: {f.name} -> Plan created.")
            
        except Exception as e:
            print(f"Error processing {f.name}: {e}")
            log_action("process_error", f.name, f"failed: {str(e)}")

    return count

def main_loop():
    print(f"Orchestrator Service started. Watching {NEEDS_ACTION_DIR}...")
    try:
        while True:
            processed = process_needs_action()
            if processed > 0:
                pass # Already printed output
            time.sleep(5) # Wait 5 seconds before next scan
    except KeyboardInterrupt:
        print("Orchestrator stopped.")

if __name__ == "__main__":
    main_loop()
