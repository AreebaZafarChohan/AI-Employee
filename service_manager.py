import os
import subprocess
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ServiceManager")

class ServiceManager:
    def __init__(self, vault_path="AI-Employee-Vault"):
        self.vault_path = Path(vault_path)
        self.log_dir = self.vault_path / "Service_Logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.processes = {}

    def start_service(self, name, command, cwd=None):
        """Starts a service and keeps track of its process."""
        if name in self.processes and self.processes[name].poll() is None:
            logger.warning(f"Service {name} is already running.")
            return False

        log_file = self.log_dir / f"{name}.log"
        logger.info(f"Starting service: {name} (Log: {log_file})")
        
        with open(log_file, "a") as f:
            proc = subprocess.Popen(
                command,
                stdout=f,
                stderr=subprocess.STDOUT,
                shell=True,
                cwd=cwd,
                text=True
            )
            self.processes[name] = {
                "process": proc,
                "command": command,
                "cwd": cwd,
                "start_time": time.time()
            }
        return True

    def stop_service(self, name):
        """Stops a running service."""
        if name in self.processes:
            proc_info = self.processes[name]
            proc = proc_info["process"]
            if proc.poll() is None:
                logger.info(f"Stopping service: {name}")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            del self.processes[name]
            return True
        return False

    def is_running(self, name):
        """Checks if a service is currently running."""
        if name in self.processes:
            return self.processes[name]["process"].poll() is None
        return False

    def restart_service(self, name):
        """Restarts a service."""
        logger.info(f"Restarting service: {name}")
        info = self.processes.get(name)
        if info:
            cmd = info["command"]
            cwd = info["cwd"]
            self.stop_service(name)
            self.start_service(name, cmd, cwd)

if __name__ == "__main__":
    # Example usage
    sm = ServiceManager()
    # sm.start_service("Local_Agent", "python src/agent_coordinator.py Local_Agent")
    # time.sleep(2)
    # print(f"Is running: {sm.is_running('Local_Agent')}")
    # sm.stop_service("Local_Agent")
