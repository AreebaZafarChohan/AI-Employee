# Approval Workflow Enforcer Skill

**Domain:** `silver`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

Automatically manage and enforce company-defined approval workflow rules for various requests.

### Prerequisites

```bash
# Set required environment variables
export APPROVAL_RULES_PATH="./config/approval-rules.json"
export APPROVAL_STATE_PATH="./state/approval_state.json"
export APPROVAL_AUDIT_LOG="./logs/approval-audit.log"
```

### Basic Usage

**Python:**
```python
from approval_enforcer import ApprovalEnforcer
from pathlib import Path
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

# Setup environment variables for demonstration
script_dir = Path("./temp_enforcer_demo")
config_dir = script_dir / "config"
state_dir = script_dir / "state"
logs_dir = script_dir / "logs"

config_dir.mkdir(parents=True, exist_ok=True)
state_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)

os.environ['APPROVAL_RULES_PATH'] = str(config_dir / "workflow-rules.json")
os.environ['APPROVAL_STATE_PATH'] = str(state_dir / "approval_state.json")
os.environ['APPROVAL_AUDIT_LOG'] = str(logs_dir / "approval-audit.log")

# Create dummy workflow rules file
dummy_rules = {
  "version": "1.0",
  "workflows": [
    {
      "id": "demo_deployment",
      "name": "Demo Deployment Approval",
      "stages": [
        {
          "id": "lead_approval",
          "name": "Lead Approval",
          "type": "any_one",
          "required_approvers": 1,
          "approvers_by": {"role": "eng-lead"},
          "timeout_hours": 1
        }
      ]
    }
  ]
}
with open(os.environ['APPROVAL_RULES_PATH'], 'w') as f:
    json.dump(dummy_rules, f, indent=2)

enforcer = ApprovalEnforcer()

request_context = {
    "initiator_id": "test_user",
    "deployment_target": "staging"
}
req = enforcer.start_workflow("demo_deployment", "DEMO-001", request_context)
print(f"Request DEMO-001 created. Status: {req.status}, Current Stage: {req.current_stage_id}, Next Approvers: {req.next_approvers}")

# Simulate approval (assuming 'eng_lead_bob' is resolved as an approver)
if 'eng_lead_bob' in req.next_approvers:
    req = enforcer.record_approval("DEMO-001", "eng_lead_bob", "approved", "Staging looks good.")
    print(f"Request DEMO-001 after approval. Status: {req.status}, Current Stage: {req.current_stage_id}")
else:
    print("Skipping approval simulation as 'eng_lead_bob' is not a resolved approver.")

# Clean up
os.remove(os.environ['APPROVAL_RULES_PATH'])
os.remove(os.environ['APPROVAL_STATE_PATH'])
os.remove(os.environ['APPROVAL_AUDIT_LOG'])
config_dir.rmdir()
state_dir.rmdir()
logs_dir.rmdir()
script_dir.rmdir()
```

## Documentation Structure

-   **[SKILL.md](./SKILL.md)** - Complete specification (1,000+ lines)
-   **[docs/patterns.md](./docs/patterns.md)** - Approval workflow patterns
-   **[docs/impact-checklist.md](./docs/impact-checklist.md)** - Quality assessment
-   **[docs/gotchas.md](./docs/gotchas.md)** - Common pitfalls

## Asset Templates

-   `assets/workflow-rules.json` - Workflow rules configuration
-   `assets/approval_enforcer.py` - Python approval enforcement engine
-   `assets/example-workflow-config.json` - Example workflow definition

## Key Features

✅ **Multi-stage Workflows**
-   Supports sequential, parallel, and hybrid approval flows.
-   Routes requests based on rules (role, department, context).

✅ **Policy Enforcement**
-   Validates approver authority and required approvals.
-   Enforces deadlines and handles escalations.

✅ **Auditability**
-   Maintains clear audit trails for all actions and decisions.
-   Tracks status changes throughout the approval lifecycle.

✅ **Exception Handling**
-   Manages timeouts, rejections, and approver unavailability.
-   Notifies relevant parties on status changes and escalations.

## Anti-Patterns to Avoid

❌ Skipping approvals or stages without proper audit.
❌ Hardcoding approvers in code, leading to inflexibility.
❌ Ignoring workflow exceptions like timeouts or rejections.
❌ Insufficient authority validation for approvers.

See [SKILL.md](./SKILL.md#anti-patterns) for detailed examples.

---

**Maintained by:** Silver Team
**Last Updated:** 2026-02-06
**License:** Internal Use Only
