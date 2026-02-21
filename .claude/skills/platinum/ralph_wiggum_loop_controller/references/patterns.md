# Ralph Wiggum Loop Controller - Common Patterns

## Overview
This document describes common integration patterns for the Ralph Wiggum Loop Controller across different use cases and architectures.

---

## Pattern 1: Task Timeout Detection and Recovery

### Use Case
Monitor long-running tasks and automatically recover from timeouts.

### Implementation

```python
import time
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    TIMED_OUT = "timed_out"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TaskInfo:
    task_id: str
    created_at: datetime
    started_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    timeout_seconds: int = 300
    state: TaskState = TaskState.PENDING
    retry_count: int = 0
    max_retries: int = 3
    callback: Optional[Callable] = None
    context: Dict[str, Any] = None


class TaskTimeoutMonitor:
    """Monitor tasks for timeouts and trigger recovery actions"""
    
    def __init__(self, check_interval: int = 30):
        self.tasks: Dict[str, TaskInfo] = {}
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
    
    def register_task(
        self, 
        task_id: str, 
        timeout_seconds: int = 300, 
        max_retries: int = 3,
        callback: Optional[Callable] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register a task for timeout monitoring"""
        with self.lock:
            if task_id in self.tasks:
                return False  # Task already registered
            
            task_info = TaskInfo(
                task_id=task_id,
                created_at=datetime.now(),
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                callback=callback,
                context=context or {}
            )
            
            self.tasks[task_id] = task_info
            return True
    
    def update_task_activity(self, task_id: str) -> bool:
        """Update the last activity timestamp for a task"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            self.tasks[task_id].last_activity_at = datetime.now()
            return True
    
    def mark_task_started(self, task_id: str) -> bool:
        """Mark a task as started"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task_info = self.tasks[task_id]
            task_info.state = TaskState.RUNNING
            task_info.started_at = datetime.now()
            task_info.last_activity_at = datetime.now()
            return True
    
    def mark_task_completed(self, task_id: str) -> bool:
        """Mark a task as completed"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            self.tasks[task_id].state = TaskState.COMPLETED
            return True
    
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the background monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Background thread to check for timeouts"""
        while self.monitoring:
            try:
                self._check_timeouts()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in monitor loop: {e}")
    
    def _check_timeouts(self):
        """Check all registered tasks for timeouts"""
        current_time = datetime.now()
        
        with self.lock:
            for task_id, task_info in list(self.tasks.items()):
                if task_info.state in [TaskState.COMPLETED, TaskState.FAILED]:
                    continue
                
                # Calculate timeout threshold
                timeout_threshold = None
                if task_info.last_activity_at:
                    timeout_threshold = task_info.last_activity_at + timedelta(seconds=task_info.timeout_seconds)
                elif task_info.started_at:
                    timeout_threshold = task_info.started_at + timedelta(seconds=task_info.timeout_seconds)
                else:
                    timeout_threshold = task_info.created_at + timedelta(seconds=task_info.timeout_seconds)
                
                # Check if task has timed out
                if current_time > timeout_threshold:
                    self._handle_timeout(task_id, task_info)
    
    def _handle_timeout(self, task_id: str, task_info: TaskInfo):
        """Handle a task timeout"""
        print(f"Task {task_id} has timed out")
        
        # Check if we can retry
        if task_info.retry_count < task_info.max_retries:
            self._trigger_retry(task_id, task_info)
        else:
            self._mark_as_failed(task_id)
    
    def _trigger_retry(self, task_id: str, task_info: TaskInfo):
        """Trigger a retry for a timed-out task"""
        print(f"Retrying task {task_id}, attempt {task_info.retry_count + 1}")
        
        with self.lock:
            task_info.state = TaskState.RETRYING
            task_info.retry_count += 1
            task_info.last_activity_at = datetime.now()
        
        # Execute retry callback if provided
        if task_info.callback:
            try:
                # Call the retry function with context
                task_info.callback(task_id, task_info.context)
            except Exception as e:
                print(f"Retry callback failed for task {task_id}: {e}")
                self._mark_as_failed(task_id)
    
    def _mark_as_failed(self, task_id: str):
        """Mark a task as failed after retries exhausted"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].state = TaskState.FAILED
                print(f"Task {task_id} marked as failed after retries exhausted")


# Usage example
def example_task_callback(task_id: str, context: Dict[str, Any]):
    """Example callback function for task retries"""
    print(f"Retrying task {task_id} with context: {context}")
    # Implement actual retry logic here

# Create monitor and register a task
monitor = TaskTimeoutMonitor(check_interval=10)
monitor.register_task(
    task_id="task-123",
    timeout_seconds=60,
    max_retries=3,
    callback=example_task_callback,
    context={"important_param": "value"}
)

monitor.start_monitoring()

# Simulate task activity
monitor.mark_task_started("task-123")
monitor.update_task_activity("task-123")

# Later, mark as completed
monitor.mark_task_completed("task-123")
```

