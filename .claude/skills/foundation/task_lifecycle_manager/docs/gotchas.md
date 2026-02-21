# Task Lifecycle Manager - Common Gotchas & Troubleshooting

## Overview
This document catalogs common mistakes, edge cases, and troubleshooting guidance for task lifecycle management operations.

---

## 1. Concurrency Issues

### Gotcha: Race Condition in Task Claiming

**Symptom:**
Multiple agents claim the same task, leading to duplicate work or conflicts.

**Problem:**
```python
# WRONG - Check and update are not atomic
def claim_task_wrong(task_id):
    task = read_task(task_id)

    if task['state'] == 'pending' and not task['owner']:  # ❌ Check
        task['state'] = 'in_progress'                     # ❌ Update (race window!)
        task['owner'] = agent_id
        write_task(task_id, task)
        return True
    return False

# Timeline:
# Agent A: Reads task (pending, no owner)
# Agent B: Reads task (pending, no owner)  ← Both see same state!
# Agent A: Writes update (claims task)
# Agent B: Writes update (overwrites A's claim)  ← Lost update!
```

**Solution:**
```python
# CORRECT - Atomic check-and-update
def claim_task_atomic(task_id):
    task_file = f'tasks/{task_id}.json'
    backup_file = f'tasks/.{task_id}.backup.{os.getpid()}'
    temp_file = f'tasks/.{task_id}.tmp.{os.getpid()}'

    try:
        # Create backup
        shutil.copy(task_file, backup_file)

        # Read current state
        with open(backup_file, 'r') as f:
            task = json.load(f)

        # Verify claimable
        if task['state'] != 'pending' or task.get('owner'):
            return False

        # Update
        task['state'] = 'in_progress'
        task['owner'] = agent_id
        task['claimed_at'] = time.time()

        # Write to temp
        with open(temp_file, 'w') as f:
            json.dump(task, f)

        # Atomic rename (CRITICAL: this is where collision is prevented)
        os.rename(temp_file, task_file)
        return True

    except FileExistsError:
        # Another agent won the race
        return False
    finally:
        # Cleanup
        try:
            os.unlink(backup_file)
        except:
            pass
```

**Prevention:**
- Always use atomic operations (rename)
- Never split read and write
- Test with concurrent agents
- Monitor collision rate

---

### Gotcha: Stale Locks Not Detected

**Symptom:**
Tasks remain locked forever after agent crashes, system gradually loses capacity.

**Problem:**
```python
# WRONG - Ignores lock timeout
def is_claimable(task):
    if task.get('owner'):
        return False  # ❌ Assumes all owned tasks are active
    return task['state'] == 'pending'

# Result: Crashed agent's tasks never recovered
```

**Solution:**
```python
# CORRECT - Check lock timeout
def is_claimable(task, lock_timeout=300):
    if task['state'] != 'pending':
        return False

    owner = task.get('owner')
    if not owner:
        return True  # No owner, claimable

    # Check if lock is stale
    claimed_at = task.get('claimed_at', 0)
    if not claimed_at:
        # No timestamp, treat as stale
        logger.warning(f"Task {task['id']} has owner but no timestamp")
        return True

    elapsed = time.time() - claimed_at
    if elapsed >= lock_timeout:
        logger.warning(f"Stale lock detected: task={task['id']}, "
                      f"owner={owner}, elapsed={elapsed}s")
        return True

    return False  # Active lock
```

**Prevention:**
- Always store claim timestamp
- Implement lock timeout checking
- Run orphan recovery daemon
- Monitor orphan task count

---

### Gotcha: Lost Updates Due to Non-Atomic Writes

**Symptom:**
Task state corruption, incomplete data, JSON parse errors.

**Problem:**
```python
# WRONG - Direct write (not atomic)
def update_task(task_id, updates):
    task = read_task(task_id)
    task.update(updates)

    # ❌ Process can crash between truncate and write
    with open(f'tasks/{task_id}.json', 'w') as f:
        json.dump(task, f)

# If crash happens during write:
# - File partially written
# - JSON is invalid
# - Task data lost
```

**Solution:**
```python
# CORRECT - Atomic write via rename
def update_task_atomic(task_id, updates):
    task = read_task(task_id)
    task.update(updates)

    task_file = f'tasks/{task_id}.json'

    # Write to temp file first
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir='tasks',
        delete=False,
        suffix='.tmp'
    ) as tmp:
        json.dump(task, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic rename
    # This is atomic on POSIX systems
    os.rename(tmp_path, task_file)
```

**Prevention:**
- Always use temp file + rename
- Never write directly to final file
- Implement backup before update
- Validate JSON after read

---

## 2. State Machine Violations

### Gotcha: Invalid State Transitions Not Prevented

**Symptom:**
Tasks skip states, end up in impossible states, workflow breaks.

