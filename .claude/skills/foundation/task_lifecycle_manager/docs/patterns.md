# Task Lifecycle Manager - Common Patterns

## Overview
This document describes common integration patterns for the Task Lifecycle Manager across different use cases and architectures.

---

## Pattern 1: Worker Pool with Task Queue

### Use Case
Multiple worker agents process tasks from a shared queue with automatic load balancing.

### Implementation

```python
from task_lifecycle_manager import TaskLifecycleManager, TaskState
import time
import logging

logger = logging.getLogger(__name__)


class WorkerAgent:
    """Worker agent that processes tasks from queue"""

    def __init__(self, agent_id: str, task_manager: TaskLifecycleManager):
        self.agent_id = agent_id
        self.task_manager = task_manager
        self.running = True

    def process_task(self, task_id: str):
        """Process a single task"""
        logger.info(f"Processing task: {task_id}")

        try:
            # Simulate work
            time.sleep(2)

            # Mark as completed
            self.task_manager.transition_task(task_id, TaskState.COMPLETED)
            logger.info(f"Completed task: {task_id}")

        except Exception as e:
            logger.error(f"Failed to process task {task_id}: {e}")
            self.task_manager.transition_task(task_id, TaskState.FAILED)

    def run(self):
        """Main worker loop"""
        logger.info(f"Worker {self.agent_id} started")

        while self.running:
            # Get claimable tasks
            claimable_tasks = self.task_manager.list_claimable_tasks()

            if not claimable_tasks:
                logger.debug("No tasks available, waiting...")
                time.sleep(5)
                continue

            # Try to claim first available task
            for task_id in claimable_tasks:
                if self.task_manager.claim_task(task_id):
                    logger.info(f"Claimed task: {task_id}")
                    self.process_task(task_id)
                    break
            else:
                # All claims failed (collision), retry
                logger.debug("Failed to claim any task, retrying...")
                time.sleep(1)

    def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info(f"Worker {self.agent_id} stopped")


# Usage
manager = TaskLifecycleManager(storage_path="./tasks")

# Start multiple workers
import threading

workers = []
for i in range(5):
    worker = WorkerAgent(f"worker-{i}", manager)
    thread = threading.Thread(target=worker.run)
    thread.start()
    workers.append((worker, thread))

# Let them run
time.sleep(60)

# Stop workers
for worker, thread in workers:
    worker.stop()
    thread.join()
```

---

## Pattern 2: Task Dependencies and DAG Execution

### Use Case
Execute tasks in dependency order (Directed Acyclic Graph).

### Implementation

```python
from typing import List, Set
from collections import defaultdict, deque


class DAGTaskExecutor:
    """Execute tasks respecting dependency graph"""

    def __init__(self, task_manager: TaskLifecycleManager):
        self.task_manager = task_manager

    def create_task_dag(self, task_definitions: List[dict]):
        """
        Create tasks with dependencies

        task_definitions: [
            {'id': 'task-1', 'priority': 10, 'dependencies': []},
            {'id': 'task-2', 'priority': 5, 'dependencies': ['task-1']},
            {'id': 'task-3', 'priority': 5, 'dependencies': ['task-1']},
            {'id': 'task-4', 'priority': 1, 'dependencies': ['task-2', 'task-3']},
        ]
        """
        for task_def in task_definitions:
            self.task_manager.create_task(
                task_id=task_def['id'],
                priority=task_def.get('priority', 0),
                dependencies=task_def.get('dependencies', []),
                tags=task_def.get('tags', [])
            )

    def get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute (all dependencies met)"""
        ready_tasks = []

        for task_id in self.task_manager.list_claimable_tasks():
            task_status = self.task_manager.get_task_status(task_id)

            if task_status and task_status['state'] == 'pending':
                # Check if all dependencies are completed
                dependencies = task_status['dependencies']
                if all(self.task_manager.is_task_completed(dep) for dep in dependencies):
                    ready_tasks.append(task_id)

        return ready_tasks

    def execute_dag(self, max_workers: int = 5):
        """Execute all tasks in dependency order"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        def process_task(task_id: str) -> bool:
            """Process a single task"""
            if not self.task_manager.claim_task(task_id):
                return False

            try:
                # Simulate work
                print(f"Processing {task_id}...")
                time.sleep(2)

                # Complete task
                self.task_manager.transition_task(task_id, TaskState.COMPLETED)
                print(f"✓ Completed {task_id}")
                return True

            except Exception as e:
                print(f"✗ Failed {task_id}: {e}")
                self.task_manager.transition_task(task_id, TaskState.FAILED)
                return False

        # Execute tasks
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while True:
                ready_tasks = self.get_ready_tasks()

                if not ready_tasks:
                    # Check if all tasks are done
                    all_tasks = list(self.task_manager.storage_path.glob("*.json"))
                    pending = [t for t in all_tasks if self.task_manager._read_task(t.stem).state == TaskState.PENDING]

                    if not pending:
                        print("All tasks completed!")
                        break

                    # Wait for dependencies to complete
                    print("Waiting for dependencies...")
                    time.sleep(2)
                    continue

                # Submit ready tasks
                futures = {executor.submit(process_task, task_id): task_id for task_id in ready_tasks}

                # Wait for at least one to complete
                for future in as_completed(futures):
                    task_id = futures[future]
                    future.result()


# Usage
manager = TaskLifecycleManager(storage_path="./tasks")
executor = DAGTaskExecutor(manager)

# Define task DAG
task_dag = [
    {'id': 'build', 'priority': 10, 'dependencies': []},
    {'id': 'test-unit', 'priority': 8, 'dependencies': ['build']},
    {'id': 'test-integration', 'priority': 8, 'dependencies': ['build']},
    {'id': 'deploy-staging', 'priority': 5, 'dependencies': ['test-unit', 'test-integration']},
    {'id': 'smoke-test', 'priority': 3, 'dependencies': ['deploy-staging']},
    {'id': 'deploy-prod', 'priority': 1, 'dependencies': ['smoke-test']},
]

# Create and execute
executor.create_task_dag(task_dag)
executor.execute_dag(max_workers=3)
```

