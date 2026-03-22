import os
import time
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables (ensure GEMINI_API_KEY is in .env)
load_dotenv()

class AgentCoordinator:
    def __init__(self, vault_path, agent_id):
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.heartbeat_file = self.vault_path / "In_Progress" / self.agent_id / "heartbeat.json"
        
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables.")
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Ensure agent directory exists
        (self.vault_path / "In_Progress" / self.agent_id).mkdir(parents=True, exist_ok=True)

    def heartbeat(self):
        """Update the agent's heartbeat file."""
        data = {
            "agent_id": self.agent_id,
            "timestamp": time.time(),
            "status": "active",
            "last_check": datetime.now().isoformat()
        }
        with open(self.heartbeat_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Heartbeat updated for {self.agent_id}")

    def scan_for_tasks(self, domain):
        """Scan for tasks in the specified domain."""
        domain_path = self.vault_path / "Needs_Action" / domain
        if not domain_path.exists():
            return []
        return list(domain_path.glob("*.md"))

    def claim_task(self, task_file):
        """Atomic claim by moving the file."""
        task_path = Path(task_file)
        if not task_path.exists():
            return None

        target_path = self.vault_path / "In_Progress" / self.agent_id / task_path.name
        try:
            shutil.move(str(task_path), str(target_path))
            logger.info(f"[{self.agent_id}] Claimed: {task_path.name}")
            self._log_action("claimed", task_path.name)
            return target_path
        except Exception as e:
            logger.error(f"Claim failed for {task_path.name}: {e}")
            return None

    def process_with_gemini(self, task_path):
        """Process the task content using Gemini API."""
        try:
            with open(task_path, 'r', encoding='utf-8') as f:
                content = f.read()

            prompt = f"You are an AI Employee ({self.agent_id}). Process the following task and provide a final result or response:\n\n{content}"
            
            logger.info(f"[{self.agent_id}] Calling Gemini API...")
            response = self.model.generate_content(prompt)
            
            result_text = response.text
            return True, result_text
        except Exception as e:
            logger.error(f"Gemini processing error: {e}")
            return False, str(e)

    def complete_task(self, task_file, success=True, summary=""):
        """Move task to final destination."""
        task_path = Path(task_file)
        target_folder = self.vault_path / ("Done" if success else "Errors")
        target_folder.mkdir(parents=True, exist_ok=True)
        target_path = target_folder / task_path.name
        
        try:
            shutil.move(str(task_path), str(target_path))
            
            with open(target_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n--- AI Employee Log ---\n")
                f.write(f"Agent: {self.agent_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Outcome: {'SUCCESS' if success else 'FAILURE'}\n")
                f.write(f"Summary: {summary}\n")
            
            self._log_action("completed" if success else "failed", task_path.name)
            logger.info(f"[{self.agent_id}] Task finalized: {task_path.name}")
        except Exception as e:
            logger.error(f"Error finalizing task: {e}")

    def _log_action(self, action, filename):
        log_file = self.vault_path / "Logs" / "coordination_log.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        entry = f"| {datetime.now().isoformat()} | {self.agent_id} | {action} | {filename} |\n"
        with open(log_file, 'a', encoding='utf-8') as f:
            if log_file.stat().st_size == 0:
                f.write("| Timestamp | Agent | Action | File |\n|---|---|---|---|\n")
            f.write(entry)

    def run_cycle(self, domains):
        """Single loop cycle: heartbeat -> scan -> claim -> process -> complete."""
        self.heartbeat()
        for domain in domains:
            tasks = self.scan_for_tasks(domain)
            for task in tasks:
                claimed = self.claim_task(task)
                if claimed:
                    success, result = self.process_with_gemini(claimed)
                    self.complete_task(claimed, success=success, summary=result)

if __name__ == "__main__":
    # Example to start as a persistent worker
    import sys
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "Local_Agent"
    
    coordinator = AgentCoordinator("AI-Employee-Vault", agent_name)
    active_domains = ["email", "social", "tasks", "accounting", "marketing"]
    
    logger.info(f"Starting {agent_name} worker...")
    try:
        while True:
            coordinator.run_cycle(active_domains)
            time.sleep(10) # Wait before next scan
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
