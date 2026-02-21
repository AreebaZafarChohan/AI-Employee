# Company Handbook Enforcer - Common Patterns

## Overview
This document describes common integration patterns for enforcing company handbook policies across different systems and workflows.

---

## Pattern 1: Pre-commit Validation Hook

### Use Case
Validate code commits against coding standards and sensitive information policies before allowing the commit to proceed.

### Implementation
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for sensitive information in staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(js|ts|py|java|json|yaml|yml)$')

while IFS= read -r file; do
    if [[ -f "$file" ]]; then
        # Run handbook enforcer on the file
        if ! company-policy-validator.sh "$file"; then
            echo "❌ Policy violation detected in $file"
            echo "Commit blocked. Please fix violations before committing."
            exit 1
        fi
    fi
done <<< "$STAGED_FILES"

echo "✅ All files comply with company policies"
exit 0
```

### Benefits
- Prevents policy violations from entering the codebase
- Provides immediate feedback to developers
- Maintains consistent standards across the team

---

## Pattern 2: Document Upload Interceptor

### Use Case
Validate documents uploaded to shared drives or document management systems against company policies.

### Implementation
```python
from company_handbook_enforcer import CompanyHandbookEnforcer

def upload_handler(file_path, uploader_info):
    enforcer = CompanyHandbookEnforcer()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    result = enforcer.validate_document(content, location=file_path)
    
    if result.is_compliant:
        # Allow upload
        store_document(file_path)
        log_upload_success(uploader_info, file_path)
        return {"status": "success", "message": "Document uploaded successfully"}
    else:
        # Block upload and return violations
        log_policy_violation(uploader_info, file_path, result.violations)
        return {
            "status": "blocked", 
            "message": f"Upload blocked due to {len(result.violations)} policy violations",
            "violations": [v.description for v in result.violations]
        }
```

### Benefits
- Prevents policy-violating documents from being stored
- Provides clear feedback on violations
- Maintains audit trail of attempted uploads

---

## Pattern 3: Continuous Integration Enforcement

### Use Case
Integrate policy validation into CI pipelines to ensure all code changes comply with company standards.

### Implementation
```yaml
# .github/workflows/policy-validation.yml
name: Policy Validation
on: [push, pull_request]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup handbook enforcer
        run: |
          pip install company-handbook-enforcer
          # Configure with organization-specific rules
          cp config/org-rules.json /etc/handbook/rules.json
      
      - name: Validate all documents
        run: |
          find . -name "*.md" -o -name "*.txt" -o -name "*.json" | while read file; do
            echo "Validating $file..."
            python -m company_handbook_enforcer "$file"
            if [ $? -ne 0 ]; then
              echo "❌ Policy violation in $file"
              exit 1
            fi
          done
```

### Benefits
- Automates policy compliance in development workflow
- Prevents violations from reaching production
- Maintains consistent standards across projects

---

## Pattern 4: Email Gateway Filter

### Use Case
Scan outgoing emails for policy violations before delivery to external recipients.

### Implementation
```python
import smtplib
from company_handbook_enforcer import CompanyHandbookEnforcer

def send_email(sender, recipient, subject, body):
    # Only scan external emails
    if is_external_recipient(recipient):
        enforcer = CompanyHandbookEnforcer()
        content = f"Subject: {subject}\n\n{body}"
        
        result = enforcer.validate_document(content, location=f"email_to_{recipient}")
        
        if not result.is_compliant:
            # Handle violations based on severity
            high_severity = [v for v in result.violations if v.severity in ['critical', 'high']]
            
            if high_severity:
                # Block email and notify sender
                notify_violation(sender, recipient, high_severity)
                return {"status": "blocked", "reason": "High severity policy violations detected"}
            else:
                # Allow with warning
                log_warning(sender, recipient, result.violations)
    
    # Send email normally
    return smtp_send(sender, recipient, subject, body)
```

### Benefits
- Prevents accidental disclosure of sensitive information
- Maintains compliance with data protection regulations
- Provides audit trail of email communications

---

## Pattern 5: HR Document Processor

### Use Case
Automatically validate HR documents like job postings, employee handbooks, and policy documents.

### Implementation
```python
from company_handbook_enforcer import CompanyHandbookEnforcer

