# Agent Claim Coordinator - Common Patterns

## Overview
This document describes common integration patterns for the Agent Claim Coordinator across different use cases and architectures.

---

## Pattern 1: Distributed Lock Acquisition

### Use Case
Multiple agents compete to claim the same task with distributed lock coordination.

### Implementation

```python
import time
import uuid
import json
from typing import Optional, Dict, Any


class DistributedLockManager:
    """Manage distributed locks for task claims"""

    def __init__(self, backend_client, namespace="claims"):
        self.backend = backend_client
        self.namespace = namespace

    def acquire_lock(self, task_id: str, agent_id: str, timeout: int = 300) -> Optional[str]:
        """
        Attempt to acquire a distributed lock for a task.
        
        Args:
            task_id: The task to claim
            agent_id: The agent requesting the claim
            timeout: Lock timeout in seconds
            
        Returns:
            Lock ID if successful, None if failed
        """
        lock_key = f"{self.namespace}:{task_id}"
        lock_id = str(uuid.uuid4())
        
        # Create lock information
        lock_info = {
            "agent_id": agent_id,
            "lock_id": lock_id,
            "acquired_at": time.time(),
            "expires_at": time.time() + timeout
        }
        
        # Attempt atomic lock acquisition
        # This simulates a Redis SET command with NX (not exists) and EX (expire) options
        success = self.backend.set_if_not_exists(
            lock_key, 
            json.dumps(lock_info), 
            expire_time=timeout
        )
        
        return lock_id if success else None

    def release_lock(self, task_id: str, lock_id: str) -> bool:
        """
        Release a distributed lock if the caller owns it.
        
        Args:
            task_id: The task to release
            lock_id: The lock ID to verify ownership
            
        Returns:
            True if successfully released, False otherwise
        """
        lock_key = f"{self.namespace}:{task_id}"
        
        # Get current lock info
        current_lock_data = self.backend.get(lock_key)
        if not current_lock_data:
            return False  # No lock exists
        
        current_lock = json.loads(current_lock_data)
        
        # Verify lock ownership
        if current_lock["lock_id"] != lock_id:
            return False  # Not the owner
        
        # Delete the lock
        self.backend.delete(lock_key)
        return True

    def renew_lock(self, task_id: str, lock_id: str, extension: int = 300) -> bool:
        """
        Renew an existing lock to extend its lifetime.
        
        Args:
            task_id: The task whose lock to renew
            lock_id: The lock ID to verify ownership
            extension: Additional seconds to extend the lock
            
        Returns:
            True if successfully renewed, False otherwise
        """
        lock_key = f"{self.namespace}:{task_id}"
        
        # Get current lock info
        current_lock_data = self.backend.get(lock_key)
        if not current_lock_data:
            return False  # No lock exists
        
        current_lock = json.loads(current_lock_data)
        
        # Verify lock ownership
        if current_lock["lock_id"] != lock_id:
            return False  # Not the owner
        
        # Update expiration time
        current_lock["expires_at"] = time.time() + extension
        
        # Set with new expiration
        self.backend.setex(
            lock_key,
            extension,
            json.dumps(current_lock)
        )
        
        return True


# Usage example
class MockBackend:
    """Mock backend for demonstration purposes"""
    
    def __init__(self):
        self.data = {}
    
    def set_if_not_exists(self, key, value, expire_time):
        if key not in self.data:
            self.data[key] = value
            return True
        return False
    
    def get(self, key):
        return self.data.get(key)
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def setex(self, key, expire_time, value):
        self.data[key] = value


# Example usage
backend = MockBackend()
lock_manager = DistributedLockManager(backend)

# Agent 1 tries to claim task
agent1_lock = lock_manager.acquire_lock("task-123", "agent-1", timeout=300)
print(f"Agent 1 lock acquired: {agent1_lock is not None}")

# Agent 2 tries to claim the same task
agent2_lock = lock_manager.acquire_lock("task-123", "agent-2", timeout=300)
print(f"Agent 2 lock acquired: {agent2_lock is not None}")

# Agent 1 releases the lock
if agent1_lock:
    released = lock_manager.release_lock("task-123", agent1_lock)
    print(f"Agent 1 lock released: {released}")
```

