# Approval Workflow Enforcer Skill

## Overview

**Skill Name:** `approval_workflow_enforcer`
**Domain:** `silver`
**Purpose:** Automatically manage and enforce company-defined approval workflow rules, ensuring that requests (e.g., code deployments, budget requests, feature releases) follow the correct sequential or parallel approval paths and obtain necessary authorizations.

**Core Capabilities:**
-   Define and manage multi-stage approval workflows (sequential, parallel, or hybrid).
-   Automatically route approval requests to the correct approvers based on defined rules (e.g., role, department, request type, value threshold).
-   Enforce approval policies, including required number of approvals, authority validation, and deadlines.
-   Track the status of approval requests throughout their lifecycle (pending, approved, rejected, escalated).
-   Handle workflow exceptions, such as approver unavailability, rejections, or escalations.
-   Provide clear audit trails for all approval actions and decisions.
-   Integrate with existing systems for notifications and status updates.

**When to Use:**
-   Automating code deployment approvals (e.g., for production releases).
-   Managing budget or expense request approvals.
-   Enforcing compliance for data access or system changes.
-   Streamlining feature release sign-offs and product launches.
-   Controlling access to sensitive environments or resources.
-   Ensuring security policy adherence for system configurations.
-   Automating contract or legal document reviews and approvals.

**When NOT to Use:**
-   Simple, single-person approvals that require no complex routing or enforcement.
-   Workflows where human judgment and ad-hoc collaboration are paramount and cannot be codified into rules.
-   As a primary user interface for approval (this skill is for enforcement, not UI).
-   For workflows that are highly dynamic and change frequently without clear patterns.
-   Storing sensitive approval request details directly in plain text (integrates with systems that do this securely).

---

## Impact Analysis

### Governance & Compliance Impact: **CRITICAL**
-   **Policy Enforcement:** Incorrect or bypassed approvals can lead to compliance violations, security breaches, and regulatory fines.
-   **Accountability:** Lack of clear audit trails obscures accountability for decisions and actions.
-   **Risk Management:** Ineffective approval workflows can increase operational, financial, and security risks.
-   **Security Vulnerabilities:** Skipping critical security reviews can expose systems to vulnerabilities.

### Operational Efficiency Impact: **HIGH**
-   **Process Streamlining:** Automated routing and enforcement reduce manual overhead and accelerate approval cycles.
-   **Error Reduction:** Minimizes human error in determining who needs to approve what and when.
-   **Bottleneck Identification:** Clear tracking helps identify and resolve workflow bottlenecks.
-   **Resource Utilization:** Efficient workflows optimize the use of approver time.

### System Integration Impact: **MEDIUM**
-   **Dependency on External Systems:** Relies on accurate data from user directories, request systems, and notification services.
-   **Failure Resilience:** Must handle failures in integrated systems gracefully without blocking critical processes.
-   **Performance:** Workflow processing must be performant enough to not introduce delays in approval-dependent operations.
-   **Configuration Complexity:** Defining and maintaining complex approval rules can be challenging.

---

## Environment Variables

### Required Variables

```bash
# Workflow configuration
APPROVAL_RULES_PATH="./config/approval-rules.json" # Path to the JSON/YAML file defining approval workflows
APPROVAL_STATE_PATH="./state/approval_state.json" # Path to persist current approval requests and their states
APPROVAL_AUDIT_LOG="./logs/approval-audit.log"    # Path to the audit log for all approval actions

# Default settings
APPROVAL_DEFAULT_TIMEOUT_HOURS="72"               # Default timeout for pending approvals
APPROVAL_ESCALATION_PATH="manager"                # Default escalation path (e.g., 'manager', 'admin')
```

### Optional Variables

```bash
# Integration endpoints
APPROVAL_USER_DIRECTORY_API="https://users.example.com/api" # API for user roles, managers, departments
APPROVAL_NOTIFICATION_SERVICE="https://notify.example.com/api" # API for sending emails/slack alerts
APPROVAL_REQUEST_SYSTEM_API="https://requests.example.com/api" # API for updating status in source system

# Authentication for integrations
APPROVAL_API_AUTH_TOKEN="<secret_token>"                      # Auth token for external APIs
APPROVAL_API_AUTH_HEADER="Authorization"                      # Header name for auth token

# Performance & concurrency
APPROVAL_POLLING_INTERVAL_SECONDS="300"           # How often to check for updates or timeouts
APPROVAL_MAX_CONCURRENT_WORKFLOWS="50"            # Max number of workflows to process simultaneously

# Debugging
APPROVAL_DEBUG_MODE="false"                       # Enable verbose logging
```

---

## Network and Authentication Implications

### Local Enforcement Mode

**Primary Mode:** Rules and state managed locally, suitable for internal, self-contained processes or prototyping.

**Requirements:**
- Read access to `APPROVAL_RULES_PATH`.
- Read/Write access to `APPROVAL_STATE_PATH`.
- Write access to `APPROVAL_AUDIT_LOG`.
- No direct network dependencies for core logic.

### Integrated Enforcement Mode

**For integration with external user directories, notification services, or request systems:**

```bash
# Example: User directory API for role-based routing
APPROVAL_USER_DIRECTORY_API="https://corporate-ldap-api.example.com/users"
APPROVAL_USER_DIRECTORY_AUTH_TYPE="bearer" # or "basic", "api_key"

# Example: Notification service for alerts
APPROVAL_NOTIFICATION_SERVICE="https://slack.com/api/chat.postMessage"
APPROVAL_NOTIFICATION_AUTH_TYPE="bearer"
```

