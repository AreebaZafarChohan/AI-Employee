#!/usr/bin/env python3
"""
Multi-Service Orchestrator Engine

A Python script that implements a multi-service orchestrator to coordinate 
multiple services (APIs, databases, queues) to complete complex workflows automatically.
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
from opentracing import tracer
from opentracing.mocktracer import MockTracer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServiceResult:
    """Represents the result of a service call."""
    
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
        self.timestamp = datetime.now()


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
    
    def __init__(self, redis_url: str, namespace: str = "orchestrator_states"):
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


class CircuitBreaker:
    """Implementation of the circuit breaker pattern."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60, reset_timeout_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.reset_timeout_seconds = reset_timeout_seconds
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_attempt_time = None
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute the function with circuit breaker logic."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.reset_timeout_seconds:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        if self.state == "HALF_OPEN":
            # Test the service by allowing one request
            if self.last_attempt_time and time.time() - self.last_attempt_time < 1:
                # Only allow one test request per second
                raise Exception("Circuit breaker is HALF_OPEN, waiting for test result")
            self.last_attempt_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        """Called when a service call succeeds."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def on_failure(self):
        """Called when a service call fails."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class RetryHandler:
    """Handles retry logic for failed service calls."""
    
    def __init__(self, max_attempts: int = 3, backoff_multiplier: float = 2.0, initial_delay_seconds: float = 1.0):
        self.max_attempts = max_attempts
        self.backoff_multiplier = backoff_multiplier
        self.initial_delay_seconds = initial_delay_seconds
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_attempts - 1:  # Not the last attempt
                    delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_attempts} attempts failed: {str(e)}")
        
        raise last_exception


class ServiceRegistry:
    """Keeps track of available services and their endpoints."""
    
    def __init__(self):
        self.services = {}
    
    def register_service(self, name: str, endpoint: str, auth_token: str = None):
        """Register a service with its endpoint and authentication token."""
        self.services[name] = {
            "endpoint": endpoint,
            "auth_token": auth_token
        }
    
    def get_service_endpoint(self, name: str) -> Optional[str]:
        """Get the endpoint for a registered service."""
        service = self.services.get(name)
        return service["endpoint"] if service else None
    
    def get_service_auth_token(self, name: str) -> Optional[str]:
        """Get the authentication token for a registered service."""
        service = self.services.get(name)
        return service["auth_token"] if service else None


class WorkflowStep:
    """Represents a single step in a workflow."""
    
    def __init__(self, step_config: Dict[str, Any]):
        self.id = step_config["id"]
        self.service = step_config["service"]
        self.endpoint = step_config["endpoint"]
        self.method = step_config.get("method", "GET")
        self.payload_template = step_config.get("payload_template", {})
        self.depends_on = step_config.get("depends_on", [])
        self.condition = step_config.get("condition")
        self.timeout_seconds = step_config.get("timeout_seconds", 30)
        self.retry_policy = step_config.get("retry_policy")
        self.circuit_breaker_config = step_config.get("circuit_breaker")
        self.parallel_branches = step_config.get("parallel_branches", [])


