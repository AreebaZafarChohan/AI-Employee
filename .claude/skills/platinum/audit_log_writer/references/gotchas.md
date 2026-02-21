# Audit Log Writer - Gotchas and Troubleshooting

## Overview
This document outlines common pitfalls, gotchas, and troubleshooting tips for the Audit Log Writer skill.

---

## Common Gotchas

### 1. The "Timestamp Precision" Problem
**Problem:** Inconsistent timestamp precision across different systems/components.
**Symptoms:** Events appearing out of sequence in logs, difficulty correlating events.
**Root Cause:** Different timestamp formats or precisions (milliseconds vs microseconds).
**Solution:** Standardize on ISO 8601 format with consistent precision.
**Prevention:** Always use UTC timezone and consistent precision.

```python
# Gotcha: Inconsistent timestamp precision
def bad_timestamp_logging():
    # Bad: Different precisions in different parts of the system
    log_entry = {
        "timestamp": str(time.time()),  # Unix timestamp (float)
        "agent_id": "agent-1",
        "action": "task_started"
    }
    
    log_entry2 = {
        "timestamp": datetime.now().isoformat(),  # Local timezone, no Z
        "agent_id": "agent-2", 
        "action": "task_completed"
    }

# Solution: Consistent timestamp format
def good_timestamp_logging():
    # Good: Consistent ISO 8601 format with UTC
    from datetime import datetime
    import pytz
    
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),  # UTC with Z suffix
        "agent_id": "agent-1",
        "action": "task_started"
    }
```

---

### 2. The "Missing Context" Anti-Pattern
**Problem:** Audit logs lack sufficient information for debugging.
**Symptoms:** Unable to reconstruct events or diagnose issues from logs alone.
**Root Cause:** Not capturing all relevant context information.
**Solution:** Include comprehensive context in all audit entries.
**Prevention:** Define required context fields upfront.

```python
# Gotcha: Minimal information
def insufficient_logging(task_id):
    # Bad: Missing important context
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "agent_id": "agent-1",
        "action": "task_processed"
        # Missing task_id, outcome, and other context!
    }
    write_log(log_entry)

# Solution: Comprehensive context
def comprehensive_logging(task_id, success=True, duration_ms=0):
    # Good: Complete context
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "agent_id": "agent-1",
        "task_id": task_id,
        "action": "task_processed",
        "outcome": "success" if success else "failure",
        "metadata": {
            "duration_ms": duration_ms,
            "source_component": "task_processor",
            "result_size_bytes": get_result_size(task_id) if success else 0
        }
    }
    write_log(log_entry)
```

---

### 3. The "Schema Drift" Problem
**Problem:** Log schemas evolve inconsistently across different parts of the system.
**Symptoms:** Downstream log consumers breaking, inconsistent field names.
**Root Cause:** Lack of centralized schema management.
**Solution:** Enforce standardized schema with validation.
**Prevention:** Use shared schema definitions and validation.

```python
# Gotcha: Inconsistent schemas
def module_a_logging():
    # Module A uses one schema
    log_entry = {
        "when": datetime.now().isoformat(),
        "who": "agent-1",
        "what": "task_created",
        "task_id": "task-123"
    }

def module_b_logging():
    # Module B uses different schema
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": "agent-1", 
        "action": "task_created",
        "taskId": "task-123"  # Different field name!
    }

# Solution: Centralized schema validation
AUDIT_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "agent_id", "action", "outcome"],
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "agent_id": {"type": "string"},
        "task_id": {"type": "string"},
        "action": {"type": "string"},
        "outcome": {"type": "string", "enum": ["success", "failure", "partial"]}
    }
}

def validated_logging(task_id, action, outcome):
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "agent_id": "agent-1",
        "task_id": task_id,
        "action": action,
        "outcome": outcome
    }
    
    # Validate against schema
    validate(log_entry, AUDIT_SCHEMA)
    write_log(log_entry)
```

---