**Authentication Patterns:**
-   **Bearer Token:** Common for modern REST APIs (e.g., Slack, GitHub).
-   **API Key:** Simple service-to-service authentication.
-   **Basic Authentication:** For legacy or internal HTTP services.
-   **OAuth 2.0:** For user-delegated permissions, though less common for automated enforcement services.

### Network Patterns

**Pattern 1: Standalone (No Network)**
```bash
# All data (rules, state, users) is local.
# No external calls for user info or notifications.
```

**Pattern 2: Hybrid (Optional Network)**
```bash
# Uses network for notifications (e.g., Slack) or fetching user info,
# but can operate with cached data or default values if network is down.
```

**Pattern 3: Fully Integrated (Network Required)**
```bash
# Heavily reliant on external systems for user data, request status updates,
# and sending notifications. Network failures can halt workflows.
```

---

## Blueprints & Templates

### Template 1: Approval Workflow Definition (JSON/YAML)

**File:** `assets/workflow-rules.json` (or `.yaml`)

```json
{
  "version": "1.0",
  "workflows": [
    {
      "id": "code_deployment_prod",
      "name": "Production Code Deployment Approval",
      "description": "Workflow for approving code deployments to production environments.",
      "triggers": ["deployment.prod.request"],
      "stages": [
        {
          "id": "security_review",
          "name": "Security Review",
          "type": "sequential",
          "required_approvers": 1,
          "approvers_by": {
            "role": "security-lead",
            "department": "security"
          },
          "timeout_hours": 48,
          "escalate_to": "security-manager"
        },
        {
          "id": "engineering_lead_signoff",
          "name": "Engineering Lead Sign-off",
          "type": "all_required",
          "required_approvers": "all",
          "approvers_by": {
            "role": "eng-lead",
            "impacted_teams": true
          },
          "timeout_hours": 24
        },
        {
          "id": "release_manager_final_approval",
          "name": "Release Manager Final Approval",
          "type": "any_one",
          "required_approvers": 1,
          "approvers_by": {
            "role": "release-manager"
          },
          "conditional_logic": "request.severity == 'critical' && request.has_p1_bug == false",
          "timeout_hours": 12,
          "auto_approve_if_no_p1_bug": true
        }
      ],
      "notifications": {
        "on_pending": ["slack", "email"],
        "on_approved": ["slack", "jira_update"],
        "on_rejected": ["slack", "email", "jira_update"]
      }
    },
    {
      "id": "budget_request_high_value",
      "name": "High-Value Budget Request Approval",
      "description": "Workflow for budget requests exceeding $50,000.",
      "triggers": ["budget.request"],
      "conditions": "request.amount > 50000",
      "stages": [
        {
          "id": "finance_review",
          "name": "Finance Department Review",
          "type": "any_one",
          "required_approvers": 1,
          "approvers_by": {
            "department": "finance"
          },
          "timeout_hours": 72
        },
        {
          "id": "vp_approval",
          "name": "VP Approval",
          "type": "any_one",
          "required_approvers": 1,
          "approvers_by": {
            "role": "vp"
          },
          "timeout_hours": 48,
          "escalate_to": "cfo"
        }
      ]
    }
  ]
}
```

### Template 2: Python Approval Enforcer Engine

**File:** `assets/approval_enforcer.py`

