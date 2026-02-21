# Agent Delegation Manager - Common Patterns

## Overview
This document describes common integration patterns for the Agent Delegation Manager across different use cases and architectures.

---

## Pattern 1: Load Balanced Task Distribution

### Use Case
Distribute tasks evenly across multiple agents to prevent overloading any single agent.

### Implementation

```python
from typing import List, Dict, Any
import time
import random
from dataclasses import dataclass


@dataclass
class Agent:
    id: str
    capabilities: List[str]
    current_load: int
    max_capacity: int
    is_available: bool = True

    def can_accept_task(self, task_type: str) -> bool:
        return (self.is_available and 
                task_type in self.capabilities and 
                self.current_load < self.max_capacity)

    def accept_task(self):
        self.current_load += 1

    def complete_task(self):
        self.current_load = max(0, self.current_load - 1)


class LoadBalancedRouter:
    """Route tasks using load balancing algorithm"""

    def __init__(self, agents: List[Agent]):
        self.agents = agents

    def route_task(self, task_type: str) -> Agent:
        """Select agent with lowest current load"""
        available_agents = [
            agent for agent in self.agents 
            if agent.can_accept_task(task_type)
        ]

        if not available_agents:
            raise Exception(f"No available agents for task type: {task_type}")

        # Select agent with lowest current load
        selected_agent = min(available_agents, key=lambda a: a.current_load)
        selected_agent.accept_task()
        return selected_agent


# Usage
agents = [
    Agent(id="agent-1", capabilities=["data_processing"], current_load=2, max_capacity=5),
    Agent(id="agent-2", capabilities=["data_processing"], current_load=0, max_capacity=5),
    Agent(id="agent-3", capabilities=["data_processing"], current_load=1, max_capacity=5),
]

router = LoadBalancedRouter(agents)

# Route multiple tasks
for i in range(5):
    agent = router.route_task("data_processing")
    print(f"Task {i+1} assigned to {agent.id} (load: {agent.current_load})")
```

---

## Pattern 2: Priority-Based Task Routing

### Use Case
Route high-priority tasks to specialized agents while maintaining load balance for routine tasks.

### Implementation

```python
from enum import Enum
from typing import List, Optional


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    id: str
    type: str
    priority: TaskPriority
    required_capabilities: List[str]


class PriorityRouter:
    """Route tasks based on priority and agent specialization"""

    def __init__(self, agents: List[Agent]):
        self.agents = agents

    def route_task(self, task: Task) -> Agent:
        """Route task based on priority and agent specialization"""
        if task.priority == TaskPriority.CRITICAL:
            # For critical tasks, find most capable agent regardless of load
            specialized_agents = [
                agent for agent in self.agents
                if all(cap in agent.capabilities for cap in task.required_capabilities)
                and agent.is_available
            ]
            
            if specialized_agents:
                # Among specialized agents, pick one with lowest load
                return min(specialized_agents, key=lambda a: a.current_load)
            else:
                # If no specialized agents, pick any available
                available = [a for a in self.agents if a.is_available]
                if available:
                    return min(available, key=lambda a: a.current_load)
        else:
            # For non-critical tasks, use load balancing
            return self._route_by_load(task)

    def _route_by_load(self, task: Task) -> Agent:
        """Route task using load balancing"""
        available_agents = [
            agent for agent in self.agents
            if all(cap in agent.capabilities for cap in task.required_capabilities)
            and agent.is_available
            and agent.current_load < agent.max_capacity
        ]

        if not available_agents:
            raise Exception(f"No available agents for task: {task.id}")

        return min(available_agents, key=lambda a: a.current_load)


# Usage
agents = [
    Agent(id="specialist-1", capabilities=["critical_data", "data_processing"], current_load=1, max_capacity=3),
    Agent(id="general-1", capabilities=["data_processing"], current_load=2, max_capacity=5),
    Agent(id="general-2", capabilities=["data_processing"], current_load=0, max_capacity=5),
]

router = PriorityRouter(agents)

# Critical task
critical_task = Task(
    id="task-1", 
    type="critical_data", 
    priority=TaskPriority.CRITICAL, 
    required_capabilities=["critical_data"]
)
agent = router.route_task(critical_task)
print(f"Critical task assigned to {agent.id}")

# Normal task
normal_task = Task(
    id="task-2", 
    type="data_processing", 
    priority=TaskPriority.MEDIUM, 
    required_capabilities=["data_processing"]
)
agent = router.route_task(normal_task)
print(f"Normal task assigned to {agent.id}")
```

