#!/usr/bin/env python3
"""
Ralph Loop: Autonomous Reasoning Loop for AI Employee

This script implements a persistent reasoning loop that keeps the AI agent 
(Claude or Gemini CLI) working until tasks in the Vault are completed.

Features:
1. Automatic task selection from Needs_Action/
2. Iterative execution with state reinjection
3. Task completion detection (Strategy 1: Tag, Strategy 2: File move)
4. Max iteration safety limit
5. Continuous logging
6. Crash recovery
"""

import os
import sys
import json
import time
import subprocess
import argparse
import logging
import re
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()
NEEDS_ACTION = VAULT / "Needs_Action"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"
STATE_FILE = VAULT / ".ralph_loop_state.json"

DEFAULT_AGENT_COMMAND = "claude"
MAX_ITERATIONS = 10
LOOP_SLEEP = 5

# Logging Setup
LOGS.mkdir(parents=True, exist_ok=True)
log_file = LOGS / f"ralph_loop_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | RalphLoop | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RalphLoop")

# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------

class LoopState:
    def __init__(self):
        self.iteration = 0
        self.current_task = None
        self.status = "idle"
        self.start_time = None
        self.last_output = ""
        self.load()

    def load(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                self.iteration = data.get("iteration", 0)
                self.current_task = data.get("current_task")
                self.status = data.get("status", "idle")
                self.start_time = data.get("start_time")
                self.last_output = data.get("last_output", "")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")

    def save(self):
        try:
            data = {
                "iteration": self.iteration,
                "current_task": self.current_task,
                "status": self.status,
                "start_time": self.start_time,
                "last_output": self.last_output,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            STATE_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def reset(self):
        self.iteration = 0
        self.current_task = None
        self.status = "idle"
        self.start_time = None
        self.last_output = ""
        self.save()

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

class RalphLoop:
    def __init__(self, agent_cmd=DEFAULT_AGENT_COMMAND, max_iters=MAX_ITERATIONS):
        self.agent_cmd = agent_cmd
        self.max_iters = max_iters
        self.state = LoopState()
        
        # Ensure directories exist
        NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
        DONE.mkdir(parents=True, exist_ok=True)

    def find_task(self):
        """Find the next task in Needs_Action."""
        tasks = list(NEEDS_ACTION.glob("*.md"))
        if not tasks:
            return None
        # Sort by mtime to get the oldest/first task
        tasks.sort(key=lambda x: x.stat().st_mtime)
        return tasks[0]

    def is_task_done(self, task_path, output):
        """
        Check if task is complete.
        Strategy 1: Output contains <promise>TASK_COMPLETE</promise>
        Strategy 2: Task file moved to /Done
        """
        # Strategy 1
        if "<promise>TASK_COMPLETE</promise>" in output:
            logger.info("Completion Strategy 1: TAG detected.")
            return True
        
        # Strategy 2
        if not task_path.exists():
            done_path = DONE / task_path.name
            if done_path.exists():
                logger.info("Completion Strategy 2: File moved to /Done.")
                return True
        
        return False

    def run_agent(self, prompt):
        """Run the AI agent CLI and capture output."""
        logger.info(f"Iteration {self.state.iteration}: Executing agent...")
        
        # We use --yes for non-interactive mode if it's claude-code
        cmd = [self.agent_cmd]
        if "claude" in self.agent_cmd:
            cmd.append("-y")  # Use -y or --yes
        
        cmd.append(prompt)
        
        try:
            # Using subprocess.PIPE to capture output
            # Setting shell=True might be needed on Windows for npm-installed commands
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                bufsize=1,
                universal_newlines=True
            )
            
            full_output = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line, end="")
                    full_output.append(line)
            
            return "".join(full_output)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return f"ERROR: {str(e)}"

    def execute_loop(self):
        """Run the main autonomous reasoning loop."""
        logger.info("Starting Ralph Loop...")
        
        while True:
            task_path = self.find_task()
            
            if not task_path:
                if self.state.status != "idle":
                    logger.info("No more tasks. Entering idle state.")
                    self.state.reset()
                time.sleep(LOOP_SLEEP)
                continue

            task_name = task_path.name
            if self.state.current_task != task_name:
                logger.info(f"New task detected: {task_name}")
                self.state.reset()
                self.state.current_task = task_name
                self.state.start_time = datetime.now(timezone.utc).isoformat()
                self.state.status = "working"
            
            if self.state.iteration >= self.max_iters:
                logger.warning(f"Max iterations ({self.max_iters}) reached for task {task_name}. Skipping.")
                # Optionally move to a /Failed or /Review folder
                self.state.reset()
                time.sleep(LOOP_SLEEP)
                continue

            self.state.iteration += 1
            self.state.save()

            # Construct Prompt
            if self.state.iteration == 1:
                task_content = task_path.read_text()
                prompt = f"""AUTONOMOUS TASK EXECUTION:
Task File: {task_name}
Content:
{task_content}

GOAL: Complete this task fully. 
1. Reason about the steps required.
2. Execute the necessary actions (file edits, commands, etc.).
3. If you finish, move the task file to AI-Employee-Vault/Done or output <promise>TASK_COMPLETE</promise>.
4. If you need more turns, just provide your progress and I will reinject you.

STOP HOOK: Do not exit until the task is complete or you have provided a clear status update.
"""
            else:
                prompt = f"""CONTINUE TASK: {task_name}
Current Iteration: {self.state.iteration}/{self.max_iters}

Last Progress:
{self.state.last_output[-2000:] if self.state.last_output else "No previous output captured."}

The task is NOT yet complete. Please continue working until completion.
Remember to output <promise>TASK_COMPLETE</promise> or move the file to /Done when finished.
"""

            # Run Agent
            output = self.run_agent(prompt)
            self.state.last_output = output
            self.state.save()

            # Check Completion
            if self.is_task_done(task_path, output):
                logger.info(f"Task {task_name} COMPLETED successfully.")
                # Ensure it's moved if not already
                if task_path.exists():
                    shutil_move_to_done(task_path)
                
                self.state.reset()
                logger.info("Waiting for next task...")
            else:
                logger.info(f"Task {task_name} still in progress. Iteration {self.state.iteration} finished.")

            time.sleep(1)

def shutil_move_to_done(task_path):
    try:
        import shutil
        target = DONE / task_path.name
        shutil.move(str(task_path), str(target))
        logger.info(f"Moved {task_path.name} to {DONE}")
    except Exception as e:
        logger.error(f"Failed to move file: {e}")

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Ralph Loop Autonomous Orchestrator")
    parser.add_argument("--agent", default=DEFAULT_AGENT_COMMAND, help="Agent CLI command (claude, gemini, etc.)")
    parser.add_argument("--max-iters", type=int, default=MAX_ITERATIONS, help="Max iterations per task")
    parser.add_argument("--task", help="Run specific task file in Needs_Action/")
    
    args = parser.parse_args()
    
    loop = RalphLoop(agent_cmd=args.agent, max_iters=args.max_iters)
    
    try:
        loop.execute_loop()
    except KeyboardInterrupt:
        logger.info("Ralph Loop stopped by user.")
        loop.state.save()
    except Exception as e:
        logger.critical(f"Ralph Loop crashed: {e}", exc_info=True)
        # State is saved in LoopState on each iteration, so it can recover on restart

if __name__ == "__main__":
    main()
