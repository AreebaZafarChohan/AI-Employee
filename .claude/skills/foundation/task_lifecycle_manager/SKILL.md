# Task Lifecycle Manager Skill

## Overview

**Skill Name:** `task_lifecycle_manager`
**Domain:** `foundation`
**Purpose:** Manage task claiming, movement, and lifecycle tracking with atomic operations to prevent race conditions and ensure data consistency in multi-agent environments.

**Core Capabilities:**
- Atomic task claiming with collision detection
- Safe task state transitions (pending → in_progress → completed)
- Task movement between agents with ownership transfer
- Lifecycle event tracking and audit trails
- Conflict resolution for concurrent modifications
- Dependency graph management
- Task priority and deadline tracking

**When to Use:**
- Multi-agent task coordination systems
- Workflow automation with parallel agents
- Task queue management with worker pools
- Project management with task dependencies
- Automated CI/CD pipeline task orchestration
- Distributed team collaboration platforms

**When NOT to Use:**
- Single-agent environments with no concurrency
- Simple to-do lists without state management
- Fire-and-forget operations without tracking
- Stateless operations that don't require coordination
- Real-time collaborative editing (use OT/CRDT instead)

---

## Impact Analysis

### System Impact: **CRITICAL**
- **Data Consistency:** Race conditions can lead to duplicate work or lost tasks
- **State Management:** Atomic operations required for all state transitions
- **File System:** Requires file locking or atomic write operations
- **Concurrency:** Multiple agents may attempt simultaneous task claims

### Operational Impact: **HIGH**
- **Performance:** Lock contention can impact throughput in high-concurrency scenarios
- **Monitoring:** Must track claim failures, state transition errors, orphaned tasks
- **Recovery:** Stale locks and crashed agents require cleanup mechanisms
- **Debugging:** Complex state machines require detailed logging

### Business Impact: **MEDIUM**
- **Productivity:** Prevents duplicate work and ensures task completion
- **Accountability:** Clear ownership and audit trails
- **Visibility:** Real-time progress tracking across distributed teams
- **Reliability:** Reduces manual coordination overhead

---

## Environment Variables

### Required Variables

```bash
# Task storage configuration
TASK_STORAGE_PATH="./tasks"              # Base path for task files
TASK_LOCK_TIMEOUT="300"                  # Lock timeout in seconds (5 minutes)
AGENT_ID="agent-$(hostname)-$$"          # Unique agent identifier

# Concurrency control
TASK_CLAIM_RETRY_COUNT="3"               # Number of retry attempts
TASK_CLAIM_RETRY_DELAY="1"               # Delay between retries (seconds)
```

### Optional Variables

```bash
# Advanced configuration
TASK_STATE_FILE="task-state.json"        # State tracking file
TASK_AUDIT_LOG="task-audit.log"          # Audit log path
TASK_MAX_CONCURRENT="10"                 # Max concurrent tasks per agent

# Monitoring and alerting
TASK_METRICS_ENABLED="true"              # Enable metrics collection
TASK_METRICS_PORT="9090"                 # Prometheus metrics port
TASK_ALERT_WEBHOOK=""                    # Webhook for critical alerts

# Recovery and cleanup
TASK_ORPHAN_TIMEOUT="3600"               # Orphan detection timeout (1 hour)
TASK_CLEANUP_INTERVAL="300"              # Cleanup interval (5 minutes)
TASK_ENABLE_AUTO_RECOVERY="true"         # Auto-recover orphaned tasks

# Development/debugging
TASK_DEBUG_MODE="false"                  # Enable verbose debug logging
TASK_DRY_RUN="false"                     # Simulate operations without writes
```

---

## Network and Authentication Implications

### Local File System Operations

**Primary Mode:** File-based task management with atomic operations

**Requirements:**
1. **File System Support:** POSIX-compliant with atomic rename operations
2. **Permissions:** Read/write access to task storage directory
3. **Locking:** Advisory file locks (flock/fcntl) or atomic operations
4. **Consistency:** NFS may have issues with locking (use local storage preferred)

### Distributed Task Coordination (Advanced)

**If using shared storage (NFS, S3, etc.):**