---

## Pattern 3: Failover and Redundancy

### Use Case
Handle agent failures gracefully by rerouting tasks to backup agents.

### Implementation

```python
import time
from typing import Dict, Set


class FailoverRouter:
    """Route tasks with failover capability"""

    def __init__(self, agents: List[Agent]):
        self.agents = {agent.id: agent for agent in agents}
        self.agent_failures: Dict[str, int] = {}  # agent_id -> failure_count
        self.failed_agents: Set[str] = set()
        self.failure_threshold = 3

    def route_task(self, task: Task) -> Agent:
        """Route task with failover capability"""
        # First, try to find a healthy agent
        available_agents = [
            agent for agent in self.agents.values()
            if self._is_healthy(agent) and 
            all(cap in agent.capabilities for cap in task.required_capabilities)
        ]

        if not available_agents:
            # If no healthy agents, try to revive failed agents
            self._reset_failed_agents()
            available_agents = [
                agent for agent in self.agents.values()
                if all(cap in agent.capabilities for cap in task.required_capabilities)
            ]

        if not available_agents:
            raise Exception(f"No agents available for task: {task.id}")

        # Use load balancing among available agents
        selected_agent = min(available_agents, key=lambda a: a.current_load)
        selected_agent.accept_task()
        return selected_agent

    def _is_healthy(self, agent: Agent) -> bool:
        """Check if agent is healthy"""
        return (
            agent.id not in self.failed_agents and
            agent.is_available and
            agent.current_load < agent.max_capacity
        )

    def record_failure(self, agent_id: str):
        """Record agent failure"""
        self.agent_failures[agent_id] = self.agent_failures.get(agent_id, 0) + 1
        
        if self.agent_failures[agent_id] >= self.failure_threshold:
            self.failed_agents.add(agent_id)
            print(f"Agent {agent_id} marked as failed after {self.failure_threshold} failures")

    def _reset_failed_agents(self):
        """Reset failed agents after cooldown period"""
        # In a real implementation, this would check if agents are responsive
        # For demo, we'll reset after a certain time
        pass

    def mark_agent_healthy(self, agent_id: str):
        """Mark a previously failed agent as healthy"""
        if agent_id in self.failed_agents:
            self.failed_agents.remove(agent_id)
            self.agent_failures[agent_id] = 0
            print(f"Agent {agent_id} marked as healthy")


# Usage
agents = [
    Agent(id="primary", capabilities=["processing"], current_load=0, max_capacity=5),
    Agent(id="backup-1", capabilities=["processing"], current_load=0, max_capacity=5),
    Agent(id="backup-2", capabilities=["processing"], current_load=0, max_capacity=5),
]

router = FailoverRouter(agents)

task = Task(id="task-1", type="processing", priority=TaskPriority.HIGH, required_capabilities=["processing"])

try:
    agent = router.route_task(task)
    print(f"Task assigned to {agent.id}")
    
    # Simulate agent failure
    router.record_failure(agent.id)
    
    # Next task should go to a different agent
    task2 = Task(id="task-2", type="processing", priority=TaskPriority.MEDIUM, required_capabilities=["processing"])
    agent2 = router.route_task(task2)
    print(f"Task 2 assigned to {agent2.id}")
    
except Exception as e:
    print(f"Error: {e}")
```

---

## Pattern 4: Capability-Based Agent Selection

### Use Case
Route tasks to agents based on their specific capabilities and expertise.

### Implementation