```python
#!/usr/bin/env python3
"""
approval_enforcer.py
Manages and enforces multi-stage approval workflows.
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ApprovalRequest:
    request_id: str
    workflow_id: str
    current_stage_id: str
    status: str # pending, approved, rejected, escalated, completed
    created_at: datetime
    updated_at: datetime
    approvals: List[Dict[str, Any]] # List of {"stage_id": "...", "approver_id": "...", "status": "approved/rejected", "timestamp": "..."}
    context: Dict[str, Any] # Data relevant to the request (e.g., deployment details, budget amount)
    history: List[Dict[str, Any]] # Audit trail of status changes, escalations, etc.
    approvers_notified: List[str] # List of approver_ids that have been notified for the current stage
    timeout_at: Optional[datetime] = None
    next_approvers: List[str] = field(default_factory=list) # Calculated approvers for the current stage

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
        if isinstance(self.timeout_at, str):
            self.timeout_at = datetime.fromisoformat(self.timeout_at)


class ApprovalEnforcer:
    """Enforces multi-stage approval workflows based on defined rules."""

    def __init__(self,
                 rules_path: Optional[Path] = None,
                 state_path: Optional[Path] = None,
                 audit_log_path: Optional[Path] = None):

        self.rules_path = rules_path or Path(os.getenv('APPROVAL_RULES_PATH', './config/approval-rules.json'))
        self.state_path = state_path or Path(os.getenv('APPROVAL_STATE_PATH', './state/approval_state.json'))
        self.audit_log_path = audit_log_path or Path(os.getenv('APPROVAL_AUDIT_LOG', './logs/approval-audit.log'))

        self.workflows = self._load_workflows()
        self.approval_requests = self._load_approval_state()

        self.default_timeout_hours = int(os.getenv('APPROVAL_DEFAULT_TIMEOUT_HOURS', '72'))
        self.escalation_path = os.getenv('APPROVAL_ESCALATION_PATH', 'manager') # Placeholder for now

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        Path(self.audit_log_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info("ApprovalEnforcer initialized.")

    def _load_workflows(self) -> Dict[str, Any]:
        """Loads approval workflow rules from a JSON/YAML file."""
        if not self.rules_path.exists():
            logger.error(f"Workflow rules file not found: {self.rules_path}")
            raise FileNotFoundError(f"Workflow rules file not found: {self.rules_path}")

        try:
            if self.rules_path.suffix == '.json':
                with open(self.rules_path, 'r') as f:
                    return {w['id']: w for w in json.load(f).get('workflows', [])}
            elif self.rules_path.suffix in ('.yaml', '.yml'):
                with open(self.rules_path, 'r') as f:
                    return {w['id']: w for w in yaml.safe_load(f).get('workflows', [])}
            else:
                raise ValueError(f"Unsupported workflow rules file type: {self.rules_path.suffix}")
        except Exception as e:
            logger.error(f"Error loading workflow rules from {self.rules_path}: {e}")
            raise

    def _load_approval_state(self) -> Dict[str, ApprovalRequest]:
        """Loads the current state of approval requests."""
        if not self.state_path.exists():
            return {}
        try:
            with open(self.state_path, 'r') as f:
                state_data = json.load(f)
                requests = {}
                for req_id, req_data in state_data.items():
                    requests[req_id] = ApprovalRequest(**req_data)
                return requests
        except Exception as e:
            logger.error(f"Error loading approval state from {self.state_path}: {e}")
            return {}

    def _save_approval_state(self):
        """Saves the current state of approval requests."""
        try:
            # Convert ApprovalRequest objects back to dicts for JSON serialization
            serializable_state = {
                req_id: asdict(req) for req_id, req in self.approval_requests.items()
            }
            with open(self.state_path, 'w') as f:
                json.dump(serializable_state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving approval state to {self.state_path}: {e}")

    def _audit_log(self, request_id: str, action: str, details: Dict[str, Any]):
        """Writes an entry to the audit log."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'request_id': request_id,
            'action': action,
            'details': details
        }
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '
')
        except Exception as e:
            logger.warning(f"Failed to write audit log entry: {e}")

    def _get_workflow_stage(self, workflow_id: str, stage_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific stage definition from a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        for stage in workflow.get('stages', []):
            if stage['id'] == stage_id:
                return stage
        return None

    def _get_next_stage(self, workflow_id: str, current_stage_id: str) -> Optional[Dict[str, Any]]:
        """Determines the next stage in a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        stages = workflow.get('stages', [])
        for i, stage in enumerate(stages):
            if stage['id'] == current_stage_id:
                if i + 1 < len(stages):
                    return stages[i+1]
                else:
                    return None # No more stages
        return None

    def _resolve_approvers(self, stage_config: Dict[str, Any], request_context: Dict[str, Any]) -> List[str]:
        """Resolves the actual approvers for a given stage based on rules and context."""
        approvers = []
        approvers_by = stage_config.get('approvers_by', {})

        # Example logic: Resolve by role
        if 'role' in approvers_by:
            # This would typically involve an API call to a user directory
            # For this example, we'll hardcode some roles
            if approvers_by['role'] == 'security-lead':
                approvers.append('sec_lead_alice')
            elif approvers_by['role'] == 'eng-lead':
                approvers.extend(['eng_lead_bob', 'eng_lead_charlie'])
            elif approvers_by['role'] == 'release-manager':
                approvers.append('release_mgr_diana')
            elif approvers_by['role'] == 'vp':
                approvers.extend(['vp_eve', 'vp_frank'])
            elif approvers_by['role'] == 'cfo':
                approvers.append('cfo_grace')

        # Example logic: Resolve by department
        if 'department' in approvers_by and request_context.get('initiator_department'):
            # More complex logic could query a user directory for all users in a department
            if approvers_by['department'] == 'finance':
                approvers.extend(['fin_auditor_harry', 'fin_mgr_irene'])
            elif approvers_by['department'] == 'security':
                 approvers.append('sec_lead_alice')

        # Example logic: If impacted_teams is true, get leads from impacted teams
        if approvers_by.get('impacted_teams') and request_context.get('impacted_teams'):
            for team in request_context['impacted_teams']:
                # Lookup team leads for these teams
                if team == 'frontend': approvers.append('frontend_lead_john')
                if team == 'backend': approvers.append('backend_lead_kate')
        
        # Remove duplicates
        return sorted(list(set(approvers)))

    def _evaluate_conditional_logic(self, conditional_logic: str, request_context: Dict[str, Any]) -> bool:
        """Evaluates conditional logic strings (e.g., 'request.amount > 1000')."""
        if not conditional_logic:
            return True
        
        # Basic, UNSAFE evaluation for demonstration. In production, use a secure expression parser.
        # This allows direct access to `request` variable which maps to request_context
        safe_context = {'request': request_context}
        try:
            # Evaluate the expression within the context of safe_context
            # WARNING: Using eval is generally dangerous. For a production system,
            # use a dedicated expression parser library (e.g., asteval, simpleeval).
            return eval(conditional_logic, {"__builtins__": None}, safe_context)
        except Exception as e:
            logger.error(f"Error evaluating conditional logic '{conditional_logic}': {e}")
            return False

    def start_workflow(self, workflow_id: str, request_id: str, context: Dict[str, Any]) -> ApprovalRequest:
        """Initiates a new approval workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found.")
        if request_id in self.approval_requests:
            raise ValueError(f"Approval request '{request_id}' already exists.")

        workflow_config = self.workflows[workflow_id]
        
        # Check overall workflow conditions
        if workflow_config.get('conditions') and not self._evaluate_conditional_logic(workflow_config['conditions'], context):
            raise ValueError(f"Workflow '{workflow_id}' conditions not met for request '{request_id}'.")

        first_stage = workflow_config['stages'][0]
        
        # Check stage-specific conditional logic
        if first_stage.get('conditional_logic') and not self._evaluate_conditional_logic(first_stage['conditional_logic'], context):
            # If first stage condition not met, skip this stage and find next valid one
            logger.info(f"Skipping first stage '{first_stage['id']}' for request '{request_id}' as conditions not met.")
            next_stage_config = self._get_next_stage(workflow_id, first_stage['id'])
            if not next_stage_config:
                 raise ValueError(f"Workflow '{workflow_id}' has no valid initial stage after skipping '{first_stage['id']}'.")
            first_stage = next_stage_config

        approvers = self._resolve_approvers(first_stage, context)
        timeout_hours = first_stage.get('timeout_hours', self.default_timeout_hours)
        timeout_at = datetime.utcnow() + timedelta(hours=timeout_hours)

        new_request = ApprovalRequest(
            request_id=request_id,
            workflow_id=workflow_id,
            current_stage_id=first_stage['id'],
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            approvals=[],
            context=context,
            history=[{'timestamp': datetime.utcnow().isoformat(), 'event': 'workflow_started', 'stage_id': first_stage['id']}],
            approvers_notified=[],
            timeout_at=timeout_at,
            next_approvers=approvers
        )
        self.approval_requests[request_id] = new_request
        self._save_approval_state()
        self._audit_log(request_id, 'workflow_started', {'workflow_id': workflow_id, 'first_stage': first_stage['id'], 'approvers': approvers})
        logger.info(f"Started workflow '{workflow_id}' for request '{request_id}'. Current stage: '{first_stage['id']}' with approvers: {approvers}")
        self._notify_approvers(new_request, approvers)
        return new_request

    def record_approval(self, request_id: str, approver_id: str, approval_status: str, comment: Optional[str] = None) -> ApprovalRequest:
        """Records an approval or rejection for a request."""
        request = self.approval_requests.get(request_id)
        if not request:
            raise ValueError(f"Approval request '{request_id}' not found.")
        if request.status != 'pending':
            raise ValueError(f"Request '{request_id}' is not pending approval (current status: {request.status}).")

        current_stage_config = self._get_workflow_stage(request.workflow_id, request.current_stage_id)
        if not current_stage_config:
            raise ValueError(f"Current stage '{request.current_stage_id}' not found in workflow '{request.workflow_id}'.")

        # Authority validation (simple check for now)
        if approver_id not in request.next_approvers:
            raise PermissionError(f"Approver '{approver_id}' is not authorized for stage '{request.current_stage_id}' of request '{request_id}'.")

        # Record approval/rejection
        request.approvals.append({
            'stage_id': request.current_stage_id,
            'approver_id': approver_id,
            'status': approval_status,
            'timestamp': datetime.utcnow().isoformat(),
            'comment': comment
        })
        request.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'event': f'approval_recorded_{approval_status}',
            'stage_id': request.current_stage_id,
            'approver_id': approver_id,
            'comment': comment
        })
        request.updated_at = datetime.utcnow()
        self._audit_log(request_id, f'approval_recorded_{approval_status}', {'approver_id': approver_id, 'stage_id': request.current_stage_id, 'comment': comment})

        if approval_status == 'rejected':
            request.status = 'rejected'
            logger.info(f"Request '{request_id}' rejected by '{approver_id}' at stage '{request.current_stage_id}'.")
            self._save_approval_state()
            self._notify_on_status_change(request)
            return request

        # Check if stage is complete
        stage_approvals = [a for a in request.approvals if a['stage_id'] == request.current_stage_id and a['status'] == 'approved']
        
        stage_complete = False
        if current_stage_config['type'] == 'sequential':
            # For sequential, one approval is enough to move to next designated approver in list,
            # but for this simplified model, we'll assume one approval moves the stage forward.
            # More complex sequential would need to track *which* specific approver was targeted next.
            stage_complete = True # Assuming one approver approval fulfills the sequential stage
        elif current_stage_config['type'] == 'any_one':
            stage_complete = len(stage_approvals) >= current_stage_config.get('required_approvers', 1)
        elif current_stage_config['type'] == 'all_required':
            stage_complete = len(stage_approvals) >= len(request.next_approvers) # All current approvers must approve

        if stage_complete:
            logger.info(f"Stage '{request.current_stage_id}' completed for request '{request_id}'.")
            next_stage_config = self._get_next_stage(request.workflow_id, request.current_stage_id)
            if next_stage_config:
                # Move to next stage
                request.current_stage_id = next_stage_config['id']
                request.history.append({'timestamp': datetime.utcnow().isoformat(), 'event': 'stage_completed', 'stage_id': next_stage_config['id']})
                
                # Resolve approvers for the new stage
                request.next_approvers = self._resolve_approvers(next_stage_config, request.context)
                
                # Set new timeout
                timeout_hours = next_stage_config.get('timeout_hours', self.default_timeout_hours)
                request.timeout_at = datetime.utcnow() + timedelta(hours=timeout_hours)
                request.approvers_notified = [] # Reset notified approvers for new stage
                
                logger.info(f"Request '{request_id}' moved to stage '{request.current_stage_id}' with approvers: {request.next_approvers}.")
                self._notify_approvers(request, request.next_approvers)
            else:
                # Workflow complete
                request.status = 'approved'
                request.current_stage_id = 'completed'
                request.next_approvers = []
                request.timeout_at = None
                request.history.append({'timestamp': datetime.utcnow().isoformat(), 'event': 'workflow_completed'})
                logger.info(f"Workflow for request '{request_id}' completed successfully.")
            self._notify_on_status_change(request) # Notify workflow completion
        
        self._save_approval_state()
        return request

    def check_for_timeouts_and_escalations(self):
        """Periodically checks pending requests for timeouts and escalates as necessary."""
        now = datetime.utcnow()
        for request_id, request in self.approval_requests.items():
            if request.status == 'pending' and request.timeout_at and now > request.timeout_at:
                logger.warning(f"Approval request '{request_id}' for stage '{request.current_stage_id}' timed out.")
                current_stage_config = self._get_workflow_stage(request.workflow_id, request.current_stage_id)
                
                escalate_to = current_stage_config.get('escalate_to', self.escalation_path)
                
                request.status = 'escalated'
                request.history.append({
                    'timestamp': now.isoformat(),
                    'event': 'timed_out_and_escalated',
                    'stage_id': request.current_stage_id,
                    'escalated_to': escalate_to
                })
                request.updated_at = now
                self._audit_log(request_id, 'timed_out_and_escalated', {'stage_id': request.current_stage_id, 'escalated_to': escalate_to})
                self._save_approval_state()
                self._notify_on_escalation(request, escalate_to)
                logger.info(f"Request '{request_id}' escalated to '{escalate_to}'.")

    def get_request_status(self, request_id: str) -> Optional[ApprovalRequest]:
        """Returns the current status of an approval request."""
        return self.approval_requests.get(request_id)

    def list_pending_requests(self, approver_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Lists all pending approval requests, optionally filtered by approver."""
        pending = []
        for request in self.approval_requests.values():
            if request.status == 'pending':
                if approver_id is None or approver_id in request.next_approvers:
                    pending.append(request)
        return pending

    def _notify_approvers(self, request: ApprovalRequest, approver_ids: List[str]):
        """Sends notifications to approvers for a new stage."""
        for approver_id in approver_ids:
            if approver_id not in request.approvers_notified:
                logger.info(f"Notifying approver '{approver_id}' for request '{request.request_id}' (stage: '{request.current_stage_id}').")
                # In a real system, this would trigger an email, Slack message, etc.
                # using a notification service API (APPROVAL_NOTIFICATION_SERVICE)
                request.approvers_notified.append(approver_id)
                self._audit_log(request.request_id, 'approver_notified', {'approver_id': approver_id, 'stage_id': request.current_stage_id})

    def _notify_on_status_change(self, request: ApprovalRequest):
        """Sends notifications on request status change (approved/rejected/completed)."""
        logger.info(f"Notifying stakeholders for request '{request.request_id}' status change to '{request.status}'.")
        # This would notify the initiator and other relevant parties.
        # Use APPROVAL_NOTIFICATION_SERVICE
        self._audit_log(request.request_id, 'status_change_notification', {'new_status': request.status})

    def _notify_on_escalation(self, request: ApprovalRequest, escalated_to: str):
        """Sends notifications when a request escalates."""
        logger.warning(f"Notifying '{escalated_to}' about escalated request '{request.request_id}'.")
        # Use APPROVAL_NOTIFICATION_SERVICE to notify the escalation path.
        self._audit_log(request.request_id, 'escalation_notification', {'escalated_to': escalated_to})

# Example usage
if __name__ == "__main__":
    from dataclasses import dataclass, field, asdict
    # Setup environment variables for demonstration
    script_dir = Path(__file__).parent
    config_dir = script_dir / "config"
    state_dir = script_dir / "state"
    logs_dir = script_dir / "logs"

    config_dir.mkdir(exist_ok=True)
    state_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)

    os.environ['APPROVAL_RULES_PATH'] = str(config_dir / "workflow-rules.json")
    os.environ['APPROVAL_STATE_PATH'] = str(state_dir / "approval_state.json")
    os.environ['APPROVAL_AUDIT_LOG'] = str(logs_dir / "approval-audit.log")

    # Create dummy workflow rules file
    dummy_rules = {
      "version": "1.0",
      "workflows": [
        {
          "id": "test_deployment",
          "name": "Test Deployment Approval",
          "description": "Simple test workflow for deployments.",
          "triggers": ["deployment.test.request"],
          "stages": [
            {
              "id": "dev_lead_approval",
              "name": "Dev Lead Approval",
              "type": "any_one",
              "required_approvers": 1,
              "approvers_by": {
                "role": "eng-lead"
              },
              "timeout_hours": 1
            },
            {
              "id": "qa_lead_approval",
              "name": "QA Lead Approval",
              "type": "any_one",
              "required_approvers": 1,
              "approvers_by": {
                "role": "qa-lead"
              },
              "timeout_hours": 1
            }
          ],
          "notifications": {
            "on_pending": ["slack"],
            "on_approved": ["slack"],
            "on_rejected": ["slack"]
          }
        },
        {
          "id": "high_value_pr",
          "name": "High Value PR Approval",
          "description": "PRs with major changes require additional approval.",
          "triggers": ["pr.merged"],
          "conditions": "request.lines_changed > 500",
          "stages": [
              {
                "id": "team_lead_approval",
                "name": "Team Lead Approval",
                "type": "all_required",
                "required_approvers": "all",
                "approvers_by": {
                    "role": "team-lead"
                },
                "timeout_hours": 2
              }
          ]
        }
      ]
    }
    with open(os.environ['APPROVAL_RULES_PATH'], 'w') as f:
        json.dump(dummy_rules, f, indent=2)

    enforcer = ApprovalEnforcer()

    # --- Scenario 1: Successful Workflow ---
    print("
--- Starting Successful Workflow Scenario ---")
    request_context_1 = {
        "initiator_id": "john_doe",
        "initiator_department": "engineering",
        "deployment_target": "staging",
        "lines_changed": 150
    }
    try:
        req1 = enforcer.start_workflow("test_deployment", "DEP-001", request_context_1)
        print(f"Request DEP-001 created. Status: {req1.status}, Current Stage: {req1.current_stage_id}, Next Approvers: {req1.next_approvers}")

        # Simulate approval by dev_lead_bob
        req1 = enforcer.record_approval("DEP-001", "eng_lead_bob", "approved", "Looks good.")
        print(f"Request DEP-001 after dev_lead_bob approval. Status: {req1.status}, Current Stage: {req1.current_stage_id}, Next Approvers: {req1.next_approvers}")

        # Simulate approval by qa_lead_sue (assuming qa-lead is 'qa_lead_sue')
        # We need to add 'qa_lead_sue' to the mock approver resolution for this to work
        # For simplicity, manually setting next_approvers for example
        req1.next_approvers = ['qa_lead_sue'] # This bypasses _resolve_approvers for example only
        req1 = enforcer.record_approval("DEP-001", "qa_lead_sue", "approved", "QA Passed.")
        print(f"Request DEP-001 after qa_lead_sue approval. Status: {req1.status}, Current Stage: {req1.current_stage_id}, Next Approvers: {req1.next_approvers}")
    except Exception as e:
        logger.error(f"Error in successful workflow scenario: {e}")

    # --- Scenario 2: Rejected Workflow ---
    print("
--- Starting Rejected Workflow Scenario ---")
    request_context_2 = {
        "initiator_id": "jane_smith",
        "initiator_department": "engineering",
        "deployment_target": "prod",
        "lines_changed": 50
    }
    try:
        req2 = enforcer.start_workflow("test_deployment", "DEP-002", request_context_2)
        print(f"Request DEP-002 created. Status: {req2.status}, Current Stage: {req2.current_stage_id}, Next Approvers: {req2.next_approvers}")

        # Simulate rejection by dev_lead_charlie
        req2 = enforcer.record_approval("DEP-002", "eng_lead_charlie", "rejected", "Found a critical bug in review.")
        print(f"Request DEP-002 after rejection. Status: {req2.status}")
    except Exception as e:
        logger.error(f"Error in rejected workflow scenario: {e}")

    # --- Scenario 3: Timed Out Workflow (simulated) ---
    print("
--- Starting Timed Out Workflow Scenario ---")
    request_context_3 = {
        "initiator_id": "bob_test",
        "initiator_department": "qa",
        "deployment_target": "dev",
        "lines_changed": 10
    }
    try:
        req3 = enforcer.start_workflow("test_deployment", "DEP-003", request_context_3)
        print(f"Request DEP-003 created. Status: {req3.status}, Current Stage: {req3.current_stage_id}, Next Approvers: {req3.next_approvers}")

        # Manually set timeout_at to a past time for testing
        req3.timeout_at = datetime.utcnow() - timedelta(minutes=5)
        enforcer._save_approval_state() # Save the manipulated state

        print("Simulating passage of time...")
        enforcer.check_for_timeouts_and_escalations()
        req3 = enforcer.get_request_status("DEP-003") # Reload status
        print(f"Request DEP-003 after timeout check. Status: {req3.status}")
    except Exception as e:
        logger.error(f"Error in timed out workflow scenario: {e}")

    # --- Scenario 4: Conditional Workflow ---
    print("
--- Starting Conditional Workflow Scenario ---")
    request_context_4_low_value = {
        "initiator_id": "admin_user",
        "initiator_department": "admin",
        "lines_changed": 100
    }
    try:
        # This request should start but not trigger 'high_value_pr' conditions
        req4_low = enforcer.start_workflow("high_value_pr", "PR-001", request_context_4_low_value)
        print(f"Request PR-001 (low value) created. Status: {req4_low.status}, Current Stage: {req4_low.current_stage_id}")
    except ValueError as e:
        print(f"Expected: {e}") # Should output conditions not met and then fail
    except Exception as e:
         logger.error(f"Error in conditional workflow scenario (low value): {e}")

    request_context_4_high_value = {
        "initiator_id": "admin_user",
        "initiator_department": "admin",
        "lines_changed": 600
    }
    try:
        req4_high = enforcer.start_workflow("high_value_pr", "PR-002", request_context_4_high_value)
        print(f"Request PR-002 (high value) created. Status: {req4_high.status}, Current Stage: {req4_high.current_stage_id}, Next Approvers: {req4_high.next_approvers}")
    except Exception as e:
        logger.error(f"Error in conditional workflow scenario (high value): {e}")
    
    # Clean up dummy files
    os.remove(os.environ['APPROVAL_RULES_PATH'])
    os.remove(os.environ['APPROVAL_STATE_PATH'])
    os.remove(os.environ['APPROVAL_AUDIT_LOG'])
    config_dir.rmdir()
    state_dir.rmdir()
    logs_dir.rmdir()
```