---

## Pattern 2: Retry with Exponential Backoff

### Use Case
Handle claim collisions with intelligent retry logic to reduce contention.

### Implementation

```python
import random
import time
from typing import Callable, Any


class RetryClaimManager:
    """Manage claim attempts with exponential backoff"""

    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def attempt_claim_with_retry(
        self,
        claim_func: Callable[[str, str], Any],
        task_id: str,
        agent_id: str
    ) -> Any:
        """
        Attempt to claim a task with exponential backoff retry logic.
        
        Args:
            claim_func: Function that attempts the claim (returns truthy on success)
            task_id: The task to claim
            agent_id: The agent requesting the claim
            
        Returns:
            Result of the claim function
        """
        for attempt in range(self.max_retries + 1):
            result = claim_func(task_id, agent_id)
            
            if result:
                # Success
                return result
            
            if attempt == self.max_retries:
                # Last attempt failed
                return result
            
            # Calculate delay with exponential backoff and jitter
            delay = min(
                self.base_delay * (2 ** attempt),  # Exponential growth
                self.max_delay                   # Cap the delay
            )
            
            # Add jitter to prevent thundering herd
            jitter = random.uniform(0, delay * 0.1)  # Up to 10% jitter
            total_delay = delay + jitter
            
            print(f"Claim attempt {attempt + 1} failed, retrying in {total_delay:.2f}s")
            time.sleep(total_delay)
        
        return None  # Should not reach here


# Example usage with the lock manager
def claim_task_wrapper(task_id: str, agent_id: str):
    """Wrapper function for claim operation"""
    return lock_manager.acquire_lock(task_id, agent_id, timeout=300)

retry_manager = RetryClaimManager(max_retries=3, base_delay=0.5)

# Simulate multiple agents competing for the same task
print("\nTesting retry mechanism:")
result = retry_manager.attempt_claim_with_retry(claim_task_wrapper, "task-456", "competing-agent")
print(f"Competing agent claim result: {result is not None}")
```

---

## Pattern 3: Lease-Based Claim Management

### Use Case
Maintain claims with periodic lease renewals to handle agent failures gracefully.

### Implementation

```python
import threading
import time
from datetime import datetime


class LeaseBasedClaimManager:
    """Manage claims with periodic lease renewals"""

    def __init__(self, lock_manager: DistributedLockManager, lease_extension: int = 60):
        self.lock_manager = lock_manager
        self.lease_extension = lease_extension
        self.active_leases = {}  # task_id -> lease info
        self.lease_lock = threading.Lock()

    def claim_with_lease(self, task_id: str, agent_id: str, initial_timeout: int = 300) -> Optional[str]:
        """
        Claim a task and start automatic lease renewal.
        
        Args:
            task_id: The task to claim
            agent_id: The agent requesting the claim
            initial_timeout: Initial lock timeout
            
        Returns:
            Lock ID if successful, None if failed
        """
        lock_id = self.lock_manager.acquire_lock(task_id, agent_id, initial_timeout)
        
        if lock_id:
            # Start lease renewal thread
            lease_thread = threading.Thread(
                target=self._renew_lease,
                args=(task_id, lock_id, agent_id),
                daemon=True
            )
            lease_thread.start()
            
            # Track the lease
            with self.lease_lock:
                self.active_leases[task_id] = {
                    'lock_id': lock_id,
                    'agent_id': agent_id,
                    'thread': lease_thread,
                    'stop_event': threading.Event()
                }
            
            return lock_id
        
        return None

    def _renew_lease(self, task_id: str, lock_id: str, agent_id: str):
        """Internal method to renew the lease periodically."""
        while True:
            # Check if we should stop
            lease_info = self.active_leases.get(task_id)
            if not lease_info or lease_info['stop_event'].is_set():
                break
            
            # Attempt to renew the lease
            renewed = self.lock_manager.renew_lock(task_id, lock_id, self.lease_extension)
            
            if not renewed:
                print(f"Failed to renew lease for task {task_id}, agent {agent_id}")
                # Lease renewal failed, stop trying
                break
            
            # Sleep until next renewal
            time.sleep(self.lease_extension / 2)  # Renew halfway through lease

    def release_claim(self, task_id: str, agent_id: str) -> bool:
        """
        Release a claimed task and stop lease renewal.
        
        Args:
            task_id: The task to release
            agent_id: The agent releasing the claim
            
        Returns:
            True if successfully released, False otherwise
        """
        with self.lease_lock:
            lease_info = self.active_leases.get(task_id)
            
            if not lease_info:
                return False  # No active lease for this task
            
            if lease_info['agent_id'] != agent_id:
                return False  # Different agent owns this lease
            
            # Signal the lease renewal thread to stop
            lease_info['stop_event'].set()
            
            # Release the lock
            released = self.lock_manager.release_lock(task_id, lease_info['lock_id'])
            
            # Remove from active leases
            del self.active_leases[task_id]
            
            return released

    def force_release_claim(self, task_id: str) -> bool:
        """
        Force release a claim without agent verification (admin function).
        
        Args:
            task_id: The task to force release
            
        Returns:
            True if successfully released, False otherwise
        """
        with self.lease_lock:
            lease_info = self.active_leases.get(task_id)
            
            if not lease_info:
                return False  # No active lease for this task
            
            # Signal the lease renewal thread to stop
            lease_info['stop_event'].set()
            
            # Release the lock
            released = self.lock_manager.release_lock(task_id, lease_info['lock_id'])
            
            # Remove from active leases
            del self.active_leases[task_id]
            
            return released


# Example usage
lease_manager = LeaseBasedClaimManager(lock_manager, lease_extension=30)

print("\nTesting lease-based claims:")
leased_lock = lease_manager.claim_with_lease("task-789", "leasing-agent", initial_timeout=120)
print(f"Leased claim acquired: {leased_lock is not None}")

# Simulate some work
time.sleep(2)

# Release the claim
released = lease_manager.release_claim("task-789", "leasing-agent")
print(f"Leased claim released: {released}")
```

