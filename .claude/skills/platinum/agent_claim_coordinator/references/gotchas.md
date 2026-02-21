# Agent Claim Coordinator - Gotchas and Troubleshooting

## Overview
This document outlines common pitfalls, gotchas, and troubleshooting tips for the Agent Claim Coordinator skill.

---

## Common Gotchas

### 1. The "Split Brain" Problem
**Problem:** Network partition causes multiple agents to believe they own the same task.
**Symptoms:** Duplicate work occurs when agents can't communicate with coordination service.
**Root Cause:** Lack of strong consistency in distributed locking mechanism.
**Solution:** Use strongly consistent coordination backend (etcd, ZooKeeper) or implement fencing tokens.
**Prevention:** Design for network partitions and implement proper consistency guarantees.

```python
# Gotcha: Weak consistency leading to split brain
def weak_claim_task(task_id, agent_id):
    # Bad: Check then set pattern vulnerable to race conditions
    if get_task_status(task_id) == 'available':
        # Another agent could claim between check and set!
        set_task_status(task_id, 'claimed', owner=agent_id)
        return True
    return False

# Solution: Atomic operation with strong consistency
def strong_claim_task(task_id, agent_id):
    # Good: Atomic compare-and-set operation
    return atomic_claim_with_fencing(task_id, agent_id, fencing_token=time.time())
```

---

### 2. The "Thundering Herd" Anti-Pattern
**Problem:** Many agents simultaneously retry claim operations after a failure.
**Symptoms:** Sudden spike in coordination service load causing cascading failures.
**Root Cause:** Synchronized retry timing without jitter.
**Solution:** Implement exponential backoff with random jitter.
**Prevention:** Always add randomness to retry intervals.

```python
import random
import time

# Gotcha: Synchronized retries
def bad_retry_mechanism():
    for attempt in range(MAX_RETRIES):
        if attempt_claim():
            return True
        time.sleep(BASE_DELAY)  # Same delay for all agents!

# Solution: Jittered retries
def good_retry_mechanism():
    for attempt in range(MAX_RETRIES):
        if attempt_claim():
            return True
        if attempt < MAX_RETRIES - 1:  # Don't sleep on last attempt
            delay = BASE_DELAY * (2 ** attempt)  # Exponential backoff
            jitter = random.uniform(0, delay * 0.1)  # 10% jitter
            time.sleep(delay + jitter)
```

---

### 3. The "Stale Lock" Trap
**Problem:** Crashed agents leave locks that never get released.
**Symptoms:** Tasks remain locked indefinitely, causing resource starvation.
**Root Cause:** No automatic expiration mechanism for locks.
**Solution:** Implement automatic lock expiration with TTL.
**Prevention:** Always set timeouts on distributed locks.

```python
import time

# Gotcha: No expiration on locks
def bad_lock_acquisition(task_id, agent_id):
    # Bad: Lock stays forever if agent crashes
    store.set(f"lock:{task_id}", agent_id)
    return True

# Solution: Time-bounded locks
def good_lock_acquisition(task_id, agent_id, timeout=300):
    # Good: Automatic expiration
    lock_info = {
        'owner': agent_id,
        'acquired_at': time.time(),
        'expires_at': time.time() + timeout,
        'lease_id': generate_unique_id()
    }
    # Store with TTL to ensure automatic cleanup
    store.setex(f"lock:{task_id}", timeout, json.dumps(lock_info))
    return lock_info['lease_id']
```

---

### 4. The "Lease Renewal" Bottleneck
**Problem:** Frequent lease renewal operations overwhelm coordination service.
**Symptoms:** High coordination service load, potential performance degradation.
**Root Cause:** Renewing leases too frequently.
**Solution:** Renew only when approaching expiration and use batch operations.
**Prevention:** Optimize renewal timing based on actual usage patterns.