---

## Pattern 2: Agent Heartbeat Monitoring

### Use Case
Monitor agent health through periodic heartbeats and detect failures.

### Implementation

```python
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class AgentInfo:
    agent_id: str
    last_heartbeat: datetime
    status: str = "active"  # active, warning, inactive
    task_count: int = 0
    error_count: int = 0
    last_error_time: Optional[datetime] = None


class AgentHeartbeatMonitor:
    """Monitor agent health through heartbeats"""
    
    def __init__(self, heartbeat_timeout: int = 120, warning_threshold: int = 60):
        self.agents: Dict[str, AgentInfo] = {}
        self.heartbeat_timeout = heartbeat_timeout
        self.warning_threshold = warning_threshold
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        self.status_callbacks: List[Callable] = []
    
    def register_agent(self, agent_id: str) -> bool:
        """Register an agent for heartbeat monitoring"""
        with self.lock:
            if agent_id in self.agents:
                return False
            
            self.agents[agent_id] = AgentInfo(
                agent_id=agent_id,
                last_heartbeat=datetime.now()
            )
            return True
    
    def record_heartbeat(self, agent_id: str) -> bool:
        """Record a heartbeat from an agent"""
        with self.lock:
            if agent_id not in self.agents:
                return False
            
            self.agents[agent_id].last_heartbeat = datetime.now()
            self.agents[agent_id].status = "active"
            return True
    
    def record_task_completion(self, agent_id: str, success: bool = True):
        """Record task completion by an agent"""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id].task_count += 1
                if not success:
                    self.agents[agent_id].error_count += 1
                    self.agents[agent_id].last_error_time = datetime.now()
    
    def add_status_callback(self, callback: Callable[[str, str, str], None]):
        """Add a callback for agent status changes"""
        self.status_callbacks.append(callback)
    
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the background monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Background thread to check agent health"""
        while self.monitoring:
            try:
                self._check_agent_health()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Error in agent monitor loop: {e}")
    
    def _check_agent_health(self):
        """Check all registered agents for health status"""
        current_time = datetime.now()
        
        with self.lock:
            for agent_id, agent_info in self.agents.items():
                time_since_heartbeat = current_time - agent_info.last_heartbeat
                
                # Determine new status based on heartbeat age
                if time_since_heartbeat > timedelta(seconds=self.heartbeat_timeout):
                    new_status = "inactive"
                elif time_since_heartbeat > timedelta(seconds=self.warning_threshold):
                    new_status = "warning"
                else:
                    new_status = "active"
                
                # Update status if changed
                if agent_info.status != new_status:
                    old_status = agent_info.status
                    agent_info.status = new_status
                    
                    # Notify callbacks of status change
                    for callback in self.status_callbacks:
                        try:
                            callback(agent_id, old_status, new_status)
                        except Exception as e:
                            print(f"Status callback failed: {e}")
    
    def get_unhealthy_agents(self) -> List[str]:
        """Get list of agents that are not active"""
        with self.lock:
            return [
                agent_id for agent_id, agent_info in self.agents.items()
                if agent_info.status != "active"
            ]


# Usage example
def agent_status_change_callback(agent_id: str, old_status: str, new_status: str):
    """Callback for agent status changes"""
    print(f"Agent {agent_id} status changed from {old_status} to {new_status}")
    if new_status == "inactive":
        print(f"Agent {agent_id} appears to be down, investigating...")

# Create monitor and register callbacks
agent_monitor = AgentHeartbeatMonitor(heartbeat_timeout=120, warning_threshold=60)
agent_monitor.add_status_callback(agent_status_change_callback)

# Register agents
agent_monitor.register_agent("agent-001")
agent_monitor.register_agent("agent-002")

agent_monitor.start_monitoring()

# Simulate heartbeats
agent_monitor.record_heartbeat("agent-001")
agent_monitor.record_task_completion("agent-001", success=True)
```

---

## Pattern 3: Adaptive Retry with Exponential Backoff

### Use Case
Implement intelligent retry logic with exponential backoff and jitter.

### Implementation

