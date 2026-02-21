# Company Handbook Enforcer Skill

## Overview

**Skill Name:** `company_handbook_enforcer`
**Domain:** `foundation`
**Purpose:** Apply company rules and policies to tasks, documents, and decisions with consistent validation, exception handling, and audit trails to ensure compliance with organizational standards.

**Core Capabilities:**
- Policy validation against company handbook rules
- Automated compliance checking for documents and tasks
- Exception handling and approval workflows
- Audit logging for policy enforcement actions
- Configurable rule sets with version control

**When to Use:**
- Validating new documents against company policies
- Checking task descriptions for compliance requirements
- Enforcing coding standards in development workflows
- Applying HR policies to employee communications
- Ensuring legal compliance in external communications

**When NOT to Use:**
- Personal projects outside company governance
- Experimental or research activities without oversight
- Emergency situations requiring rapid deviation from policy
- Third-party tools without integration capabilities

## Impact Analysis

### Security Impact: MEDIUM
- Policy enforcement prevents accidental disclosure of sensitive information
- Rule configurations may contain sensitive policy details
- Audit logs could contain confidential information
- Access controls required for rule modification

### System Impact: HIGH
- Integration with document management systems required
- Real-time validation may impact performance of authoring tools
- Rule updates must be propagated across all systems
- Backup and versioning of rule configurations needed

### Operational Impact: CRITICAL
- False positives may block legitimate work
- Policy updates require careful rollout planning
- Exception handling processes must be well-defined
- Regular rule maintenance and updates required

### Business Impact: CRITICAL
- Ensures compliance with legal and regulatory requirements
- Reduces risk of policy violations and associated penalties
- Maintains consistent application of company standards
- Supports corporate governance initiatives

## Environment Variables

### Required Variables
```
HANDBOOK_RULES_PATH=/path/to/rules/config.json
AUDIT_LOG_PATH=/var/log/handbook-audit.log
POLICY_EXCEPTIONS_PATH=/path/to/exceptions.json
```

### Optional Variables
```
HANDBOOK_DEBUG_MODE=false
HANDBOOK_CACHE_TTL=3600
HANDBOOK_MAX_FILE_SIZE=10485760  # 10MB
HANDBOOK_TIMEOUT_SECONDS=30
HANDBOOK_RULE_VERSION=v1.0.0
HANDBOOK_AUDIT_LEVEL=info
HANDBOOK_EXCEPTION_APPROVERS=admin@example.com
```

## Network and Authentication Implications

### Authentication Requirements
- LDAP/Active Directory integration for user identification
- OAuth/JWT tokens for API access to validation services
- Certificate-based authentication for secure rule updates
- Multi-factor authentication for rule modification access

### Network Considerations
- Local rule cache to minimize network dependencies
- Secure HTTPS connections for remote rule updates
- Firewall rules allowing access to central policy repository
- Bandwidth considerations for large document validation

### Integration Points
- Document management systems (SharePoint, Google Drive, etc.)
- Code repository systems (GitHub, GitLab, Bitbucket)
- Communication platforms (Slack, Teams, email systems)
- HR systems for personnel policy enforcement

## Blueprints

