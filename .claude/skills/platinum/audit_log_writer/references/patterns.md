# Audit Log Writer - Common Patterns

## Overview
This document describes common integration patterns for the Audit Log Writer across different use cases and architectures.

---

## Pattern 1: Structured JSON Audit Logging

### Use Case
Log application events in a structured JSON format for compliance and debugging.

### Implementation

```python
import json
import time
from datetime import datetime
import pytz
from typing import Dict, Any, Optional


class AuditLogger:
    """Structured JSON audit logger with standardized schema"""
    
    def __init__(self, log_path: str, agent_id: str, validate_schema: bool = True):
        self.log_path = log_path
        self.agent_id = agent_id
        self.validate_schema = validate_schema
        self.session_id = self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session identifier"""
        import uuid
        return f"sess-{uuid.uuid4()}"
    
    def _create_log_entry(
        self, 
        action: str, 
        outcome: str, 
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized log entry"""
        entry = {
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "outcome": outcome,
            "session_id": self.session_id,
            "version": "1.0.0"
        }
        
        if task_id:
            entry["task_id"] = task_id
            
        if metadata:
            entry["metadata"] = metadata
            
        if source_ip:
            entry["source_ip"] = source_ip
            
        return entry
    
    def log_action(
        self, 
        action: str, 
        outcome: str, 
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None
    ) -> bool:
        """Log an action with standardized format"""
        try:
            entry = self._create_log_entry(action, outcome, task_id, metadata, source_ip)
            
            if self.validate_schema:
                if not self._validate_entry(entry):
                    print(f"Invalid log entry: {entry}")
                    return False
            
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            
            return True
            
        except Exception as e:
            print(f"Failed to write audit log: {e}")
            return False
    
    def _validate_entry(self, entry: Dict[str, Any]) -> bool:
        """Validate log entry against schema"""
        required_fields = ["timestamp", "agent_id", "action", "outcome"]
        
        for field in required_fields:
            if field not in entry:
                return False
                
        # Validate timestamp format
        try:
            datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            return False
            
        # Validate action is not empty
        if not entry["action"].strip():
            return False
            
        # Validate outcome is one of allowed values
        if entry["outcome"] not in ["success", "failure", "partial"]:
            return False
            
        return True


# Usage example
logger = AuditLogger("./audit.log", "web-agent-001")

# Log a task creation event
logger.log_action(
    action="task_created",
    outcome="success",
    task_id="task-12345",
    metadata={
        "task_type": "data_processing",
        "priority": "high",
        "creator": "user-123"
    }
)

# Log a task claim event
logger.log_action(
    action="task_claimed",
    outcome="success",
    task_id="task-12345",
    source_ip="192.168.1.100"
)
```

---

## Pattern 2: Context-Aware Logging Decorator

### Use Case
Automatically log method calls with context information.

### Implementation

```python
import functools
from typing import Callable, Any


def audit_log(action: str, include_args: bool = False, include_result: bool = False):
    """
    Decorator to automatically log method calls.
    
    Args:
        action: The action name to log
        include_args: Whether to include function arguments in metadata
        include_result: Whether to include function result in metadata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract logger from instance if available
            logger = getattr(args[0], 'audit_logger', None) if args else None
            
            if logger:
                # Prepare metadata
                metadata = {}
                
                if include_args:
                    # Include function arguments (excluding 'self')
                    func_args = args[1:] if args else ()
                    metadata['args'] = [str(arg) for arg in func_args]
                    metadata['kwargs'] = {k: str(v) for k, v in kwargs.items()}
                
                # Log the start of the action
                logger.log_action(
                    action=f"{action}_started",
                    outcome="success",
                    metadata=metadata
                )
            
            try:
                # Execute the original function
                result = func(*args, **kwargs)
                
                if logger:
                    # Log successful completion
                    result_metadata = metadata.copy() if include_result else {}
                    if include_result:
                        result_metadata['result'] = str(result)
                    
                    logger.log_action(
                        action=f"{action}_completed",
                        outcome="success",
                        metadata=result_metadata
                    )
                
                return result
                
            except Exception as e:
                if logger:
                    # Log failure
                    logger.log_action(
                        action=f"{action}_failed",
                        outcome="failure",
                        metadata={
                            **metadata,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                
                raise  # Re-raise the exception
        
        return wrapper
    return decorator


# Example usage
class TaskProcessor:
    def __init__(self, logger):
        self.audit_logger = logger
    
    @audit_log("process_task", include_args=True, include_result=True)
    def process_task(self, task_id: str, data: dict) -> dict:
        """Process a task with automatic audit logging"""
        # Simulate processing
        result = {"processed": True, "output": f"Processed task {task_id}"}
        return result


# Usage
logger = AuditLogger("./audit.log", "processor-agent-001")
processor = TaskProcessor(logger)

# This will automatically log the start, completion, and result
result = processor.process_task("task-67890", {"input": "sample data"})
```