```python
import threading
import time

class BadLeaseManager:
    def __init__(self):
        self.renewal_threads = {}
    
    # Gotcha: Renewing too frequently
    def start_aggressive_renewal(self, task_id, lease_id):
        def aggressive_renew():
            while True:
                # Renew every 10 seconds regardless of need
                time.sleep(10)
                self.renew_lease(task_id, lease_id)
        
        thread = threading.Thread(target=aggressive_renew, daemon=True)
        thread.start()
        self.renewal_threads[task_id] = thread

class GoodLeaseManager:
    def __init__(self):
        self.renewal_threads = {}
    
    # Solution: Renew only when needed
    def start_efficient_renewal(self, task_id, lease_id, lease_duration):
        def efficient_renew():
            # Renew only when approaching expiration (at 50% of duration)
            sleep_time = lease_duration * 0.5
            while True:
                time.sleep(sleep_time)
                # Check if lease still exists and belongs to us
                if self.verify_lease_ownership(task_id, lease_id):
                    if self.renew_lease(task_id, lease_id):
                        # Renewal successful, continue with same interval
                        continue
                    else:
                        # Renewal failed, stop trying
                        break
                else:
                    # Lease no longer ours, stop renewal
                    break
        
        thread = threading.Thread(target=efficient_renew, daemon=True)
        thread.start()
        self.renewal_threads[task_id] = thread
```

---

### 5. The "Race Condition" During Release
**Problem:** Multiple agents try to release the same lock simultaneously.
**Symptoms:** Inconsistent lock state, potential for double-release.
**Root Cause:** No verification of lock ownership during release.
**Solution:** Verify ownership before releasing the lock.
**Prevention:** Always check ownership before modifying lock state.

```python
# Gotcha: Releasing without ownership verification
def bad_release_lock(task_id, agent_id):
    # Bad: Anyone can release any lock
    store.delete(f"lock:{task_id}")
    return True

# Solution: Verify ownership before release
def good_release_lock(task_id, expected_lease_id):
    # Get current lock info
    lock_data = store.get(f"lock:{task_id}")
    if not lock_data:
        return False  # Lock doesn't exist
    
    lock_info = json.loads(lock_data)
    
    # Verify this agent owns the lock
    if lock_info['lease_id'] != expected_lease_id:
        return False  # Not the owner
    
    # Atomically delete only if still owned by this agent
    return atomic_delete_if_owned(f"lock:{task_id}", expected_lease_id)
```

---

## Troubleshooting Guide

### Issue 1: High Collision Rate
**Symptoms:** Frequent claim failures due to simultaneous attempts.
**Diagnosis Steps:**
1. Check collision detection logs
2. Analyze claim timing patterns
3. Review agent synchronization mechanisms
4. Examine coordination service performance

**Resolution:**
- Implement better jitter in retry mechanisms
- Add more entropy to claim selection
- Consider task batching to reduce contention
- Optimize coordination service performance

### Issue 2: Stale Lock Accumulation
**Symptoms:** Increasing number of locked tasks that aren't being processed.
**Diagnosis Steps:**
1. Check lock expiration settings
2. Review agent crash detection
3. Examine lease renewal mechanisms
4. Analyze system logs for agent failures

**Resolution:**
- Reduce lock timeout values appropriately
- Implement lock cleanup daemon
- Add health checks for active agents
- Implement heartbeat mechanism for agents

### Issue 3: Claim Performance Degradation
**Symptoms:** Slow claim acquisition times affecting overall system performance.
**Diagnosis Steps:**
1. Profile coordination service calls
2. Measure network latency to coordination backend
3. Check coordination service resource utilization
4. Analyze lock contention patterns

**Resolution:**
- Optimize coordination service queries
- Implement caching for frequently accessed locks
- Add connection pooling to coordination service
- Scale coordination service infrastructure

### Issue 4: Agent Eligibility Problems
**Symptoms:** Healthy agents unable to claim tasks or unhealthy agents getting claims.
**Diagnosis Steps:**
1. Check agent health monitoring
2. Review eligibility criteria
3. Examine health status propagation
4. Verify health check accuracy

**Resolution:**
- Improve health check accuracy
- Adjust health check intervals
- Implement more granular health metrics
- Add health status validation

### Issue 5: Network Partition Issues
**Symptoms:** Duplicate claims occurring during network issues.
**Diagnosis Steps:**
1. Check for network partition logs
2. Review consistency model of coordination service
3. Examine partition handling logic
4. Analyze system behavior during network events

**Resolution:**
- Use strongly consistent coordination service
- Implement fencing mechanisms
- Add partition detection and handling
- Design for graceful degradation

---

## Performance Gotchas