```bash
# Distributed locking via Redis
TASK_DISTRIBUTED_LOCK="true"
TASK_REDIS_URL="redis://localhost:6379"
TASK_LOCK_PREFIX="task-lock:"

# Or via database
TASK_DATABASE_URL="postgresql://localhost/tasks"
TASK_USE_DB_TRANSACTIONS="true"
```

**Authentication Considerations:**
- **Agent Identity:** Each agent must have unique identifier
- **File Permissions:** Shared storage requires appropriate group permissions
- **API Auth:** If using REST API, require authentication tokens
- **Audit Trail:** All operations must log authenticated agent identity

### Network Patterns

**Pattern 1: Local File System (Recommended for single-host)**
```bash
# No network requirements
# Direct file system access with atomic operations
```

**Pattern 2: Shared File System (Multi-host with NFS/CIFS)**
```bash
# Requirements:
# - Reliable network connection to file server
# - Advisory file locking support
# - Low latency (<10ms preferred)
```

**Pattern 3: Distributed Coordination (High scale)**
```bash
# Requirements:
# - Redis/etcd cluster for distributed locking
# - Database for persistent state
# - Message queue for event notifications
# - Load balancer for API endpoints
```

---

## Blueprints & Templates

### Template 1: Atomic Task Claim Operation

**File:** `assets/task-claim-template.sh`

```bash
#!/usr/bin/env bash
# task-claim-template.sh
# Atomically claim a task with collision detection

set -euo pipefail

TASK_ID="${1:?Usage: $0 <task-id>}"
AGENT_ID="${AGENT_ID:-agent-$(hostname)-$$}"
TASK_STORAGE_PATH="${TASK_STORAGE_PATH:-./tasks}"
TASK_LOCK_TIMEOUT="${TASK_LOCK_TIMEOUT:-300}"

# Audit logging
audit_log() {
    local level="$1"
    local action="$2"
    local task_id="$3"
    local status="$4"
    local message="${5:-}"

    echo "$(date -Iseconds) [$level] agent=$AGENT_ID action=$action task=$task_id status=$status $message" \
        >> "${TASK_AUDIT_LOG:-/dev/stderr}"
}

# Check if task exists and is claimable
check_task_claimable() {
    local task_id="$1"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"

    if [[ ! -f "$task_file" ]]; then
        audit_log "ERROR" "CLAIM_CHECK" "$task_id" "NOT_FOUND"
        return 1
    fi

    # Parse current state and owner
    local current_state
    local current_owner
    current_state=$(jq -r '.state // "unknown"' "$task_file")
    current_owner=$(jq -r '.owner // ""' "$task_file")

    # Task is claimable if:
    # 1. State is "pending" and no owner
    # 2. State is "pending" and owner is stale (lock expired)
    if [[ "$current_state" != "pending" ]]; then
        audit_log "WARN" "CLAIM_CHECK" "$task_id" "NOT_CLAIMABLE" "state=$current_state"
        return 1
    fi

    if [[ -n "$current_owner" ]]; then
        # Check if lock is stale
        local claimed_at
        claimed_at=$(jq -r '.claimed_at // 0' "$task_file")
        local now
        now=$(date +%s)
        local elapsed=$((now - claimed_at))

        if [[ $elapsed -lt $TASK_LOCK_TIMEOUT ]]; then
            audit_log "WARN" "CLAIM_CHECK" "$task_id" "ALREADY_CLAIMED" "owner=$current_owner"
            return 1
        else
            audit_log "INFO" "CLAIM_CHECK" "$task_id" "STALE_LOCK" "owner=$current_owner elapsed=${elapsed}s"
        fi
    fi

    return 0
}

# Atomically claim task using rename operation
claim_task_atomic() {
    local task_id="$1"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"
    local temp_file="$TASK_STORAGE_PATH/.$task_id.tmp.$$"
    local backup_file="$TASK_STORAGE_PATH/.$task_id.backup.$$"

    audit_log "INFO" "CLAIM_ATTEMPT" "$task_id" "STARTED"

    # Read current task data
    if ! cp "$task_file" "$backup_file"; then
        audit_log "ERROR" "CLAIM_ATTEMPT" "$task_id" "BACKUP_FAILED"
        return 1
    fi

    # Update task with claim information
    if ! jq --arg agent "$AGENT_ID" \
            --arg timestamp "$(date -Iseconds)" \
            --arg unix_time "$(date +%s)" \
            '.state = "in_progress" | .owner = $agent | .claimed_at = ($unix_time | tonumber) | .claimed_timestamp = $timestamp' \
            "$backup_file" > "$temp_file"; then
        audit_log "ERROR" "CLAIM_ATTEMPT" "$task_id" "UPDATE_FAILED"
        rm -f "$temp_file" "$backup_file"
        return 1
    fi

    # Atomic rename (this is the critical section)
    # If another agent renamed the file between our check and now, this will fail
    if mv "$temp_file" "$task_file" 2>/dev/null; then
        audit_log "INFO" "CLAIM_ATTEMPT" "$task_id" "SUCCESS"
        rm -f "$backup_file"
        return 0
    else
        audit_log "WARN" "CLAIM_ATTEMPT" "$task_id" "COLLISION" "Another agent claimed the task"
        rm -f "$temp_file" "$backup_file"
        return 1
    fi
}

# Main claim logic with retries
claim_task() {
    local task_id="$1"
    local retry_count="${TASK_CLAIM_RETRY_COUNT:-3}"
    local retry_delay="${TASK_CLAIM_RETRY_DELAY:-1}"

    for attempt in $(seq 1 "$retry_count"); do
        audit_log "INFO" "CLAIM" "$task_id" "ATTEMPT_$attempt"

        # Check if task is claimable
        if ! check_task_claimable "$task_id"; then
            audit_log "WARN" "CLAIM" "$task_id" "NOT_CLAIMABLE_ATTEMPT_$attempt"
            return 1
        fi

        # Attempt atomic claim
        if claim_task_atomic "$task_id"; then
            audit_log "INFO" "CLAIM" "$task_id" "SUCCESS_ATTEMPT_$attempt"
            echo "$task_id"
            return 0
        fi

        # Collision detected, wait and retry
        if [[ $attempt -lt $retry_count ]]; then
            audit_log "INFO" "CLAIM" "$task_id" "RETRY_WAIT" "delay=${retry_delay}s"
            sleep "$retry_delay"
        fi
    done

    audit_log "ERROR" "CLAIM" "$task_id" "FAILED_ALL_ATTEMPTS"
    return 1
}

# Execute claim
if claim_task "$TASK_ID"; then
    echo "Successfully claimed task: $TASK_ID"
    exit 0
else
    echo "Failed to claim task: $TASK_ID" >&2
    exit 1
fi
```

