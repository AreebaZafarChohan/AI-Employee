# Agent Delegation Manager - Gotchas and Troubleshooting

## Overview
This document outlines common pitfalls, gotchas, and troubleshooting tips for the Agent Delegation Manager skill.

---

## Common Gotchas

### 1. The "Busy Agent" Paradox
**Problem:** Agents appear busy but aren't actually processing tasks efficiently.
**Symptoms:** High agent load metrics but low task completion rates.
**Root Cause:** Agents accepting tasks but failing to process them due to internal issues.
**Solution:** Implement task completion monitoring and timeout mechanisms.
**Prevention:** Add health checks that verify agents are actively processing tasks, not just accepting them.

```python
# Bad: Only track task assignment
def assign_task(self, agent_id, task):
    self.agents[agent_id].current_load += 1
    # No verification that task is actually processed

# Good: Track both assignment and completion
def assign_task(self, agent_id, task):
    self.agents[agent_id].current_load += 1
    self.active_tasks[task.id] = {
        'agent_id': agent_id,
        'assigned_at': time.time(),
        'expected_completion': time.time() + task.estimated_duration
    }

def monitor_active_tasks(self):
    now = time.time()
    for task_id, task_info in self.active_tasks.items():
        if now > task_info['expected_completion']:
            # Task is taking too long, investigate
            self.handle_potential_hang(task_id, task_info['agent_id'])
```

---

### 2. The "Overeager Agent" Problem
**Problem:** Some agents accept more tasks than they can handle.
**Symptoms:** Certain agents have disproportionately high load and poor performance.
**Root Cause:** Agents don't accurately report their capacity or capabilities.
**Solution:** Implement capacity verification and rate limiting per agent.
**Prevention:** Validate agent-reported capacity against observed performance.

```bash
# Gotcha: Trusting agent-reported capacity without verification
calculate_assignment() {
    # Bad: Only use agent-reported capacity
    AVAILABLE_SLOTS=$(get_agent_capacity "$AGENT_ID")  # Agent reports 100 slots
    if [ $AVAILABLE_SLOTS -gt 0 ]; then
        assign_task "$AGENT_ID" "$TASK"
    fi
}

# Solution: Cross-reference with historical performance
calculate_assignment() {
    # Good: Verify capacity against actual performance
    REPORTED_CAPACITY=$(get_agent_capacity "$AGENT_ID")
    ACTUAL_THROUGHPUT=$(get_recent_throughput "$AGENT_ID")
    
    # Use the minimum of reported capacity and proven throughput
    EFFECTIVE_CAPACITY=$((REPORTED_CAPACITY < ACTUAL_THROUGHPUT ? REPORTED_CAPACITY : ACTUAL_THROUGHPUT))
    
    if [ $EFFECTIVE_CAPACITY -gt 0 ]; then
        assign_task "$AGENT_ID" "$TASK"
    fi
}
```

---

### 3. The "Cascade Failure" Trap
**Problem:** Failure of one agent causes failures in others due to reassignment.
**Symptoms:** Small failure leads to system-wide degradation.
**Root Cause:** Poor isolation between agent failures and task reassignment logic.
**Solution:** Implement circuit breakers and isolation mechanisms.
**Prevention:** Design failure domains and limit blast radius.

```python
# Gotcha: Immediate reassignment without considering failure patterns
def handle_agent_failure(self, agent_id):
    # Bad: Immediately reassign all tasks from failed agent
    tasks_to_reassign = self.get_tasks_for_agent(agent_id)
    for task in tasks_to_reassign:
        self.route_task(task)  # Could overwhelm other agents
```

```python
# Solution: Isolated failure handling with backpressure
def handle_agent_failure(self, agent_id):
    # Good: Controlled reassignment with rate limiting
    tasks_to_reassign = self.get_tasks_for_agent(agent_id)
    
    # Mark agent as failed to prevent new assignments
    self.mark_agent_failed(agent_id)
    
    # Reassign tasks gradually to prevent overwhelming other agents
    for i, task in enumerate(tasks_to_reassign):
        # Add delay between reassignments
        time.sleep(0.1)  # Prevent thundering herd
        
        # Verify system capacity before reassignment
        if self.system_load_factor() < 0.8:  # Only if system is not overloaded
            try:
                self.route_task(task)
            except NoAvailableAgentsException:
                # Queue for later if no agents available
                self.queue_for_retry(task, delay=min(60, 2**i))  # Exponential backoff
        else:
            # System is overloaded, queue for later
            self.queue_for_retry(task, delay=30)
```

---

### 4. The "Sticky Session" Anti-Pattern
**Problem:** Tasks are consistently routed to the same agents regardless of load.
**Symptoms:** Uneven load distribution despite load balancing mechanisms.
**Root Cause:** Sticky routing based on task attributes that don't vary much.
**Solution:** Implement proper load-aware routing algorithms.
**Prevention:** Regularly rebalance assignments based on current load.

