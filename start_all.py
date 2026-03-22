#!/usr/bin/env python3
# =============================================================================
# AI Employee - Start All Services
# =============================================================================
# Cross-platform script to start all AI Employee services
# Usage: python start_all.py [start|stop|status|restart]
# =============================================================================

import os
import sys
import subprocess
import time
import signal
import json
from pathlib import Path
from datetime import datetime

# Service configuration
SERVICES = {
    "backend": {
        "command": ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        "cwd": "./backend",
        "port": 8000,
        "url": "http://localhost:8000",
        "description": "Backend API (FastAPI)"
    },
    "frontend": {
        "command": ["npm", "run", "dev"],
        "cwd": "./frontend",
        "port": 3000,
        "url": "http://localhost:3000",
        "description": "Frontend (Next.js)"
    },
    "watcher-gmail": {
        "command": ["python", "run.py", "watcher", "gmail", "--watch"],
        "cwd": ".",
        "description": "Gmail Watcher"
    },
    "watcher-linkedin": {
        "command": ["python", "run.py", "watcher", "linkedin", "--watch"],
        "cwd": ".",
        "description": "LinkedIn Watcher"
    },
    "watcher-whatsapp": {
        "command": ["python", "run.py", "watcher", "whatsapp", "--watch"],
        "cwd": ".",
        "description": "WhatsApp Watcher"
    },
    "orchestrator": {
        "command": ["python", "run.py", "orchestrator"],
        "cwd": ".",
        "description": "Task Orchestrator"
    },
    "ai-agent": {
        "command": ["python", "run.py", "agent"],
        "cwd": ".",
        "description": "AI Agent (Ralph Loop)"
    }
}

PID_DIR = Path("./logs/pids")
LOG_DIR = Path("./logs")

class ServiceManager:
    def __init__(self):
        self.processes = {}
        PID_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    def check_prerequisites(self):
        """Check if Python and Node.js are installed"""
        print("\n" + "="*70)
        print("              AI EMPLOYEE - STARTING ALL SERVICES")
        print("="*70 + "\n")
        
        # Check Python
        try:
            python_version = subprocess.check_output(
                ["python", "--version"], 
                stderr=subprocess.STDOUT
            ).decode().strip()
            print(f"[✓] Python: {python_version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[✗] Python is not installed or not in PATH")
            print("Please install Python 3.8+ and add it to PATH")
            return False
        
        # Check Node.js
        try:
            node_version = subprocess.check_output(
                ["node", "--version"], 
                stderr=subprocess.STDOUT
            ).decode().strip()
            print(f"[✓] Node.js: {node_version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[✗] Node.js is not installed or not in PATH")
            print("Please install Node.js 20+ and add it to PATH")
            return False
        
        # Check .env file
        if not Path(".env").exists():
            print("[⚠] WARNING: .env file not found")
            print("    Please create .env file from .env.example")
            response = input("Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                return False
        
        print()
        return True
    
    def start_service(self, name, config):
        """Start a single service"""
        print(f"[INFO] Starting {config['description']}...")
        
        try:
            # Start process
            process = subprocess.Popen(
                config["command"],
                cwd=Path(config["cwd"]),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            # Save PID
            pid_file = PID_DIR / f"{name}.pid"
            pid_file.write_text(str(process.pid))
            
            # Start log thread
            log_file = LOG_DIR / f"{name}.log"
            self.processes[name] = {
                "process": process,
                "pid": process.pid,
                "start_time": datetime.now(),
                "config": config
            }
            
            print(f"  ✓ Started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")
            return False
    
    def start_all(self):
        """Start all services"""
        if not self.check_prerequisites():
            return False
        
        started = 0
        for name, config in SERVICES.items():
            if self.start_service(name, config):
                started += 1
                time.sleep(2)  # Stagger startup
        
        print("\n" + "="*70)
        print("                    ALL SERVICES STARTED")
        print("="*70)
        print(f"\nServices started: {started}/{len(SERVICES)}")
        print("\nAccess URLs:")
        print(f"  • Backend API  : {SERVICES['backend']['url']}")
        print(f"  • Frontend     : {SERVICES['frontend']['url']}")
        print(f"\nActive Watchers:")
        print(f"  • Gmail")
        print(f"  • LinkedIn")
        print(f"  • WhatsApp")
        print(f"\nBackground Services:")
        print(f"  • Orchestrator (Task lifecycle)")
        print(f"  • AI Agent (Ralph reasoning loop)")
        print(f"\nLogs directory: {LOG_DIR.absolute()}")
        print(f"PID files: {PID_DIR.absolute()}")
        print("\nTo stop all services: python start_all.py stop")
        print("="*70 + "\n")
        
        return True
    
    def stop_service(self, name):
        """Stop a single service"""
        pid_file = PID_DIR / f"{name}.pid"
        if not pid_file.exists():
            print(f"[INFO] {name} is not running (no PID file)")
            return
        
        try:
            pid = int(pid_file.read_text().strip())
            process = self.processes.get(name, {}).get("process")
            
            if process:
                process.terminate()
            else:
                # Try to kill by PID
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                 capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
            
            pid_file.unlink()
            print(f"[✓] Stopped {name} (PID: {pid})")
            
        except Exception as e:
            print(f"[✗] Failed to stop {name}: {str(e)}")
    
    def stop_all(self):
        """Stop all services"""
        print("\n" + "="*70)
        print("                 STOPPING ALL SERVICES")
        print("="*70 + "\n")
        
        for name in SERVICES.keys():
            self.stop_service(name)
        
        print("\n[✓] All services stopped")
        print("="*70 + "\n")
    
    def status(self):
        """Show status of all services"""
        print("\n" + "="*70)
        print("                   SERVICE STATUS")
        print("="*70 + "\n")
        
        for name, config in SERVICES.items():
            pid_file = PID_DIR / f"{name}.pid"
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    # Check if process is running
                    if sys.platform == "win32":
                        result = subprocess.run(
                            ["tasklist", "/FI", f"PID eq {pid}"],
                            capture_output=True,
                            text=True
                        )
                        is_running = str(pid) in result.stdout
                    else:
                        is_running = os.path.exists(f"/proc/{pid}")
                    
                    if is_running:
                        print(f"✓ {config['description']:30} (PID: {pid})")
                    else:
                        print(f"✗ {config['description']:30} (PID: {pid}) - NOT RUNNING")
                        pid_file.unlink()
                except Exception as e:
                    print(f"✗ {config['description']:30} - Error: {str(e)}")
            else:
                print(f"- {config['description']:30} (Not started)")
        
        print("\n" + "="*70 + "\n")


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python start_all.py [start|stop|status|restart]")
        print("\nCommands:")
        print("  start   - Start all services")
        print("  stop    - Stop all services")
        print("  status  - Show status of all services")
        print("  restart - Restart all services")
        print()
        sys.exit(1)
    
    manager = ServiceManager()
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_all()
    elif command == "stop":
        manager.stop_all()
    elif command == "status":
        manager.status()
    elif command == "restart":
        manager.stop_all()
        time.sleep(3)
        manager.start_all()
    else:
        print(f"[ERROR] Unknown command: {command}")
        print("Use 'start', 'stop', 'status', or 'restart'")
        sys.exit(1)


if __name__ == "__main__":
    main()
