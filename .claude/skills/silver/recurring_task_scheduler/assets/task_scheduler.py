#!/usr/bin/env python3
"""
Recurring Task Scheduler

A Python script that implements a recurring task scheduler with support for various
scheduling patterns, dependencies, and audit logging. This script reads task
definitions from a configuration file and executes them according to their schedules.
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    from croniter import croniter
except ImportError:
    print("Error: The 'croniter' library is required but not installed.")
    print("Install it with: pip install croniter")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TaskState:
    """Manages the state of scheduled tasks."""
    
    def __init__(self, state_file_path):
        self.state_file_path = Path(state_file_path)
        self.state_data = self.load_state()
        
    def load_state(self):
        """Load task state from file."""
        if self.state_file_path.exists():
            with open(self.state_file_path, 'r') as f:
                return json.load(f)
        else:
            # Initialize with empty state
            return {
                "tasks": {},
                "last_check_time": None
            }
    
    def save_state(self):
        """Save task state to file."""
        self.state_data["last_check_time"] = datetime.now().isoformat()
        with open(self.state_file_path, 'w') as f:
            json.dump(self.state_data, f, indent=2)
    
    def get_task_state(self, task_id):
        """Get the state for a specific task."""
        return self.state_data["tasks"].get(task_id, {
            "last_run_time": None,
            "last_completion_time": None,
            "consecutive_failures": 0,
            "executions": []
        })
    
    def update_task_state(self, task_id, completion_time=None, success=True, output=None):
        """Update the state for a specific task."""
        if task_id not in self.state_data["tasks"]:
            self.state_data["tasks"][task_id] = {
                "last_run_time": None,
                "last_completion_time": None,
                "consecutive_failures": 0,
                "executions": []
            }
        
        task_state = self.state_data["tasks"][task_id]
        run_time = datetime.now().isoformat()
        
        # Update consecutive failures counter
        if success:
            task_state["consecutive_failures"] = 0
        else:
            task_state["consecutive_failures"] += 1
            
        # Record execution
        execution_record = {
            "run_time": run_time,
            "completion_time": completion_time.isoformat() if completion_time else None,
            "success": success,
            "output": output
        }
        task_state["executions"].append(execution_record)
        
        # Limit execution history to last 100 entries
        if len(task_state["executions"]) > 100:
            task_state["executions"] = task_state["executions"][-100:]
            
        task_state["last_run_time"] = run_time
        if success:
            task_state["last_completion_time"] = completion_time.isoformat() if completion_time else None


class TaskScheduler:
    """Main class for the recurring task scheduler."""
    
    def __init__(self, config_path, state_file_path, audit_log_path):
        self.config_path = Path(config_path)
        self.state_manager = TaskState(state_file_path)
        self.audit_log_path = Path(audit_log_path)
        self.config = self.load_config()
        self.running = False
        self.task_threads = {}
        self.lock = threading.Lock()
        
        # Create directories if they don't exist
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_manager.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        
    def load_config(self):
        """Load the task configuration from file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def audit_log(self, event_type, task_id, message, details=None):
        """Log an event to the audit log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "task_id": task_id,
            "message": message
        }
        if details:
            log_entry["details"] = details
            
        with open(self.audit_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def should_run_task(self, task, now=None):
        """Check if a task should run based on its schedule."""
        if not task.get("enabled", True):
            return False
            
        if now is None:
            now = datetime.now()
        
        task_state = self.state_manager.get_task_state(task["id"])
        schedule = task["schedule"]
        
        if schedule["type"] == "cron":
            # Parse the cron expression and timezone
            cron_exp = schedule["expression"]
            tz_name = schedule.get("timezone", "UTC")
            
            # For simplicity, we'll assume UTC if timezone isn't handled properly
            # In a real implementation, you'd want to handle timezone conversion
            try:
                # Create a croniter object starting from the last run time or from the beginning of time
                last_run = task_state["last_run_time"]
                start_time = datetime.fromisoformat(last_run) if last_run else datetime.min
                
                # Get the next scheduled time
                cron_iter = croniter(cron_exp, start_time)
                next_run = cron_iter.get_next(datetime)
                
                # Check if the next run time is now or in the past
                if next_run <= now:
                    # Also check if this is a new scheduling cycle since the last run
                    # to avoid running multiple times in the same schedule window
                    if not last_run or next_run > datetime.fromisoformat(last_run):
                        return True
            except ValueError as e:
                logger.error(f"Invalid cron expression for task {task['id']}: {cron_exp}")
                return False
        
        elif schedule["type"] == "interval":
            # Calculate the interval in seconds
            unit = schedule["unit"]
            frequency = schedule["frequency"]
            
            if unit == "seconds":
                interval = timedelta(seconds=frequency)
            elif unit == "minutes":
                interval = timedelta(minutes=frequency)
            elif unit == "hours":
                interval = timedelta(hours=frequency)
            elif unit == "days":
                interval = timedelta(days=frequency)
            elif unit == "weeks":
                interval = timedelta(weeks=frequency)
            else:
                logger.error(f"Unsupported interval unit for task {task['id']}: {unit}")
                return False
            
            # Check if enough time has passed since the last run
            last_run_str = task_state["last_run_time"]
            if last_run_str:
                last_run = datetime.fromisoformat(last_run_str)
                if now >= last_run + interval:
                    return True
            else:
                # If never run before, run now
                return True
        
        elif schedule["type"] == "triggered":
            # Triggered tasks are run based on external triggers or dependencies
            # For now, we'll just return False since we're not implementing triggers
            return False
        
        else:
            logger.warning(f"Unknown schedule type for task {task['id']}: {schedule['type']}")
            return False
        
        return False
    
    def check_dependencies(self, task):
        """Check if task dependencies are satisfied."""
        dependencies = task.get("dependencies", [])
        
        for dep_id in dependencies:
            dep_state = self.state_manager.get_task_state(dep_id)
            last_completion = dep_state.get("last_completion_time")
            
            # For this implementation, we just check if the dependency has run successfully recently
            if not last_completion:
                logger.info(f"Dependency {dep_id} has never run for task {task['id']}")
                return False
            
            # Check if the dependency completed successfully in the last hour
            last_comp_time = datetime.fromisoformat(last_completion)
            if datetime.now() - last_comp_time > timedelta(hours=1):
                logger.info(f"Dependency {dep_id} hasn't run successfully in the last hour for task {task['id']}")
                return False
        
        return True
    
    def execute_task(self, task):
        """Execute a single task."""
        task_id = task["id"]
        
        # Acquire lock to prevent multiple threads from running the same task
        with self.lock:
            # Double-check if the task should still run (in case another thread just ran it)
            if not self.should_run_task(task):
                return False
                
            # Check dependencies
            if not self.check_dependencies(task):
                logger.info(f"Dependencies not satisfied for task {task_id}, skipping execution")
                return False
        
        logger.info(f"Starting execution of task: {task_id}")
        self.audit_log("task_started", task_id, f"Task started execution")
        
        start_time = datetime.now()
        output = ""
        success = True
        
        try:
            # Prepare command
            cmd = [task["command"]]
            if "arguments" in task:
                cmd.extend(task["arguments"])
                
            # Set up environment
            env = os.environ.copy()
            if "environment" in task:
                for key, value in task["environment"].items():
                    # Expand environment variables in the value
                    expanded_value = os.path.expandvars(value)
                    env[key] = expanded_value
            
            # Set working directory
            cwd = task.get("working_directory", os.getcwd())
            
            # Set timeout
            timeout = task.get("timeout_seconds", 3600)  # Default to 1 hour
            
            # Execute the command
            logger.debug(f"Executing command: {' '.join(cmd)} in directory: {cwd}")
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                timeout=timeout,
                capture_output=True,
                text=True
            )
            
            # Capture output
            output = result.stdout + result.stderr
            logger.debug(f"Task {task_id} output: {output[:500]}...")  # Limit log size
            
            # Check if the command succeeded
            if result.returncode != 0:
                logger.error(f"Task {task_id} failed with return code {result.returncode}")
                success = False
            else:
                logger.info(f"Task {task_id} completed successfully")
                
        except subprocess.TimeoutExpired:
            logger.error(f"Task {task_id} timed out after {timeout} seconds")
            success = False
            output = f"Task timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            success = False
            output = f"Error executing task: {str(e)}"
        
        # Update task state
        completion_time = datetime.now()
        self.state_manager.update_task_state(task_id, completion_time, success, output)
        
        # Log completion
        if success:
            self.audit_log("task_succeeded", task_id, f"Task completed successfully", {
                "execution_duration": (completion_time - start_time).total_seconds()
            })
        else:
            self.audit_log("task_failed", task_id, f"Task failed during execution", {
                "error_output": output,
                "execution_duration": (completion_time - start_time).total_seconds()
            })
        
        # Send notifications if configured
        self.send_notifications(task, success, output)
        
        return success
    
    def send_notifications(self, task, success, output):
        """Send notifications for task completion/failure."""
        notifications = task.get("notifications", {})
        task_id = task["id"]
        
        # Determine who to notify based on success/failure
        notification_list = []
        if success and "on_success" in notifications:
            notification_list.extend(notifications["on_success"])
        elif not success and "on_failure" in notifications:
            notification_list.extend(notifications["on_failure"])
        
        if notification_list:
            # In a real implementation, you would send emails or other notifications here
            logger.info(f"Notifications would be sent to {notification_list} for task {task_id}")
    
    def check_for_timeouts_and_escalations(self):
        """Check for tasks that have been running too long and handle escalations."""
        # This is a simplified implementation - in reality, you'd track running tasks differently
        pass
    
    def run_scheduler_loop(self):
        """Main loop that checks for and runs scheduled tasks."""
        logger.info("Starting recurring task scheduler")
        self.running = True
        
        while self.running:
            try:
                # Get current time
                now = datetime.now()
                
                # Iterate through all enabled tasks
                for task in self.config["tasks"]:
                    if not task.get("enabled", True):
                        continue
                    
                    # Check if this task should run now
                    if self.should_run_task(task, now):
                        # Execute the task in a separate thread
                        thread = threading.Thread(target=self.execute_task, args=(task,))
                        thread.start()
                        self.task_threads[task["id"]] = thread
                
                # Clean up completed threads
                for task_id, thread in list(self.task_threads.items()):
                    if not thread.is_alive():
                        del self.task_threads[task_id]
                
                # Save state periodically
                self.state_manager.save_state()
                
                # Sleep for a short time before checking again
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                self.running = False
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Wait a minute before trying again
        
        # Wait for all task threads to complete
        for thread in self.task_threads.values():
            thread.join()
        
        logger.info("Scheduler stopped")
    
    def start(self):
        """Start the scheduler."""
        self.run_scheduler_loop()


def main():
    """Main entry point for the scheduler."""
    # Default paths
    config_path = os.getenv("TASK_SCHEDULE_RULES_PATH", "./assets/task-schedule-rules.json")
    state_path = os.getenv("TASK_STATE_FILE_PATH", "./state/task_state.json")
    audit_path = os.getenv("TASK_AUDIT_LOG_PATH", "./logs/task-audit.log")
    
    # Allow command-line overrides
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    if len(sys.argv) > 2:
        state_path = sys.argv[2]
    if len(sys.argv) > 3:
        audit_path = sys.argv[3]
    
    # Create scheduler instance
    scheduler = TaskScheduler(config_path, state_path, audit_path)
    
    # Start the scheduler
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler shutdown requested")
    except Exception as e:
        logger.error(f"Scheduler failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# Example usage and testing code
if __name__ == "__main__":
    # This section provides examples of how to use the scheduler
    print("Recurring Task Scheduler")
    print("Usage: python task_scheduler.py [config_path] [state_path] [audit_path]")
    print("")
    print("Environment variables:")
    print("  TASK_SCHEDULE_RULES_PATH - Path to task schedule rules file (default: ./assets/task-schedule-rules.json)")
    print("  TASK_STATE_FILE_PATH - Path to task state file (default: ./state/task_state.json)")
    print("  TASK_AUDIT_LOG_PATH - Path to audit log file (default: ./logs/task-audit.log)")
    print("")
    
    # Example of running a simple test
    if "--test" in sys.argv:
        print("Running scheduler test...")
        
        # Use the example config
        config_path = "./assets/example-schedule-config.json"
        state_path = "./state/example_task_state.json"
        audit_path = "./logs/example_task-audit.log"
        
        # Create directories if needed
        Path("./state").mkdir(exist_ok=True)
        Path("./logs").mkdir(exist_ok=True)
        
        scheduler = TaskScheduler(config_path, state_path, audit_path)
        
        # Just validate the config and show what would run
        print("Validating configuration...")
        for task in scheduler.config["tasks"]:
            print(f"  - Task '{task['id']}': {task['schedule']['type']} - {task['description']}")
        
        print("\nScheduler initialized successfully!")