### Template 3: Approval State File (JSON)

**File:** `state/approval_state.json` (Managed by `approval_enforcer.py`)

```json
{
  "REQ-001": {
    "request_id": "REQ-001",
    "workflow_id": "code_deployment_prod",
    "current_stage_id": "security_review",
    "status": "pending",
    "created_at": "2026-02-06T10:00:00.000000",
    "updated_at": "2026-02-06T10:00:00.000000",
    "approvals": [],
    "context": {
      "initiator_id": "user_dev",
      "change_summary": "Feature X v1.0 deployment",
      "impacted_teams": ["frontend", "backend"],
      "environment": "production"
    },
    "history": [
      {
        "timestamp": "2026-02-06T10:00:00.000000",
        "event": "workflow_started",
        "stage_id": "security_review"
      }
    ],
    "approvers_notified": ["security-lead-john"],
    "timeout_at": "2026-02-08T10:00:00.000000",
    "next_approvers": ["security-lead-john"]
  }
}
```

### Template 4: Audit Log (JSONL)

**File:** `logs/approval-audit.log` (Managed by `approval_enforcer.py`)

```jsonl
{"timestamp": "2026-02-06T10:00:00.000000", "request_id": "REQ-001", "action": "workflow_started", "details": {"workflow_id": "code_deployment_prod", "first_stage": "security_review", "approvers": ["security-lead-john"]}}
{"timestamp": "2026-02-06T10:05:00.000000", "request_id": "REQ-001", "action": "approver_notified", "details": {"approver_id": "security-lead-john", "stage_id": "security_review"}}
{"timestamp": "2026-02-06T10:30:00.000000", "request_id": "REQ-001", "action": "approval_recorded_approved", "details": {"approver_id": "security-lead-john", "stage_id": "security_review", "comment": "Security review passed."}}
{"timestamp": "2026-02-06T10:30:00.000000", "request_id": "REQ-001", "action": "status_change_notification", "details": {"new_status": "pending"}}
```