**Problem:**
```python
# WRONG - No transition validation
def set_task_state(task_id, new_state):
    task = read_task(task_id)
    task['state'] = new_state  # ❌ Any state to any state!
    write_task(task_id, task)

# Allows:
# pending -> completed (skips in_progress)
# completed -> pending (zombie task)
# failed -> in_progress (no cleanup)
```

**Solution:**
```python
# CORRECT - Validate transitions
VALID_TRANSITIONS = {
    ('pending', 'in_progress'),
    ('in_progress', 'completed'),
    ('in_progress', 'failed'),
    ('in_progress', 'blocked'),
    ('blocked', 'in_progress'),
    ('failed', 'pending'),  # Retry allowed
}

def transition_task(task_id, new_state):
    task = read_task(task_id)
    current_state = task['state']

    # Validate transition
    if (current_state, new_state) not in VALID_TRANSITIONS:
        raise ValueError(
            f"Invalid transition for {task_id}: "
            f"{current_state} -> {new_state}"
        )

    # Update with history
    task['state'] = new_state
    task['history'].append({
        'from': current_state,
        'to': new_state,
        'timestamp': datetime.utcnow().isoformat(),
        'agent': agent_id
    })

    write_task_atomic(task_id, task)
```

**Prevention:**
- Define valid transitions explicitly
- Reject invalid transitions
- Log all transitions
- Add state machine diagram to docs

---

### Gotcha: Forgetting to Release Ownership

**Symptom:**
Tasks complete but remain owned, preventing dependencies from running.

**Problem:**
```python
# WRONG - Ownership not cleared on completion
def complete_task(task_id):
    task = read_task(task_id)
    task['state'] = 'completed'
    # ❌ Owner still set!
    write_task(task_id, task)

# Result: Dependent tasks see owner and think it's in progress
```

**Solution:**
```python
# CORRECT - Clear ownership on terminal states
def complete_task(task_id):
    task = read_task(task_id)

    # Verify ownership
    if task['owner'] != agent_id:
        raise ValueError("Not the owner")

    # Update state
    task['state'] = 'completed'
    task['owner'] = None  # ✓ Release ownership
    task['completed_at'] = datetime.utcnow().isoformat()

    write_task_atomic(task_id, task)
```

**Prevention:**
- Clear owner on completed/failed states
- Add assertion in state transition code
- Test dependency execution
- Monitor tasks with owner but terminal state

---

## 3. Dependency Management Issues

### Gotcha: Circular Dependencies Not Detected

**Symptom:**
Tasks wait forever, deadlock, system hangs.

**Problem:**
```python
# WRONG - No cycle detection
manager.create_task('task-A', dependencies=['task-B'])
manager.create_task('task-B', dependencies=['task-A'])

# Result: Neither task can ever run (circular dependency)
```

**Solution:**
```python
# CORRECT - Detect cycles before creating task
def has_circular_dependency(task_id, dependencies, tasks):
    """Check for circular dependencies using DFS"""
    visited = set()

    def visit(current_id):
        if current_id in visited:
            return True  # Cycle detected

        visited.add(current_id)

        # Get dependencies of current task
        current_task = tasks.get(current_id)
        if current_task:
            for dep in current_task.get('dependencies', []):
                if visit(dep):
                    return True

        visited.remove(current_id)
        return False

    # Check each dependency
    for dep in dependencies:
        if dep == task_id:
            return True  # Self-dependency
        if visit(dep):
            return True

    return False

def create_task_with_validation(task_id, dependencies):
    all_tasks = load_all_tasks()

    if has_circular_dependency(task_id, dependencies, all_tasks):
        raise ValueError(f"Circular dependency detected for {task_id}")

    create_task(task_id, dependencies)
```

**Prevention:**
- Validate dependency graph on creation
- Use topological sort
- Visualize dependency graph
- Limit dependency depth

---

### Gotcha: Missing Dependency Not Checked

**Symptom:**
Tasks claim dependencies that don't exist, get stuck in blocked state.

**Problem:**
```python
# WRONG - Doesn't verify dependencies exist
def claim_task(task_id):
    task = read_task(task_id)

    # ❌ Assumes dependencies exist
    if all(is_completed(dep) for dep in task['dependencies']):
        # Claim task...
        pass
```

**Solution:**
```python
# CORRECT - Verify dependencies exist
def can_claim_task(task_id):
    task = read_task(task_id)

    if not task or task['state'] != 'pending':
        return False

    # Check dependencies
    for dep_id in task['dependencies']:
        dep_task = read_task(dep_id)

        if not dep_task:
            logger.error(f"Missing dependency: {dep_id} for task {task_id}")
            # Mark task as failed
            task['state'] = 'failed'
            task['error'] = f"Missing dependency: {dep_id}"
            write_task_atomic(task_id, task)
            return False

        if dep_task['state'] != 'completed':
            return False  # Dependency not ready

    return True
```