---

## Pattern 3: Priority-Based Task Scheduling

### Use Case
High-priority tasks are processed before low-priority tasks.

### Implementation

```python
import heapq
from typing import Tuple


class PriorityTaskScheduler:
    """Schedule tasks based on priority"""

    def __init__(self, task_manager: TaskLifecycleManager):
        self.task_manager = task_manager

    def get_next_task(self) -> Optional[str]:
        """Get highest priority claimable task"""
        claimable = self.task_manager.list_claimable_tasks()

        if not claimable:
            return None

        # Already sorted by priority (highest first)
        return claimable[0]

    def schedule_tasks(self, task_list: List[Tuple[str, int]]):
        """
        Schedule tasks with priorities

        task_list: [(task_id, priority), ...]
        Higher priority = processed first
        """
        for task_id, priority in task_list:
            self.task_manager.create_task(
                task_id=task_id,
                priority=priority,
                tags=['scheduled']
            )

    def run_scheduler(self, worker_count: int = 3):
        """Run scheduler with multiple workers"""
        from concurrent.futures import ThreadPoolExecutor
        import time

        def worker():
            while True:
                task_id = self.get_next_task()

                if not task_id:
                    time.sleep(1)
                    continue

                if self.task_manager.claim_task(task_id):
                    print(f"Processing priority task: {task_id}")
                    time.sleep(2)  # Simulate work
                    self.task_manager.transition_task(task_id, TaskState.COMPLETED)

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            for _ in range(worker_count):
                executor.submit(worker)


# Usage
manager = TaskLifecycleManager(storage_path="./tasks")
scheduler = PriorityTaskScheduler(manager)

# Schedule tasks with different priorities
scheduler.schedule_tasks([
    ('urgent-bug-fix', 100),
    ('feature-request', 50),
    ('documentation', 10),
    ('refactoring', 5),
])
```

---

## Pattern 4: Task Retry with Exponential Backoff

### Use Case
Automatically retry failed tasks with increasing delays.

### Implementation

```python
import time
import math


class TaskRetryHandler:
    """Handle task retries with exponential backoff"""

    def __init__(self, task_manager: TaskLifecycleManager):
        self.task_manager = task_manager

    def process_with_retry(
        self,
        task_id: str,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> bool:
        """
        Process task with automatic retry on failure

        Exponential backoff: delay = base_delay * (2 ^ attempt)
        """
        for attempt in range(max_retries):
            try:
                # Claim task
                if not self.task_manager.claim_task(task_id):
                    print(f"Failed to claim {task_id}")
                    return False

                # Process task
                print(f"Processing {task_id} (attempt {attempt + 1}/{max_retries})")
                self._do_work(task_id)

                # Success
                self.task_manager.transition_task(task_id, TaskState.COMPLETED)
                print(f"✓ Completed {task_id}")
                return True

            except Exception as e:
                print(f"✗ Attempt {attempt + 1} failed: {e}")

                # Mark as failed
                self.task_manager.transition_task(task_id, TaskState.FAILED)

                if attempt < max_retries - 1:
                    # Reset to pending for retry
                    self.task_manager.transition_task(task_id, TaskState.PENDING)

                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    print(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"✗ All retries exhausted for {task_id}")
                    return False

        return False

    def _do_work(self, task_id: str):
        """Simulate work that might fail"""
        import random
        if random.random() < 0.3:  # 30% failure rate
            raise RuntimeError("Simulated failure")
        time.sleep(1)


# Usage
manager = TaskLifecycleManager(storage_path="./tasks")
retry_handler = TaskRetryHandler(manager)

manager.create_task("flaky-task-1", tags=["retry"])
retry_handler.process_with_retry("flaky-task-1", max_retries=5, base_delay=2.0)
```

