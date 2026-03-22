import time
import logging
from pathlib import Path
from datetime import datetime
from service_manager import ServiceManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
logger = logging.getLogger("Watchdog")

class AIEmployeeWatchdog:
    def __init__(self, vault_path="AI-Employee-Vault"):
        self.vault_path = Path(vault_path)
        self.sm = ServiceManager(vault_path)
        self.alerts_dir = self.vault_path / "Alerts"
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # Define services to monitor
        self.services_config = {
            "Orchestrator": {"cmd": "python run_processor.py", "enabled": True},
            "Watchers": {"cmd": "python run_all_watchers.py", "enabled": True},
            "Cloud_Agent": {"cmd": "python src/agent_coordinator.py Cloud_Agent", "enabled": True},
            "Local_Agent": {"cmd": "python src/agent_coordinator.py Local_Agent", "enabled": True},
            # "Odoo_MCP": {"cmd": "node mcp/odoo-server/src/index.js", "cwd": "mcp/odoo-server", "enabled": False} # Set to false if not needed
        }

    def log_alert(self, service_name, status, message):
        alert_file = self.alerts_dir / f"Alerts_{datetime.now().strftime('%Y-%m-%d')}.md"
        timestamp = datetime.now().isoformat()
        
        with open(alert_file, "a") as f:
            if alert_file.stat().st_size == 0:
                f.write("| Timestamp | Service | Status | Message |\n|---|---|---|---|\n")
            f.write(f"| {timestamp} | {service_name} | {status} | {message} |\n")
        logger.warning(f"ALERT: {service_name} - {status} - {message}")

    def start_all_services(self):
        logger.info("Initializing all core services...")
        self.log_alert("SYSTEM", "STARTUP", "Watchdog starting all services.")
        for name, config in self.services_config.items():
            if config.get("enabled", True):
                self.sm.start_service(name, config["cmd"], config.get("cwd"))

    def monitor_loop(self):
        logger.info("Watchdog monitor loop started.")
        try:
            while True:
                for name, config in self.services_config.items():
                    if config.get("enabled", True):
                        if not self.sm.is_running(name):
                            message = f"Service {name} crashed. Restarting..."
                            self.log_alert(name, "CRASHED", message)
                            self.sm.start_service(name, config["cmd"], config.get("cwd"))
                        else:
                            # logger.debug(f"Service {name} is healthy.")
                            pass
                time.sleep(10) # Check every 10 seconds
        except KeyboardInterrupt:
            logger.info("Stopping all services due to Watchdog shutdown.")
            for name in self.services_config.keys():
                self.sm.stop_service(name)
            logger.info("Shutdown complete.")

if __name__ == "__main__":
    watchdog = AIEmployeeWatchdog()
    watchdog.start_all_services()
    watchdog.monitor_loop()