### 4. The "Performance Bottleneck" Issue
**Problem:** Logging operations blocking application execution.
**Symptoms:** Slower application response times, reduced throughput.
**Root Cause:** Synchronous logging with I/O operations.
**Solution:** Use asynchronous logging with buffering.
**Prevention:** Design logging as non-blocking from the start.

```python
# Gotcha: Synchronous blocking logging
def sync_logging_bottleneck():
    # Bad: Blocking I/O operation in hot path
    for i in range(1000):
        process_item(i)
        # This slows down the loop significantly!
        log_action("item_processed", "success", f"item-{i}")

# Solution: Asynchronous logging
import queue
import threading

class AsyncAuditLogger:
    def __init__(self):
        self.log_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._log_worker, daemon=True)
        self.worker_thread.start()
    
    def _log_worker(self):
        while True:
            try:
                entry = self.log_queue.get(timeout=1)
                if entry is None:  # Shutdown signal
                    break
                write_log(entry)
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in log worker: {e}")
    
    def log_action(self, action, outcome, task_id=None):
        entry = {
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "agent_id": "agent-1",
            "action": action,
            "outcome": outcome
        }
        if task_id:
            entry["task_id"] = task_id
        
        # Non-blocking add to queue
        self.log_queue.put(entry)

# Usage
async_logger = AsyncAuditLogger()
for i in range(1000):
    process_item(i)
    async_logger.log_action("item_processed", "success", f"item-{i}")  # Non-blocking!
```

---

### 5. The "Sensitive Data Exposure" Risk
**Problem:** Audit logs containing sensitive information.
**Symptoms:** Data breaches, compliance violations, privacy issues.
**Root Cause:** Logging data without sanitization.
**Solution:** Implement data sanitization filters.
**Prevention:** Identify and sanitize sensitive data before logging.

```python
# Gotcha: Logging sensitive information
def dangerous_logging(user_data):
    # Bad: Logging potentially sensitive user data
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "agent_id": "auth-service",
        "action": "user_authenticated",
        "metadata": {
            "user_data": user_data,  # Could contain passwords, SSNs, etc.
            "ip_address": "192.168.1.100"
        }
    }
    write_log(log_entry)

# Solution: Sanitize sensitive data
import re

SENSITIVE_PATTERNS = [
    r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
    r'\b\d{16}\b',               # Credit card
    r'"password".*?"([^"]*)"',    # Password fields
]

def sanitize_data(data):
    """Sanitize sensitive information from data"""
    if isinstance(data, str):
        sanitized = data
        for pattern in SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '"[REDACTED]"', sanitized)
        return sanitized
    elif isinstance(data, dict):
        sanitized_dict = {}
        for key, value in data.items():
            sanitized_dict[key] = sanitize_data(value)
        return sanitized_dict
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    else:
        return data

def safe_logging(user_data):
    # Good: Sanitizing sensitive information
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "agent_id": "auth-service",
        "action": "user_authenticated",
        "metadata": {
            "user_data": sanitize_data(user_data),  # Sanitized!
            "ip_address": "192.168.1.100"
        }
    }
    write_log(log_entry)
```

---

## Troubleshooting Guide

### Issue 1: Log Volume Spikes
**Symptoms:** Sudden increase in log volume consuming storage rapidly.
**Diagnosis Steps:**
1. Check for application loops generating excessive logs
2. Review recent code deployments for logging changes
3. Examine system health for error conditions
4. Analyze log patterns to identify root cause

**Resolution:**
- Implement log sampling for high-frequency events
- Add rate limiting to prevent log flooding
- Review and optimize application error handling
- Implement circuit breakers for problematic components

### Issue 2: Schema Validation Failures
**Symptoms:** Log entries being rejected due to schema validation errors.
**Diagnosis Steps:**
1. Check validation error logs for specific failures
2. Review recent code changes affecting logging
3. Examine schema definition for correctness
4. Verify all logging components use same schema

**Resolution:**
- Fix code producing invalid log entries
- Update schema if requirements have changed
- Implement graceful handling of validation errors
- Add schema versioning to handle evolution