---

## Pattern 4: Fair Claim Distribution

### Use Case
Distribute tasks fairly among agents to prevent monopolization.

### Implementation

```python
import hashlib
from collections import defaultdict, deque
from typing import List


class FairClaimDistributor:
    """Distribute claims fairly among agents"""

    def __init__(self, agents: List[str]):
        self.agents = agents
        self.agent_stats = defaultdict(lambda: {'claims': 0, 'success_rate': 1.0})
        self.agent_queue = deque(agents)  # Round-robin queue

    def select_next_agent(self, task_id: str) -> str:
        """
        Select the next agent based on fairness algorithm.
        
        Args:
            task_id: The task to assign
            
        Returns:
            Selected agent ID
        """
        # Option 1: Round-robin selection
        agent = self.agent_queue[0]
        self.agent_queue.rotate(-1)  # Move first element to end
        return agent

    def select_least_claimed_agent(self) -> str:
        """
        Select the agent with the fewest claims.
        
        Returns:
            Selected agent ID
        """
        min_claims = float('inf')
        selected_agent = None
        
        for agent in self.agents:
            claims = self.agent_stats[agent]['claims']
            if claims < min_claims:
                min_claims = claims
                selected_agent = agent
        
        return selected_agent or self.agents[0]  # Fallback to first agent

    def select_consistent_agent(self, task_id: str) -> str:
        """
        Select an agent consistently based on task ID (sticky routing).
        
        Args:
            task_id: The task to assign
            
        Returns:
            Selected agent ID
        """
        # Hash task ID and map to agent index
        hash_value = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
        agent_index = hash_value % len(self.agents)
        return self.agents[agent_index]

    def record_claim_result(self, agent_id: str, success: bool):
        """
        Record the result of a claim attempt for fairness metrics.
        
        Args:
            agent_id: The agent that attempted the claim
            success: Whether the claim was successful
        """
        self.agent_stats[agent_id]['claims'] += 1
        
        # Update success rate (simple moving average)
        current_rate = self.agent_stats[agent_id]['success_rate']
        new_rate = 0.9 * current_rate + 0.1 * (1.0 if success else 0.0)
        self.agent_stats[agent_id]['success_rate'] = new_rate

    def get_fairness_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get fairness metrics for all agents.
        
        Returns:
            Dictionary of agent metrics
        """
        return {
            agent: {
                'claims': stats['claims'],
                'success_rate': stats['success_rate']
            }
            for agent, stats in self.agent_stats.items()
        }


# Example usage
agents = ["agent-1", "agent-2", "agent-3"]
distributor = FairClaimDistributor(agents)

print("\nTesting fair distribution:")
for i in range(5):
    task_id = f"fair-task-{i}"
    agent = distributor.select_next_agent(task_id)
    print(f"Task {task_id} assigned to {agent}")
    
    # Simulate claim result
    distributor.record_claim_result(agent, success=True)

print("\nFairness metrics:")
metrics = distributor.get_fairness_metrics()
for agent, stats in metrics.items():
    print(f"  {agent}: {stats['claims']} claims, {stats['success_rate']:.2f} success rate")
```

