# Task Lifecycle Manager Skill

**Domain:** `foundation`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

This skill provides comprehensive task lifecycle management with atomic operations, preventing race conditions and ensuring data consistency in multi-agent environments.

### Prerequisites

```bash
# Set required environment variables
export TASK_STORAGE_PATH="./tasks"
export AGENT_ID="agent-$(hostname)-$$"
export TASK_LOCK_TIMEOUT="300"

# Optional
export TASK_CLAIM_RETRY_COUNT="3"
export TASK_AUDIT_LOG="task-audit.log"
```

### Basic Usage

**Python:**
```python
from task_lifecycle_manager import TaskLifecycleManager, TaskState

# Initialize
manager = TaskLifecycleManager(storage_path="./tasks")

# Create task
manager.create_task("my-task", priority=10, tags=["urgent"])

# Claim task
if manager.claim_task("my-task"):
    print("Task claimed successfully")

    # Do work...

    # Complete task
    manager.transition_task("my-task", TaskState.COMPLETED)
```

**Shell:**
```bash
# Claim task
./assets/task-claim-template.sh my-task

# Transition state
./assets/task-transition-template.sh my-task completed
```

## Documentation Structure

- **[SKILL.md](./SKILL.md)** - Complete skill specification with blueprints and anti-patterns
- **[docs/patterns.md](./docs/patterns.md)** - Common integration patterns (7 examples)
- **[docs/impact-checklist.md](./docs/impact-checklist.md)** - System impact assessment (100+ items)
- **[docs/gotchas.md](./docs/gotchas.md)** - Common pitfalls and troubleshooting (20+ issues)

## Asset Templates

All templates use atomic operations to prevent race conditions:

- `assets/task-claim-template.sh` - Bash script for atomic task claiming
- `assets/task-transition-template.sh` - Bash script for safe state transitions
- `assets/task_lifecycle_manager.py` - Python class with full lifecycle management

## Key Features

✅ **Atomic Operations**
- File-based atomic rename for consistency
- No partial state writes
- Collision detection and retry logic
- Backup and rollback on failure

✅ **State Machine Validation**
- Enforces valid state transitions
- Prevents invalid workflows
- History tracking for audit trail
- Terminal state handling

✅ **Concurrency Safe**
- Multiple agents can work concurrently
- Collision detection prevents duplicate claims
- Stale lock recovery for crashed agents
- Ownership verification on all operations

✅ **Production Ready**
- Comprehensive error handling
- Audit logging for all operations
- Retry logic with exponential backoff
- Orphan task recovery

## State Machine

Valid transitions:
```
pending → in_progress → completed
                     → failed
                     → blocked → in_progress
failed → pending (retry)
```

## Common Patterns

### Pattern 1: Worker Pool
```python
while True:
    tasks = manager.list_claimable_tasks()

    for task_id in tasks:
        if manager.claim_task(task_id):
            process_task(task_id)
            manager.transition_task(task_id, TaskState.COMPLETED)
            break

    time.sleep(1)
```

### Pattern 2: Dependency DAG
```python
# Create tasks with dependencies
manager.create_task("build", priority=10)
manager.create_task("test", dependencies=["build"])
manager.create_task("deploy", dependencies=["test"])

# Only claimable when dependencies complete
claimable = manager.list_claimable_tasks()  # Returns ["build"]
```

### Pattern 3: Orphan Recovery
```python
from orphan_recovery import OrphanTaskRecovery

recovery = OrphanTaskRecovery(manager, timeout=300)
orphaned = recovery.find_orphaned_tasks()
recovered = recovery.recover_orphaned_tasks(auto_reset=True)
```

## Anti-Patterns to Avoid

❌ Non-atomic file operations
❌ Check-then-act race conditions
❌ Ignoring stale locks
❌ Invalid state transitions
❌ No audit logging

See [SKILL.md](./SKILL.md#anti-patterns) for detailed examples.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Claim collisions | Increase retry count, add jitter |
| Orphaned tasks | Enable auto-recovery, check lock timeout |
| State corruption | Verify atomic operations, check disk space |
| Performance issues | Use indexing, shard tasks across agents |

See [gotchas.md](./docs/gotchas.md) for comprehensive troubleshooting.

## Monitoring

Key metrics to track:
- Task claim success/failure rate
- Collision rate
- Task completion rate
- Average task duration
- Orphan task count
- State transition errors

## Architecture

```
task_lifecycle_manager/
├── SKILL.md                           # Main specification
├── README.md                          # This file
├── assets/                            # Reusable templates
│   ├── task-claim-template.sh        # Atomic claim script
│   ├── task-transition-template.sh   # Safe transition script
│   └── task_lifecycle_manager.py     # Python module
└── docs/                              # Supporting documentation
    ├── patterns.md                    # Integration patterns
    ├── impact-checklist.md            # System impact assessment
    └── gotchas.md                     # Troubleshooting guide
```

## Best Practices

1. **Always use atomic operations** - Prevents race conditions
2. **Implement retry logic** - Handle transient failures
3. **Track history** - Maintain audit trail
4. **Handle orphans** - Implement recovery for crashed agents
5. **Validate transitions** - Enforce state machine
6. **Monitor metrics** - Track performance and errors
7. **Test concurrency** - Verify behavior with multiple agents
8. **Use dependencies** - Express task relationships
9. **Set priorities** - Control execution order
10. **Log everything** - Enable debugging and accountability

## Requirements

- **Python 3.7+** (for dataclasses)
- **jq** (for bash scripts)
- **POSIX file system** (for atomic rename)
- **Sufficient disk space** (for task files and logs)

## Performance

Typical operation latencies:
- Task creation: < 10ms
- Task claim: < 100ms
- State transition: < 50ms
- List tasks: < 200ms (depends on task count)

Scalability:
- Tested with 10,000+ tasks
- Supports 100+ concurrent agents
- Use database indexing for >10,000 tasks

## Support

For issues, questions, or contributions:
1. Check [gotchas.md](./docs/gotchas.md) for known problems
2. Review [patterns.md](./docs/patterns.md) for usage examples
3. Complete [impact-checklist.md](./docs/impact-checklist.md) for deployment review
4. Consult main [SKILL.md](./SKILL.md) for complete reference

---

**Maintained by:** Foundation Team
**Last Updated:** 2026-02-06
**License:** Internal Use Only
