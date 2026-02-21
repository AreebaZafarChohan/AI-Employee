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