```python
from typing import Dict, List, Set


class CapabilityRouter:
    """Route tasks based on agent capabilities and expertise"""

    def __init__(self, agents: List[Agent]):
        self.agents = agents
        self.capability_index: Dict[str, List[Agent]] = {}
        self._build_capability_index()

    def _build_capability_index(self):
        """Build index mapping capabilities to agents"""
        for agent in self.agents:
            for capability in agent.capabilities:
                if capability not in self.capability_index:
                    self.capability_index[capability] = []
                self.capability_index[capability].append(agent)

    def route_task(self, task: Task) -> Agent:
        """Route task based on required capabilities"""
        # Find agents that have all required capabilities
        candidate_agents = None

        for capability in task.required_capabilities:
            agents_with_capability = self.capability_index.get(capability, [])
            available_agents = [
                agent for agent in agents_with_capability
                if agent.is_available and agent.current_load < agent.max_capacity
            ]

            if candidate_agents is None:
                candidate_agents = set(available_agents)
            else:
                # Intersect with agents that have this capability
                candidate_agents &= set(available_agents)

        if not candidate_agents:
            raise Exception(f"No agents available with all required capabilities for task: {task.id}")

        # Among candidates, select based on load
        return min(candidate_agents, key=lambda a: a.current_load)

    def add_agent(self, agent: Agent):
        """Add a new agent to the router"""
        self.agents.append(agent)
        for capability in agent.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = []
            self.capability_index[capability].append(agent)

    def remove_agent(self, agent_id: str):
        """Remove an agent from the router"""
        self.agents = [agent for agent in self.agents if agent.id != agent_id]
        # Rebuild index (could be optimized in production)
        self._build_capability_index()


# Usage
agents = [
    Agent(id="data-expert", capabilities=["data_processing", "analytics"], current_load=1, max_capacity=3),
    Agent(id="report-expert", capabilities=["report_generation", "visualization"], current_load=0, max_capacity=2),
    Agent(id="general", capabilities=["data_processing", "report_generation"], current_load=2, max_capacity=5),
]

router = CapabilityRouter(agents)

# Task requiring specific capabilities
task = Task(
    id="analytics-task", 
    type="analytics", 
    priority=TaskPriority.HIGH, 
    required_capabilities=["data_processing", "analytics"]
)

agent = router.route_task(task)
print(f"Analytics task assigned to {agent.id} (capabilities: {agent.capabilities})")
```

---

## Pattern 5: Geographic-Aware Task Routing

### Use Case
Route tasks to geographically optimal agents to minimize latency.

### Implementation

```python
from typing import Dict


@dataclass
class GeoAgent(Agent):
    location: str  # e.g., "us-east-1", "eu-west-2"
    latency_map: Dict[str, float]  # region -> avg latency in ms


class GeographicRouter:
    """Route tasks based on geographic proximity"""

    def __init__(self, agents: List[GeoAgent]):
        self.agents = agents

    def route_task(self, task: Task, client_region: str) -> GeoAgent:
        """Route task to geographically closest available agent"""
        available_agents = [
            agent for agent in self.agents
            if agent.is_available and 
            agent.current_load < agent.max_capacity and
            all(cap in agent.capabilities for cap in task.required_capabilities)
        ]

        if not available_agents:
            raise Exception(f"No available agents for task: {task.id}")

        # Find agent with lowest latency to client region
        best_agent = min(
            available_agents, 
            key=lambda a: a.latency_map.get(client_region, float('inf'))
        )
        
        best_agent.accept_task()
        return best_agent


# Usage
agents = [
    GeoAgent(
        id="us-agent", 
        capabilities=["processing"], 
        current_load=1, 
        max_capacity=5,
        location="us-east-1",
        latency_map={"us-east-1": 10.0, "eu-west-1": 80.0, "ap-southeast-1": 150.0}
    ),
    GeoAgent(
        id="eu-agent", 
        capabilities=["processing"], 
        current_load=0, 
        max_capacity=5,
        location="eu-west-1",
        latency_map={"us-east-1": 80.0, "eu-west-1": 15.0, "ap-southeast-1": 200.0}
    ),
    GeoAgent(
        id="asia-agent", 
        capabilities=["processing"], 
        current_load=2, 
        max_capacity=5,
        location="ap-southeast-1",
        latency_map={"us-east-1": 150.0, "eu-west-1": 200.0, "ap-southeast-1": 20.0}
    ),
]

router = GeographicRouter(agents)

task = Task(id="geo-task", type="processing", priority=TaskPriority.MEDIUM, required_capabilities=["processing"])

# Client from US East
us_agent = router.route_task(task, "us-east-1")
print(f"US task assigned to {us_agent.id} (latency: {us_agent.latency_map['us-east-1']}ms)")

# Client from Europe
eu_task = Task(id="eu-task", type="processing", priority=TaskPriority.MEDIUM, required_capabilities=["processing"])
eu_agent = router.route_task(eu_task, "eu-west-1")
print(f"EU task assigned to {eu_agent.id} (latency: {eu_agent.latency_map['eu-west-1']}ms)")
```