**Prevention:**
- Validate dependencies on task creation
- Check dependency existence before claiming
- Handle missing dependencies gracefully
- Monitor failed tasks for missing deps

---

## 4. File System Issues

### Gotcha: NFS File Locking Problems

**Symptom:**
Inconsistent task claiming, corruption, "stale file handle" errors.

**Problem:**
NFS doesn't always guarantee atomic operations or proper locking.

```python
# On NFS, this might not be atomic
os.rename(temp_file, task_file)

# Lock might not work across NFS clients
fcntl.flock(f, fcntl.LOCK_EX)
```

**Solution:**

**Option 1: Use local storage**
```bash
# Mount local SSD for task storage
TASK_STORAGE_PATH="/var/lib/tasks"  # Local, not NFS
```

**Option 2: Use distributed locking**
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def claim_task_with_redis_lock(task_id):
    lock_key = f"task-lock:{task_id}"
    lock_acquired = False

    try:
        # Try to acquire lock (with timeout)
        lock_acquired = redis_client.set(
            lock_key,
            agent_id,
            nx=True,  # Only if not exists
            ex=300    # 5 minute expiry
        )

        if not lock_acquired:
            return False

        # Now safe to claim task
        return claim_task_local(task_id)

    finally:
        if lock_acquired:
            redis_client.delete(lock_key)
```

**Prevention:**
- Prefer local storage for task files
- Use distributed locks for shared storage
- Test on actual deployment file system
- Document NFS limitations

---

### Gotcha: Disk Space Exhaustion

**Symptom:**
Task writes fail, system becomes unusable, data loss.

**Problem:**
```python
# WRONG - No disk space check
def create_task(task_id, data):
    with open(f'tasks/{task_id}.json', 'w') as f:
        json.dump(data, f)  # ❌ Fails silently on disk full
```

**Solution:**
```python
import shutil

def check_disk_space(path, required_mb=100):
    """Check if sufficient disk space available"""
    stat = shutil.disk_usage(path)
    available_mb = stat.free / (1024 * 1024)

    if available_mb < required_mb:
        raise IOError(
            f"Insufficient disk space: {available_mb:.1f}MB available, "
            f"{required_mb}MB required"
        )

def create_task_safe(task_id, data):
    # Check space before writing
    check_disk_space('tasks', required_mb=10)

    try:
        with open(f'tasks/{task_id}.json', 'w') as f:
            json.dump(data, f)
    except IOError as e:
        if 'No space left on device' in str(e):
            logger.critical("Disk full! Cannot create task")
            # Trigger cleanup
            cleanup_old_tasks()
        raise
```

**Prevention:**
- Monitor disk space continuously
- Alert at 80% full
- Implement automatic cleanup
- Archive completed tasks
- Set up log rotation

---

## 5. Performance Issues

### Gotcha: Slow Directory Listing

**Symptom:**
`list_claimable_tasks()` takes seconds, high CPU usage, poor scalability.

**Problem:**
```python
# WRONG - Lists all files every time
def list_claimable_tasks():
    claimable = []

    # ❌ Slow with thousands of files
    for task_file in os.listdir('tasks'):
        if task_file.endswith('.json'):
            task = read_task(task_file[:-5])
            if task['state'] == 'pending':
                claimable.append(task['id'])

    return claimable
```

**Solution:**

**Option 1: Index by state**
```python
# Maintain state index
# tasks/
#   pending/         ← Symlinks to pending tasks
#   in_progress/     ← Symlinks to in-progress tasks
#   completed/       ← Symlinks to completed tasks
#   all/             ← Actual task files

def list_claimable_tasks_fast():
    """List pending tasks using directory index"""
    claimable = []

    for link in os.listdir('tasks/pending'):
        task_id = link[:-5]  # Remove .json
        task = read_task(task_id)

        # Verify still pending (might be stale symlink)
        if task and task['state'] == 'pending':
            claimable.append(task_id)

    return claimable

def update_task_with_index(task_id, new_state):
    """Update task and maintain state index"""
    task = read_task(task_id)
    old_state = task['state']

    # Update task
    task['state'] = new_state
    write_task_atomic(task_id, task)

    # Update symlinks
    old_link = f'tasks/{old_state}/{task_id}.json'
    new_link = f'tasks/{new_state}/{task_id}.json'

    if os.path.exists(old_link):
        os.unlink(old_link)

    os.symlink(f'../all/{task_id}.json', new_link)
```

**Option 2: Use database**
```python
import sqlite3

def init_task_db():
    """Initialize SQLite database for task index"""
    conn = sqlite3.connect('tasks/index.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            owner TEXT,
            priority INTEGER,
            created_at TIMESTAMP,
            claimed_at TIMESTAMP
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_state ON tasks(state)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority DESC)')
    conn.commit()
    return conn