```python
# Gotcha: Hash-based routing without considering load
def route_task_bad(self, task):
    # Bad: Consistent hash routing ignores load
    agent_hash = hash(task.user_id) % len(self.agents)
    return self.agents[agent_hash]

# Solution: Load-aware routing
def route_task_good(self, task):
    # Good: Consider both consistency and load
    eligible_agents = [
        agent for agent in self.agents
        if all(cap in agent.capabilities for cap in task.required_capabilities)
        and agent.current_load < agent.max_capacity
    ]
    
    if not eligible_agents:
        raise NoAvailableAgentsException()
    
    # Pick agent with lowest load among eligible ones
    return min(eligible_agents, key=lambda a: a.current_load)
```

---

### 5. The "Cold Start" Bottleneck
**Problem:** New agents are underutilized initially due to lack of tasks.
**Symptoms:** New agents sit idle while existing agents are overloaded.
**Root Cause:** Task assignment algorithms favor established agents.
**Solution:** Implement ramp-up strategies for new agents.
**Prevention:** Design assignment algorithms that account for agent readiness.

```python
# Gotcha: Not accounting for new agent warmup
def route_task(self, task):
    # Bad: Treat new agents the same as established ones
    available_agents = [a for a in self.agents if a.is_available()]
    return self.select_agent_by_load(available_agents)

# Solution: Warmup strategy for new agents
def route_task(self, task):
    # Good: Consider agent readiness and warmup state
    ready_agents = []
    
    for agent in self.agents:
        if not agent.is_available():
            continue
            
        # Check if agent is in warmup phase
        if agent.status == 'warming_up':
            # Only assign light tasks during warmup
            if task.complexity <= agent.warmup_capacity:
                ready_agents.append(agent)
        else:
            # Normal assignment for warmed-up agents
            ready_agents.append(agent)
    
    return self.select_agent_by_load(ready_agents)
```

---

## Troubleshooting Guide

### Issue 1: Task Assignment Delays
**Symptoms:** Tasks sitting in queue for extended periods.
**Diagnosis Steps:**
1. Check agent availability: `check_agent_health.sh`
2. Verify agent capabilities match task requirements
3. Examine delegation manager logs for errors
4. Review system resource utilization

**Resolution:**
- Restart unresponsive agents
- Adjust agent capability definitions
- Scale delegation manager resources
- Check for network connectivity issues

### Issue 2: Uneven Load Distribution
**Symptoms:** Some agents consistently busier than others.
**Diagnosis Steps:**
1. Analyze load distribution metrics
2. Check for capability mismatches
3. Review routing algorithm configuration
4. Examine agent performance characteristics

**Resolution:**
- Adjust routing algorithm weights
- Recalibrate agent capacity estimates
- Implement load rebalancing
- Check for sticky routing patterns

### Issue 3: Task Loss
**Symptoms:** Tasks disappear from system without completion or error.
**Diagnosis Steps:**
1. Check delegation logs for missing task records
2. Verify agent acknowledgment of task receipt
3. Examine error handling in delegation code
4. Review timeout and retry configurations

**Resolution:**
- Implement transactional task assignment
- Add end-to-end task tracking
- Improve error handling and recovery
- Adjust timeout values appropriately

### Issue 4: Agent Failures Not Detected
**Symptoms:** System continues assigning tasks to failed agents.
**Diagnosis Steps:**
1. Verify heartbeat mechanism is functioning
2. Check failure detection thresholds
3. Review agent status update frequency
4. Examine network connectivity between components

**Resolution:**
- Adjust heartbeat intervals and failure timeouts
- Implement redundant health checks
- Add agent self-reporting mechanisms
- Improve network monitoring

### Issue 5: Performance Degradation
**Symptoms:** Slower task completion times after implementing delegation.
**Diagnosis Steps:**
1. Profile delegation manager performance
2. Measure task assignment latency
3. Analyze inter-agent communication overhead
4. Review algorithm complexity

**Resolution:**
- Optimize delegation algorithms
- Implement caching for agent availability
- Reduce communication overhead
- Scale delegation manager horizontally

---

## Performance Gotchas

### Gotcha 1: Synchronous Agent Verification
**Problem:** Waiting for agent response before proceeding with next task.
**Impact:** Severe performance degradation under load.
**Solution:** Use asynchronous verification and batch operations.

```python
# Bad: Synchronous verification
def route_and_assign(self, task):
    for agent in self.agents:
        if self.verify_agent_can_handle(agent, task):  # Blocks here
            return self.assign_task(agent, task)
    return None

# Good: Asynchronous verification
async def route_and_assign_async(self, task):
    # Concurrently check all agents
    verification_tasks = [
        self.verify_agent_can_handle_async(agent, task) 
        for agent in self.agents
    ]
    
    results = await asyncio.gather(*verification_tasks, return_exceptions=True)
    
    # Find first available agent
    for i, result in enumerate(results):
        if result is True:
            return await self.assign_task_async(self.agents[i], task)
    
    return None
```

### Gotcha 2: Global Locks in Hot Paths
**Problem:** Using global locks for agent state updates.
**Impact:** Serialization of concurrent operations, reducing throughput.
**Solution:** Use fine-grained locking or lock-free data structures.