### Gotcha 1: Synchronous Lock Operations
**Problem:** Blocking operations for lock acquisition affecting throughput.
**Impact:** Severe performance degradation under load.
**Solution:** Use asynchronous operations and non-blocking I/O.

```python
# Bad: Synchronous blocking
def synchronous_claim(task_id, agent_id):
    # Blocks entire thread waiting for lock
    result = coordination_service.acquire_lock(task_id, agent_id)
    return result

# Good: Asynchronous operations
async def asynchronous_claim(task_id, agent_id):
    # Doesn't block the event loop
    result = await coordination_service.acquire_lock_async(task_id, agent_id)
    return result
```

### Gotcha 2: Inefficient Lock Key Design
**Problem:** Poor key structure causing hotspots in coordination service.
**Impact:** Uneven load distribution on coordination backend.
**Solution:** Design keys to distribute load evenly.

```python
# Bad: Sequential keys causing hotspots
def bad_key_design(task_id):
    # All tasks in sequence will hit same shard
    return f"lock:{task_id}"

# Good: Distributed keys
def good_key_design(task_id):
    # Distribute based on hash to spread load
    shard = hash(task_id) % NUM_SHARDS
    return f"lock:shard_{shard}:{task_id}"
```

---

## Configuration Gotchas

### Gotcha 1: Incorrect Timeout Values
**Problem:** Timeouts too short cause false failures; too long cause slow recovery.
**Solution:** Set timeouts based on actual system measurements.

```yaml
# Bad: Arbitrary timeout values
locking:
  claim_timeout_seconds: 1    # Too short for complex tasks
  lease_duration_seconds: 3600  # Too long, causing stale locks
  renewal_interval_seconds: 1800  # Half of lease, too conservative

# Good: Measured timeout values
locking:
  claim_timeout_seconds: 30   # Based on 99th percentile coordination time
  lease_duration_seconds: 300  # Balanced for task completion time
  renewal_interval_seconds: 120  # Renew well before expiration
```

### Gotcha 2: Static Retry Parameters
**Problem:** Fixed retry counts don't adapt to changing system conditions.
**Solution:** Dynamically adjust retry parameters based on system load.

```python
class AdaptiveRetryManager:
    def __init__(self):
        self.base_retry_count = 3
        self.current_backlog = 0
    
    def get_retry_params(self):
        # Adjust based on system conditions
        if self.current_backlog > HIGH_THRESHOLD:
            # More retries during high contention
            return {
                'max_retries': self.base_retry_count * 2,
                'base_delay': 2.0
            }
        else:
            # Normal parameters
            return {
                'max_retries': self.base_retry_count,
                'base_delay': 1.0
            }
```

---

## Monitoring Gotchas

### Gotcha 1: Missing Critical Metrics
**Problem:** Not tracking metrics that matter for claim effectiveness.
**Solution:** Monitor both system-level and claim-specific metrics.

```python
# Track these critical metrics:
class ClaimMetrics:
    def __init__(self):
        self.claim_attempts = 0
        self.claim_successes = 0
        self.collisions_detected = 0
        self.stale_locks_found = 0
        self.average_claim_time = []  # Rolling average
        self.lock_contestation_rate = 0.0
```

### Gotcha 2: Alerting on Wrong Indicators
**Problem:** Alerts trigger for non-actionable issues or miss critical problems.
**Solution:** Focus alerts on actionable metrics that indicate real problems.

```python
# Bad: Alert on every minor fluctuation
ALERT_IF: claim_collision_rate > 0.01  # Too sensitive

# Good: Alert on meaningful indicators
ALERT_IF: (
    claim_collision_rate > 0.1 AND    # High collision rate
    consecutive_minutes > 5 AND       # Sustained for 5+ minutes
    system_load > 0.7                 # System is under load
)
```

---

## Security Gotchas

### Gotcha 1: Insufficient Authentication
**Problem:** Weak authentication allows unauthorized claim attempts.
**Solution:** Implement strong authentication and authorization.