### Template 2: Safe Task State Transition

**File:** `assets/task-transition-template.sh`

```bash
#!/usr/bin/env bash
# task-transition-template.sh
# Safely transition task state with validation

set -euo pipefail

TASK_ID="${1:?Usage: $0 <task-id> <new-state>}"
NEW_STATE="${2:?Usage: $0 <task-id> <new-state>}"
AGENT_ID="${AGENT_ID:-agent-$(hostname)-$$}"
TASK_STORAGE_PATH="${TASK_STORAGE_PATH:-./tasks}"

# Valid state transitions
declare -A VALID_TRANSITIONS=(
    ["pending:in_progress"]="1"
    ["in_progress:completed"]="1"
    ["in_progress:failed"]="1"
    ["in_progress:blocked"]="1"
    ["blocked:in_progress"]="1"
    ["failed:pending"]="1"        # Allow retry
)

audit_log() {
    local level="$1"
    local action="$2"
    local task_id="$3"
    local status="$4"
    local message="${5:-}"

    echo "$(date -Iseconds) [$level] agent=$AGENT_ID action=$action task=$task_id status=$status $message" \
        >> "${TASK_AUDIT_LOG:-/dev/stderr}"
}

# Validate state transition
validate_transition() {
    local current_state="$1"
    local new_state="$2"
    local transition_key="${current_state}:${new_state}"

    if [[ -n "${VALID_TRANSITIONS[$transition_key]:-}" ]]; then
        return 0
    else
        return 1
    fi
}

# Verify agent owns the task
verify_ownership() {
    local task_id="$1"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"

    if [[ ! -f "$task_file" ]]; then
        audit_log "ERROR" "VERIFY_OWNERSHIP" "$task_id" "NOT_FOUND"
        return 1
    fi

    local current_owner
    current_owner=$(jq -r '.owner // ""' "$task_file")

    if [[ "$current_owner" != "$AGENT_ID" ]]; then
        audit_log "ERROR" "VERIFY_OWNERSHIP" "$task_id" "NOT_OWNER" "current_owner=$current_owner"
        return 1
    fi

    return 0
}

# Transition task state
transition_task() {
    local task_id="$1"
    local new_state="$2"
    local task_file="$TASK_STORAGE_PATH/$task_id.json"
    local temp_file="$TASK_STORAGE_PATH/.$task_id.tmp.$$"

    audit_log "INFO" "TRANSITION" "$task_id" "STARTED" "new_state=$new_state"

    # Verify ownership
    if ! verify_ownership "$task_id"; then
        return 1
    fi

    # Read current state
    local current_state
    current_state=$(jq -r '.state' "$task_file")

    # Validate transition
    if ! validate_transition "$current_state" "$new_state"; then
        audit_log "ERROR" "TRANSITION" "$task_id" "INVALID" "from=$current_state to=$new_state"
        echo "Invalid transition: $current_state -> $new_state" >&2
        return 1
    fi

    # Update state with metadata
    if ! jq --arg new_state "$new_state" \
            --arg timestamp "$(date -Iseconds)" \
            --arg agent "$AGENT_ID" \
            '.state = $new_state |
             .updated_at = $timestamp |
             .updated_by = $agent |
             .history += [{
                "from": .state,
                "to": $new_state,
                "timestamp": $timestamp,
                "agent": $agent
             }]' \
            "$task_file" > "$temp_file"; then
        audit_log "ERROR" "TRANSITION" "$task_id" "UPDATE_FAILED"
        rm -f "$temp_file"
        return 1
    fi

    # Atomic replace
    if mv "$temp_file" "$task_file"; then
        audit_log "INFO" "TRANSITION" "$task_id" "SUCCESS" "from=$current_state to=$new_state"

        # Special handling for terminal states
        if [[ "$new_state" == "completed" || "$new_state" == "failed" ]]; then
            # Clear owner on completion
            jq '.owner = null | .completed_at = (now | tostring)' "$task_file" > "$temp_file"
            mv "$temp_file" "$task_file"
            audit_log "INFO" "RELEASE" "$task_id" "AUTO_RELEASED"
        fi

        return 0
    else
        audit_log "ERROR" "TRANSITION" "$task_id" "ATOMIC_WRITE_FAILED"
        rm -f "$temp_file"
        return 1
    fi
}

# Execute transition
if transition_task "$TASK_ID" "$NEW_STATE"; then
    echo "Successfully transitioned task $TASK_ID to $NEW_STATE"
    exit 0
else
    echo "Failed to transition task $TASK_ID" >&2
    exit 1
fi
```

