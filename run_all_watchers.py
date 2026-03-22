"""Main Orchestrator to run all watchers and monitor approvals."""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
VAULT_PATH = ROOT / "AI-Employee-Vault"
APPROVED_DIR = VAULT_PATH / "Approved"
DONE_DIR = VAULT_PATH / "Done"

# Watchers to run
WATCHERS = [
    [sys.executable, "src/watcher/whatsapp_watcher.py", "--watch"],
    [sys.executable, "src/watcher/gmail_watcher.py", "--watch"],
    [sys.executable, "src/watcher/linkedin_watcher.py", "--watch"],
    [sys.executable, "src/watcher/odoo_watcher.py", "--watch"],
    [sys.executable, "src/watcher/social_watcher.py", "--watch"],
]

processes = []

def signal_handler(sig, frame):
    print("\nStopping all watchers...")
    for p in processes:
        try:
            p.terminate()
        except:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_social_post(platform: str, content: str):
    """Call the appropriate script to post to social media."""
    print(f"🚀 Posting to {platform}...")
    
    if platform == "linkedin":
        # Use the LinkedIn post executor
        script_path = ROOT / "mcp" / "linkedin-server" / "post_executor.js"
        if script_path.exists():
            # Create a temp file for the content to avoid shell escaping issues
            temp_content = ROOT / ".temp_post_content.txt"
            temp_content.write_text(content, encoding="utf-8")
            try:
                # Use node directly
                cmd = ["node", str(script_path), str(temp_content)]
                subprocess.run(cmd, check=True)
                print(f"✅ Posted to LinkedIn successfully.")
                return True
            except Exception as e:
                print(f"❌ LinkedIn post failed: {e}")
                return False
            finally:
                if temp_content.exists():
                    temp_content.unlink()
        else:
            print(f"⚠️ LinkedIn post script not found at {script_path}")
    
    elif platform == "twitter":
        # Use the Twitter post executor (Playwright version)
        script_path = ROOT / "mcp" / "twitter-server" / "src" / "post_executor.js"
        if script_path.exists():
            # Create a temp file for the content to avoid shell escaping issues
            temp_content = ROOT / ".temp_twitter_post_content.txt"
            temp_content.write_text(content, encoding="utf-8")
            try:
                # Use node directly
                print(f"📡 Executing script: node {script_path}")
                cmd = ["node", str(script_path), str(temp_content)]
                subprocess.run(cmd, check=True)
                print(f"✅ Posted to Twitter successfully.")
                return True
            except Exception as e:
                print(f"❌ Twitter post failed: {e}")
                return False
            finally:
                if temp_content.exists():
                    temp_content.unlink()
        else:
            print(f"⚠️ Twitter post script not found at {script_path}")
    
    elif platform == "whatsapp":
        # Use the WhatsApp sender script
        script_path = ROOT / "whatsapp_sender.py"
        if script_path.exists():
            try:
                # Format: python3 whatsapp_sender.py --contact "Contact" --instruction "Content"
                # But our script is meant to take instruction and generate. 
                # Let's adapt it to take raw message if we want, or just use the current one.
                # Actually, social_service.py generates the content, so we just need to SEND it.
                # For now, let's just log it.
                print(f"⚠️ WhatsApp outbound posting from generated content not yet fully implemented.")
                return False
            except Exception as e:
                print(f"❌ WhatsApp post failed: {e}")
                return False
        else:
            print(f"⚠️ WhatsApp sender script not found.")
    
    # Add other platforms here...
    print(f"⚠️ Posting for {platform} not yet implemented in orchestrator.")
    return False

def monitor_approvals():
    """Check Approved/ folder for social posts to execute."""
    if not APPROVED_DIR.exists():
        return

    # Look for social-post-*.md
    approved_files = list(APPROVED_DIR.glob("social-post-*.md"))
    for f in approved_files:
        print(f"🔎 Found approved post: {f.name}")
        try:
            content = f.read_text(encoding="utf-8")
            
            # Simple parser for the markdown content I generated in social_service.py
            platform = ""
            post_content = ""
            
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("platform:"):
                    platform = line.split(":", 1)[1].strip().strip('"')
                if line.strip() == "## Content":
                    # Content starts after this heading
                    post_content = "\n".join(lines[i+2:])
                    # Remove the footer/instructions part
                    if "---" in post_content:
                        post_content = post_content.split("---")[0].strip()
                    break
            
            if platform and post_content:
                if run_social_post(platform, post_content):
                    # Move to Done
                    DONE_DIR.mkdir(parents=True, exist_ok=True)
                    dest = DONE_DIR / f.name
                    f.rename(dest)
                    print(f"✅ Executed and moved to Done: {f.name}")
                else:
                    print(f"❌ Failed to execute post for {f.name}")
            else:
                print(f"⚠️ Could not parse platform or content from {f.name}")
                
        except Exception as e:
            print(f"Error processing approved file {f.name}: {e}")

def main():
    print("🌟 AI Employee Orchestrator Starting...")
    print(f"Vault: {VAULT_PATH}")
    
    # Ensure directories exist
    for d in ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Done", "Logs"]:
        (VAULT_PATH / d).mkdir(parents=True, exist_ok=True)

    # Start watchers
    for cmd in WATCHERS:
        print(f"📡 Starting watcher: {' '.join(cmd)}")
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        processes.append(p)

    print("\n✅ All watchers running. Monitoring Approvals...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            monitor_approvals()
            # Check if any process died
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    print(f"⚠️ Watcher {WATCHERS[i][1]} died with code {p.returncode}. Restarting...")
                    processes[i] = subprocess.Popen(WATCHERS[i], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            
            time.sleep(10)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