def process_hr_document(doc_path, doc_type):
    enforcer = CompanyHandbookEnforcer()
    
    with open(doc_path, 'r') as f:
        content = f.read()
    
    # Different validation rules based on document type
    if doc_type == "job_posting":
        # Check for discriminatory language
        content += "\nThis is a job posting document."
    elif doc_type == "employee_handbook":
        # Ensure all required policies are included
        content += "\nThis is an employee handbook document."
    
    result = enforcer.validate_document(content, location=doc_path)
    
    report = {
        "document": doc_path,
        "type": doc_type,
        "compliant": result.is_compliant,
        "violations": [],
        "timestamp": result.timestamp.isoformat()
    }
    
    if not result.is_compliant:
        for violation in result.violations:
            report["violations"].append({
                "rule_id": violation.rule_id,
                "severity": violation.severity,
                "description": violation.description,
                "location": violation.location
            })
    
    # Store report for compliance tracking
    store_compliance_report(report)
    
    return report
```

### Benefits
- Ensures HR documents comply with employment laws
- Maintains consistency in HR communications
- Provides compliance reporting for audits

---

## Pattern 6: API Response Validator

### Use Case
Validate API responses to ensure they don't expose sensitive information or violate data policies.

### Implementation
```python
from flask import Flask, jsonify, g
from company_handbook_enforcer import CompanyHandbookEnforcer

app = Flask(__name__)
enforcer = CompanyHandbookEnforcer()

@app.after_request
def validate_api_response(response):
    # Only validate responses to external consumers
    if hasattr(g, 'is_internal_call') and not g.is_internal_call:
        content = response.get_data(as_text=True)
        
        # Skip validation for error responses
        if response.status_code < 400:
            result = enforcer.validate_document(content, location=f"API_{request.endpoint}")
            
            if not result.is_compliant:
                # Log violations but don't block responses to avoid service disruption
                log_api_violations(request.endpoint, result.violations)
    
    return response
```

### Benefits
- Prevents sensitive data exposure through APIs
- Maintains service availability while monitoring compliance
- Provides insight into API security posture

---

## Pattern 7: Automated Exception Workflow

### Use Case
Handle policy exceptions through an automated approval workflow.

### Implementation
```python
from company_handbook_enforcer import CompanyHandbookEnforcer
import smtplib
from datetime import datetime, timedelta

def request_policy_exception(item_path, violation_desc, business_reason, requester):
    enforcer = CompanyHandbookEnforcer()
    
    # Generate unique exception ID
    exception_id = f"EXC-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(item_path) % 10000}"
    
    exception_request = {
        "id": exception_id,
        "item_path": item_path,
        "violation": violation_desc,
        "business_reason": business_reason,
        "requester": requester,
        "request_date": datetime.now().isoformat(),
        "status": "pending",
        "expires_in_days": 30  # Default expiry
    }
    
    # Determine approvers based on violation type
    approvers = determine_approvers(violation_desc)
    
    # Send approval request
    send_approval_request(exception_request, approvers)
    
    # Store request for tracking
    store_exception_request(exception_request)
    
    return {
        "status": "submitted",
        "exception_id": exception_id,
        "message": f"Exception request submitted to {', '.join(approvers)}"
    }

def process_approval(exception_id, approver, decision, reason=None):
    # Retrieve request
    request = get_exception_request(exception_id)
    
    if decision == "approved":
        # Temporarily allow the item
        add_temporary_allowance(request["item_path"], request["expires_in_days"])
        
        # Update request status
        update_exception_status(exception_id, "approved", approver, reason)
        
        # Log the approval
        log_exception_approval(request, approver, reason)
    else:
        update_exception_status(exception_id, "rejected", approver, reason)
        log_exception_rejection(request, approver, reason)
```

### Benefits
- Formalizes the exception handling process
- Maintains audit trail of approvals
- Provides time-limited exceptions to minimize risk