### Blueprint 1: Policy Validation Script (Bash)
```bash
#!/usr/bin/env bash
# company-policy-validator.sh
# Validates documents against company handbook policies

set -euo pipefail

# Configuration
RULES_PATH="${HANDBOOK_RULES_PATH:-/etc/handbook/rules.json}"
AUDIT_LOG="${AUDIT_LOG_PATH:-/tmp/handbook-audit.log}"
DEBUG="${HANDBOOK_DEBUG_MODE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_event() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local user=$(whoami)
    
    echo "{\"timestamp\":\"${timestamp}\",\"level\":\"${level}\",\"user\":\"${user}\",\"message\":\"${message}\"}" >> "${AUDIT_LOG}"
}

# Validate input file
validate_document() {
    local file_path="$1"
    local violations=()
    
    if [[ ! -f "$file_path" ]]; then
        echo -e "${RED}Error: File does not exist: ${file_path}${NC}" >&2
        return 1
    fi
    
    # Check file size
    local max_size=${HANDBOOK_MAX_FILE_SIZE:-10485760}
    local file_size=$(stat -c%s "$file_size")
    if [[ $file_size -gt $max_size ]]; then
        violations+=("File exceeds maximum size limit of $(($max_size / 1024))KB")
    fi
    
    # Read file content
    local content
    content=$(cat "$file_path")
    
    # Load rules
    if [[ ! -f "$RULES_PATH" ]]; then
        echo -e "${RED}Error: Rules file not found: ${RULES_PATH}${NC}" >&2
        return 1
    fi
    
    # Check for prohibited patterns (simplified example)
    # In a real implementation, this would use jq to parse rules.json
    if echo "$content" | grep -qiE "(password|secret|token|api_key|private_key)"; then
        violations+=("Potential sensitive information detected")
    fi
    
    if echo "$content" | grep -qiE "(confidential|proprietary|internal use only)"; then
        violations+=("Confidential marking detected without proper authorization")
    fi
    
    # Log validation event
    if [[ ${#violations[@]} -eq 0 ]]; then
        log_event "INFO" "Document validated successfully: $file_path"
        echo -e "${GREEN}✓ Document complies with company policies${NC}"
        return 0
    else
        log_event "WARN" "Policy violations found in $file_path: ${violations[*]}"
        echo -e "${RED}✗ Policy violations detected:${NC}"
        for violation in "${violations[@]}"; do
            echo -e "  - $violation"
        done
        return 1
    fi
}

# Main execution
main() {
    if [[ $# -ne 1 ]]; then
        echo "Usage: $0 <document_path>"
        exit 1
    fi
    
    local doc_path="$1"
    
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Validating document: $doc_path"
        echo "Debug: Using rules from: $RULES_PATH"
    fi
    
    validate_document "$doc_path"
    local result=$?
    
    exit $result
}

main "$@"
```