### Template 3: Python Task Lifecycle Manager

**File:** `assets/task_lifecycle_manager.py`

```python
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
```

---

## Validation Checklist

### Pre-Deployment Checklist

- [ ] **Storage Configuration**
  - [ ] Task storage path exists and is writable
  - [ ] File system supports atomic rename operations
  - [ ] Sufficient disk space for task files and logs
  - [ ] Backup strategy for task data

- [ ] **Concurrency Control**
  - [ ] Agent ID generation is unique per instance
  - [ ] Lock timeout configured appropriately
  - [ ] Retry logic implemented with backoff
  - [ ] Collision detection tested

- [ ] **State Management**
  - [ ] All valid state transitions defined
  - [ ] Invalid transitions are rejected
  - [ ] History tracking enabled
  - [ ] Audit logging configured

- [ ] **Error Handling**
  - [ ] File not found errors handled
  - [ ] Permission denied errors handled
  - [ ] Disk full scenarios handled
  - [ ] Corrupted task files handled

- [ ] **Monitoring**
  - [ ] Audit log path configured
  - [ ] Metrics collection enabled
  - [ ] Alerting for critical errors
  - [ ] Dashboard for task status

- [ ] **Recovery Mechanisms**
  - [ ] Orphan detection configured
  - [ ] Auto-recovery enabled
  - [ ] Cleanup intervals set
  - [ ] Manual recovery procedures documented