---

## Validation Checklist

### Pre-Deployment Checklist

-   [ ] **Workflow Definitions**
    -   [ ] All required workflows defined in `workflow-rules.json`.
    -   [ ] Each workflow has a unique `id` and clear `name`/`description`.
    -   [ ] All stages within workflows have unique `id`s and `name`s.
    -   [ ] Stage types (`sequential`, `any_one`, `all_required`) are correctly specified.
    -   [ ] `required_approvers` are valid for the stage type (number for `any_one`, "all" for `all_required`).
    -   [ ] `approvers_by` rules are comprehensive and correctly map to known roles/departments/teams.
    -   [ ] `conditional_logic` expressions are syntactically correct and cover expected scenarios.
    -   [ ] `timeout_hours` and `escalate_to` are defined where necessary for critical stages.

-   [ ] **Data Integration & Lookups**
    -   [ ] User directory integration (if used) provides accurate user roles, managers, and departments.
    -   [ ] Notification service integration (if used) correctly sends alerts to specified channels.
    -   [ ] Request system integration (if used) can update request statuses as workflows progress.

-   [ ] **Configuration**
    -   [ ] All required environment variables are set (e.g., `APPROVAL_RULES_PATH`, `APPROVAL_STATE_PATH`).
    -   [ ] File paths (`rules`, `state`, `audit_log`) are correct and accessible.
    -   [ ] Default timeout and escalation paths are appropriate for the organization.