### Blueprint 2: Policy Enforcement Class (Python)
```python
#!/usr/bin/env python3
"""
company_handbook_enforcer.py
Enforce company handbook policies on documents and tasks
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PolicyViolation:
    """Represents a policy violation found during enforcement."""
    rule_id: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    location: Optional[str] = None  # file path, section, etc.
    suggested_fix: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a policy validation."""
    is_compliant: bool
    violations: List[PolicyViolation]
    timestamp: datetime
    processed_by: str


class CompanyHandbookEnforcer:
    """
    Enforces company handbook policies on documents, tasks, and decisions.
    
    This class provides methods to validate content against configured
    company policies and generate reports on compliance status.
    """
    
    def __init__(self, rules_path: Optional[str] = None, audit_log_path: Optional[str] = None):
        """
        Initialize the enforcer with rules and audit configuration.
        
        Args:
            rules_path: Path to the JSON file containing policy rules
            audit_log_path: Path to the audit log file
        """
        self.rules_path = rules_path or os.getenv('HANDBOOK_RULES_PATH', '/etc/handbook/rules.json')
        self.audit_log_path = audit_log_path or os.getenv('AUDIT_LOG_PATH', '/var/log/handbook-audit.log')
        self.cache_ttl = int(os.getenv('HANDBOOK_CACHE_TTL', '3600'))
        self.timeout_seconds = int(os.getenv('HANDBOOK_TIMEOUT_SECONDS', '30'))
        
        # Configure logging
        self.logger = self._setup_logger()
        
        # Load rules
        self.rules = self._load_rules()
        
        # Track last load time for cache invalidation
        self.last_loaded = datetime.now()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for audit trail."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create file handler for audit log
        handler = logging.FileHandler(self.audit_log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_rules(self) -> Dict:
        """Load policy rules from the configured path."""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                self.logger.info(f"Loaded policy rules from {self.rules_path}")
                return rules
        except FileNotFoundError:
            self.logger.error(f"Rules file not found: {self.rules_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in rules file {self.rules_path}: {str(e)}")
            return {}
    
    def refresh_rules(self) -> bool:
        """Refresh the loaded rules from the file."""
        current_time = datetime.now()
        if (current_time - self.last_loaded).seconds > self.cache_ttl:
            self.rules = self._load_rules()
            self.last_loaded = current_time
            return True
        return False
    
    def validate_document(self, content: str, location: Optional[str] = None) -> ValidationResult:
        """
        Validate document content against company policies.
        
        Args:
            content: The content to validate
            location: Optional location identifier (e.g., file path)
            
        Returns:
            ValidationResult object with compliance status and violations
        """
        violations = []
        user = os.getenv('USER', 'unknown')
        
        # Check for sensitive information
        sensitive_patterns = [
            (r'(password|secret|token|api_key|private_key)', 'Critical: Potential credentials exposed'),
            (r'(confidential|proprietary|internal use only)', 'Warning: Confidential marking without authorization'),
            (r'(CEO|CFO|CTO|VP|Director)\s+compensation', 'Info: Executive compensation details require approval'),
        ]
        
        for pattern, description in sensitive_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(PolicyViolation(
                    rule_id=f"sensitive_{pattern.replace('|', '_')}",
                    severity="high" if "credentials" in description else "medium",
                    description=description,
                    location=f"{location}:{match.start()}-{match.end()}" if location else None
                ))
        
        # Check for policy-specific terms
        if 'rules' in self.rules:
            for rule in self.rules.get('rules', []):
                if rule.get('enabled', True):
                    rule_pattern = rule.get('pattern', '')
                    rule_severity = rule.get('severity', 'medium')
                    rule_description = rule.get('description', 'Policy violation')
                    
                    if rule_pattern:
                        matches = re.finditer(rule_pattern, content, re.IGNORECASE)
                        for match in matches:
                            violations.append(PolicyViolation(
                                rule_id=rule.get('id', 'unknown_rule'),
                                severity=rule_severity,
                                description=rule_description,
                                location=f"{location}:{match.start()}-{match.end()}" if location else None
                            ))
        
        # Create validation result
        is_compliant = len(violations) == 0
        result = ValidationResult(
            is_compliant=is_compliant,
            violations=violations,
            timestamp=datetime.now(),
            processed_by=user
        )
        
        # Log the validation event
        self.logger.info(f"Validation completed for {location or 'content'}. "
                         f"Compliant: {is_compliant}, Violations: {len(violations)}")
        
        return result
    
    def validate_task(self, task_title: str, task_description: str) -> ValidationResult:
        """
        Validate a task against company policies.
        
        Args:
            task_title: The task title
            task_description: The task description
            
        Returns:
            ValidationResult object with compliance status and violations
        """
        combined_content = f"{task_title}\n\n{task_description}"
        return self.validate_document(combined_content, location="task")
    
    def generate_compliance_report(self, results: List[ValidationResult]) -> Dict:
        """
        Generate a compliance report from validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Dictionary containing compliance statistics
        """
        total_validated = len(results)
        compliant_count = sum(1 for r in results if r.is_compliant)
        non_compliant_count = total_validated - compliant_count
        
        # Count violations by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for result in results:
            for violation in result.violations:
                severity = violation.severity.lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_validated': total_validated,
            'compliant_count': compliant_count,
            'non_compliant_count': non_compliant_count,
            'compliance_rate': compliant_count / total_validated if total_validated > 0 else 0,
            'severity_breakdown': severity_counts,
            'summary': f"{compliant_count}/{total_validated} items compliant ({(compliant_count/total_validated)*100:.1f}%)"
        }
        
        return report
    
    def request_exception(self, item_location: str, reason: str, approver_email: str) -> bool:
        """
        Request an exception to policy enforcement.
        
        Args:
            item_location: Location of the item needing exception
            reason: Reason for requesting the exception
            approver_email: Email of the person who can approve the exception
            
        Returns:
            Boolean indicating if the exception request was submitted successfully
        """
        exception_request = {
            'request_id': f"EXC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'item_location': item_location,
            'reason': reason,
            'requested_by': os.getenv('USER', 'unknown'),
            'requested_at': datetime.now().isoformat(),
            'approver_email': approver_email,
            'status': 'pending'
        }
        
        # Log the exception request
        self.logger.warning(f"Exception requested: {exception_request}")
        
        # In a real implementation, this would send an email or create a ticket
        # For now, we'll just log it
        print(f"Exception request submitted: {exception_request['request_id']}")
        return True


def main():
    """Example usage of the CompanyHandbookEnforcer."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: company_handbook_enforcer.py <document_path>")
        sys.exit(1)
    
    doc_path = sys.argv[1]
    
    # Initialize enforcer
    enforcer = CompanyHandbookEnforcer()
    
    # Read document
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {doc_path}")
        sys.exit(1)
    
    # Validate document
    result = enforcer.validate_document(content, location=doc_path)
    
    # Print results
    if result.is_compliant:
        print("✓ Document complies with company policies")
        sys.exit(0)
    else:
        print(f"✗ Found {len(result.violations)} policy violation(s):")
        for violation in result.violations:
            severity_marker = "!" if violation.severity.lower() in ['critical', 'high'] else "?"
            print(f"  {severity_marker} [{violation.severity.upper()}] {violation.description}")
            if violation.location:
                print(f"    Location: {violation.location}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Blueprint 3: Rule Configuration Template (JSON)
```json
{
  "version": "1.0.0",
  "last_updated": "2026-02-06T00:00:00Z",
  "rules": [
    {
      "id": "cred_exposure",
      "pattern": "(password|secret|token|api_key|private_key)",
      "severity": "high",
      "description": "Potential credentials exposed in content",
      "enabled": true,
      "action": "block",
      "suggested_fix": "Remove credentials and use secure storage"
    },
    {
      "id": "conf_marking",
      "pattern": "(confidential|proprietary|internal use only)",
      "severity": "medium",
      "description": "Confidential marking detected without proper authorization",
      "enabled": true,
      "action": "warn",
      "suggested_fix": "Verify proper authorization for confidential marking"
    },
    {
      "id": "exec_comp",
      "pattern": "(CEO|CFO|CTO|VP|Director)\\s+compensation",
      "severity": "high",
      "description": "Executive compensation details require approval",
      "enabled": true,
      "action": "review",
      "suggested_fix": "Submit for executive approval before sharing"
    },
    {
      "id": "legal_disclaimer",
      "pattern": "legal disclaimer required",
      "severity": "medium",
      "description": "Legal disclaimer missing from document",
      "enabled": true,
      "action": "warn",
      "suggested_fix": "Add required legal disclaimer"
    },
    {
      "id": "brand_guidelines",
      "pattern": "company logo|brand guidelines",
      "severity": "low",
      "description": "Brand guidelines not followed",
      "enabled": true,
      "action": "info",
      "suggested_fix": "Review brand guidelines for proper usage"
    }
  ],
  "exceptions": [
    {
      "id": "dev_credentials",
      "pattern": "/development/",
      "description": "Allow credentials in development environments",
      "approvers": ["admin@example.com"],
      "expires": "2026-12-31T23:59:59Z"
    }
  ],
  "metadata": {
    "created_by": "Company Governance Team",
    "reviewed_by": "Legal and Compliance Team",
    "next_review_date": "2026-05-06T00:00:00Z"
  }
}
```

## Pre-Deployment Validation Checklist

### Configuration Validation
- [ ] Verify HANDBOOK_RULES_PATH points to a valid JSON file
- [ ] Confirm AUDIT_LOG_PATH directory is writable
- [ ] Check that all required environment variables are set
- [ ] Validate rule configuration syntax using schema
- [ ] Test exception approval workflow

### Security Validation
- [ ] Ensure rules file has appropriate permissions (600)
- [ ] Verify audit logs are protected from unauthorized access
- [ ] Confirm sensitive rule information is encrypted
- [ ] Test authentication mechanisms for rule updates
- [ ] Validate that credentials are not stored in rules

### Functional Validation
- [ ] Test validation on sample documents with violations
- [ ] Verify exception handling process works correctly
- [ ] Confirm audit logging captures all required events
- [ ] Test performance with large documents
- [ ] Validate integration with target systems

### Operational Validation
- [ ] Verify backup and recovery procedures for rules
- [ ] Test rule update propagation mechanism
- [ ] Confirm monitoring and alerting for failures
- [ ] Validate rollback procedures for rule changes
- [ ] Test failover mechanisms if applicable

## Anti-Patterns

### Anti-Pattern 1: Hardcoded Policy Exceptions
**Problem:** Embedding policy exceptions directly in code rather than using configuration
**Risk:** Makes policies difficult to update and creates inconsistent enforcement
**Solution:** Use configuration-driven exception handling with proper approval workflows

**Wrong:**
```python
# Bad: Hardcoded exception
if user.department == "engineering":
    skip_policy_check("cred_exposure")