---

## Pattern 3: Batch Logging for Performance

### Use Case
Improve performance by batching log writes instead of writing each entry individually.

### Implementation

```python
import threading
import time
from queue import Queue
from typing import List


class BatchAuditLogger:
    """Audit logger that batches entries for performance"""
    
    def __init__(self, log_path: str, agent_id: str, batch_size: int = 100, flush_interval: int = 5):
        self.log_path = log_path
        self.agent_id = agent_id
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_queue = Queue()
        self.buffer = []
        self.lock = threading.Lock()
        self.shutdown = False
        self.session_id = self._generate_session_id()
        
        # Start the background flush thread
        self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self.flush_thread.start()
    
    def _generate_session_id(self) -> str:
        import uuid
        return f"sess-{uuid.uuid4()}"
    
    def log_action(
        self, 
        action: str, 
        outcome: str, 
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None
    ) -> bool:
        """Add log entry to the queue for batch processing"""
        try:
            entry = {
                "timestamp": datetime.now(pytz.UTC).isoformat(),
                "agent_id": self.agent_id,
                "action": action,
                "outcome": outcome,
                "session_id": self.session_id,
                "version": "1.0.0"
            }
            
            if task_id:
                entry["task_id"] = task_id
            if metadata:
                entry["metadata"] = metadata
            if source_ip:
                entry["source_ip"] = source_ip
            
            self.log_queue.put(entry)
            return True
            
        except Exception as e:
            print(f"Failed to queue audit log: {e}")
            return False
    
    def _flush_worker(self):
        """Background thread to flush log entries"""
        last_flush = time.time()
        
        while not self.shutdown:
            try:
                # Check if we have entries to process
                if not self.log_queue.empty():
                    # Get the next entry
                    try:
                        entry = self.log_queue.get(timeout=0.1)
                        with self.lock:
                            self.buffer.append(entry)
                            
                            # Flush if buffer is full
                            if len(self.buffer) >= self.batch_size:
                                self._flush_buffer()
                    except:
                        # Queue is empty, continue
                        pass
                else:
                    # Check if it's time to flush due to timeout
                    current_time = time.time()
                    if current_time - last_flush >= self.flush_interval:
                        with self.lock:
                            if self.buffer:  # Only flush if there's something to flush
                                self._flush_buffer()
                                last_flush = current_time
                    
                    time.sleep(0.1)  # Small sleep to prevent busy waiting
                    
            except Exception as e:
                print(f"Error in flush worker: {e}")
    
    def _flush_buffer(self):
        """Write buffered entries to the log file"""
        if not self.buffer:
            return
            
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                for entry in self.buffer:
                    f.write(json.dumps(entry) + "\n")
            
            # Clear the buffer
            self.buffer.clear()
            
        except Exception as e:
            print(f"Failed to flush audit log buffer: {e}")
    
    def shutdown_logger(self):
        """Shut down the logger and flush remaining entries"""
        self.shutdown = True
        self.flush_thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
        
        # Flush any remaining entries
        with self.lock:
            if self.buffer:
                self._flush_buffer()


# Usage example
batch_logger = BatchAuditLogger("./audit.log", "batch-agent-001", batch_size=10, flush_interval=2)

# Log multiple entries quickly
for i in range(15):
    batch_logger.log_action(
        action="task_processed",
        outcome="success",
        task_id=f"task-{i}",
        metadata={"iteration": i}
    )

# Shutdown to ensure all entries are flushed
time.sleep(3)  # Allow time for background flush
batch_logger.shutdown_logger()
```