-   [ ] **Security & Compliance**
    -   [ ] Authentication tokens/API keys for external integrations are secured (e.g., environment variables, secret manager).
    -   [ ] Audit log captures all relevant actions (start, approve, reject, escalate, timeout).
    -   [ ] Access control for who can initiate/approve requests is correctly implemented (potentially external to this skill).

### Post-Deployment Validation

-   [ ] **Functional Testing**
    -   [ ] Basic approval workflow (e.g., single stage) completes successfully.
    -   [ ] Multi-stage sequential workflow progresses correctly through all stages.
    -   [ ] Parallel approval (all_required, any_one) behaves as expected.
    -   [ ] Rejections correctly stop the workflow and set status to 'rejected'.
    -   [ ] Conditional logic correctly routes or modifies workflow behavior.
    -   [ ] Approver authority is validated; unauthorized approvals are rejected.

-   [ ] **Timeout & Escalation Testing**
    -   [ ] Requests time out correctly and transition to 'escalated' status.
    -   [ ] Escalation notifications are sent to the designated escalation path.

-   [ ] **Integration Testing**
    -   [ ] Notifications (email, Slack) are sent at the correct stages (pending, approved, rejected, escalated).
    -   [ ] External request systems (e.g., Jira) are updated with correct status changes.
    -   [ ] User lookups for approver resolution function correctly.