```python
# Bad: Global lock for all operations
class BadDelegationManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.agents = {}
    
    def assign_task(self, task):
        with self.lock:  # Global lock affects all operations
            # Find and assign agent
            pass

# Good: Fine-grained locking
class GoodDelegationManager:
    def __init__(self):
        self.agent_locks = {}  # Per-agent locks
        self.agents = {}
    
    def assign_task(self, task):
        # Only lock the specific agent being modified
        agent = self.find_suitable_agent(task)
        with self.agent_locks[agent.id]:
            # Update only this agent's state
            pass
```

---

## Configuration Gotchas

### Gotcha 1: Incorrect Timeout Values
**Problem:** Timeouts too short cause false failures; too long cause slow recovery.
**Solution:** Set timeouts based on actual system measurements.

```yaml
# Bad: Arbitrary timeout values
agent_communication:
  timeout_seconds: 5    # Too short for complex tasks
  heartbeat_interval: 30
  failure_threshold: 3

# Good: Measured timeout values
agent_communication:
  timeout_seconds: 30   # Based on 99th percentile task completion time
  heartbeat_interval: 10  # Shorter than timeout for quick detection
  failure_threshold: 2    # Allow one missed heartbeat
```

### Gotcha 2: Static Capacity Values
**Problem:** Fixed capacity values don't reflect changing system conditions.
**Solution:** Dynamically adjust capacity based on observed performance.

```python
# Bad: Static capacity
class StaticAgent:
    def __init__(self):
        self.max_capacity = 10  # Fixed value

# Good: Dynamic capacity adjustment
class DynamicAgent:
    def __init__(self):
        self.base_capacity = 10
        self.performance_multiplier = 1.0  # Adjusts based on performance
    
    def get_effective_capacity(self):
        # Adjust capacity based on recent performance
        recent_success_rate = self.get_recent_success_rate()
        if recent_success_rate < 0.8:
            self.performance_multiplier *= 0.9  # Reduce capacity
        elif recent_success_rate > 0.95:
            self.performance_multiplier *= 1.1  # Increase capacity
        
        # Bound the multiplier to prevent extreme values
        self.performance_multiplier = max(0.5, min(2.0, self.performance_multiplier))
        
        return int(self.base_capacity * self.performance_multiplier)
```

---

## Monitoring Gotchas

### Gotcha 1: Missing Critical Metrics
**Problem:** Not tracking metrics that matter for delegation effectiveness.
**Solution:** Monitor both system-level and delegation-specific metrics.

```python
# Track these critical metrics:
class DelegationMetrics:
    def __init__(self):
        self.assignment_latency = []  # Time to assign tasks
        self.routing_efficiency = []  # Percentage of optimal routing
        self.agent_utilization = {}   # Per-agent utilization
        self.failure_rates = {}       # Per-agent failure rates
        self.queue_depth = []         # Pending tasks count
        self.task_completion_time = [] # End-to-end task time
```

### Gotcha 2: Alerting on Wrong Indicators
**Problem:** Alerts trigger for non-actionable issues or miss critical problems.
**Solution:** Focus alerts on actionable metrics that indicate real problems.

```python
# Bad: Alert on every minor fluctuation
ALERT_IF: agent_load > 0.6  # Too sensitive

# Good: Alert on meaningful indicators
ALERT_IF: (
    agent_failure_rate > 0.05 AND  # More than 5% failures
    consecutive_minutes > 5        # For more than 5 minutes
)
```

---

## Security Gotchas

### Gotcha 1: Insufficient Agent Authentication
**Problem:** Agents can impersonate each other or register maliciously.
**Solution:** Implement strong authentication and authorization.

```python
# Bad: No authentication
def register_agent(self, agent_info):
    self.agents[agent_info.id] = agent_info  # Anyone can register

# Good: Strong authentication
def register_agent(self, agent_info, auth_token):
    # Verify token authenticity
    if not self.verify_auth_token(auth_token, agent_info.id):
        raise UnauthorizedAccessError()
    
    # Validate agent capabilities
    if not self.validate_capabilities(agent_info.capabilities):
        raise InvalidCapabilitiesError()
    
    # Register agent with verified information
    self.agents[agent_info.id] = agent_info
```

---

## Testing Gotchas

### Gotcha 1: Not Testing Failure Scenarios
**Problem:** Code works in ideal conditions but fails during actual failures.
**Solution:** Test failure scenarios extensively.

```python
# Test failure scenarios
def test_agent_failure_handling(self):
    # Create delegation manager with 3 agents
    manager = DelegationManager([agent1, agent2, agent3])
    
    # Assign tasks to all agents
    tasks = [create_task(f"task{i}") for i in range(10)]
    for task in tasks:
        manager.route_task(task)
    
    # Simulate agent failure
    manager.simulate_agent_failure(agent2.id)
    
    # Verify tasks are reassigned appropriately
    remaining_tasks = manager.get_uncompleted_tasks()
    assert len(remaining_tasks) == expected_reassigned_count
    
    # Verify system continues operating
    new_task = create_task("new_task")
    assigned_agent = manager.route_task(new_task)
    assert assigned_agent.id in [agent1.id, agent3.id]
```

---

**Last Updated:** 2026-02-07