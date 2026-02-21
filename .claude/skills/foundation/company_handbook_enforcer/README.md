# Company Handbook Enforcer Skill

**Domain:** `foundation`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

This skill provides comprehensive company handbook policy enforcement with configurable rules, validation, and audit trails. It helps ensure compliance with organizational standards across documents, tasks, and decisions.

### Prerequisites
- Python 3.8+
- Bash shell environment
- JSON processing tools (jq recommended)

### Installation
1. Clone or copy the skill assets to your system
2. Ensure the required environment variables are set
3. Place the rule configuration file in the designated location
4. Make the scripts executable: `chmod +x *.sh`

### Configuration
Set the required environment variables:
```bash
export HANDBOOK_RULES_PATH=/path/to/rules/config.json
export AUDIT_LOG_PATH=/var/log/handbook-audit.log
export POLICY_EXCEPTIONS_PATH=/path/to/exceptions.json
```

## Core Components

### 1. Policy Validation Script
The `company-policy-validator.sh` script validates documents against company handbook policies. It checks for sensitive information, proper markings, and other policy requirements.

Usage:
```bash
./company-policy-validator.sh /path/to/document.txt
```

### 2. Policy Enforcement Class
The `company_handbook_enforcer.py` Python module provides programmatic access to policy enforcement capabilities. It includes methods for validating documents, tasks, and generating compliance reports.

Usage:
```python
from company_handbook_enforcer import CompanyHandbookEnforcer

enforcer = CompanyHandbookEnforcer()
result = enforcer.validate_document(content, location="my-document.txt")
```

### 3. Rule Configuration
The `rules.json` file defines the policies to enforce, including patterns to detect, severity levels, and suggested fixes.

## Environment Variables

### Required Variables
- `HANDBOOK_RULES_PATH`: Path to the JSON file containing policy rules
- `AUDIT_LOG_PATH`: Path to the audit log file
- `POLICY_EXCEPTIONS_PATH`: Path to the exceptions configuration

### Optional Variables
- `HANDBOOK_DEBUG_MODE`: Enable debug output (default: false)
- `HANDBOOK_CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `HANDBOOK_MAX_FILE_SIZE`: Maximum file size in bytes (default: 10485760)
- `HANDBOOK_TIMEOUT_SECONDS`: Timeout for validation in seconds (default: 30)
- `HANDBOOK_RULE_VERSION`: Expected rule version (default: v1.0.0)
- `HANDBOOK_AUDIT_LEVEL`: Audit logging level (default: info)
- `HANDBOOK_EXCEPTION_APPROVERS`: Comma-separated list of exception approvers

## Integration Examples

### Git Pre-commit Hook
Add to `.git/hooks/pre-commit` to validate code changes:
```bash
#!/bin/bash
# Check for sensitive information in staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(js|ts|py|java|json|yaml|yml)$')

while IFS= read -r file; do
    if [[ -f "$file" ]]; then
        if ! ./company-policy-validator.sh "$file"; then
            echo "❌ Policy violation detected in $file"
            exit 1
        fi
    fi
done <<< "$STAGED_FILES"
```

### Document Upload Validation
Integrate into document management systems:
```python
def validate_upload(file_path):
    import subprocess
    result = subprocess.run(['./company-policy-validator.sh', file_path], 
                          capture_output=True, text=True)
    return result.returncode == 0
```

## Best Practices

1. **Regular Rule Updates**: Review and update policy rules regularly to reflect changing requirements
2. **Exception Management**: Use the exception workflow for legitimate deviations from policy
3. **Audit Monitoring**: Regularly review audit logs for patterns or recurring issues
4. **Performance Considerations**: Monitor validation performance, especially with large documents
5. **Testing**: Thoroughly test new rules in a staging environment before production deployment

## Troubleshooting

Refer to the `docs/gotchas.md` file for common issues and solutions.

For additional support, consult the integration patterns in `docs/patterns.md` and the impact checklist in `docs/impact-checklist.md`.