```python
# Bad: No authentication
def claim_task_no_auth(task_id, agent_id):
    # Anyone can claim anything
    return attempt_claim(task_id, agent_id)

# Good: Strong authentication
def claim_task_with_auth(task_id, agent_id, auth_token):
    # Verify token authenticity
    if not verify_auth_token(auth_token, agent_id):
        raise UnauthorizedAccessError()
    
    # Validate agent permissions
    if not has_claim_permission(agent_id, task_id):
        raise PermissionDeniedError()
    
    return attempt_claim(task_id, agent_id)
```

### Gotcha 2: Information Disclosure
**Problem:** Exposing sensitive information in claim logs.
**Solution:** Sanitize logs and metrics of sensitive data.

```python
# Bad: Logging sensitive information
def log_claim_attempt(task_id, agent_id, task_details):
    logger.info(f"Agent {agent_id} claiming task {task_id} with details {task_details}")

# Good: Sanitized logging
def log_claim_attempt_sanitized(task_id, agent_id, task_details):
    # Log only non-sensitive information
    logger.info(f"Agent {agent_id} claiming task {task_id}")
    # Don't log task_details which might contain sensitive data
```

---

## Testing Gotchas

### Gotcha 1: Not Testing Failure Scenarios
**Problem:** Code works in ideal conditions but fails during actual failures.
**Solution:** Test failure scenarios extensively.

```python
# Test failure scenarios
def test_network_partition_handling(self):
    # Setup: Create claim coordinator with 3 agents
    coordinator = ClaimCoordinator(agents=['agent1', 'agent2', 'agent3'])
    
    # Simulate network partition affecting agent2
    coordinator.simulate_network_partition('agent2')
    
    # Agent 1 and 3 should still be able to coordinate
    claim1 = coordinator.claim_task('task1', 'agent1')
    claim3 = coordinator.claim_task('task3', 'agent3')
    
    # Verify claims succeeded for connected agents
    assert claim1.success
    assert claim3.success
    
    # Verify agent2 couldn't claim anything during partition
    claim2 = coordinator.claim_task('task2', 'agent2')
    assert not claim2.success  # Should fail during partition
    
    # After partition heals, agent2 should be able to claim
    coordinator.heal_network_partition('agent2')
    claim2_retry = coordinator.claim_task('task4', 'agent2')
    assert claim2_retry.success
```

### Gotcha 2: Not Testing High Contention
**Problem:** Code works with few agents but fails under high contention.
**Solution:** Test with many concurrent agents.

```python
def test_high_contention_scenario(self):
    # Test with many agents competing for few tasks
    coordinator = ClaimCoordinator(agents=[f'agent{i}' for i in range(50)])
    
    # Create few tasks to increase contention
    tasks = [f'task{i}' for i in range(5)]
    
    # Run many concurrent claim attempts
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for _ in range(200):  # 200 claim attempts
            for task in tasks:
                future = executor.submit(coordinator.claim_task, task, random.choice(coordinator.agents))
                futures.append(future)
        
        # Wait for all attempts
        results = [f.result() for f in futures]
        
        # Verify only one agent claimed each task (no duplicates)
        claimed_tasks = {}
        for result in results:
            if result.success:
                if result.task_id in claimed_tasks:
                    assert False, f"Task {result.task_id} claimed twice!"
                claimed_tasks[result.task_id] = result.agent_id
```

---

## Operational Gotchas

### Gotcha 1: Manual Intervention Complexity
**Problem:** When things go wrong, difficult to manually fix state.
**Solution:** Provide administrative tools for manual intervention.

```python
class AdministrativeTools:
    def force_release_lock(self, task_id, reason="admin_override"):
        """Force release a lock for operational purposes."""
        lock_info = self.get_lock_info(task_id)
        if lock_info:
            logger.warning(f"Admin: Forcing release of lock for task {task_id} "
                          f"previously held by {lock_info['owner']}. Reason: {reason}")
            return self.release_lock_force(task_id)
        return False
    
    def list_stale_locks(self, age_threshold_minutes=60):
        """List locks older than threshold for cleanup."""
        stale_locks = []
        for task_id, lock_info in self.all_locks.items():
            if time.time() - lock_info['acquired_at'] > age_threshold_minutes * 60:
                stale_locks.append({
                    'task_id': task_id,
                    'holder': lock_info['owner'],
                    'age_minutes': (time.time() - lock_info['acquired_at']) / 60
                })
        return stale_locks
```

---

**Last Updated:** 2026-02-07