---

## Pattern 4: Conditional Logging Based on Sensitivity

### Use Case
Control logging based on the sensitivity of the data being processed.

### Implementation

```python
import re
from enum import Enum


class LogLevel(Enum):
    """Different levels of logging detail"""
    MINIMAL = "minimal"      # Only basic events
    STANDARD = "standard"    # Standard audit trail
    VERBOSE = "verbose"      # Full details including data


class ConditionalAuditLogger:
    """Audit logger with conditional detail based on sensitivity"""
    
    def __init__(self, log_path: str, agent_id: str, log_level: LogLevel = LogLevel.STANDARD):
        self.log_path = log_path
        self.agent_id = agent_id
        self.log_level = log_level
        self.session_id = self._generate_session_id()
        
        # Patterns for identifying sensitive data
        self.sensitive_patterns = [
            r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
            r'\b\d{16}\b',               # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}\.\d{3}\.\d{3}\.\d{3}\b'  # IP address
        ]
    
    def _generate_session_id(self) -> str:
        import uuid
        return f"sess-{uuid.uuid4()}"
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize sensitive information from data"""
        if isinstance(data, str):
            # Apply sensitive data patterns
            sanitized = data
            for pattern in self.sensitive_patterns:
                sanitized = re.sub(pattern, "[REDACTED]", sanitized)
            return sanitized
        elif isinstance(data, dict):
            # Recursively sanitize dictionary values
            sanitized_dict = {}
            for key, value in data.items():
                sanitized_dict[key] = self._sanitize_data(value)
            return sanitized_dict
        elif isinstance(data, list):
            # Recursively sanitize list items
            return [self._sanitize_data(item) for item in data]
        else:
            # Return as-is for other types
            return data
    
    def log_action(
        self, 
        action: str, 
        outcome: str, 
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        sensitivity_level: LogLevel = LogLevel.STANDARD
    ) -> bool:
        """Log an action with conditional detail based on sensitivity"""
        try:
            # Determine if this entry should be logged based on sensitivity
            if sensitivity_level.value > self.log_level.value:
                return True  # Pretend it was logged successfully
            
            entry = {
                "timestamp": datetime.now(pytz.UTC).isoformat(),
                "agent_id": self.agent_id,
                "action": action,
                "outcome": outcome,
                "session_id": self.session_id,
                "version": "1.0.0"
            }
            
            if task_id:
                entry["task_id"] = task_id
            if source_ip:
                entry["source_ip"] = source_ip
            
            # Add metadata based on sensitivity level
            if metadata and sensitivity_level.value <= self.log_level.value:
                if sensitivity_level == LogLevel.MINIMAL:
                    # Only include non-sensitive metadata
                    safe_metadata = {k: v for k, v in metadata.items() 
                                   if not self._contains_sensitive_data(str(v))}
                    entry["metadata"] = safe_metadata
                elif sensitivity_level == LogLevel.STANDARD:
                    # Sanitize sensitive data
                    entry["metadata"] = self._sanitize_data(metadata)
                else:  # VERBOSE
                    # Include everything as-is
                    entry["metadata"] = metadata
            
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            
            return True
            
        except Exception as e:
            print(f"Failed to write audit log: {e}")
            return False
    
    def _contains_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive data patterns"""
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text):
                return True
        return False


# Usage example
logger = ConditionalAuditLogger("./audit.log", "sensitive-agent-001", LogLevel.STANDARD)

# Log with minimal sensitivity (will be fully logged)
logger.log_action(
    action="user_login",
    outcome="success",
    task_id=None,
    metadata={"username": "johndoe", "login_method": "oauth"},
    sensitivity_level=LogLevel.MINIMAL
)

# Log with standard sensitivity (sensitive data will be sanitized)
logger.log_action(
    action="profile_update",
    outcome="success",
    task_id=None,
    metadata={
        "user_id": "user-123",
        "email": "john.doe@example.com",  # Will be sanitized
        "phone": "555-123-4567"          # Will be sanitized
    },
    sensitivity_level=LogLevel.STANDARD
)
```

