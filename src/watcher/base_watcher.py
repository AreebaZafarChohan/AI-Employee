import json
import logging
import os
import shutil
import time
import sys
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

class BaseWatcher(ABC):
    """
    Base class for all Watcher agents.
    Provides common functionality for logging, vault interaction, and error handling.
    """

    def __init__(self, agent_name: str, vault_path: Optional[Path] = None):
        self.agent_name = agent_name
        self.root = Path(__file__).resolve().parent.parent.parent
        self.vault_path = vault_path or Path(os.getenv("VAULT_PATH", self.root / "AI-Employee-Vault")).resolve()
        
        # Configuration
        self.poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
        self.dry_run = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
        
        # Paths
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.log_file = self.logs_dir / f"{self.agent_name}.json"
        
        # Ensure directories exist
        for d in [self.needs_action_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        # Logging setup
        self.logger = logging.getLogger(self.agent_name)
        self._setup_logging()

    def _setup_logging(self):
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=getattr(logging, log_level, logging.INFO),
                format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

    def log_event(self, action: str, details: Optional[Dict[str, Any]] = None, status: str = "success"):
        """Log significant action to the agent's log file."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": self.agent_name,
            "action": action,
            "status": status,
            "details": details or {}
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")

    def notify_backend(self, filename: str, metadata: Optional[Dict[str, Any]] = None):
        """Notify the backend API of a new event."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would notify backend: {filename}")
            return

        url = f"{self.backend_url}/events/new"
        payload = {
            "source": self.agent_name,
            "file": filename,
            "metadata": metadata or {}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Backend notified: {filename}")
            else:
                self.logger.warning(f"Backend notification failed ({response.status_code}): {response.text}")
        except Exception as e:
            self.logger.error(f"Failed to notify backend: {e}")

    def write_to_needs_action(self, category: str, filename: str, content: Dict[str, Any]) -> Optional[Path]:
        """Write a new task to Needs_Action/<category>/."""
        category_dir = self.needs_action_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Slugify filename
        filename = filename.replace(" ", "-").replace("/", "-")
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest_path = category_dir / f"{ts}-{filename}.json"
        
        # Metadata
        if "metadata" not in content:
            content["metadata"] = {}
        
        content["metadata"].update({
            "source": self.agent_name,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "pending"
        })
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write task: {dest_path.name}")
            return dest_path

        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
            
            self.logger.info(f"Created task: {dest_path.name}")
            self.log_event("create_task", {"file": str(dest_path), "category": category})
            
            # Auto-notify backend
            self.notify_backend(dest_path.name, content.get("metadata"))
            
            return dest_path
        except Exception as e:
            self.logger.error(f"Failed to write task file: {e}")
            self.log_event("create_task", {"error": str(e)}, status="error")
            return None

    @abstractmethod
    def poll(self) -> Dict[str, Any]:
        """Perform one poll cycle. Return summary dict."""
        pass

    def run(self, watch: bool = False):
        """Run the watcher."""
        self.logger.info(f"Starting {self.agent_name} (dry_run={self.dry_run}, watch={watch})...")
        self.log_event("start", {"watch": watch})
        
        try:
            if watch:
                while True:
                    summary = self.poll()
                    self.logger.info(f"Poll complete: {summary}")
                    time.sleep(self.poll_interval)
            else:
                summary = self.poll()
                self.logger.info(f"Poll complete: {summary}")
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            self.logger.critical(f"Watcher crashed: {e}", exc_info=True)
            self.log_event("crash", {"error": str(e)}, status="error")
            sys.exit(1)

    def stop(self):
        """Cleanup logic."""
        self.logger.info(f"Stopping {self.agent_name}...")
        self.log_event("stop")