-   [ ] **Audit & State Management**
    -   [ ] Audit log contains accurate and complete records for all workflow actions.
    -   [ ] Approval state file (`approval_state.json`) accurately reflects the current status of all requests.
    -   [ ] State is correctly persisted and reloaded across restarts of the enforcer.

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Skipping Approvals or Stages

**Bad Example:**
```python
# Code that bypasses workflow stages based on a quick check, without proper audit
if request_context.get('initiator_role') == 'admin':
    request.status = 'approved' # ❌ Bypasses entire workflow
```

**Why It's Bad:**
-   Violates compliance and governance policies.
-   Creates security risks by allowing unauthorized changes.
-   Undermines the purpose of the approval workflow.
-   Leaves no audit trail for the bypassed steps.

**Correct Approach:**
-   All requests MUST pass through defined stages.
-   Conditional logic can route to different *valid* stages or adjust `required_approvers`, but not skip the enforcement entirely without explicit, auditable approval.
-   Implement an "emergency bypass" ONLY with multi-factor authentication, extensive logging, and explicit management approval.

---

### ❌ Anti-Pattern 2: Hardcoding Approvers in Code

**Bad Example:**
```python
# Approvers hardcoded in the enforcement logic
if stage_id == 'security_review':
    return ['sec_lead_john', 'sec_team_jane'] # ❌ Hardcoded
```

