"""
Watcher Service - Manages all watcher processes with start/stop/status control.
Similar to PM2 process management for AI Employee watchers.
"""

import os
import sys
import json
import signal
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("watcher_service")

# Root paths
ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
LOGS_DIR = VAULT_PATH / "Logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# State file to track watcher processes
STATE_FILE = LOGS_DIR / "watcher_service_state.json"


@dataclass
class WatcherProcess:
    """Represents a watcher process with its metadata."""
    id: str
    name: str
    script: str
    command: List[str]
    status: str  # running, stopped, error, unknown
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    restart_count: int = 0
    uptime_seconds: int = 0
    last_log: Optional[str] = None
    last_log_time: Optional[str] = None
    logs_today: int = 0
    items_processed: int = 0
    started_at: Optional[str] = None
    error_message: Optional[str] = None


class WatcherService:
    """Service to manage all watcher processes."""
    
    # Registry of all available watchers
    WATCHER_REGISTRY = {
        "gmail": {
            "name": "Gmail Watcher",
            "script": "src/watcher/gmail_watcher.py",
            "command": [sys.executable, "src/watcher/gmail_watcher.py", "--watch"],
            "icon": "mail",
            "color": "red",
            "description": "Monitors Gmail for important emails",
        },
        "whatsapp": {
            "name": "WhatsApp Watcher",
            "script": "src/watcher/whatsapp_watcher.py",
            "command": [sys.executable, "src/watcher/whatsapp_watcher.py", "--watch"],
            "icon": "message-square",
            "color": "green",
            "description": "Monitors WhatsApp messages",
        },
        "linkedin": {
            "name": "LinkedIn Watcher",
            "script": "src/watcher/linkedin_watcher.py",
            "command": [sys.executable, "src/watcher/linkedin_watcher.py", "--watch"],
            "icon": "linkedin",
            "color": "blue",
            "description": "Monitors LinkedIn DMs and mentions",
        },
        "odoo": {
            "name": "Odoo Watcher",
            "script": "src/watcher/odoo_watcher.py",
            "command": [sys.executable, "src/watcher/odoo_watcher.py", "--watch"],
            "icon": "shopping-cart",
            "color": "purple",
            "description": "Monitors Odoo for accounting events",
        },
        "social": {
            "name": "Social Media Watcher",
            "script": "src/watcher/social_watcher.py",
            "command": [sys.executable, "src/watcher/social_watcher.py", "--watch"],
            "icon": "globe",
            "color": "cyan",
            "description": "Monitors all social media platforms",
        },
        "twitter": {
            "name": "Twitter Watcher",
            "script": "mcp/twitter-server/src/index.js",
            "command": ["node", "mcp/twitter-server/src/index.js"],
            "icon": "twitter",
            "color": "sky-blue",
            "description": "Monitors Twitter mentions and replies",
        },
        "facebook": {
            "name": "Facebook Watcher",
            "script": "mcp/facebook-server/src/index.js",
            "command": ["node", "mcp/facebook-server/src/index.js"],
            "icon": "facebook",
            "color": "blue",
            "description": "Monitors Facebook page interactions",
        },
        "instagram": {
            "name": "Instagram Watcher",
            "script": "mcp/instagram-server/src/index.js",
            "command": ["node", "mcp/instagram-server/src/index.js"],
            "icon": "instagram",
            "color": "pink",
            "description": "Monitors Instagram DMs and comments",
        },
        "bank": {
            "name": "Bank Watcher",
            "script": "src/watcher/bank_watcher.py",
            "command": [sys.executable, "src/watcher/bank_watcher.py", "--watch"],
            "icon": "dollar-sign",
            "color": "green",
            "description": "Monitors bank transactions via Plaid/TrueLayer",
        },
        "vault": {
            "name": "Vault Watcher",
            "script": "src/watcher/vault_watcher.py",
            "command": [sys.executable, "src/watcher/vault_watcher.py", "--watch"],
            "icon": "folder",
            "color": "orange",
            "description": "Monitors vault file changes",
        },
        "webhook": {
            "name": "Webhook Receiver",
            "script": "src/watcher/webhook_watcher.py",
            "command": [sys.executable, "src/watcher/webhook_watcher.py", "--watch"],
            "icon": "webhook",
            "color": "yellow",
            "description": "Receives and processes webhooks",
        },
        "gmail-pubsub": {
            "name": " Gmail PubSub",
            "script": "src/watcher/gmail_pubsub_watcher.py",
            "command": [sys.executable, "src/watcher/gmail_pubsub_watcher.py", "--watch"],
            "icon": "mail",
            "color": "red",
            "description": "Gmail PubSub real-time notifications",
        },
        "vault-rag": {
            "name": "Vault RAG Watcher",
            "script": "src/watcher/vault_rag_watcher.py",
            "command": [sys.executable, "src/watcher/vault_rag_watcher.py", "--watch"],
            "icon": "brain",
            "color": "violet",
            "description": "Processes vault content for RAG",
        },
        "ceo-briefing-weekly": {
            "name": "CEO Weekly Briefing",
            "script": "monday_ceo_briefing.py",
            "command": [sys.executable, "monday_ceo_briefing.py"],
            "icon": "briefcase",
            "color": "indigo",
            "description": "Generates weekly CEO briefing",
        },
        # MCP Servers
        "mcp-odoo": {
            "name": "MCP Odoo Server",
            "script": "mcp/odoo-server/src/index.js",
            "command": ["node", "mcp/odoo-server/src/index.js"],
            "icon": "server",
            "color": "orange",
            "description": "MCP server for Odoo integration",
        },
        "mcp-email": {
            "name": "MCP Email Server",
            "script": "mcp/email-server/src/index.js",
            "command": ["node", "mcp/email-server/src/index.js"],
            "icon": "server",
            "color": "red",
            "description": "MCP server for email operations",
        },
        "mcp-whatsapp": {
            "name": "MCP WhatsApp Server",
            "script": "mcp/whatsapp-server/src/index.js",
            "command": ["node", "mcp/whatsapp-server/src/index.js"],
            "icon": "server",
            "color": "green",
            "description": "MCP server for WhatsApp",
        },
        "mcp-linkedin": {
            "name": "MCP LinkedIn Server",
            "script": "mcp/linkedin-server/src/index.js",
            "command": ["node", "mcp/linkedin-server/src/index.js"],
            "icon": "server",
            "color": "blue",
            "description": "MCP server for LinkedIn",
        },
        "mcp-twitter": {
            "name": "MCP Twitter Server",
            "script": "mcp/twitter-server/src/index.js",
            "command": ["node", "mcp/twitter-server/src/index.js"],
            "icon": "server",
            "color": "sky-blue",
            "description": "MCP server for Twitter",
        },
        "mcp-watcher": {
            "name": "MCP Watcher Server",
            "script": "mcp/watcher-server/src/index.js",
            "command": ["node", "mcp/watcher-server/src/index.js"],
            "icon": "server",
            "color": "gray",
            "description": "MCP server for watcher control",
        },
    }
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.watcher_data: Dict[str, WatcherProcess] = {}
        self.lock = threading.Lock()
        self._load_state()
        self._sync_with_existing_processes()
    
    def _load_state(self):
        """Load watcher state from file."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                    for watcher_id, data in state.items():
                        self.watcher_data[watcher_id] = WatcherProcess(**data)
                logger.info(f"Loaded state for {len(self.watcher_data)} watchers")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save watcher state to file."""
        try:
            state = {}
            for watcher_id, data in self.watcher_data.items():
                # Convert to dict, excluding None fields
                state[watcher_id] = asdict(data)
            
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _sync_with_existing_processes(self):
        """Sync state with any existing running processes."""
        for watcher_id in self.WATCHER_REGISTRY:
            if watcher_id not in self.watcher_data:
                registry_entry = self.WATCHER_REGISTRY[watcher_id]
                self.watcher_data[watcher_id] = WatcherProcess(
                    id=watcher_id,
                    name=registry_entry["name"],
                    script=registry_entry["script"],
                    command=registry_entry["command"],
                    status="stopped",
                )
        
        self._save_state()
    
    def _check_process_status(self, watcher_id: str) -> str:
        """Check if a process is still running."""
        if watcher_id not in self.processes:
            return "stopped"
        
        process = self.processes[watcher_id]
        if process.poll() is None:
            return "running"
        else:
            return "error"
    
    def _get_script_path(self, script: str) -> Path:
        """Get full path to script."""
        if Path(script).is_absolute():
            return Path(script)
        return ROOT / script
    
    def _script_exists(self, watcher_id: str) -> bool:
        """Check if watcher script exists."""
        registry_entry = self.WATCHER_REGISTRY.get(watcher_id)
        if not registry_entry:
            return False
        
        script_path = self._get_script_path(registry_entry["script"])
        return script_path.exists()
    
    def _read_last_log(self, watcher_id: str) -> Optional[str]:
        """Read the last log entry for a watcher."""
        log_file = LOGS_DIR / f"{watcher_id}.json"
        if not log_file.exists():
            return None
        
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    return last_entry.get("details", {}).get("message", last_entry.get("action", "Unknown"))
        except Exception:
            pass
        return None
    
    def _count_logs_today(self, watcher_id: str) -> int:
        """Count log entries for today."""
        log_file = LOGS_DIR / f"{watcher_id}.json"
        if not log_file.exists():
            return 0
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        count = 0
        
        try:
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("timestamp", "").startswith(today):
                            count += 1
                    except:
                        continue
        except Exception:
            pass
        
        return count
    
    def _get_process_stats(self, pid: int) -> tuple[float, float]:
        """Get CPU and memory usage for a process."""
        try:
            import psutil
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.1)
            memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            return cpu, memory
        except ImportError:
            # psutil not available, return estimates
            logger.debug("psutil not available, CPU/RAM metrics unavailable")
            return 0.0, 0.0
        except Exception as e:
            logger.debug(f"Failed to get process stats: {e}")
            return 0.0, 0.0
    
    def start_watcher(self, watcher_id: str) -> Dict[str, Any]:
        """Start a watcher process."""
        with self.lock:
            if watcher_id not in self.WATCHER_REGISTRY:
                return {"success": False, "error": f"Unknown watcher: {watcher_id}"}
            
            if not self._script_exists(watcher_id):
                return {"success": False, "error": f"Script not found for watcher: {watcher_id}"}
            
            # Check if already running
            if self._check_process_status(watcher_id) == "running":
                return {"success": False, "error": f"Watcher {watcher_id} is already running"}
            
            registry_entry = self.WATCHER_REGISTRY[watcher_id]
            script_path = self._get_script_path(registry_entry["script"])
            
            try:
                # Start the process
                process = subprocess.Popen(
                    registry_entry["command"],
                    cwd=str(ROOT),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,  # Create new process group
                )
                
                self.processes[watcher_id] = process
                
                # Update watcher data
                watcher = self.watcher_data[watcher_id]
                watcher.status = "running"
                watcher.pid = process.pid
                watcher.started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                watcher.error_message = None
                watcher.restart_count += 1
                
                self._save_state()
                
                logger.info(f"Started watcher {watcher_id} (PID: {process.pid})")
                
                return {
                    "success": True,
                    "watcher_id": watcher_id,
                    "pid": process.pid,
                    "message": f"Started {registry_entry['name']}",
                }
                
            except Exception as e:
                logger.error(f"Failed to start watcher {watcher_id}: {e}")
                
                watcher = self.watcher_data[watcher_id]
                watcher.status = "error"
                watcher.error_message = str(e)
                self._save_state()
                
                return {"success": False, "error": str(e)}
    
    def stop_watcher(self, watcher_id: str) -> Dict[str, Any]:
        """Stop a watcher process."""
        with self.lock:
            if watcher_id not in self.processes:
                return {"success": False, "error": f"Watcher {watcher_id} not running"}
            
            process = self.processes[watcher_id]
            
            try:
                # Try graceful termination first
                process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if not terminated
                    process.kill()
                    process.wait(timeout=2)
                
                # Update watcher data
                watcher = self.watcher_data[watcher_id]
                watcher.status = "stopped"
                watcher.pid = None
                watcher.started_at = None
                
                # Remove from processes dict
                del self.processes[watcher_id]
                
                self._save_state()
                
                logger.info(f"Stopped watcher {watcher_id}")
                
                return {
                    "success": True,
                    "watcher_id": watcher_id,
                    "message": f"Stopped {watcher['name']}",
                }
                
            except Exception as e:
                logger.error(f"Failed to stop watcher {watcher_id}: {e}")
                return {"success": False, "error": str(e)}
    
    def restart_watcher(self, watcher_id: str) -> Dict[str, Any]:
        """Restart a watcher process."""
        # Stop first (ignore errors if not running)
        self.stop_watcher(watcher_id)
        
        # Small delay to ensure clean restart
        import time
        time.sleep(1)
        
        # Start again
        return self.start_watcher(watcher_id)
    
    def get_watcher_status(self, watcher_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific watcher."""
        if watcher_id not in self.watcher_data:
            return None
        
        watcher = self.watcher_data[watcher_id]
        registry_entry = self.WATCHER_REGISTRY.get(watcher_id, {})
        
        # Update runtime stats
        if watcher.pid and watcher.status == "running":
            cpu, memory = self._get_process_stats(watcher.pid)
            watcher.cpu_percent = cpu
            watcher.memory_mb = memory
            
            if watcher.started_at:
                try:
                    started = datetime.fromisoformat(watcher.started_at.replace("Z", "+00:00"))
                    watcher.uptime_seconds = int((datetime.now(timezone.utc) - started).total_seconds())
                except:
                    pass
        
        # Get last log
        if not watcher.last_log or watcher.status == "running":
            watcher.last_log = self._read_last_log(watcher_id)
            watcher.logs_today = self._count_logs_today(watcher_id)
        
        return {
            "id": watcher.id,
            "name": watcher.name,
            "script": watcher.script,
            "status": self._check_process_status(watcher_id) if watcher.status == "running" else watcher.status,
            "pid": watcher.pid,
            "cpu_percent": round(watcher.cpu_percent, 1),
            "memory_mb": round(watcher.memory_mb, 1),
            "restart_count": watcher.restart_count,
            "uptime_seconds": watcher.uptime_seconds,
            "last_log": watcher.last_log,
            "logs_today": watcher.logs_today,
            "items_processed": watcher.items_processed,
            "icon": registry_entry.get("icon", "eye"),
            "color": registry_entry.get("color", "gray"),
            "description": registry_entry.get("description", ""),
        }
    
    def list_watchers(self) -> List[Dict[str, Any]]:
        """List all watchers with their status."""
        watchers = []
        
        for watcher_id in self.WATCHER_REGISTRY:
            status = self.get_watcher_status(watcher_id)
            if status:
                watchers.append(status)
        
        return watchers
    
    def start_all_watchers(self) -> Dict[str, Any]:
        """Start all available watchers."""
        results = {"started": [], "failed": [], "skipped": []}
        
        for watcher_id in self.WATCHER_REGISTRY:
            if not self._script_exists(watcher_id):
                results["skipped"].append({
                    "watcher_id": watcher_id,
                    "reason": "Script not found",
                })
                continue
            
            result = self.start_watcher(watcher_id)
            if result["success"]:
                results["started"].append(watcher_id)
            else:
                results["failed"].append({
                    "watcher_id": watcher_id,
                    "error": result.get("error", "Unknown error"),
                })
        
        return results
    
    def stop_all_watchers(self) -> Dict[str, Any]:
        """Stop all running watchers."""
        results = {"stopped": [], "failed": []}
        
        for watcher_id in list(self.processes.keys()):
            result = self.stop_watcher(watcher_id)
            if result["success"]:
                results["stopped"].append(watcher_id)
            else:
                results["failed"].append({
                    "watcher_id": watcher_id,
                    "error": result.get("error", "Unknown error"),
                })
        
        return results
    
    def get_watcher_logs(self, watcher_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs for a watcher."""
        log_file = LOGS_DIR / f"{watcher_id}.json"
        if not log_file.exists():
            return []
        
        logs = []
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        entry = json.loads(line)
                        logs.append({
                            "time": entry.get("timestamp", "").split("T")[1].replace("Z", "") if "T" in entry.get("timestamp", "") else entry.get("timestamp", ""),
                            "message": entry.get("action", "") + ": " + json.dumps(entry.get("details", {})),
                            "status": entry.get("status", "unknown"),
                        })
                    except:
                        continue
        except Exception as e:
            logger.error(f"Failed to read logs for {watcher_id}: {e}")
        
        return logs
    
    def get_service_summary(self) -> Dict[str, Any]:
        """Get summary of all services."""
        watchers = self.list_watchers()
        
        total = len(watchers)
        running = sum(1 for w in watchers if w["status"] == "running")
        stopped = sum(1 for w in watchers if w["status"] == "stopped")
        error = sum(1 for w in watchers if w["status"] == "error")
        
        total_logs = sum(w["logs_today"] for w in watchers)
        total_processed = sum(w["items_processed"] for w in watchers)
        
        return {
            "total": total,
            "running": running,
            "stopped": stopped,
            "error": error,
            "total_logs": total_logs,
            "total_processed": total_processed,
            "health": "healthy" if error == 0 else "degraded",
        }


# Global singleton instance
watcher_service = WatcherService()


def get_watcher_service() -> WatcherService:
    """Get the global watcher service instance."""
    return watcher_service