class WorkflowInstance:
    """Represents an instance of a running workflow."""
    
    def __init__(self, workflow_def: Dict[str, Any], input_data: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.workflow_def = workflow_def
        self.input_data = input_data
        self.status = WorkflowStatus.PENDING
        self.steps = {step["id"]: WorkflowStep(step) for step in workflow_def["steps"]}
        self.results = {}
        self.started_at = None
        self.completed_at = None
        self.error = None
    
    def update_result(self, step_id: str, result: ServiceResult):
        """Update the result for a specific step."""
        self.results[step_id] = result
    
    def is_step_ready(self, step_id: str) -> bool:
        """Check if a step is ready to execute based on dependencies."""
        step = self.steps[step_id]
        
        # Check if all dependencies are completed
        for dep_id in step.depends_on:
            if dep_id not in self.results:
                return False
            if not self.results[dep_id].success:
                return False
        
        # Check condition if specified
        if step.condition:
            # Simplified condition evaluation - in a real implementation, 
            # this would be more sophisticated
            return self._evaluate_condition(step.condition)
        
        return True
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a condition string against workflow context."""
        # This is a simplified implementation
        # In a real system, this would use a proper expression evaluator
        try:
            # Replace placeholders with actual values from results
            eval_str = condition
            for step_id, result in self.results.items():
                placeholder = f"{{{step_id}.response}}"
                if placeholder in eval_str:
                    # Convert result data to a boolean representation
                    eval_str = eval_str.replace(placeholder, str(result.success))
            
            return eval(eval_str)
        except Exception:
            logger.error(f"Failed to evaluate condition: {condition}")
            return False


class WorkflowOrchestrator:
    """Main orchestrator class that manages workflow execution."""
    
    def __init__(self, config_path: str, state_backend: StateBackend):
        self.config_path = config_path
        self.state_backend = state_backend
        self.service_registry = ServiceRegistry()
        self.workflows = {}
        self.active_instances = {}
        self.session = None
        
        # Initialize tracing
        self.tracer = MockTracer()
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load workflow definitions from the configuration file."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Register workflows
        for workflow_def in config["workflows"]:
            self.workflows[workflow_def["id"]] = workflow_def
        
        # Set up global settings
        global_settings = config.get("global_settings", {})
        self.default_timeout = global_settings.get("default_timeout_seconds", 30)
        self.max_concurrent = global_settings.get("max_concurrent_workflows", 50)
        
        logger.info(f"Loaded {len(self.workflows)} workflows")
    
    async def initialize(self):
        """Initialize the orchestrator."""
        self.session = aiohttp.ClientSession()
        logger.info("Orchestrator initialized")
    
    async def close(self):
        """Close the orchestrator and clean up resources."""
        if self.session:
            await self.session.close()
        logger.info("Orchestrator closed")
    
    async def start_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> str:
        """Start a new workflow instance."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow_def = self.workflows[workflow_id]
        if not workflow_def.get("enabled", True):
            raise ValueError(f"Workflow {workflow_id} is not enabled")
        
        # Create workflow instance
        instance = WorkflowInstance(workflow_def, input_data)
        instance.started_at = datetime.now()
        instance.status = WorkflowStatus.RUNNING
        
        # Store in active instances
        self.active_instances[instance.id] = instance
        
        # Save initial state
        await self.state_backend.save_state(instance.id, {
            "workflow_id": workflow_id,
            "status": instance.status.value,
            "input_data": instance.input_data,
            "results": {},
            "started_at": instance.started_at.isoformat()
        })
        
        # Execute workflow asynchronously
        asyncio.create_task(self._execute_workflow(instance))
        
        logger.info(f"Started workflow instance {instance.id} for workflow {workflow_id}")
        return instance.id
    
    async def _execute_workflow(self, instance: WorkflowInstance):
        """Execute a workflow instance."""
        span = self.tracer.start_span(f"execute_workflow_{instance.workflow_def['id']}")
        
        try:
            # Execute steps in dependency order
            completed_steps = set()
            max_retries = 5  # Prevent infinite loops in case of circular dependencies
            retry_count = 0
            
            while len(completed_steps) < len(instance.steps) and instance.status == WorkflowStatus.RUNNING:
                # Find ready steps
                ready_steps = [
                    step_id for step_id in instance.steps.keys() 
                    if step_id not in completed_steps and instance.is_step_ready(step_id)
                ]
                
                if not ready_steps:
                    # No steps are ready, check if we're stuck in a loop
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"Workflow {instance.id} appears to be stuck, aborting")
                        instance.status = WorkflowStatus.FAILED
                        instance.error = "Workflow execution appears to be stuck in a loop"
                        break
                    
                    # Wait a bit before checking again
                    await asyncio.sleep(0.5)
                    continue
                
                # Execute ready steps concurrently
                tasks = [self._execute_step(instance, step_id) for step_id in ready_steps]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update completed steps
                for i, step_id in enumerate(ready_steps):
                    if not isinstance(results[i], Exception):
                        completed_steps.add(step_id)
                    else:
                        logger.error(f"Step {step_id} failed in workflow {instance.id}: {results[i]}")
                        instance.status = WorkflowStatus.FAILED
                        instance.error = str(results[i])
                        break
                
                # Save state after each batch of executions
                await self._update_state(instance)
            
            # Set final status
            if instance.status == WorkflowStatus.RUNNING:
                instance.status = WorkflowStatus.COMPLETED
                instance.completed_at = datetime.now()
                logger.info(f"Workflow {instance.id} completed successfully")
            else:
                logger.warning(f"Workflow {instance.id} failed: {instance.error}")
            
            # Save final state
            await self._update_state(instance)
            
        except Exception as e:
            logger.error(f"Unexpected error in workflow {instance.id}: {str(e)}")
            instance.status = WorkflowStatus.FAILED
            instance.error = str(e)
            
            # Save final state
            await self._update_state(instance)
        finally:
            span.finish()
            # Remove from active instances
            if instance.id in self.active_instances:
                del self.active_instances[instance.id]
    
    async def _execute_step(self, instance: WorkflowInstance, step_id: str):
        """Execute a single step in a workflow."""
        span = self.tracer.start_span(f"execute_step_{step_id}")
        
        try:
            step = instance.steps[step_id]
            
            # Prepare payload with template substitution
            payload = self._substitute_placeholders(step.payload_template, instance.results, instance.input_data)
            
            # Get service endpoint
            service_endpoint = self.service_registry.get_service_endpoint(step.service)
            if not service_endpoint:
                raise ValueError(f"Service {step.service} not registered")
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            auth_token = self.service_registry.get_service_auth_token(step.service)
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            # Apply circuit breaker if configured
            circuit_breaker = None
            if step.circuit_breaker_config:
                circuit_breaker = CircuitBreaker(
                    failure_threshold=step.circuit_breaker_config.get("failure_threshold", 5),
                    timeout_seconds=step.circuit_breaker_config.get("timeout_seconds", 60),
                    reset_timeout_seconds=step.circuit_breaker_config.get("reset_timeout_seconds", 300)
                )
            
            # Prepare the service call
            url = f"{service_endpoint.rstrip('/')}/{step.endpoint.lstrip('/')}"
            
            async def make_request():
                timeout = aiohttp.ClientTimeout(total=step.timeout_seconds)
                async with self.session.request(
                    method=step.method,
                    url=url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    response_data = await response.json()
                    if response.status >= 400:
                        raise Exception(f"Service call failed with status {response.status}: {response_data}")
                    return response_data
            
            # Apply retry logic if configured
            if step.retry_policy:
                retry_handler = RetryHandler(
                    max_attempts=step.retry_policy.get("max_attempts", 3),
                    backoff_multiplier=step.retry_policy.get("backoff_multiplier", 2.0),
                    initial_delay_seconds=step.retry_policy.get("initial_delay_seconds", 1.0)
                )
                result_data = await retry_handler.execute_with_retry(make_request)
            else:
                result_data = await make_request()
            
            # Record success
            result = ServiceResult(success=True, data=result_data)
            instance.update_result(step_id, result)
            
            logger.info(f"Step {step_id} in workflow {instance.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Step {step_id} in workflow {instance.id} failed: {str(e)}")
            result = ServiceResult(success=False, error=str(e))
            instance.update_result(step_id, result)
            
            # If this is a required step, fail the whole workflow
            instance.status = WorkflowStatus.FAILED
            
        finally:
            span.finish()
    
    def _substitute_placeholders(self, template: Any, results: Dict[str, ServiceResult], input_data: Dict[str, Any]) -> Any:
        """Substitute placeholders in a template with actual values."""
        if isinstance(template, str):
            # Simple placeholder substitution
            result = template
            for step_id, step_result in results.items():
                placeholder = f"{{{step_id}.response}}"
                if placeholder in result:
                    if step_result.success and step_result.data:
                        # Replace with the actual data from the step result
                        # This is a simplified implementation - in reality, you'd need to handle nested properties
                        result = result.replace(placeholder, json.dumps(step_result.data))
                    
                # Handle input data placeholders
                input_placeholder = f"{{input.{step_id}}}"
                if input_placeholder in result and step_id in input_data:
                    result = result.replace(input_placeholder, json.dumps(input_data[step_id]))
            
            # Handle general input data placeholders
            for key, value in input_data.items():
                input_placeholder = f"{{input.{key}}}"
                if input_placeholder in result:
                    result = result.replace(input_placeholder, json.dumps(value))
            
            return result
        elif isinstance(template, dict):
            return {k: self._substitute_placeholders(v, results, input_data) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._substitute_placeholders(item, results, input_data) for item in template]
        else:
            return template
    
    async def _update_state(self, instance: WorkflowInstance):
        """Update the state of a workflow instance."""
        state = {
            "workflow_id": instance.workflow_def["id"],
            "status": instance.status.value,
            "input_data": instance.input_data,
            "results": {
                step_id: {
                    "success": result.success,
                    "data": result.data,
                    "error": result.error,
                    "timestamp": result.timestamp.isoformat()
                }
                for step_id, result in instance.results.items()
            },
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "error": instance.error
        }
        
        await self.state_backend.save_state(instance.id, state)
    
    async def get_workflow_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow instance."""
        # First check if it's in memory
        if instance_id in self.active_instances:
            instance = self.active_instances[instance_id]
            return {
                "id": instance.id,
                "status": instance.status.value,
                "workflow_id": instance.workflow_def["id"],
                "results": {
                    step_id: {
                        "success": result.success,
                        "data": result.data,
                        "error": result.error
                    }
                    for step_id, result in instance.results.items()
                },
                "started_at": instance.started_at.isoformat() if instance.started_at else None,
                "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
                "error": instance.error
            }
        
        # If not in memory, try loading from state storage
        state = await self.state_backend.load_state(instance_id)
        return state


async def main():
    """Main entry point for the orchestrator."""
    # Default paths
    config_path = os.getenv("ORCHESTRATOR_WORKFLOW_DEFINITIONS_PATH", "./assets/workflow_definitions.json")
    state_backend_type = os.getenv("ORCHESTRATOR_STATE_BACKEND", "memory")
    
    # Initialize state backend
    if state_backend_type == "redis":
        redis_url = os.getenv("ORCHESTRATOR_REDIS_URL", "redis://localhost:6379")
        state_backend = RedisStateBackend(redis_url)
    else:
        state_backend = MemoryStateBackend()
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(config_path, state_backend)
    await orchestrator.initialize()
    
    # Example usage
    try:
        # Start a sample workflow
        workflow_input = {
            "customer_data": {
                "email": "john.doe@example.com",
                "profile": {"name": "John Doe", "country": "US"},
                "plan": "premium"
            }
        }
        
        logger.info("Starting customer_onboarding workflow...")
        instance_id = await orchestrator.start_workflow("customer_onboarding", workflow_input)
        logger.info(f"Started workflow instance: {instance_id}")
        
        # Wait a bit for execution
        await asyncio.sleep(5)
        
        # Check status
        status = await orchestrator.get_workflow_status(instance_id)
        if status:
            logger.info(f"Workflow status: {status['status']}")
            logger.info(f"Results: {status['results']}")
        
        # Another example with order processing
        order_input = {
            "order": {
                "id": "ORD-12345",
                "customer_id": "CUST-67890",
                "items": [{"id": "ITEM-001", "quantity": 2}],
                "total": 99.99,
                "payment_method": "credit_card",
                "shipping_address": "123 Main St, Anytown"
            }
        }
        
        logger.info("Starting order_processing workflow...")
        instance_id2 = await orchestrator.start_workflow("order_processing", order_input)
        logger.info(f"Started workflow instance: {instance_id2}")
        
        # Wait for execution
        await asyncio.sleep(10)
        
        # Check status
        status2 = await orchestrator.get_workflow_status(instance_id2)
        if status2:
            logger.info(f"Workflow status: {status2['status']}")
            logger.info(f"Results: {len(status2['results'])} steps completed")
        
    except KeyboardInterrupt:
        logger.info("Shutting down orchestrator...")
    except Exception as e:
        logger.error(f"Error in orchestrator: {str(e)}")
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())