---

## Pattern 6: Adaptive Load Balancing

### Use Case
Dynamically adjust load balancing based on real-time performance metrics.

### Implementation

```python
import statistics
from datetime import datetime, timedelta


@dataclass
class PerformanceMetrics:
    response_times: List[float]
    success_rate: float
    throughput: float  # tasks per second
    last_updated: datetime

    def get_avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else float('inf')


class AdaptiveRouter:
    """Route tasks using adaptive load balancing based on performance metrics"""

    def __init__(self, agents: List[Agent]):
        self.agents = agents
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.performance_weight = 0.7  # Weight given to performance vs load
        self.load_weight = 0.3         # Weight given to current load

    def route_task(self, task: Task) -> Agent:
        """Route task using adaptive algorithm considering both load and performance"""
        available_agents = [
            agent for agent in self.agents
            if agent.is_available and 
            agent.current_load < agent.max_capacity and
            all(cap in agent.capabilities for cap in task.required_capabilities)
        ]

        if not available_agents:
            raise Exception(f"No available agents for task: {task.id}")

        # Calculate score for each agent (lower is better)
        scored_agents = []
        for agent in available_agents:
            metric = self.metrics.get(agent.id)
            
            # Normalize load (0 to 1)
            normalized_load = agent.current_load / agent.max_capacity
            
            # Get performance score (lower response time is better)
            performance_score = 1.0
            if metric:
                avg_response_time = metric.get_avg_response_time()
                # Normalize response time (assuming max expected time is 10s)
                performance_score = min(avg_response_time / 10.0, 1.0)
            
            # Combined score
            score = (self.performance_weight * performance_score) + (self.load_weight * normalized_load)
            scored_agents.append((agent, score))

        # Select agent with lowest score
        best_agent, _ = min(scored_agents, key=lambda x: x[1])
        best_agent.accept_task()
        return best_agent

    def update_metrics(self, agent_id: str, response_time: float, success: bool):
        """Update performance metrics for an agent"""
        if agent_id not in self.metrics:
            self.metrics[agent_id] = PerformanceMetrics(
                response_times=[],
                success_rate=1.0,
                throughput=0.0,
                last_updated=datetime.now()
            )

        metric = self.metrics[agent_id]
        
        # Update response times (keep last 10 measurements)
        metric.response_times.append(response_time)
        if len(metric.response_times) > 10:
            metric.response_times.pop(0)
        
        # Update success rate (simple moving average)
        prev_success_rate = metric.success_rate
        new_success_rate = 0.9 * prev_success_rate + 0.1 * (1.0 if success else 0.0)
        metric.success_rate = new_success_rate
        
        metric.last_updated = datetime.now()


# Usage
agents = [
    Agent(id="fast-low-load", capabilities=["processing"], current_load=1, max_capacity=5),
    Agent(id="slow-high-load", capabilities=["processing"], current_load=4, max_capacity=5),
    Agent(id="balanced", capabilities=["processing"], current_load=2, max_capacity=5),
]

router = AdaptiveRouter(agents)

# Simulate some performance metrics
router.update_metrics("fast-low-load", 0.1, True)  # Very fast
router.update_metrics("slow-high-load", 2.0, True)  # Slow
router.update_metrics("balanced", 0.5, True)       # Medium speed

task = Task(id="adaptive-task", type="processing", priority=TaskPriority.MEDIUM, required_capabilities=["processing"])
agent = router.route_task(task)
print(f"Adaptive routing assigned task to {agent.id}")
```

---

## Pattern 7: Circuit Breaker for Agent Failures

### Use Case
Prevent repeated requests to consistently failing agents.

### Implementation