---

## Pattern 5: Collision Detection and Resolution

### Use Case
Detect and resolve simultaneous claim attempts to prevent double work.

### Implementation

```python
import time
from typing import Dict, List, Optional


class CollisionDetector:
    """Detect and resolve claim collisions"""

    def __init__(self, detection_window: float = 5.0):
        self.detection_window = detection_window
        self.claim_history = {}  # task_id -> list of claim attempts
        self.history_lock = threading.Lock()

    def record_claim_attempt(self, task_id: str, agent_id: str) -> str:
        """
        Record a claim attempt and detect collisions.
        
        Args:
            task_id: The task being claimed
            agent_id: The agent making the claim
            
        Returns:
            Attempt ID for tracking
        """
        attempt_id = f"{agent_id}:{int(time.time())}:{hash(task_id)}"
        
        with self.history_lock:
            if task_id not in self.claim_history:
                self.claim_history[task_id] = []
            
            # Clean up old attempts outside the detection window
            current_time = time.time()
            self.claim_history[task_id] = [
                attempt for attempt in self.claim_history[task_id]
                if current_time - attempt['timestamp'] <= self.detection_window
            ]
            
            # Record this attempt
            self.claim_history[task_id].append({
                'agent_id': agent_id,
                'attempt_id': attempt_id,
                'timestamp': current_time
            })
        
        return attempt_id

    def detect_collisions(self, task_id: str) -> List[Dict[str, str]]:
        """
        Detect collisions for a specific task.
        
        Args:
            task_id: The task to check for collisions
            
        Returns:
            List of colliding claim attempts
        """
        with self.history_lock:
            attempts = self.claim_history.get(task_id, [])
            current_time = time.time()
            
            # Filter to recent attempts
            recent_attempts = [
                attempt for attempt in attempts
                if current_time - attempt['timestamp'] <= self.detection_window
            ]
            
            if len(recent_attempts) > 1:
                return recent_attempts
            else:
                return []

    def resolve_collision(self, task_id: str, winning_agent: str) -> List[str]:
        """
        Resolve a collision by determining the winner and notifying losers.
        
        Args:
            task_id: The task with collision
            winning_agent: The agent that wins the claim
            
        Returns:
            List of losing agent IDs
        """
        collisions = self.detect_collisions(task_id)
        
        if len(collisions) <= 1:
            return []  # No collision to resolve
        
        losers = []
        for attempt in collisions:
            if attempt['agent_id'] != winning_agent:
                losers.append(attempt['agent_id'])
        
        print(f"Collision resolved for {task_id}: {winning_agent} wins, {losers} lose")
        return losers


# Example usage
detector = CollisionDetector(detection_window=10.0)

print("\nTesting collision detection:")
# Simulate multiple agents trying to claim the same task
agents = ["agent-a", "agent-b", "agent-c"]

for agent in agents:
    attempt_id = detector.record_claim_attempt("collision-task", agent)
    print(f"Agent {agent} made claim attempt {attempt_id}")

# Check for collisions
collisions = detector.detect_collisions("collision-task")
print(f"\nDetected {len(collisions)} collision attempts")

if len(collisions) > 1:
    # Resolve by picking the first agent alphabetically
    winning_agent = min([attempt['agent_id'] for attempt in collisions])
    losers = detector.resolve_collision("collision-task", winning_agent)
    print(f"Winning agent: {winning_agent}, Losers: {losers}")
```

---

## Pattern 6: Health-Based Claim Eligibility