---

## Pattern 5: Task Timeout and Orphan Recovery

### Use Case
Detect and recover orphaned tasks from crashed agents.

### Implementation

```python
import time
from datetime import datetime, timedelta


class OrphanTaskRecovery:
    """Recover orphaned tasks from crashed agents"""

    def __init__(self, task_manager: TaskLifecycleManager, timeout: int = 300):
        self.task_manager = task_manager
        self.timeout = timeout  # 5 minutes default

    def find_orphaned_tasks(self) -> List[str]:
        """Find tasks with stale locks"""
        orphaned = []
        now = time.time()

        for task_file in self.task_manager.storage_path.glob("*.json"):
            task_id = task_file.stem
            metadata = self.task_manager._read_task(task_id)

            if not metadata:
                continue

            # Check for stale locks
            if (metadata.state == TaskState.IN_PROGRESS and
                metadata.owner and
                metadata.claimed_at):

                elapsed = now - metadata.claimed_at

                if elapsed > self.timeout:
                    orphaned.append({
                        'task_id': task_id,
                        'owner': metadata.owner,
                        'elapsed': elapsed,
                        'claimed_at': metadata.claimed_timestamp
                    })

        return orphaned

    def recover_orphaned_tasks(self, auto_reset: bool = True) -> int:
        """Recover orphaned tasks"""
        orphaned = self.find_orphaned_tasks()
        recovered = 0

        for orphan in orphaned:
            task_id = orphan['task_id']
            print(f"Found orphaned task: {task_id} (owner: {orphan['owner']}, "
                  f"elapsed: {orphan['elapsed']:.0f}s)")

            if auto_reset:
                # Reset to pending
                metadata = self.task_manager._read_task(task_id)
                metadata.state = TaskState.PENDING
                metadata.owner = None
                metadata.history.append({
                    'action': 'orphan_recovery',
                    'from': 'in_progress',
                    'to': 'pending',
                    'timestamp': datetime.utcnow().isoformat(),
                    'recovered_from': orphan['owner'],
                    'elapsed_seconds': orphan['elapsed']
                })

                if self.task_manager._write_task_atomic(task_id, metadata):
                    print(f"  ✓ Recovered {task_id}")
                    recovered += 1
                else:
                    print(f"  ✗ Failed to recover {task_id}")

        return recovered

    def run_recovery_daemon(self, interval: int = 60):
        """Run orphan recovery as background daemon"""
        print(f"Starting orphan recovery daemon (interval: {interval}s)")

        while True:
            try:
                recovered = self.recover_orphaned_tasks(auto_reset=True)
                if recovered > 0:
                    print(f"Recovered {recovered} orphaned tasks")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("Stopping recovery daemon")
                break
            except Exception as e:
                print(f"Recovery error: {e}")
                time.sleep(interval)


# Usage
manager = TaskLifecycleManager(storage_path="./tasks")
recovery = OrphanTaskRecovery(manager, timeout=300)

# Run as daemon
import threading
daemon_thread = threading.Thread(target=recovery.run_recovery_daemon, args=(60,))
daemon_thread.daemon = True
daemon_thread.start()

# Or run manually
orphaned = recovery.find_orphaned_tasks()
print(f"Found {len(orphaned)} orphaned tasks")
recovered = recovery.recover_orphaned_tasks(auto_reset=True)
print(f"Recovered {recovered} tasks")
```

---

## Pattern 6: Task Progress Tracking

### Use Case
Track fine-grained progress within a long-running task.

### Implementation

