#!/usr/bin/env python3
"""
Dynamic Workflow Adaptor Engine

A Python script that implements a dynamic workflow adaptor to modify existing 
workflows based on real-time events, priority changes, or resource availability.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

import aiohttp
import redis
from asyncio import Lock


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_adaptor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AdaptationActionType(Enum):
    REROUTE_TASK = "reroute_task"
    ADJUST_PRIORITY = "adjust_priority"
    SWITCH_RESOURCE = "switch_resource"
    UPDATE_WORKFLOW_PATH = "update_workflow_path"
    THROTTLE_WORKFLOW = "throttle_workflow"
    SKIP_OPTIONAL_STEPS = "skip_optional_steps"
    INCREASE_PARALLELISM = "increase_parallelism"
    SET_DEADLINE = "set_deadline"


class WorkflowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    ADAPTING = "adapting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Event:
    """Represents an event that may trigger workflow adaptation."""
    
    def __init__(self, event_type: str, data: Dict[str, Any], timestamp: datetime = None):
        self.id = str(uuid.uuid4())
        self.type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()


class AdaptationRule:
    """Defines a rule for adapting workflows based on events."""
    
    def __init__(self, rule_config: Dict[str, Any]):
        self.id = rule_config["id"]
        self.name = rule_config["name"]
        self.description = rule_config.get("description", "")
        self.enabled = rule_config.get("enabled", True)
        self.trigger = rule_config["trigger"]
        self.actions = rule_config["actions"]
        self.rate_limit = rule_config.get("rate_limit", {})
        self.validation = rule_config.get("validation", {})


class StateBackend(ABC):
    """Abstract base class for state storage backends."""
    
    @abstractmethod
    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    async def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def delete_state(self, workflow_id: str) -> None:
        pass


class RedisStateBackend(StateBackend):
    """Redis implementation for state storage."""
    
    def __init__(self, redis_url: str, namespace: str = "workflow_adaptations"):
        self.redis_client = redis.from_url(redis_url)
        self.namespace = namespace
    
    def _get_key(self, workflow_id: str) -> str:
        return f"{self.namespace}:{workflow_id}"
    
    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> None:
        key = self._get_key(workflow_id)
        self.redis_client.set(key, json.dumps(state))
    
    async def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        key = self._get_key(workflow_id)
        state_json = self.redis_client.get(key)
        if state_json:
            return json.loads(state_json.decode('utf-8'))
        return None
    
    async def delete_state(self, workflow_id: str) -> None:
        key = self._get_key(workflow_id)
        self.redis_client.delete(key)


class MemoryStateBackend(StateBackend):
    """In-memory implementation for state storage (for testing)."""
    
    def __init__(self):
        self._states = {}
    
    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> None:
        self._states[workflow_id] = state
    
    async def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        return self._states.get(workflow_id)
    
    async def delete_state(self, workflow_id: str) -> None:
        if workflow_id in self._states:
            del self._states[workflow_id]


class RateLimiter:
    """Implements rate limiting for adaptation rules."""
    
    def __init__(self, max_per_minute: int = 20, window_seconds: int = 60):
        self.max_per_minute = max_per_minute
        self.window_seconds = window_seconds
        self.requests = {}
        self.lock = Lock()
    
    async def is_allowed(self, rule_id: str) -> bool:
        """Check if a request for a rule is allowed based on rate limits."""
        async with self.lock:
            now = time.time()
            if rule_id not in self.requests:
                self.requests[rule_id] = []
            
            # Remove requests older than the window
            self.requests[rule_id] = [
                req_time for req_time in self.requests[rule_id]
                if now - req_time < self.window_seconds
            ]
            
            # Check if we're under the limit
            if len(self.requests[rule_id]) < self.max_per_minute:
                self.requests[rule_id].append(now)
                return True
            
            return False


class WorkflowAdaptor:
    """Main class for the dynamic workflow adaptor."""
    
    def __init__(self, config_path: str, state_backend: StateBackend):
        self.config_path = config_path
        self.state_backend = state_backend
        self.rules = {}
        self.active_workflows = {}
        self.event_queue = asyncio.Queue()
        self.rate_limiters = {}
        self.session = None
        self.monitoring_interval = 1000  # ms
        self.running = False
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load adaptation rules from the configuration file."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Load adaptation rules
        for rule_config in config["adaptation_rules"]:
            if rule_config.get("enabled", True):
                rule = AdaptationRule(rule_config)
                self.rules[rule.id] = rule
                
                # Create rate limiter for the rule
                rate_limit = rule_config.get("rate_limit", config.get("global_settings", {}).get("default_rate_limit", {}))
                self.rate_limiters[rule.id] = RateLimiter(
                    rate_limit.get("max_per_minute", 20),
                    rate_limit.get("window_seconds", 60)
                )
        
        # Load global settings
        global_settings = config.get("global_settings", {})
        self.monitoring_interval = global_settings.get("event_polling_interval_ms", 1000)
        
        logger.info(f"Loaded {len(self.rules)} adaptation rules")
    
    async def initialize(self):
        """Initialize the adaptor."""
        self.session = aiohttp.ClientSession()
        logger.info("Workflow Adaptor initialized")
    
    async def close(self):
        """Close the adaptor and clean up resources."""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("Workflow Adaptor closed")
    
    async def start_listening(self):
        """Start listening for events that may trigger adaptations."""
        self.running = True
        logger.info("Starting to listen for events...")
        
        while self.running:
            try:
                # Process events from the queue
                while not self.event_queue.empty():
                    event = await self.event_queue.get()
                    await self.process_event(event)
                
                # Poll for events from external sources
                await self.poll_external_events()
                
                # Small delay to prevent busy-waiting
                await asyncio.sleep(self.monitoring_interval / 1000.0)
                
            except Exception as e:
                logger.error(f"Error in event listening loop: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def poll_external_events(self):
        """Poll external event sources for new events."""
        # This is a simplified implementation
        # In a real system, this would connect to actual event sources
        pass
    
    async def process_event(self, event: Event):
        """Process an event and apply relevant adaptations."""
        logger.info(f"Processing event: {event.type} (ID: {event.id})")
        
        for rule_id, rule in self.rules.items():
            try:
                # Check if the event matches the rule's trigger
                if self.event_matches_trigger(event, rule.trigger):
                    # Check rate limit
                    if not await self.rate_limiters[rule_id].is_allowed(rule_id):
                        logger.warning(f"Rate limit exceeded for rule {rule_id}")
                        continue
                    
                    # Apply the rule's actions
                    await self.apply_adaptation_rule(rule, event)
                    
            except Exception as e:
                logger.error(f"Error applying rule {rule_id} for event {event.id}: {str(e)}")
    
    def event_matches_trigger(self, event: Event, trigger: Dict[str, Any]) -> bool:
        """Check if an event matches a rule's trigger conditions."""
        # Check event type
        if event.type != trigger.get("event_type"):
            return False
        
        # Check condition if specified (simplified implementation)
        condition = trigger.get("condition")
        if condition:
            # This is a simplified condition evaluation
            # In a real implementation, you'd use a proper expression evaluator
            try:
                # For demonstration, we'll just check some common patterns
                if "severity === 'critical'" in condition and event.data.get("severity") == "critical":
                    return True
                elif "priority === 'urgent'" in condition and event.data.get("priority") == "urgent":
                    return True
                elif "status === 'unavailable'" in condition and event.data.get("status") == "unavailable":
                    return True
                else:
                    # More complex condition evaluation would go here
                    return True
            except Exception:
                logger.warning(f"Could not evaluate condition: {condition}")
                return False
        
        return True
    
    async def apply_adaptation_rule(self, rule: AdaptationRule, event: Event):
        """Apply an adaptation rule to relevant workflows."""
        logger.info(f"Applying adaptation rule: {rule.name} (ID: {rule.id})")
        
        # For now, we'll just log the planned actions
        # In a real implementation, this would connect to workflow engines
        for action in rule.actions:
            logger.info(f"Planning action: {action['type']} for {action.get('target_workflow', 'current_workflow')}")
            
            # Record the adaptation in workflow state
            # This is a simplified implementation - in reality, you'd have a mapping of
            # events to workflows and apply changes to specific workflow instances
            await self.record_adaptation(event, rule, action)
    
    async def record_adaptation(self, event: Event, rule: AdaptationRule, action: Dict[str, Any]):
        """Record an adaptation in the workflow state."""
        # This is a simplified implementation
        # In a real system, this would update specific workflow instances
        adaptation_record = {
            "event_id": event.id,
            "rule_id": rule.id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "status": "applied"  # or "pending" if async
        }
        
        # In a real implementation, this would update the state of the affected workflow
        logger.info(f"Recorded adaptation: {adaptation_record}")
    
    async def queue_event(self, event: Event):
        """Queue an event for processing."""
        await self.event_queue.put(event)
        logger.debug(f"Queued event: {event.type}")
    
    def inject_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Inject an event directly for testing purposes."""
        event = Event(event_type, data)
        asyncio.create_task(self.queue_event(event))
        return event.id


class EventSourceSimulator:
    """Simulates external event sources for testing."""
    
    def __init__(self, adaptor: WorkflowAdaptor):
        self.adaptor = adaptor
        self.running = False
    
    async def start_simulation(self):
        """Start simulating events."""
        self.running = True
        logger.info("Starting event simulation...")
        
        while self.running:
            try:
                # Simulate different types of events
                import random
                
                event_type = random.choice([
                    "system_error", 
                    "priority_change", 
                    "resource_status_change", 
                    "performance_metrics",
                    "deadline_monitor"
                ])
                
                if event_type == "system_error":
                    data = {
                        "severity": random.choice(["low", "medium", "critical"]),
                        "component": "database",
                        "message": "Connection timeout"
                    }
                elif event_type == "priority_change":
                    data = {
                        "priority": random.choice(["normal", "high", "urgent"]),
                        "workflow_id": f"wf-{random.randint(1000, 9999)}"
                    }
                elif event_type == "resource_status_change":
                    data = {
                        "resource": {
                            "id": f"res-{random.randint(1, 10)}",
                            "type": random.choice(["primary", "secondary"]),
                            "status": random.choice(["available", "unavailable", "degraded"])
                        }
                    }
                elif event_type == "performance_metrics":
                    data = {
                        "system_load": random.uniform(0.1, 0.99),
                        "cpu_utilization": random.uniform(0.1, 0.99),
                        "memory_utilization": random.uniform(0.1, 0.99)
                    }
                elif event_type == "deadline_monitor":
                    data = {
                        "remaining_time": random.randint(100, 7200),  # seconds
                        "progress_met_threshold": random.choice([True, False])
                    }
                
                # Inject the simulated event
                event_id = self.adaptor.inject_event(event_type, data)
                logger.debug(f"Simulated event: {event_type} (ID: {event_id})")
                
                # Wait a bit before simulating the next event
                await asyncio.sleep(random.uniform(1, 5))
                
            except Exception as e:
                logger.error(f"Error in event simulation: {str(e)}")
                await asyncio.sleep(1)
    
    def stop_simulation(self):
        """Stop the event simulation."""
        self.running = False


async def main():
    """Main entry point for the workflow adaptor."""
    # Default paths
    config_path = os.getenv("DYNAMIC_WORKFLOW_ADAPTATION_RULES_PATH", "./assets/adaptation_rules.json")
    state_backend_type = os.getenv("DYNAMIC_WORKFLOW_STATE_PERSISTENCE", "memory")
    
    # Initialize state backend
    if state_backend_type == "redis":
        redis_url = os.getenv("DYNAMIC_WORKFLOW_REDIS_URL", "redis://localhost:6379")
        state_backend = RedisStateBackend(redis_url)
    else:
        state_backend = MemoryStateBackend()
    
    # Create workflow adaptor
    adaptor = WorkflowAdaptor(config_path, state_backend)
    await adaptor.initialize()
    
    # Create event simulator for demonstration
    simulator = EventSourceSimulator(adaptor)
    
    try:
        # Start the adaptor in the background
        adaptor_task = asyncio.create_task(adaptor.start_listening())
        
        # Start the simulator in the background
        simulator_task = asyncio.create_task(simulator.start_simulation())
        
        # Run for a specified time (or indefinitely)
        await asyncio.sleep(30)  # Run for 30 seconds for demo
        
        # Stop the simulator
        simulator.stop_simulation()
        
        # Wait for tasks to complete
        await asyncio.wait_for(simulator_task, timeout=5.0)
        adaptor.running = False
        await asyncio.wait_for(adaptor_task, timeout=5.0)
        
        logger.info("Demo completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Shutting down workflow adaptor...")
        simulator.stop_simulation()
        await adaptor.close()
    except Exception as e:
        logger.error(f"Error in workflow adaptor: {str(e)}")
        simulator.stop_simulation()
        await adaptor.close()


if __name__ == "__main__":
    asyncio.run(main())