### Post-Deployment Validation

- [ ] **Functional Tests**
  - [ ] Task creation succeeds
  - [ ] Task claiming succeeds
  - [ ] State transitions work correctly
  - [ ] Task release works
  - [ ] Dependency checking works

- [ ] **Concurrency Tests**
  - [ ] Multiple agents can claim different tasks
  - [ ] Collision detection prevents double claiming
  - [ ] Stale lock recovery works
  - [ ] High concurrency scenarios tested

- [ ] **Failure Tests**
  - [ ] Agent crash recovery works
  - [ ] Network failure handling works
  - [ ] Disk full handling works
  - [ ] Corrupted file recovery works

- [ ] **Performance Tests**
  - [ ] Claim operation latency acceptable
  - [ ] Transition operation latency acceptable
  - [ ] List operations scale with task count
  - [ ] Lock contention doesn't cause deadlocks

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Overwriting Tasks Without Checks

**Bad Example:**
```bash
# NEVER do this - no collision detection
TASK_FILE="tasks/$TASK_ID.json"
jq '.state = "in_progress" | .owner = "'$AGENT_ID'"' "$TASK_FILE" > "$TASK_FILE.tmp"
mv "$TASK_FILE.tmp" "$TASK_FILE"
```

**Why It's Bad:**
- No verification of current state
- Race condition: multiple agents can claim simultaneously
- Lost updates: second write overwrites first
- No audit trail

**Correct Approach:**
```bash
# Read current state
current_state=$(jq -r '.state' "$TASK_FILE")
current_owner=$(jq -r '.owner // ""' "$TASK_FILE")

# Verify claimable
if [[ "$current_state" != "pending" ]] || [[ -n "$current_owner" ]]; then
    echo "Task not claimable" >&2
    exit 1
fi

# Atomic update with backup
cp "$TASK_FILE" "$TASK_FILE.backup"
jq '.state = "in_progress" | .owner = "'$AGENT_ID'"' "$TASK_FILE.backup" > "$TASK_FILE.tmp"

# Atomic rename
if ! mv "$TASK_FILE.tmp" "$TASK_FILE"; then
    echo "Collision detected" >&2
    rm -f "$TASK_FILE.tmp" "$TASK_FILE.backup"
    exit 1
fi
```

---

### ❌ Anti-Pattern 2: Ignoring State Transition Rules

**Bad Example:**
```python
# NEVER do this - allows invalid transitions
def complete_task(task_id):
    task = read_task(task_id)
    task['state'] = 'completed'  # ❌ No validation
    write_task(task_id, task)
```

**Why It's Bad:**
- Can transition from any state to any other state
- No business logic enforcement
- Can mark pending tasks as completed without claiming
- Breaks workflow integrity

**Correct Approach:**
```python
VALID_TRANSITIONS = {
    ('pending', 'in_progress'),
    ('in_progress', 'completed'),
    ('in_progress', 'failed'),
    ('in_progress', 'blocked'),
    ('blocked', 'in_progress'),
    ('failed', 'pending'),
}

def complete_task(task_id):
    task = read_task(task_id)
    current_state = task['state']
    new_state = 'completed'

    # Validate transition
    if (current_state, new_state) not in VALID_TRANSITIONS:
        raise ValueError(f"Invalid transition: {current_state} -> {new_state}")

    # Verify ownership
    if task['owner'] != agent_id:
        raise ValueError("Not the owner of this task")

    # Update with history
    task['state'] = new_state
    task['history'].append({
        'from': current_state,
        'to': new_state,
        'timestamp': datetime.now().isoformat(),
        'agent': agent_id
    })

    write_task_atomic(task_id, task)
```

---

### ❌ Anti-Pattern 3: Not Handling Stale Locks