```python
import time
import random
import threading
from typing import Callable, Any, Optional
from enum import Enum


class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


class AdaptiveRetryController:
    """Control retries with adaptive backoff strategies"""
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.jitter = jitter
        self.retry_stats = {}  # task_id -> [delays_used, success_count, failure_count]
        self.lock = threading.Lock()
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on strategy and attempt number"""
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        else:  # EXPONENTIAL
            delay = self.base_delay * (2 ** (attempt - 1))
        
        # Cap the delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            jitter_factor = random.uniform(0.8, 1.2)  # ±20% jitter
            delay = delay * jitter_factor
        
        return delay
    
    def execute_with_retry(
        self,
        task_id: str,
        operation: Callable[[], Any],
        should_retry: Callable[[Exception], bool] = lambda e: True
    ) -> tuple[bool, Any, int]:
        """
        Execute an operation with retry logic.
        
        Returns: (success: bool, result: Any, attempts: int)
        """
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                result = operation()
                # Record success
                self._record_attempt(task_id, attempt, success=True)
                return True, result, attempt
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this exception
                if not should_retry(e):
                    self._record_attempt(task_id, attempt, success=False)
                    return False, e, attempt
                
                # If this was the last attempt, don't sleep
                if attempt == self.max_retries:
                    break
                
                # Calculate and apply delay
                delay = self.calculate_delay(attempt)
                print(f"Attempt {attempt} failed for task {task_id}, retrying in {delay:.2f}s: {e}")
                
                time.sleep(delay)
        
        # All attempts failed
        self._record_attempt(task_id, self.max_retries, success=False)
        return False, last_exception, self.max_retries
    
    def _record_attempt(self, task_id: str, attempt: int, success: bool):
        """Record retry statistics"""
        with self.lock:
            if task_id not in self.retry_stats:
                self.retry_stats[task_id] = {
                    'delays_used': [],
                    'success_count': 0,
                    'failure_count': 0,
                    'total_attempts': 0
                }
            
            stats = self.retry_stats[task_id]
            stats['total_attempts'] += 1
            if success:
                stats['success_count'] += 1
            else:
                stats['failure_count'] += 1


# Usage example
def flaky_operation():
    """Example operation that sometimes fails"""
    import random
    if random.random() < 0.7:  # 70% chance of failure
        raise Exception("Random failure")
    return "Success!"

# Create retry controller
retry_controller = AdaptiveRetryController(
    max_retries=5,
    base_delay=1.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL,
    jitter=True
)

# Execute with retry
success, result, attempts = retry_controller.execute_with_retry(
    task_id="flaky-task-001",
    operation=flaky_operation
)

print(f"Operation completed: success={success}, result={result}, attempts={attempts}")
```

---

## Pattern 4: Task Escalation System

### Use Case
Escalate tasks that repeatedly fail or exceed time limits to higher-level handlers.

### Implementation

