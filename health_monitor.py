import os
import time
import json
import logging
import psutil
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HealthMonitor")

class HealthMonitor:
    def __init__(self, vault_path="AI-Employee-Vault"):
        self.vault_path = Path(vault_path)
        self.health_report_path = self.vault_path / "System_Health" / "health_report.md"
        self.in_progress_dir = self.vault_path / "In_Progress"
        self.agents = ["Cloud_Agent", "Local_Agent"]

    def check_heartbeats(self):
        heartbeats = {}
        for agent in self.agents:
            heartbeat_file = self.in_progress_dir / agent / "heartbeat.json"
            if heartbeat_file.exists():
                try:
                    with open(heartbeat_file, 'r') as f:
                        data = json.load(f)
                        last_ts = data.get("timestamp", 0)
                        diff = time.time() - last_ts
                        if diff < 120: # 2 minutes
                            status = "🟢 Healthy"
                        else:
                            status = f"🔴 Stale ({int(diff)}s ago)"
                except Exception as e:
                    status = f"🟠 Error: {e}"
            else:
                status = "⚪ Missing"
            heartbeats[agent] = status
        return heartbeats

    def get_system_stats(self):
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": f"{cpu}%",
            "mem": f"{mem.percent}% ({mem.used // (1024*1024)}MB / {mem.total // (1024*1024)}MB)",
            "disk": f"{disk.percent}%"
        }

    def generate_report(self):
        stats = self.get_system_stats()
        heartbeats = self.check_heartbeats()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# AI Employee Health Report - {timestamp}

## 🖥️ System Performance
| Metric | Value |
|---|---|
| CPU Usage | {stats['cpu']} |
| Memory Usage | {stats['mem']} |
| Disk Usage | {stats['disk']} |

## 🤖 Agent Heartbeats
| Agent | Status |
|---|---|
"""
        for agent, status in heartbeats.items():
            report += f"| {agent} | {status} |\n"
            
        report += "\n## 🛡️ Service Status (Active Watchdog Required)\n"
        report += "Check `AI-Employee-Vault/Alerts/` for detailed crash logs.\n"
        
        report += f"\n\n*Last Scan: {timestamp}*"
        
        with open(self.health_report_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        logger.info(f"Health report updated at {self.health_report_path}")

if __name__ == "__main__":
    monitor = HealthMonitor()
    # monitor.generate_report()
    # try:
    #     while True:
    #         monitor.generate_report()
    #         time.sleep(60)
    # except KeyboardInterrupt:
    #     print("Stopped.")
    print("Health Monitor initialized. Use generate_report() to update the report.")
