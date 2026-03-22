#!/usr/bin/env python3
"""
AI Employee Master Runner — Starts all watchers, MCP servers, and approval monitor.
Single entry point: python run_master.py
"""
import os
import sys
import time
import json
import signal
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
VAULT = ROOT / "AI-Employee-Vault"
APPROVED_DIR = VAULT / "Approved"
DONE_DIR = VAULT / "Done"
LOGS_DIR = VAULT / "Logs"

# All services to run
SERVICES = [
    {"name": "Gmail Watcher", "cmd": [sys.executable, "src/watcher/gmail_watcher.py", "--watch"]},
    {"name": "LinkedIn Watcher", "cmd": [sys.executable, "src/watcher/linkedin_watcher.py", "--watch"]},
    {"name": "WhatsApp Watcher", "cmd": [sys.executable, "src/watcher/whatsapp_watcher.py", "--watch"]},
    {"name": "Odoo Watcher", "cmd": [sys.executable, "src/watcher/odoo_watcher.py", "--watch"]},
    {"name": "Social Watcher", "cmd": [sys.executable, "src/watcher/social_watcher.py", "--watch"]},
    {"name": "MCP Odoo Server", "cmd": ["node", "mcp/odoo-server/src/index.js"]},
]

processes: dict[str, subprocess.Popen] = {}
running = True


def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"master-{time.strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def start_service(svc: dict) -> subprocess.Popen | None:
    name = svc["name"]
    cmd = svc["cmd"]
    # Check if the script/binary exists
    target = cmd[1] if len(cmd) > 1 else cmd[0]
    target_path = ROOT / target if not Path(target).is_absolute() else Path(target)
    if not target_path.exists():
        log(f"  SKIP {name} — {target} not found")
        return None
    try:
        p = subprocess.Popen(
            cmd, cwd=str(ROOT),
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
        log(f"  Started {name} (PID {p.pid})")
        return p
    except Exception as e:
        log(f"  FAIL {name}: {e}")
        return None


def stop_all():
    global running
    running = False
    log("Stopping all services...")
    for name, p in processes.items():
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    log("All services stopped.")


def signal_handler(sig, frame):
    print()
    stop_all()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def run_social_post(platform: str, content: str) -> bool:
    """Execute a social media post for an approved file."""
    if platform == "twitter":
        script = ROOT / "mcp" / "twitter-server" / "src" / "post_executor.js"
    elif platform == "linkedin":
        script = ROOT / "mcp" / "linkedin-server" / "post_executor.js"
    elif platform == "facebook":
        script = ROOT / "mcp" / "facebook-server" / "src" / "post_executor.js"
    elif platform == "instagram":
        script = ROOT / "mcp" / "instagram-server" / "src" / "post_executor.js"
    else:
        log(f"  No executor for platform: {platform}")
        return False

    if not script.exists():
        log(f"  Executor not found: {script}")
        return False

    temp = ROOT / f".temp_{platform}_post.txt"
    temp.write_text(content, encoding="utf-8")
    try:
        subprocess.run(["node", str(script), str(temp)], check=True, timeout=60, cwd=str(ROOT))
        return True
    except Exception as e:
        log(f"  Post failed: {e}")
        return False
    finally:
        if temp.exists():
            temp.unlink()


def monitor_approvals():
    """Check Approved/ folder and execute approved posts."""
    if not APPROVED_DIR.exists():
        return
    for f in APPROVED_DIR.glob("social-post-*.md"):
        log(f"Found approved: {f.name}")
        try:
            text = f.read_text(encoding="utf-8")
            platform = ""
            post_content = ""
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("platform:"):
                    platform = line.split(":", 1)[1].strip().strip('"')
                if line.strip() == "## Content":
                    post_content = "\n".join(lines[i + 2:])
                    if "---" in post_content:
                        post_content = post_content.split("---")[0].strip()
                    break

            if platform and post_content:
                if run_social_post(platform, post_content):
                    DONE_DIR.mkdir(parents=True, exist_ok=True)
                    f.rename(DONE_DIR / f.name)
                    log(f"  Executed & moved to Done: {f.name}")
                else:
                    log(f"  Execution failed: {f.name}")
            else:
                log(f"  Could not parse: {f.name}")
        except Exception as e:
            log(f"  Error processing {f.name}: {e}")


def print_status():
    """Print current service status."""
    alive = sum(1 for p in processes.values() if p and p.poll() is None)
    total = len(processes)
    log(f"Services: {alive}/{total} running")


def main():
    print()
    print("\u2501" * 50)
    print("  AI Employee Master Runner")
    print("\u2501" * 50)

    # Ensure vault dirs
    for d in ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Done", "Logs"]:
        (VAULT / d).mkdir(parents=True, exist_ok=True)

    # Start all services
    log("Starting services...")
    for svc in SERVICES:
        p = start_service(svc)
        processes[svc["name"]] = p

    alive = sum(1 for p in processes.values() if p and p.poll() is None)
    log(f"\n  {alive}/{len(SERVICES)} services running. Monitoring approvals...")
    print("  Press Ctrl+C to stop.\n")

    cycle = 0
    while running:
        try:
            # Monitor approvals every cycle
            monitor_approvals()

            # Auto-restart dead services
            for svc in SERVICES:
                name = svc["name"]
                p = processes.get(name)
                if p and p.poll() is not None:
                    log(f"  {name} died (code {p.returncode}). Restarting...")
                    processes[name] = start_service(svc)

            # Print status every 6 cycles (~60s)
            cycle += 1
            if cycle % 6 == 0:
                print_status()

            time.sleep(10)
        except KeyboardInterrupt:
            break

    stop_all()


if __name__ == "__main__":
    main()