### Issue 3: Performance Degradation from Logging
**Symptoms:** Application slowdown correlated with logging activity.
**Diagnosis Steps:**
1. Profile application to identify logging bottlenecks
2. Measure log write performance
3. Check for blocking I/O operations
4. Analyze system resource utilization

**Resolution:**
- Switch to asynchronous logging
- Implement batching for log writes
- Optimize schema validation performance
- Add buffering to reduce I/O frequency

### Issue 4: Log Correlation Issues
**Symptoms:** Difficulty correlating related events across multiple logs.
**Diagnosis Steps:**
1. Check for consistent use of correlation IDs
2. Verify timestamp synchronization across systems
3. Review log format consistency
4. Examine query patterns for correlation

**Resolution:**
- Implement consistent correlation ID generation
- Ensure synchronized clocks across systems
- Standardize log formats and fields
- Add cross-references between related events

### Issue 5: Storage Capacity Issues
**Symptoms:** Log storage filling up faster than expected.
**Diagnosis Steps:**
1. Analyze log volume trends over time
2. Review retention policies and archival
3. Check for log duplication or inefficiencies
4. Examine compression ratios

**Resolution:**
- Optimize retention policies
- Implement more aggressive log compression
- Review and reduce unnecessary logging
- Add alerts for storage capacity

---

## Performance Gotchas

### Gotcha 1: Synchronous File I/O
**Problem:** Blocking file operations in hot paths affecting performance.
**Impact:** Significant performance degradation under load.
**Solution:** Use asynchronous I/O or buffering.

```python
# Bad: Synchronous file writes
def sync_file_logging(entry):
    with open("audit.log", "a") as f:  # Blocking operation
        f.write(json.dumps(entry) + "\n")  # This blocks the thread!

# Good: Buffered writes
class BufferedAuditLogger:
    def __init__(self, filepath, buffer_size=100):
        self.filepath = filepath
        self.buffer_size = buffer_size
        self.buffer = []
        self.lock = threading.Lock()
    
    def log_entry(self, entry):
        with self.lock:
            self.buffer.append(entry)
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        with open(self.filepath, "a") as f:
            for entry in self.buffer:
                f.write(json.dumps(entry) + "\n")
        self.buffer.clear()
```

### Gotcha 2: Expensive Schema Validation
**Problem:** Heavy schema validation in performance-critical paths.
**Impact:** Slows down application execution.
**Solution:** Optimize validation or defer to background process.

```python
# Bad: Expensive validation in hot path
def expensive_validation_logging(entry):
    # Complex validation that takes time
    deeply_nested_schema_validate(entry)  # Slow!
    write_log(entry)

# Good: Optimized validation
def optimized_validation_logging(entry):
    # Quick validation of essential fields only
    if not entry.get("timestamp") or not entry.get("agent_id"):
        raise ValueError("Missing required fields")
    
    # Defer complex validation to background
    queue_validation_task(entry)
    write_log(entry)
```

---

## Configuration Gotchas

### Gotcha 1: Hardcoded Log Paths
**Problem:** Log file paths embedded directly in code.
**Impact:** Makes deployment and configuration management difficult.
**Solution:** Use configurable log destinations.

```yaml
# Bad: Hardcoded paths in config
logging:
  path: "/var/log/app/audit.log"  # Fixed path

# Good: Configurable paths
logging:
  path: "{{AUDIT_LOG_PATH}}"  # Configurable
  level: "{{AUDIT_LOG_LEVEL}}"
  format: "{{AUDIT_LOG_FORMAT}}"
```

### Gotcha 2: No Log Rotation Configuration
**Problem:** Log files growing indefinitely without rotation.
**Impact:** Storage exhaustion over time.
**Solution:** Configure automatic log rotation.

```python
# Bad: No rotation
def simple_logging():
    with open("audit.log", "a") as f:
        f.write(json.dumps(entry) + "\n")

# Good: Rotation handled
import logging.handlers

def setup_rotated_logging():
    logger = logging.getLogger("audit")
    handler = logging.handlers.RotatingFileHandler(
        "audit.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    logger.addHandler(handler)
    return logger
```