def list_claimable_tasks_db(conn):
    """Fast query using database index"""
    cursor = conn.execute('''
        SELECT task_id
        FROM tasks
        WHERE state = 'pending'
        ORDER BY priority DESC, created_at ASC
        LIMIT 100
    ''')
    return [row[0] for row in cursor.fetchall()]
```

**Prevention:**
- Use indexing for large task counts
- Consider database for >1000 tasks
- Benchmark with realistic data
- Monitor query performance

---

### Gotcha: High Lock Contention

**Symptom:**
Many claim collision errors, low throughput despite many agents.

**Problem:**
```python
# All agents trying to claim same high-priority task
# Timeline:
# Agent 1: Reads task-1 (pending)
# Agent 2: Reads task-1 (pending)
# Agent 3: Reads task-1 (pending)
# Agent 1: Claims task-1 (SUCCESS)
# Agent 2: Tries to claim task-1 (COLLISION)
# Agent 3: Tries to claim task-1 (COLLISION)
# Agents 2&3 retry same task... more collisions
```

**Solution:**

**Option 1: Random selection**
```python
import random

def get_next_task_random(claimable_tasks):
    """Randomly select from top N priority tasks"""
    if not claimable_tasks:
        return None

    # Take top 10 by priority
    top_tasks = claimable_tasks[:10]

    # Random selection reduces contention
    return random.choice(top_tasks)
```

**Option 2: Agent-specific queues**
```python
def get_next_task_sharded(agent_id, claimable_tasks):
    """Partition tasks by agent ID"""
    if not claimable_tasks:
        return None

    # Hash agent ID to determine shard
    agent_hash = hash(agent_id)
    shard_count = 10
    shard_id = agent_hash % shard_count

    # Filter tasks in this shard
    shard_tasks = [
        task_id for task_id in claimable_tasks
        if hash(task_id) % shard_count == shard_id
    ]

    return shard_tasks[0] if shard_tasks else None
```

**Prevention:**
- Add randomness to selection
- Shard tasks across agents
- Monitor collision rate
- Tune retry backoff

---

## 6. Monitoring & Debugging

### Gotcha: No Visibility Into System State

**Symptom:**
Can't diagnose issues, don't know what's happening, blind to problems.

**Problem:**
```python
# WRONG - No logging or metrics
def claim_task(task_id):
    task = read_task(task_id)
    task['state'] = 'in_progress'
    task['owner'] = agent_id
    write_task(task_id, task)
    # ❌ No trace of what happened
```

**Solution:**
```python
import logging
from datetime import datetime

# Structured logging
logger = logging.getLogger(__name__)

def claim_task_observable(task_id):
    start_time = time.time()

    logger.info(
        "task_claim_attempt",
        extra={
            'task_id': task_id,
            'agent_id': agent_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    )

    try:
        task = read_task(task_id)

        # Validate
        if task['state'] != 'pending':
            logger.warning(
                "task_claim_failed",
                extra={
                    'task_id': task_id,
                    'reason': 'not_pending',
                    'current_state': task['state']
                }
            )
            return False

        # Claim
        task['state'] = 'in_progress'
        task['owner'] = agent_id
        write_task_atomic(task_id, task)

        duration = time.time() - start_time
        logger.info(
            "task_claim_success",
            extra={
                'task_id': task_id,
                'duration_ms': duration * 1000
            }
        )

        # Metrics
        metrics.increment('task_claims_success')
        metrics.histogram('task_claim_duration', duration)

        return True

    except Exception as e:
        logger.error(
            "task_claim_error",
            extra={
                'task_id': task_id,
                'error': str(e)
            },
            exc_info=True
        )

        metrics.increment('task_claims_error')
        raise
```

**Key Metrics to Track:**
- Task creation rate
- Claim success/failure rate
- Collision rate
- Average task duration
- Queue depth by priority
- Orphan task count
- Error rate by type

**Prevention:**
- Log all operations
- Use structured logging
- Export metrics to monitoring system
- Create dashboards
- Set up alerts

---

## Quick Reference: Common Error Messages

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `FileExistsError` | Claim collision | Retry with backoff |
| `PermissionError` | Wrong file permissions | Check directory permissions |
| `JSONDecodeError` | Corrupted task file | Restore from backup, validate writes |
| `Invalid transition: X -> Y` | State machine violation | Check transition rules |
| `Not the owner` | Ownership violation | Verify agent claimed task |
| `No space left on device` | Disk full | Clean up old tasks, add storage |
| `Stale file handle` | NFS issue | Use local storage or distributed locks |
| `Task not found` | Race condition or deleted | Handle missing tasks gracefully |

---

**Last Updated:** 2026-02-06
**Contribute:** Found a new gotcha? Document it here!
