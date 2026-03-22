import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

class VaultOrchestrator:
    """
    Gold Tier Vault Orchestrator.
    Implements real AI-driven task orchestration and state transitions.
    """

    def __init__(self, vault_path: Optional[Path] = None):
        self.root = Path(__file__).resolve().parent.parent.parent
        self.vault_path = vault_path or Path(os.getenv("VAULT_PATH", self.root / "AI-Employee-Vault")).resolve()
        
        # AGENT_ROLE: cloud (triage/planning) or local (execution)
        self.agent_role = os.getenv("AGENT_ROLE", "cloud").lower()
        self.agent_cmd = os.getenv("AGENT_CMD", "claude").lower()
        
        # Folder structure
        self.folders = {
            "needs_action": self.vault_path / "Needs_Action",
            "plans": self.vault_path / "Plans",
            "in_progress": self.vault_path / "In_Progress",
            "pending_approval": self.vault_path / "Pending_Approval",
            "approved": self.vault_path / "Approved",
            "rejected": self.vault_path / "Rejected",
            "done": self.vault_path / "Done",
            "logs": self.vault_path / "Logs"
        }
        
        for folder in self.folders.values():
            folder.mkdir(parents=True, exist_ok=True)
            
        self.logger = logging.getLogger(f"vault_orch_{self.agent_role}")
        self._setup_logging()
        self.log_file = self.folders["logs"] / f"orchestrator-{self.agent_role}.json"

    def _setup_logging(self):
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=getattr(logging, log_level, logging.INFO),
                format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

    def log_action(self, action: str, details: Dict[str, Any], status: str = "success"):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": f"orch_{self.agent_role}",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _move_file(self, src_path: Path, dest_dir: Path) -> Path:
        dest_path = dest_dir / src_path.name
        if dest_path.exists():
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            dest_path = dest_dir / f"{src_path.stem}_{ts}{src_path.suffix}"
        
        shutil.move(str(src_path), str(dest_path))
        self.logger.info(f"Moved {src_path.name} -> {dest_dir.name}")
        return dest_path

    def run_agent(self, prompt: str) -> str:
        """Execute the AI agent CLI and capture output."""
        self.logger.info(f"Running AI agent ({self.agent_cmd})...")
        cmd = [self.agent_cmd]
        if "claude" in self.agent_cmd:
            cmd.append("-y")
        cmd.append(prompt)
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True
            )
            output, _ = process.communicate()
            return output
        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}")
            return f"ERROR: {str(e)}"

    def process_needs_action(self):
        """Cloud Role: Needs_Action -> Plans (Triage & Planning)."""
        if self.agent_role != "cloud":
            return

        # Look for subdirectories in Needs_Action
        for category_dir in self.folders["needs_action"].iterdir():
            if not category_dir.is_dir():
                continue
                
            for task_file in category_dir.glob("*.json"):
                self.logger.info(f"Processing new task: {task_file.name}")
                
                # Move to In_Progress (Claim)
                in_progress_path = self._move_file(task_file, self.folders["in_progress"])
                
                # AI Planning
                task_content = in_progress_path.read_text(encoding="utf-8")
                prompt = f"""TRIAGE AND PLAN:
Task File: {task_file.name}
Content:
{task_content}

GOAL: Create a structured JSON plan for this task.
The plan MUST include:
1. plan_id (unique string)
2. goal (brief summary)
3. steps (list of actions)
4. risk_level (low, medium, high)
5. action_type (send_email, publish_post, reply_whatsapp, etc.)
6. params (dictionary of parameters for the action)

Output ONLY the JSON plan in a code block.
"""
                output = self.run_agent(prompt)
                
                # Extract JSON from output
                try:
                    json_match = subprocess.check_output(["powershell", "-Command", f"$input | Select-String -Pattern '(?s)```json\\s*(.*?)\\s*```' | % {{ $_.Matches.Groups[1].Value }}"], input=output, text=True)
                    if not json_match.strip():
                        # Fallback: find any JSON-like structure
                        import re
                        match = re.search(r"(\{.*\})", output, re.DOTALL)
                        json_str = match.group(1) if match else "{}"
                    else:
                        json_str = json_match.strip()
                        
                    plan_data = json.loads(json_str)
                    plan_id = plan_data.get("plan_id", f"plan-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
                    
                    # Save plan to /Plans
                    plan_path = self.folders["plans"] / f"{plan_id}.json"
                    with open(plan_path, "w", encoding="utf-8") as f:
                        json.dump(plan_data, f, indent=2)
                    
                    self.logger.info(f"Created plan: {plan_id}")
                    self.log_action("create_plan", {"plan_id": plan_id, "task": task_file.name})
                    
                    # Move plan to Pending_Approval
                    self._move_file(plan_path, self.folders["pending_approval"])
                    
                    # Move original task to Done
                    self._move_file(in_progress_path, self.folders["done"])
                    
                except Exception as e:
                    self.logger.error(f"Failed to parse AI plan: {e}")
                    self.log_action("plan_failed", {"task": task_file.name, "error": str(e)}, status="error")
                    # Move back to needs_action or error folder?
                    self._move_file(in_progress_path, self.folders["rejected"])

    def process_approved(self):
        """Local Role: Approved -> In_Progress -> Execution."""
        if self.agent_role != "local":
            return

        for plan_file in self.folders["approved"].glob("*.json"):
            self.logger.info(f"Executing approved plan: {plan_file.name}")
            
            # Move to In_Progress (Claim)
            execution_path = self._move_file(plan_file, self.folders["in_progress"])
            
            # Real execution would happen via ApprovalOrchestrator or directly here via MCP
            # For Gold Tier, we might want the AI to execute the steps one-by-one
            self.execute_plan_with_ai(execution_path)

    def execute_plan_with_ai(self, plan_path: Path):
        """Execute a plan using the local AI agent."""
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        
        prompt = f"""EXECUTE PLAN:
Plan: {json.dumps(plan_data, indent=2)}

GOAL: Execute the steps in this plan using your available MCP tools.
1. Perform each step carefully.
2. If an error occurs, try to recover or provide a detailed log.
3. When finished, confirm completion.
"""
        output = self.run_agent(prompt)
        
        if "ERROR" not in output:
            self._move_file(plan_path, self.folders["done"])
            self.log_action("execution_complete", {"plan": plan_path.name})
        else:
            self.logger.error(f"Execution failed: {output}")
            self._move_file(plan_path, self.folders["rejected"])
            self.log_action("execution_failed", {"plan": plan_path.name, "output": output}, status="error")

    def run_cycle(self):
        self.logger.info(f"Starting cycle as {self.agent_role}...")
        if self.agent_role == "cloud":
            self.process_needs_action()
        elif self.agent_role == "local":
            self.process_approved()
        self.logger.info("Cycle complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=["cloud", "local"], default=os.getenv("AGENT_ROLE", "cloud"))
    args = parser.parse_args()
    
    os.environ["AGENT_ROLE"] = args.role
    orch = VaultOrchestrator()
    while True:
        orch.run_cycle()
        time.sleep(30)
