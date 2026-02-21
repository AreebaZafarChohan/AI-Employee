#!/usr/bin/env python3
"""
task_lifecycle_manager.py
Complete task lifecycle management with atomic operations
"""

import os
import json
import time
import fcntl
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskState(Enum):
    """Valid task states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskTransitionError(Exception):
    """Invalid state transition error"""
    pass


class TaskCollisionError(Exception):
    """Task claim collision error"""
    pass


@dataclass
class TaskMetadata:
    """Task metadata structure"""
    task_id: str
    state: TaskState
    owner: Optional[str] = None
    claimed_at: Optional[float] = None
    claimed_timestamp: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    completed_at: Optional[str] = None
    priority: int = 0
    dependencies: List[str] = None
    tags: List[str] = None
    history: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.history is None:
            self.history = []
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class TaskLifecycleManager:
    """Manage task lifecycle with atomic operations"""

    # Valid state transitions
    VALID_TRANSITIONS = {
        (TaskState.PENDING, TaskState.IN_PROGRESS),
        (TaskState.IN_PROGRESS, TaskState.COMPLETED),
        (TaskState.IN_PROGRESS, TaskState.FAILED),
        (TaskState.IN_PROGRESS, TaskState.BLOCKED),
        (TaskState.BLOCKED, TaskState.IN_PROGRESS),
        (TaskState.FAILED, TaskState.PENDING),  # Retry
    }

    def __init__(
        self,
        storage_path: str = None,
        agent_id: str = None,
        lock_timeout: int = 300
    ):
        self.storage_path = Path(storage_path or os.getenv('TASK_STORAGE_PATH', './tasks'))
        self.agent_id = agent_id or os.getenv('AGENT_ID', f"agent-{os.getpid()}")
        self.lock_timeout = lock_timeout
        self.audit_log_path = os.getenv('TASK_AUDIT_LOG', 'task-audit.log')

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"TaskLifecycleManager initialized: agent={self.agent_id}")

    def _audit_log(self, level: str, action: str, task_id: str, status: str, message: str = ""):
        """Write audit log entry"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"{timestamp} [{level}] agent={self.agent_id} action={action} task={task_id} status={status} {message}\n"

        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    def _get_task_file(self, task_id: str) -> Path:
        """Get path to task file"""
        return self.storage_path / f"{task_id}.json"

    def _read_task(self, task_id: str) -> Optional[TaskMetadata]:
        """Read task metadata from file"""
        task_file = self._get_task_file(task_id)

        if not task_file.exists():
            return None

        try:
            with open(task_file, 'r') as f:
                data = json.load(f)
                data['state'] = TaskState(data['state'])
                return TaskMetadata(**data)
        except Exception as e:
            logger.error(f"Failed to read task {task_id}: {e}")
            return None

    def _write_task_atomic(self, task_id: str, metadata: TaskMetadata) -> bool:
        """Write task metadata atomically"""
        task_file = self._get_task_file(task_id)

        # Convert to dict for JSON serialization
        data = asdict(metadata)
        data['state'] = metadata.state.value

        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.storage_path,
                delete=False,
                suffix='.tmp'
            ) as tmp:
                json.dump(data, tmp, indent=2)
                tmp_path = tmp.name

            # Atomic rename
            os.rename(tmp_path, task_file)
            return True

        except Exception as e:
            logger.error(f"Failed to write task {task_id}: {e}")
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            return False

    def create_task(
        self,
        task_id: str,
        priority: int = 0,
        dependencies: List[str] = None,
        tags: List[str] = None
    ) -> bool:
        """Create a new task in pending state"""
        self._audit_log("INFO", "CREATE", task_id, "ATTEMPT")

        task_file = self._get_task_file(task_id)
        if task_file.exists():
            self._audit_log("ERROR", "CREATE", task_id, "ALREADY_EXISTS")
            return False

        metadata = TaskMetadata(
            task_id=task_id,
            state=TaskState.PENDING,
            priority=priority,
            dependencies=dependencies or [],
            tags=tags or []
        )

        if self._write_task_atomic(task_id, metadata):
            self._audit_log("INFO", "CREATE", task_id, "SUCCESS")
            return True
        else:
            self._audit_log("ERROR", "CREATE", task_id, "FAILED")
            return False

    def claim_task(self, task_id: str, retry_count: int = 3) -> bool:
        """Atomically claim a task"""
        for attempt in range(1, retry_count + 1):
            self._audit_log("INFO", "CLAIM", task_id, f"ATTEMPT_{attempt}")

            # Read current task state
            metadata = self._read_task(task_id)
            if not metadata:
                self._audit_log("ERROR", "CLAIM", task_id, "NOT_FOUND")
                return False

            # Check if claimable
            if metadata.state != TaskState.PENDING:
                self._audit_log("WARN", "CLAIM", task_id, "NOT_CLAIMABLE", f"state={metadata.state.value}")
                return False

            # Check for stale lock
            if metadata.owner:
                if metadata.claimed_at:
                    elapsed = time.time() - metadata.claimed_at
                    if elapsed < self.lock_timeout:
                        self._audit_log("WARN", "CLAIM", task_id, "ALREADY_CLAIMED", f"owner={metadata.owner}")
                        return False
                    else:
                        self._audit_log("INFO", "CLAIM", task_id, "STALE_LOCK", f"owner={metadata.owner} elapsed={elapsed}s")

            # Update with claim information
            metadata.state = TaskState.IN_PROGRESS
            metadata.owner = self.agent_id
            metadata.claimed_at = time.time()
            metadata.claimed_timestamp = datetime.utcnow().isoformat()
            metadata.updated_at = datetime.utcnow().isoformat()
            metadata.updated_by = self.agent_id

            # Add to history
            metadata.history.append({
                "from": TaskState.PENDING.value,
                "to": TaskState.IN_PROGRESS.value,
                "timestamp": metadata.claimed_timestamp,
                "agent": self.agent_id,
                "action": "claim"
            })

            # Attempt atomic write
            if self._write_task_atomic(task_id, metadata):
                self._audit_log("INFO", "CLAIM", task_id, "SUCCESS", f"attempt={attempt}")
                return True

            # Collision detected
            self._audit_log("WARN", "CLAIM", task_id, "COLLISION", f"attempt={attempt}")
            if attempt < retry_count:
                time.sleep(1)  # Wait before retry

        self._audit_log("ERROR", "CLAIM", task_id, "FAILED_ALL_ATTEMPTS")
        return False

    def transition_task(self, task_id: str, new_state: TaskState) -> bool:
        """Transition task to new state with validation"""
        self._audit_log("INFO", "TRANSITION", task_id, "STARTED", f"new_state={new_state.value}")

        # Read current task
        metadata = self._read_task(task_id)
        if not metadata:
            self._audit_log("ERROR", "TRANSITION", task_id, "NOT_FOUND")
            return False

        # Verify ownership (except for initial claim)
        if metadata.state != TaskState.PENDING and metadata.owner != self.agent_id:
            self._audit_log("ERROR", "TRANSITION", task_id, "NOT_OWNER", f"current_owner={metadata.owner}")
            return False

        # Validate transition
        transition = (metadata.state, new_state)
        if transition not in self.VALID_TRANSITIONS:
            self._audit_log("ERROR", "TRANSITION", task_id, "INVALID",
                          f"from={metadata.state.value} to={new_state.value}")
            raise TaskTransitionError(f"Invalid transition: {metadata.state.value} -> {new_state.value}")

        # Update state
        old_state = metadata.state
        metadata.state = new_state
        metadata.updated_at = datetime.utcnow().isoformat()
        metadata.updated_by = self.agent_id

        # Add to history
        metadata.history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": metadata.updated_at,
            "agent": self.agent_id,
            "action": "transition"
        })

        # Clear owner on terminal states
        if new_state in (TaskState.COMPLETED, TaskState.FAILED):
            metadata.owner = None
            metadata.completed_at = datetime.utcnow().isoformat()

        # Write atomically
        if self._write_task_atomic(task_id, metadata):
            self._audit_log("INFO", "TRANSITION", task_id, "SUCCESS",
                          f"from={old_state.value} to={new_state.value}")
            return True
        else:
            self._audit_log("ERROR", "TRANSITION", task_id, "FAILED")
            return False

    def release_task(self, task_id: str) -> bool:
        """Release a claimed task back to pending"""
        self._audit_log("INFO", "RELEASE", task_id, "ATTEMPT")

        metadata = self._read_task(task_id)
        if not metadata:
            self._audit_log("ERROR", "RELEASE", task_id, "NOT_FOUND")
            return False

        # Verify ownership
        if metadata.owner != self.agent_id:
            self._audit_log("ERROR", "RELEASE", task_id, "NOT_OWNER")
            return False

        # Transition back to pending
        return self.transition_task(task_id, TaskState.PENDING)

    def list_claimable_tasks(self) -> List[str]:
        """List all tasks available for claiming"""
        claimable = []

        for task_file in self.storage_path.glob("*.json"):
            task_id = task_file.stem
            metadata = self._read_task(task_id)

            if metadata and metadata.state == TaskState.PENDING:
                # Check dependencies
                if all(self.is_task_completed(dep) for dep in metadata.dependencies):
                    claimable.append(task_id)

        # Sort by priority (higher first)
        claimable.sort(key=lambda tid: self._read_task(tid).priority, reverse=True)

        return claimable

    def is_task_completed(self, task_id: str) -> bool:
        """Check if task is completed"""
        metadata = self._read_task(task_id)
        return metadata and metadata.state == TaskState.COMPLETED

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and metadata"""
        metadata = self._read_task(task_id)
        if not metadata:
            return None

        return {
            'task_id': metadata.task_id,
            'state': metadata.state.value,
            'owner': metadata.owner,
            'claimed_at': metadata.claimed_timestamp,
            'created_at': metadata.created_at,
            'updated_at': metadata.updated_at,
            'priority': metadata.priority,
            'dependencies': metadata.dependencies,
            'tags': metadata.tags,
            'history_count': len(metadata.history)
        }


# Example usage
if __name__ == "__main__":
    manager = TaskLifecycleManager(storage_path="./tasks")

    # Create tasks
    manager.create_task("task-1", priority=10, tags=["urgent"])
    manager.create_task("task-2", priority=5, dependencies=["task-1"])

    # Claim and work on task
    if manager.claim_task("task-1"):
        print("Successfully claimed task-1")

        # Do work...
        time.sleep(1)

        # Complete task
        manager.transition_task("task-1", TaskState.COMPLETED)
        print("Task-1 completed")

    # List available tasks
    claimable = manager.list_claimable_tasks()
    print(f"Claimable tasks: {claimable}")