---

## Pattern 5: Multi-Destination Logging

### Use Case
Send audit logs to multiple destinations (local file, remote service, etc.).

### Implementation

```python
import requests
from abc import ABC, abstractmethod


class LogDestination(ABC):
    """Abstract base class for log destinations"""
    
    @abstractmethod
    def write_log(self, entry: Dict[str, Any]) -> bool:
        """Write a log entry to this destination"""
        pass


class FileLogDestination(LogDestination):
    """Log destination for local file system"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def write_log(self, entry: Dict[str, Any]) -> bool:
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            return True
        except Exception as e:
            print(f"Failed to write to file {self.file_path}: {e}")
            return False


class RemoteLogDestination(LogDestination):
    """Log destination for remote HTTP service"""
    
    def __init__(self, endpoint_url: str, api_key: str, timeout: int = 30):
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.timeout = timeout
    
    def write_log(self, entry: Dict[str, Any]) -> bool:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.post(
                self.endpoint_url,
                json=entry,
                headers=headers,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to write to remote endpoint {self.endpoint_url}: {e}")
            return False


class MultiDestinationAuditLogger:
    """Audit logger that sends entries to multiple destinations"""
    
    def __init__(self, destinations: List[LogDestination], agent_id: str):
        self.destinations = destinations
        self.agent_id = agent_id
        self.session_id = self._generate_session_id()
        self.errors = []  # Track destinations that are failing
    
    def _generate_session_id(self) -> str:
        import uuid
        return f"sess-{uuid.uuid4()}"
    
    def log_action(
        self, 
        action: str, 
        outcome: str, 
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None
    ) -> Dict[str, bool]:  # Returns success status for each destination
        """Log an action to all configured destinations"""
        entry = {
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "outcome": outcome,
            "session_id": self.session_id,
            "version": "1.0.0"
        }
        
        if task_id:
            entry["task_id"] = task_id
        if metadata:
            entry["metadata"] = metadata
        if source_ip:
            entry["source_ip"] = source_ip
        
        results = {}
        for i, dest in enumerate(self.destinations):
            # Skip destinations that have been failing recently
            if i in self.errors:
                results[f"dest_{i}"] = False
                continue
                
            try:
                success = dest.write_log(entry)
                results[f"dest_{i}"] = success
                
                # Track errors for circuit breaker functionality
                if not success:
                    self.errors.append(i)
                    # Remove from error list after some time or successful write
                elif i in self.errors:
                    self.errors.remove(i)
                    
            except Exception as e:
                print(f"Unexpected error writing to destination {i}: {e}")
                results[f"dest_{i}"] = False
        
        return results


# Usage example
file_dest = FileLogDestination("./local-audit.log")
remote_dest = RemoteLogDestination("https://api.example.com/logs", "your-api-key")

multi_logger = MultiDestinationAuditLogger([file_dest, remote_dest], "multi-agent-001")

# Log an action - will be written to both destinations
results = multi_logger.log_action(
    action="task_completed",
    outcome="success",
    task_id="task-multi-001",
    metadata={"duration_ms": 1500, "result_size_bytes": 1024}
)

print(f"Logging results: {results}")
```

---

## Pattern 6: Log Aggregation and Filtering

### Use Case
Aggregate logs from multiple sources and apply filters for analysis.

### Implementation