**Bad Example:**
```python
# NEVER do this - ignores lock timeout
def is_task_claimable(task):
    if task['owner']:
        return False  # ❌ Assumes all owned tasks are active
    return task['state'] == 'pending'
```

**Why It's Bad:**
- Crashed agents leave tasks permanently locked
- No recovery mechanism for orphaned tasks
- System degrades over time
- Manual intervention required

**Correct Approach:**
```python
def is_task_claimable(task, lock_timeout=300):
    if task['state'] != 'pending':
        return False

    if task['owner']:
        # Check if lock is stale
        claimed_at = task.get('claimed_at', 0)
        elapsed = time.time() - claimed_at

        if elapsed < lock_timeout:
            # Active lock
            return False
        else:
            # Stale lock - can reclaim
            logger.warning(f"Stale lock detected for task {task['task_id']}: "
                         f"owner={task['owner']}, elapsed={elapsed}s")
            return True

    return True
```

---

### ❌ Anti-Pattern 4: Non-Atomic File Operations

**Bad Example:**
```python
# NEVER do this - not atomic
def update_task(task_id, updates):
    task = read_task(task_id)
    task.update(updates)

    # ❌ Direct write - can be interrupted
    with open(f'tasks/{task_id}.json', 'w') as f:
        json.dump(task, f)
```

**Why It's Bad:**
- File can be corrupted if process crashes mid-write
- Another agent might read partially written file
- No recovery from interrupted writes
- Data loss possible

**Correct Approach:**
```python
import tempfile
import os

def update_task_atomic(task_id, updates):
    task = read_task(task_id)
    task.update(updates)

    task_file = f'tasks/{task_id}.json'

    # Write to temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir='tasks',
        delete=False,
        suffix='.tmp'
    ) as tmp:
        json.dump(task, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic rename
    os.rename(tmp_path, task_file)

    # If rename fails, tmp_path still exists for recovery
```

---

### ❌ Anti-Pattern 5: No Audit Trail

**Bad Example:**
```python
# NEVER do this - no history tracking
def claim_task(task_id):
    task = read_task(task_id)
    task['state'] = 'in_progress'
    task['owner'] = agent_id
    # ❌ No audit trail
    write_task(task_id, task)
```

**Why It's Bad:**
- Can't debug issues
- No accountability
- Can't track task timeline
- Can't identify patterns

**Correct Approach:**
```python
def claim_task(task_id):
    task = read_task(task_id)

    old_state = task['state']
    task['state'] = 'in_progress'
    task['owner'] = agent_id
    task['claimed_at'] = time.time()
    task['claimed_timestamp'] = datetime.utcnow().isoformat()

    # Add to history
    task['history'].append({
        'action': 'claim',
        'from_state': old_state,
        'to_state': 'in_progress',
        'timestamp': task['claimed_timestamp'],
        'agent': agent_id,
        'metadata': {
            'hostname': socket.gethostname(),
            'pid': os.getpid()
        }
    })

    # Write audit log
    audit_log('INFO', 'CLAIM', task_id, 'SUCCESS', f'agent={agent_id}')

    write_task_atomic(task_id, task)
```

---

## Related Documentation

- [patterns.md](./docs/patterns.md) - Common task management patterns
- [impact-checklist.md](./docs/impact-checklist.md) - Full system impact assessment
- [gotchas.md](./docs/gotchas.md) - Common pitfalls and troubleshooting

---

## Support and Troubleshooting

### Common Issues

1. **Task Claim Collisions**
   - Increase retry count
   - Add random jitter to retry delay
   - Check system clock synchronization

2. **Orphaned Tasks**
   - Verify lock timeout is appropriate
   - Enable auto-recovery
   - Run manual cleanup scripts

3. **Performance Degradation**
   - Check for lock contention
   - Increase concurrency limits
   - Optimize file I/O operations

4. **State Corruption**
   - Validate JSON structure on read
   - Implement automatic recovery
   - Keep backups of task files

### Getting Help

- Review audit logs for detailed operation history
- Check system metrics for performance issues
- Consult patterns.md for usage examples
- Complete impact-checklist.md for deployment review

---

**Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** Foundation Team