```python
from enum import Enum
import time


class CircuitState(Enum):
    CLOSED = 1      # Normal operation
    OPEN = 2        # Tripped, requests blocked
    HALF_OPEN = 3   # Testing if agent recovered


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    timeout: int = 60  # seconds
    last_failure_time: float = 0.0
    failure_count: int = 0
    state: CircuitState = CircuitState.CLOSED


class CircuitBreakerRouter:
    """Route tasks with circuit breaker pattern for agent failures"""

    def __init__(self, agents: List[Agent]):
        self.agents = {agent.id: agent for agent in agents}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            agent.id: CircuitBreaker() for agent in agents
        }

    def route_task(self, task: Task) -> Agent:
        """Route task considering circuit breaker states"""
        available_agents = []
        
        for agent_id, agent in self.agents.items():
            cb = self.circuit_breakers[agent_id]
            
            # Check circuit breaker state
            if cb.state == CircuitState.OPEN:
                # Check if timeout has passed to move to half-open
                if time.time() - cb.last_failure_time > cb.timeout:
                    cb.state = CircuitState.HALF_OPEN
                else:
                    continue  # Skip agent with open circuit
            
            # If half-open, allow one request to test recovery
            if cb.state == CircuitState.HALF_OPEN and not self._is_test_slot_available(agent_id):
                continue  # Only one test request allowed in half-open state
            
            # Check if agent is available and has required capabilities
            if (agent.is_available and 
                agent.current_load < agent.max_capacity and
                all(cap in agent.capabilities for cap in task.required_capabilities)):
                
                available_agents.append(agent)

        if not available_agents:
            raise Exception(f"No available agents for task: {task.id}")

        # Use simple load balancing among available agents
        selected_agent = min(available_agents, key=lambda a: a.current_load)
        
        # If agent was in half-open state, mark as closed if successful
        cb = self.circuit_breakers[selected_agent.id]
        if cb.state == CircuitState.HALF_OPEN:
            cb.state = CircuitState.CLOSED
            cb.failure_count = 0
        
        selected_agent.accept_task()
        return selected_agent

    def _is_test_slot_available(self, agent_id: str) -> bool:
        """Check if test slot is available for half-open circuit"""
        # In a real implementation, this would track if a test request is already in flight
        # For demo, we'll just return True occasionally
        return True

    def record_success(self, agent_id: str):
        """Record successful request to agent"""
        cb = self.circuit_breakers[agent_id]
        if cb.state != CircuitState.CLOSED:
            cb.state = CircuitState.CLOSED
            cb.failure_count = 0

    def record_failure(self, agent_id: str):
        """Record failed request to agent"""
        cb = self.circuit_breakers[agent_id]
        cb.failure_count += 1
        cb.last_failure_time = time.time()
        
        if cb.failure_count >= cb.failure_threshold:
            cb.state = CircuitState.OPEN
            print(f"Circuit breaker opened for agent {agent_id}")


# Usage
agents = [
    Agent(id="stable-agent", capabilities=["processing"], current_load=0, max_capacity=5),
    Agent(id="unstable-agent", capabilities=["processing"], current_load=0, max_capacity=5),
]

router = CircuitBreakerRouter(agents)

task = Task(id="circuit-task", type="processing", priority=TaskPriority.MEDIUM, required_capabilities=["processing"])

try:
    # First few requests to unstable agent fail
    for i in range(6):
        try:
            agent = router.route_task(task)
            print(f"Request {i+1} assigned to {agent.id}")
            
            if agent.id == "unstable-agent":
                # Simulate failure
                router.record_failure(agent.id)
            else:
                router.record_success(agent.id)
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    # After threshold, unstable agent should be skipped
    agent = router.route_task(task)
    print(f"Next request assigned to {agent.id} (should be stable-agent)")
    
except Exception as e:
    print(f"Error: {e}")
```

---

## Best Practices Summary

1. **Use Appropriate Routing Strategy** - Match routing algorithm to your use case (load balancing, priority, etc.)
2. **Implement Fallback Mechanisms** - Always have backup plans for agent failures
3. **Monitor Performance Metrics** - Track response times, success rates, and throughput
4. **Apply Circuit Breakers** - Prevent cascading failures from unhealthy agents
5. **Consider Geographic Factors** - Route tasks to geographically optimal agents when latency matters
6. **Balance Load Effectively** - Prevent overloading any single agent
7. **Validate Capabilities** - Ensure agents have required skills before assignment
8. **Maintain Audit Trails** - Log all delegation decisions for debugging and compliance
9. **Implement Adaptive Algorithms** - Adjust routing based on real-time performance
10. **Test Failure Scenarios** - Verify system behavior under various failure conditions

---

**Last Updated:** 2026-02-07