```python
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, Optional
from enum import Enum


class EscalationLevel(Enum):
    LEVEL_1 = 1  # Basic retry
    LEVEL_2 = 2  # Alternative implementation
    LEVEL_3 = 3  # Reassign to different agent
    LEVEL_4 = 4  # Human intervention
    LEVEL_5 = 5  # Supervisor notification


@dataclass
class EscalationRule:
    level: EscalationLevel
    max_attempts: int
    timeout_seconds: int
    action: Callable  # Function to execute at this level


class TaskEscalationSystem:
    """System for escalating tasks through multiple levels"""
    
    def __init__(self):
        self.escalation_rules: Dict[EscalationLevel, EscalationRule] = {}
        self.task_states = {}  # task_id -> {level, attempts, start_time, ...}
        self.lock = threading.Lock()
        self.escalation_callbacks = []
    
    def add_rule(self, rule: EscalationRule):
        """Add an escalation rule"""
        self.escalation_rules[rule.level] = rule
    
    def register_task(self, task_id: str, task_type: str = "default"):
        """Register a task for escalation monitoring"""
        with self.lock:
            self.task_states[task_id] = {
                'level': EscalationLevel.LEVEL_1,
                'attempts': 0,
                'start_time': datetime.now(),
                'task_type': task_type,
                'last_escalation': datetime.now(),
                'errors': []
            }
    
    def record_failure(self, task_id: str, error: Exception):
        """Record a task failure and check for escalation"""
        with self.lock:
            if task_id not in self.task_states:
                return
            
            state = self.task_states[task_id]
            state['attempts'] += 1
            state['errors'].append({
                'timestamp': datetime.now(),
                'error': str(error),
                'attempt': state['attempts']
            })
            
            # Check if we need to escalate
            current_rule = self.escalation_rules.get(state['level'])
            if not current_rule:
                return
            
            # Escalate if max attempts reached or timeout exceeded
            time_elapsed = datetime.now() - state['start_time']
            should_escalate = (
                state['attempts'] >= current_rule.max_attempts or
                time_elapsed.total_seconds() >= current_rule.timeout_seconds
            )
            
            if should_escalate and state['level'] != max(EscalationLevel):
                # Move to next escalation level
                next_level = EscalationLevel(state['level'].value + 1)
                if next_level in self.escalation_rules:
                    state['level'] = next_level
                    state['last_escalation'] = datetime.now()
                    
                    # Execute escalation action
                    self._execute_escalation(task_id, state, next_level)
    
    def _execute_escalation(self, task_id: str, state: Dict, level: EscalationLevel):
        """Execute escalation action for a task"""
        rule = self.escalation_rules.get(level)
        if not rule:
            return
        
        print(f"Escalating task {task_id} to level {level.value}")
        
        try:
            # Execute the escalation action
            rule.action(task_id, state)
            
            # Notify escalation callbacks
            for callback in self.escalation_callbacks:
                try:
                    callback(task_id, state['level'], state)
                except Exception as e:
                    print(f"Escalation callback failed: {e}")
        except Exception as e:
            print(f"Escalation action failed for task {task_id}: {e}")
    
    def add_escalation_callback(self, callback: Callable[[str, EscalationLevel, Dict], None]):
        """Add a callback for escalation events"""
        self.escalation_callbacks.append(callback)


# Example escalation actions
def level_2_action(task_id: str, state: Dict):
    """Level 2: Try alternative implementation"""
    print(f"Level 2 escalation: Trying alternative implementation for task {task_id}")
    # Implement alternative task execution logic here

def level_3_action(task_id: str, state: Dict):
    """Level 3: Reassign to different agent"""
    print(f"Level 3 escalation: Reassigning task {task_id} to different agent")
    # Implement agent reassignment logic here

def level_4_action(task_id: str, state: Dict):
    """Level 4: Human intervention"""
    print(f"Level 4 escalation: Task {task_id} requires human intervention")
    # Implement human notification logic here

def level_5_action(task_id: str, state: Dict):
    """Level 5: Supervisor notification"""
    print(f"Level 5 escalation: Notifying supervisor about task {task_id}")
    # Implement supervisor notification logic here


# Usage example
escalation_system = TaskEscalationSystem()

# Add escalation rules
escalation_system.add_rule(EscalationRule(
    level=EscalationLevel.LEVEL_1,
    max_attempts=3,
    timeout_seconds=120,
    action=lambda task_id, state: print(f"Level 1: Basic retry for {task_id}")
))

escalation_system.add_rule(EscalationRule(
    level=EscalationLevel.LEVEL_2,
    max_attempts=2,
    timeout_seconds=180,
    action=level_2_action
))

escalation_system.add_rule(EscalationRule(
    level=EscalationLevel.LEVEL_3,
    max_attempts=1,
    timeout_seconds=300,
    action=level_3_action
))

escalation_system.add_rule(EscalationRule(
    level=EscalationLevel.LEVEL_4,
    max_attempts=1,
    timeout_seconds=600,
    action=level_4_action
))

escalation_system.add_rule(EscalationRule(
    level=EscalationLevel.LEVEL_5,
    max_attempts=1,
    timeout_seconds=1200,
    action=level_5_action
))

# Register a task
escalation_system.register_task("problematic-task-001")

# Simulate failures to trigger escalations
for i in range(10):
    escalation_system.record_failure("problematic-task-001", Exception(f"Attempt {i+1} failed"))
    time.sleep(1)
```

---

## Pattern 5: Comprehensive Task Loop Controller

### Use Case
Combine all monitoring elements into a unified task loop controller.

### Implementation