```python
class ProgressTracker:
    """Track progress of long-running tasks"""

    def __init__(self, task_manager: TaskLifecycleManager):
        self.task_manager = task_manager

    def update_progress(
        self,
        task_id: str,
        progress: float,
        message: str = ""
    ):
        """Update task progress (0.0 to 1.0)"""
        metadata = self.task_manager._read_task(task_id)

        if not metadata:
            raise ValueError(f"Task {task_id} not found")

        # Add progress metadata
        if not hasattr(metadata, 'progress'):
            metadata.progress = []

        metadata.progress.append({
            'percent': progress * 100,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })

        self.task_manager._write_task_atomic(task_id, metadata)

    def get_progress(self, task_id: str) -> Optional[float]:
        """Get current progress percentage"""
        metadata = self.task_manager._read_task(task_id)

        if not metadata or not hasattr(metadata, 'progress'):
            return None

        if metadata.progress:
            return metadata.progress[-1]['percent'] / 100.0

        return None

    def process_with_progress(self, task_id: str, steps: List[str]):
        """Process task with progress updates"""
        if not self.task_manager.claim_task(task_id):
            print(f"Failed to claim {task_id}")
            return False

        try:
            total_steps = len(steps)

            for i, step in enumerate(steps):
                print(f"[{i+1}/{total_steps}] {step}")

                # Update progress
                progress = (i + 1) / total_steps
                self.update_progress(task_id, progress, step)

                # Simulate work
                time.sleep(1)

            # Complete
            self.task_manager.transition_task(task_id, TaskState.COMPLETED)
            return True

        except Exception as e:
            print(f"Error: {e}")
            self.task_manager.transition_task(task_id, TaskState.FAILED)
            return False


# Usage
manager = TaskLifecycleManager(storage_path="./tasks")
tracker = ProgressTracker(manager)

manager.create_task("long-task", tags=["progress-tracking"])

steps = [
    "Initializing environment",
    "Loading data",
    "Processing batch 1",
    "Processing batch 2",
    "Processing batch 3",
    "Finalizing results"
]

tracker.process_with_progress("long-task", steps)
```

---

## Pattern 7: Task Cancellation

### Use Case
Allow tasks to be cancelled while in progress.

### Implementation

```python
class TaskCancellationHandler:
    """Handle task cancellation"""

    def __init__(self, task_manager: TaskLifecycleManager):
        self.task_manager = task_manager
        self.cancellation_requests = set()

    def request_cancellation(self, task_id: str):
        """Request task cancellation"""
        self.cancellation_requests.add(task_id)
        print(f"Cancellation requested for {task_id}")

    def is_cancelled(self, task_id: str) -> bool:
        """Check if task is cancelled"""
        return task_id in self.cancellation_requests

    def process_with_cancellation(self, task_id: str):
        """Process task with cancellation support"""
        if not self.task_manager.claim_task(task_id):
            return False

        try:
            for i in range(10):
                # Check for cancellation
                if self.is_cancelled(task_id):
                    print(f"Task {task_id} cancelled by user")
                    self.task_manager.transition_task(task_id, TaskState.FAILED)
                    self.cancellation_requests.remove(task_id)
                    return False

                print(f"Processing step {i+1}/10")
                time.sleep(1)

            # Complete
            self.task_manager.transition_task(task_id, TaskState.COMPLETED)
            return True

        except Exception as e:
            print(f"Error: {e}")
            self.task_manager.transition_task(task_id, TaskState.FAILED)
            return False


# Usage
manager = TaskLifecycleManager(storage_path="./tasks")
cancellation = TaskCancellationHandler(manager)

manager.create_task("cancellable-task")

# Start processing in background
import threading
thread = threading.Thread(target=cancellation.process_with_cancellation, args=("cancellable-task",))
thread.start()

# Cancel after 3 seconds
time.sleep(3)
cancellation.request_cancellation("cancellable-task")
thread.join()
```

---

## Best Practices Summary

1. **Always Use Atomic Operations** - Use atomic file operations to prevent corruption
2. **Implement Retry Logic** - Retry task claims with exponential backoff
3. **Track Task History** - Maintain audit trail for debugging and accountability
4. **Handle Orphaned Tasks** - Implement recovery for crashed agents
5. **Validate State Transitions** - Enforce valid state machine transitions
6. **Use Priority Scheduling** - Process high-priority tasks first
7. **Respect Dependencies** - Execute tasks in correct order (DAG)
8. **Monitor Performance** - Track claim rates, collision rates, task duration
9. **Implement Timeouts** - Detect and recover stale locks
10. **Test Concurrency** - Verify behavior under high contention

---

**Last Updated:** 2026-02-06