---

## Monitoring Gotchas

### Gotcha 1: Missing Critical Metrics
**Problem:** Not tracking metrics that matter for audit log health.
**Solution:** Monitor both system-level and audit-specific metrics.

```python
# Track these critical metrics:
class AuditMetrics:
    def __init__(self):
        self.entries_written = 0
        self.validation_errors = 0
        self.write_failures = 0
        self.average_write_time = []  # Rolling average
        self.storage_usage = 0.0
```

### Gotcha 2: Alerting on Wrong Indicators
**Problem:** Alerts trigger for non-actionable issues or miss critical problems.
**Solution:** Focus alerts on actionable metrics that indicate real problems.

```python
# Bad: Alert on every minor fluctuation
ALERT_IF: log_write_time > 0.01  # Too sensitive

# Good: Alert on meaningful indicators
ALERT_IF: (
    log_write_time > 1.0 AND      # Slow writes (>1s)
    consecutive_minutes > 5 AND   # Sustained for 5+ minutes
    error_rate > 0.05            # And error rate >5%
)
```

---

## Security Gotchas

### Gotcha 1: Insufficient Data Sanitization
**Problem:** Logging sensitive information without proper sanitization.
**Solution:** Implement comprehensive data sanitization.

```python
# Bad: No sanitization
def log_with_sensitive_data(user_input):
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "agent_id": "web-service",
        "action": "form_submitted",
        "metadata": {"form_data": user_input}  # Could contain sensitive data!
    }
    write_log(log_entry)

# Good: Sanitization applied
def log_with_sanitized_data(user_input):
    sanitized_input = sanitize_sensitive_data(user_input)
    log_entry = {
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "agent_id": "web-service", 
        "action": "form_submitted",
        "metadata": {"form_data": sanitized_input}
    }
    write_log(log_entry)
```

### Gotcha 2: Weak Access Controls
**Problem:** Insufficient access controls on audit logs.
**Solution:** Implement proper authentication and authorization.

```python
# Bad: No access controls
def write_log_unsecured(entry):
    with open("audit.log", "a") as f:
        f.write(json.dumps(entry) + "\n")

# Good: Access controls
def write_log_secured(entry, auth_token):
    if not verify_auth_token(auth_token):
        raise PermissionError("Unauthorized access to audit logs")
    
    # Additional checks for authorization
    if not has_audit_write_permission(get_user_from_token(auth_token)):
        raise PermissionError("Insufficient privileges to write audit logs")
    
    with open("audit.log", "a") as f:
        f.write(json.dumps(entry) + "\n")
```

---

## Testing Gotchas

### Gotcha 1: Not Testing Error Scenarios
**Problem:** Code works in ideal conditions but fails during logging errors.
**Solution:** Test logging failure scenarios extensively.

```python
# Test error scenarios
def test_logging_with_storage_full():
    # Simulate full disk scenario
    with mock.patch('builtins.open', side_effect=OSError(28, 'No space left on device')):
        logger = AuditLogger("./audit.log", "test-agent")
        
        # Verify logging handles the error gracefully
        result = logger.log_action("test_action", "success")
        assert result == False  # Should return False on failure
        
        # Verify error was handled appropriately
        assert logger.last_error is not None
```

### Gotcha 2: Not Testing Schema Evolution
**Problem:** Schema changes break existing log consumers.
**Solution:** Test backward compatibility.

```python
def test_backward_compatibility():
    # Test that old schema still works with new code
    old_entry = {
        "timestamp": "2026-02-07T10:30:00Z",
        "agent_id": "test-agent",
        "action": "test_action",
        "outcome": "success"
        # Missing new fields
    }
    
    # Should still validate successfully
    assert validate_schema(old_entry) == True
    
    # Test that new schema works too
    new_entry = {
        "timestamp": "2026-02-07T10:30:00Z",
        "agent_id": "test-agent", 
        "action": "test_action",
        "outcome": "success",
        "new_field": "value"
    }
    
    assert validate_schema(new_entry) == True
```

---

**Last Updated:** 2026-02-07