```python
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass


@dataclass
class LoopControllerConfig:
    monitoring_interval: int = 30
    heartbeat_timeout: int = 120
    warning_threshold: int = 60
    default_task_timeout: int = 600
    max_retries: int = 5
    base_retry_delay: float = 1.0
    max_retry_delay: float = 60.0


class ComprehensiveLoopController:
    """Unified controller combining all monitoring and recovery mechanisms"""
    
    def __init__(self, config: LoopControllerConfig = None):
        self.config = config or LoopControllerConfig()
        self.task_monitor = TaskTimeoutMonitor(check_interval=self.config.monitoring_interval)
        self.agent_monitor = AgentHeartbeatMonitor(
            heartbeat_timeout=self.config.heartbeat_timeout,
            warning_threshold=self.config.warning_threshold
        )
        self.retry_controller = AdaptiveRetryController(
            max_retries=self.config.max_retries,
            base_delay=self.config.base_retry_delay,
            max_delay=self.config.max_retry_delay
        )
        self.escalation_system = TaskEscalationSystem()
        
        self.controller_thread = None
        self.running = False
        self.lock = threading.Lock()
    
    def start(self):
        """Start all monitoring components"""
        if self.running:
            return
        
        self.running = True
        self.task_monitor.start_monitoring()
        self.agent_monitor.start_monitoring()
        
        # Start main controller loop
        self.controller_thread = threading.Thread(target=self._controller_loop, daemon=True)
        self.controller_thread.start()
    
    def stop(self):
        """Stop all monitoring components"""
        self.running = False
        self.task_monitor.stop_monitoring()
        self.agent_monitor.stop_monitoring()
        if self.controller_thread:
            self.controller_thread.join(timeout=5)
    
    def register_task(
        self,
        task_id: str,
        timeout_seconds: int = None,
        max_retries: int = None,
        task_type: str = "default"
    ):
        """Register a task with all monitoring systems"""
        timeout = timeout_seconds or self.config.default_task_timeout
        retries = max_retries or self.config.max_retries
        
        # Register with task monitor
        self.task_monitor.register_task(
            task_id=task_id,
            timeout_seconds=timeout,
            max_retries=retries
        )
        
        # Register with escalation system
        self.escalation_system.register_task(task_id, task_type)
    
    def record_task_activity(self, task_id: str):
        """Record task activity across all systems"""
        self.task_monitor.update_task_activity(task_id)
    
    def record_task_completion(self, task_id: str, success: bool = True):
        """Record task completion and update monitoring systems"""
        self.task_monitor.mark_task_completed(task_id)
        
        if not success:
            self.escalation_system.record_failure(task_id, Exception("Task failed"))
    
    def record_agent_heartbeat(self, agent_id: str):
        """Record agent heartbeat"""
        self.agent_monitor.record_heartbeat(agent_id)
    
    def _controller_loop(self):
        """Main controller loop"""
        while self.running:
            try:
                # Perform any additional coordination tasks here
                time.sleep(self.config.monitoring_interval)
            except Exception as e:
                print(f"Error in controller loop: {e}")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        with self.lock:
            return {
                "task_monitor": {
                    "registered_tasks": len(self.task_monitor.tasks),
                    "active_tasks": len([t for t in self.task_monitor.tasks.values() 
                                       if t.state in [TaskState.RUNNING, TaskState.RETRYING]])
                },
                "agent_monitor": {
                    "registered_agents": len(self.agent_monitor.agents),
                    "active_agents": len([a for a in self.agent_monitor.agents.values() 
                                        if a.status == "active"]),
                    "unhealthy_agents": self.agent_monitor.get_unhealthy_agents()
                },
                "system": {
                    "running": self.running
                }
            }


# Usage example
controller = ComprehensiveLoopController(
    LoopControllerConfig(
        monitoring_interval=10,
        heartbeat_timeout=60,
        default_task_timeout=120,
        max_retries=3
    )
)

controller.start()

# Register a task
controller.register_task("comprehensive-task-001", timeout_seconds=180)

# Simulate task activity
controller.record_task_activity("comprehensive-task-001")

# Record agent heartbeat
controller.record_agent_heartbeat("agent-001")

# Get status report
status = controller.get_status_report()
print("Controller Status:", status)

# Stop controller when done
# controller.stop()
```

---

## Best Practices Summary

1. **Use Appropriate Timeouts**: Set realistic timeouts based on task complexity
2. **Implement Exponential Backoff**: Use exponential backoff with jitter for retries
3. **Monitor Agent Health**: Track agent heartbeats and responsiveness
4. **Track Task State**: Maintain comprehensive state information for each task
5. **Implement Escalation**: Have multiple levels of escalation for persistent issues
6. **Provide Adequate Logging**: Log all monitoring and intervention actions
7. **Handle Edge Cases**: Account for system restarts and state persistence
8. **Configure Sensibly**: Adjust parameters based on your specific use case
9. **Test Failure Scenarios**: Verify behavior under various failure conditions
10. **Monitor Performance**: Track monitoring overhead and system performance

---

**Last Updated:** 2026-02-07