**Why It's Bad:**
-   Inflexible: Requires code changes for personnel changes or organizational restructuring.
-   Error-prone: Easy to forget to update code when approvers change.
-   Lack of scalability: Difficult to manage for many workflows or large organizations.

**Correct Approach:**
-   Resolve approvers dynamically using `approvers_by` rules in `workflow-rules.json`.
-   Integrate with a centralized user directory (e.g., LDAP, HR system API) to lookup users by role, group, or manager hierarchy.
-   Allow workflow definitions to specify approver groups or departments, not individual names.

---

### ❌ Anti-Pattern 3: Ignoring Workflow Exceptions

**Bad Example:**
```python
# No handling for timeouts or rejections
try:
    process_approval()
except Exception:
    pass # ❌ Silently ignores errors
```

**Why It's Bad:**
-   Requests can get stuck indefinitely (if timed out and not escalated).
-   Rejected requests might not be communicated back to the initiator.
-   Critical processes remain blocked without clear resolution paths.
-   Lack of visibility into workflow failures.

**Correct Approach:**
-   Implement robust timeout mechanisms with clear escalation paths (`timeout_hours`, `escalate_to`).
-   Ensure explicit notification for all workflow status changes (pending, approved, rejected, escalated, timed out).
-   Provide clear audit logs for all exceptions, including who was notified and when.
-   Have manual override procedures for exceptional circumstances, with strong logging.

---

### ❌ Anti-Pattern 4: Insufficient Authority Validation

**Bad Example:**
```python
# Any user can approve any request
def record_approval(request_id, approver_id, status):
    request = get_request(request_id)
    request.add_approval(approver_id, status) # ❌ No check if approver_id is valid
```

**Why It's Bad:**
-   Allows unauthorized individuals to approve requests.
-   Compromises security and compliance.
-   Leads to invalid audit trails.

**Correct Approach:**
-   The `record_approval` function MUST validate that `approver_id` is among the `next_approvers` designated for the `current_stage_id` of the request.
-   Approver lists should be dynamically resolved from a trusted source, not input directly by the request initiator.
-   For critical approvals, consider multi-factor authentication for the approver.

---

### ❌ Anti-Pattern 5: Lack of Audit Trail

**Bad Example:**
```python
# No logging of workflow progress
def start_workflow(...):
    # ... starts workflow
    # No record of who started it, when, or what parameters
    pass # ❌ No audit
```

**Why It's Bad:**
-   Impossible to debug issues or understand workflow progression.
-   No accountability for approval decisions.
-   Fails to meet compliance and regulatory requirements.
-   Cannot analyze workflow performance or identify bottlenecks.

**Correct Approach:**
-   Maintain a comprehensive, immutable audit log (`APPROVAL_AUDIT_LOG`) for every significant event: workflow start, stage transitions, approval/rejection, escalation, timeout, and notification.
-   Each log entry should include a timestamp, request ID, event type, and relevant details (e.g., approver ID, stage ID, comments).
-   Integrate audit logs with a centralized logging system.

---

## Related Documentation

-   [patterns.md](./docs/patterns.md) - Approval workflow patterns and best practices.
-   [impact-checklist.md](./docs/impact-checklist.md) - Full system impact assessment for approval workflows.
-   [gotchas.md](./docs/gotchas.md) - Common pitfalls and troubleshooting for approval enforcement.

---

## Support and Troubleshooting

### Common Issues

1.  **Workflow Not Progressing**
    -   Check if `required_approvers` count has been met for the current stage.
    -   Verify `approver_id` matches expected approvers (case sensitivity).
    -   Review `conditional_logic` for the current stage; it might not be evaluating to `true`.
    -   Check audit logs for errors or unexpected events.

2.  **Approvers Not Notified**
    -   Verify `APPROVAL_NOTIFICATION_SERVICE` is configured correctly.
    -   Check network connectivity and authentication tokens for the notification service.
    -   Ensure approver IDs exist in the notification system.

3.  **Requests Timed Out Unexpectedly**
    -   Check `timeout_hours` in `workflow-rules.json` for the relevant stage.
    -   Verify `APPROVAL_DEFAULT_TIMEOUT_HOURS` environment variable.
    -   Ensure the `check_for_timeouts_and_escalations` method is being called periodically (e.g., via a cron job or background process).

4.  **Unauthorized Approval Error**
    -   This indicates `approver_id` is not among the designated approvers for the current stage.
    -   Review `approvers_by` rules in `workflow-rules.json` and the `_resolve_approvers` logic.
    -   Verify user roles/department data from the user directory.

### Getting Help

-   Review audit logs (`APPROVAL_AUDIT_LOG`) for detailed event history and errors.
-   Inspect `approval_state.json` to understand the current state of requests.
-   Consult `workflow-rules.json` to verify workflow definitions.
-   Refer to `gotchas.md` for common issues and solutions.

---

**Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** Silver Team
