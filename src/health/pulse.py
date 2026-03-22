import os
import json
import time
import argparse
from datetime import datetime

class PulseMonitor:
    def __init__(self, vault_path, role):
        self.vault_path = vault_path
        self.role = role
        self.pulse_dir = os.path.join(vault_path, "Logs", "Heartbeats")
        os.makedirs(self.pulse_dir, exist_ok=True)
        self.pulse_file = os.path.join(self.pulse_dir, f"{role}.json")

    def beat(self):
        """Write current timestamp to signal 'alive' status."""
        data = {
            "last_seen": datetime.now().isoformat(),
            "role": self.role,
            "status": "online"
        }
        with open(self.pulse_file, "w") as f:
            json.dump(data, f)
        print(f"[Pulse] {self.role} is beating at {data['last_seen']}")

    def check_partner(self):
        """Check if the other role is online (seen in last 5 minutes)."""
        partner = "local" if self.role == "cloud" else "cloud"
        partner_file = os.path.join(self.pulse_dir, f"{partner}.json")
        
        if not os.path.exists(partner_file):
            return False, "never_seen"
            
        try:
            with open(partner_file, "r") as f:
                data = json.load(f)
                last_seen = datetime.fromisoformat(data["last_seen"])
                diff = (datetime.now() - last_seen).total_seconds()
                if diff < 300: # 5 minutes
                    return True, "online"
                else:
                    return False, f"offline_for_{int(diff)}s"
        except Exception as e:
            return False, str(e)

    def run(self):
        while True:
            self.beat()
            online, status = self.check_partner()
            if not online:
                print(f"[Pulse] WARNING: Partner role is {status}")
            time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True, choices=["cloud", "local"])
    parser.add_argument("--vault", default="./AI-Employee-Vault")
    args = parser.parse_args()
    
    monitor = PulseMonitor(args.vault, args.role)
    monitor.run()