```

**Correct:**
```python
# Good: Configuration-driven exception
def should_skip_policy(user_dept, policy_id):
    exceptions = load_exceptions_config()
    for exc in exceptions:
        if exc.policy_id == policy_id and user_dept in exc.departments:
            return True, exc.approval_required
    return False, False
```

### Anti-Pattern 2: Inconsistent Severity Classification
**Problem:** Applying different severity levels to the same type of violation across systems
**Risk:** Creates confusion and inconsistent remediation priorities
**Solution:** Establish standardized severity classification based on impact

**Wrong:**
```python
# Bad: Inconsistent severity
if contains_password(text):
    if source == "email": 
        severity = "medium"  # Password in email is medium
    elif source == "document":
        severity = "high"    # Password in doc is high
```

**Correct:**
```python
# Good: Consistent severity
VIOLATION_SEVERITY_MAP = {
    "cred_exposure": "high",
    "conf_marking": "medium",
    "exec_comp": "high"
}

def get_violation_severity(rule_id):
    return VIOLATION_SEVERITY_MAP.get(rule_id, "medium")
```

### Anti-Pattern 3: Blocking Critical Workflows
**Problem:** Overly strict policy enforcement that blocks essential business operations
**Risk:** Causes productivity loss and encourages policy circumvention
**Solution:** Implement risk-based enforcement with override mechanisms for critical operations

**Wrong:**
```python
# Bad: Unconditional blocking
if has_policy_violation(content):
    raise PolicyViolationError("Content blocked due to policy violation")
