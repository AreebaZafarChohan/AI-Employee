#!/usr/bin/env python3
"""
AI Employee - Unified Entry Point (Gold Tier)

Usage:
    python run.py orchestrator          # Start the Vault Orchestrator
    python run.py watcher gmail         # Start the Gmail Watcher
    python run.py watcher linkedin      # Start the LinkedIn Watcher
    python run.py watcher whatsapp      # Start the WhatsApp Watcher
    python run.py all                   # Start all default agents (Orchestrator + Watchers)
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ["PYTHONPATH"] = str(ROOT)

def start_agent(path: str, args: list = None):
    """Start an agent process."""
    cmd = [sys.executable, str(ROOT / path)]
    if args:
        cmd.extend(args)
    
    print(f"[*] Starting agent: {path} {' '.join(args or [])}")
    return subprocess.Popen(cmd)

def main():
    parser = argparse.ArgumentParser(description="AI Employee Runner")
    parser.add_argument("command", choices=["orchestrator", "watcher", "all"], help="Command to run")
    parser.add_argument("subcommand", nargs="?", help="Sub-command (e.g. gmail, linkedin)")
    parser.add_argument("--watch", action="store_true", help="Run in watch mode")
    parser.add_argument("--role", choices=["cloud", "local"], default="cloud", help="Role for orchestrator")
    
    args = parser.parse_args()

    processes = []

    if args.command == "orchestrator":
        orchestrator_args = ["--role", args.role]
        p = start_agent("src/orchestration/vault_orchestrator.py", orchestrator_args)
        processes.append(p)
    
    elif args.command == "watcher":
        if not args.subcommand:
            print("Error: Specify a watcher name (gmail, linkedin, whatsapp, odoo, social, filesystem)")
            sys.exit(1)
        
        watcher_map = {
            "gmail": "src/watcher/gmail_watcher.py",
            "linkedin": "src/watcher/linkedin_watcher.py",
            "whatsapp": "src/watcher/whatsapp_watcher.py",
            "odoo": "src/watcher/odoo_watcher.py",
            "social": "src/watcher/social_watcher.py",
            "filesystem": "src/watcher/filesystem_watcher.py"
        }
        
        script_path = watcher_map.get(args.subcommand)
        if not script_path:
            print(f"Error: Unknown watcher '{args.subcommand}'")
            sys.exit(1)
            
        watcher_args = ["--watch"] if args.watch else []
        p = start_agent(script_path, watcher_args)
        processes.append(p)
    
    elif args.command == "all":
        # Start both brains (Gold Tier)
        print("[*] Starting Gold Tier Brains (Cloud & Local)...")
        processes.append(start_agent("src/orchestration/vault_orchestrator.py", ["--role", "cloud"]))
        processes.append(start_agent("src/orchestration/vault_orchestrator.py", ["--role", "local"]))
        
        # Start core watchers in watch mode
        watchers = ["gmail", "linkedin", "whatsapp"]
        for w in watchers:
            processes.append(start_agent(f"src/watcher/{w}_watcher.py", ["--watch"]))

    try:
        print(f"\n[!] Running {len(processes)} agents. Press Ctrl+C to stop.\n")
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n[!] Stopping all agents...")
        for p in processes:
            p.terminate()
        print("[!] Goodbye!")

if __name__ == "__main__":
    main()