```python
import gzip
from datetime import datetime, timedelta
from typing import Iterator, Callable


class LogAggregator:
    """Aggregate and filter audit logs from multiple sources"""
    
    def __init__(self, log_paths: List[str]):
        self.log_paths = log_paths
    
    def read_logs(self) -> Iterator[Dict[str, Any]]:
        """Read logs from all configured paths"""
        for path in self.log_paths:
            try:
                # Handle both regular and gzipped log files
                open_func = gzip.open if path.endswith('.gz') else open
                
                with open_func(path, 'rt', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                print(f"Skipping invalid JSON line: {line[:100]}...")
            except FileNotFoundError:
                print(f"Log file not found: {path}")
            except Exception as e:
                print(f"Error reading log file {path}: {e}")
    
    def filter_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Iterator[Dict[str, Any]]:
        """Filter logs by date range"""
        for log_entry in self.read_logs():
            try:
                entry_time = datetime.fromisoformat(
                    log_entry["timestamp"].replace("Z", "+00:00")
                )
                
                if start_date <= entry_time <= end_date:
                    yield log_entry
            except (KeyError, ValueError):
                # Skip entries without valid timestamp
                continue
    
    def filter_by_agent(self, agent_ids: List[str]) -> Iterator[Dict[str, Any]]:
        """Filter logs by agent ID"""
        for log_entry in self.read_logs():
            try:
                if log_entry["agent_id"] in agent_ids:
                    yield log_entry
            except KeyError:
                # Skip entries without agent_id
                continue
    
    def filter_by_action(self, actions: List[str]) -> Iterator[Dict[str, Any]]:
        """Filter logs by action type"""
        for log_entry in self.read_logs():
            try:
                if log_entry["action"] in actions:
                    yield log_entry
            except KeyError:
                # Skip entries without action
                continue
    
    def aggregate_by_task(self) -> Dict[str, List[Dict[str, Any]]]:
        """Aggregate logs by task ID"""
        task_logs = {}
        
        for log_entry in self.read_logs():
            try:
                task_id = log_entry.get("task_id")
                if task_id:
                    if task_id not in task_logs:
                        task_logs[task_id] = []
                    task_logs[task_id].append(log_entry)
            except Exception:
                # Skip problematic entries
                continue
        
        return task_logs
    
    def search_logs(self, predicate: Callable[[Dict[str, Any]], bool]) -> Iterator[Dict[str, Any]]:
        """Search logs using a custom predicate function"""
        for log_entry in self.read_logs():
            if predicate(log_entry):
                yield log_entry


# Usage example
aggregator = LogAggregator(["./audit1.log", "./audit2.log"])

# Find all task completion events from the last hour
one_hour_ago = datetime.now(pytz.UTC) - timedelta(hours=1)
recent_completions = list(aggregator.filter_by_date_range(one_hour_ago, datetime.now(pytz.UTC)))
task_completions = [log for log in recent_completions if log.get("action") == "task_completed"]

print(f"Found {len(task_completions)} task completions in the last hour")

# Aggregate logs by task to see the full lifecycle
task_aggregates = aggregator.aggregate_by_task()
for task_id, events in list(task_aggregates.items())[:5]:  # Show first 5 tasks
    print(f"\nTask {task_id} lifecycle:")
    for event in sorted(events, key=lambda x: x["timestamp"]):
        print(f"  {event['timestamp']}: {event['action']} ({event['outcome']})")
```

---

## Best Practices Summary

1. **Standardize Schema**: Use consistent field names and value formats across all log entries
2. **Include Essential Context**: Always include timestamp, agent ID, and action type
3. **Validate Before Writing**: Verify log entries conform to schema before writing
4. **Sanitize Sensitive Data**: Remove or mask sensitive information in logs
5. **Batch for Performance**: Use batching to reduce I/O overhead
6. **Handle Errors Gracefully**: Don't let logging failures break the main application
7. **Use Appropriate Detail Levels**: Adjust logging verbosity based on environment
8. **Enable Search and Query**: Structure logs for easy querying and analysis
9. **Implement Rotation**: Manage log file sizes with rotation and retention policies
10. **Monitor Log Health**: Track log writing success rates and storage usage

---

**Last Updated:** 2026-02-07