### Use Case
Only allow healthy agents to claim tasks to ensure reliable processing.

### Implementation

```python
import time
from enum import Enum
from typing import Dict, Optional


class AgentHealthStatus(Enum):
    HEALTHY = "healthy"
    UNSTABLE = "unstable"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthBasedClaimManager:
    """Manage claims based on agent health status"""

    def __init__(self, health_check_interval: int = 30):
        self.health_status = {}  # agent_id -> health info
        self.health_check_interval = health_check_interval
        self.last_check_time = {}  # agent_id -> timestamp

    def update_agent_health(self, agent_id: str, status: AgentHealthStatus, details: Dict = None):
        """
        Update the health status of an agent.
        
        Args:
            agent_id: The agent ID
            status: Health status
            details: Additional health details
        """
        self.health_status[agent_id] = {
            'status': status,
            'details': details or {},
            'updated_at': time.time()
        }
        self.last_check_time[agent_id] = time.time()

    def is_agent_eligible_for_claims(self, agent_id: str) -> bool:
        """
        Check if an agent is eligible to make claims based on health.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            True if eligible, False otherwise
        """
        health_info = self.health_status.get(agent_id)
        
        if not health_info:
            # Unknown health status - assume unhealthy
            return False
        
        return health_info['status'] in [AgentHealthStatus.HEALTHY, AgentHealthStatus.UNSTABLE]

    def can_claim_task(self, task_id: str, agent_id: str) -> bool:
        """
        Check if an agent can claim a specific task.
        
        Args:
            task_id: The task to claim
            agent_id: The agent requesting the claim
            
        Returns:
            True if agent can claim, False otherwise
        """
        # Check agent health
        if not self.is_agent_eligible_for_claims(agent_id):
            print(f"Agent {agent_id} is not eligible for claims due to health status")
            return False
        
        # Additional checks could go here (capacity, etc.)
        return True

    def get_healthy_agents(self) -> List[str]:
        """
        Get list of agents that are eligible for claims.
        
        Returns:
            List of eligible agent IDs
        """
        eligible_agents = []
        for agent_id, health_info in self.health_status.items():
            if self.is_agent_eligible_for_claims(agent_id):
                eligible_agents.append(agent_id)
        return eligible_agents


# Example usage
health_manager = HealthBasedClaimManager()

# Update agent health statuses
health_manager.update_agent_health(
    "healthy-agent", 
    AgentHealthStatus.HEALTHY, 
    {"cpu": 30, "memory": 45, "response_time_ms": 12}
)
health_manager.update_agent_health(
    "unstable-agent", 
    AgentHealthStatus.UNSTABLE, 
    {"cpu": 85, "memory": 70, "response_time_ms": 200}
)
health_manager.update_agent_health(
    "unhealthy-agent", 
    AgentHealthStatus.UNHEALTHY, 
    {"cpu": 95, "memory": 90, "error_rate": 0.8}
)

print("\nTesting health-based eligibility:")
agents = ["healthy-agent", "unstable-agent", "unhealthy-agent", "unknown-agent"]

for agent in agents:
    eligible = health_manager.can_claim_task("test-task", agent)
    print(f"Agent {agent} eligible: {eligible}")

healthy_agents = health_manager.get_healthy_agents()
print(f"\nHealthy agents: {healthy_agents}")
```

---

## Best Practices Summary

1. **Use Atomic Operations** - Always use atomic operations for lock acquisition to prevent race conditions
2. **Implement Retry Logic** - Use exponential backoff with jitter to handle collisions gracefully
3. **Monitor Lease Health** - Renew leases periodically and detect stale locks
4. **Ensure Fair Distribution** - Use algorithms to distribute claims fairly among agents
5. **Detect Collisions** - Implement collision detection to prevent double work
6. **Verify Agent Health** - Only allow healthy agents to claim tasks
7. **Maintain Audit Trails** - Log all claim operations for debugging and compliance
8. **Handle Timeouts Gracefully** - Implement automatic cleanup of expired locks
9. **Use Unique Identifiers** - Generate unique IDs for each claim to detect stale locks
10. **Test Under Contention** - Verify behavior under high contention scenarios

---

**Last Updated:** 2026-02-07