```

**Correct:**
```python
# Good: Risk-based enforcement
def enforce_policy(content, context):
    violations = check_policy_violations(content)
    
    # Allow overrides for critical operations
    if context.is_critical_operation:
        return handle_critical_operation(violations, content)
    
    # Apply standard enforcement
    return apply_standard_enforcement(violations)
```

### Anti-Pattern 4: Insufficient Audit Trail
**Problem:** Not logging sufficient information to investigate policy violations
**Risk:** Inability to understand why violations occurred or who approved exceptions
**Solution:** Maintain comprehensive audit logs with all relevant context

**Wrong:**
```python
# Bad: Minimal logging
logger.warning(f"Policy violation: {rule_id}")
```

**Correct:**
```python
# Good: Comprehensive audit trail
audit_log = {
    "timestamp": datetime.utcnow().isoformat(),
    "event_type": "policy_violation",
    "user": get_current_user(),
    "source_ip": get_client_ip(),
    "rule_id": rule_id,
    "severity": severity,
    "content_preview": content[:100],  # Sanitized preview
    "location": location,
    "action_taken": action,
    "session_id": get_session_id()
}
logger.warning(json.dumps(audit_log))
```

### Anti-Pattern 5: Static Rule Updates
**Problem:** Manual rule updates without version control or approval process
**Risk:** Inconsistent policies across systems, unauthorized changes
**Solution:** Implement automated rule distribution with approval workflow

**Wrong:**
```bash
# Bad: Manual rule updates
scp new-rules.json server:/etc/handbook/rules.json
ssh server systemctl restart handbook-enforcer
```

**Correct:**
```python
# Good: Automated rule management
class RuleManager:
    def update_rules(self, new_rules, approver):
        """Update rules with approval workflow and versioning."""
        old_version = self.get_current_version()
        new_version = self.generate_new_version(old_version)
        
        # Store with version info
        self.store_versioned_rules(new_rules, new_version, approver)
        
        # Notify all enforcers to update
        self.notify_enforcers(new_version)
        
        # Log the update
        self.audit_rule_update(old_version, new_version, approver)
```