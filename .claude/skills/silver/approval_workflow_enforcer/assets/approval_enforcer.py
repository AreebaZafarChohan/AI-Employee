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
from dataclasses import dataclass, field, asdict


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
            elif approvers_by['role'] == 'qa-lead': # Added for test_deployment example
                approvers.append('qa_lead_sue')
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
        """Evaluates conditional logic strings (e.g., 'context.amount > 1000')."""
        if not conditional_logic:
            return True
        
        # Basic, UNSAFE evaluation for demonstration. In production, use a secure expression parser.
        # This allows direct access to `context` variable which maps to request_context
        safe_context = {'context': request_context}
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

        first_stage_index = 0
        first_stage = workflow_config['stages'][first_stage_index]
        
        # Check stage-specific conditional logic
        while first_stage.get('conditional_logic') and not self._evaluate_conditional_logic(first_stage['conditional_logic'], context):
            logger.info(f"Skipping stage '{first_stage['id']}' for request '{request_id}' as conditions not met.")
            first_stage_index += 1
            if first_stage_index >= len(workflow_config['stages']):
                raise ValueError(f"Workflow '{workflow_id}' has no valid initial stage after skipping all stages.")
            first_stage = workflow_config['stages'][first_stage_index]


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
            
            # Skip subsequent stages if their conditional_logic is not met
            while next_stage_config and next_stage_config.get('conditional_logic') and not self._evaluate_conditional_logic(next_stage_config['conditional_logic'], request.context):
                logger.info(f"Skipping stage '{next_stage_config['id']}' for request '{request_id}' as conditions not met.")
                next_stage_config = self._get_next_stage(request.workflow_id, next_stage_config['id'])


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
          "id": "conditional_test",
          "name": "Conditional Stage Test",
          "description": "Tests conditional stage skipping.",
          "stages": [
              {
                  "id": "stage1_always_run",
                  "name": "Stage 1",
                  "type": "any_one",
                  "required_approvers": 1,
                  "approvers_by": {"role": "eng-lead"},
                  "timeout_hours": 1
              },
              {
                  "id": "stage2_conditional",
                  "name": "Stage 2 (Conditional)",
                  "type": "any_one",
                  "required_approvers": 1,
                  "approvers_by": {"role": "qa-lead"},
                  "conditional_logic": "context.skip_qa == false",
                  "timeout_hours": 1
              },
              {
                  "id": "stage3_always_run",
                  "name": "Stage 3",
                  "type": "any_one",
                  "required_approvers": 1,
                  "approvers_by": {"role": "release-manager"},
                  "timeout_hours": 1
              }
          ]
        },
        {
          "id": "high_value_pr",
          "name": "High Value PR Approval",
          "description": "PRs with major changes require additional approval.",
          "triggers": ["pr.merged"],
          "conditions": "context.lines_changed > 500",
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
        # In a real system, _resolve_approvers would find 'qa_lead_sue' for the 'qa_lead_approval' stage
        # For this demo, assuming it's resolved:
        # req1.next_approvers = ['qa_lead_sue']
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

    # --- Scenario 4: Conditional Workflow (skip stage) ---
    print("
--- Starting Conditional Workflow (skip stage) Scenario ---")
    request_context_4_skip_qa = {
        "initiator_id": "admin_user",
        "initiator_department": "engineering",
        "skip_qa": True # Context for conditional_logic
    }
    try:
        req4_skip = enforcer.start_workflow("conditional_test", "COND-001", request_context_4_skip_qa)
        print(f"Request COND-001 (skip QA) created. Status: {req4_skip.status}, Current Stage: {req4_skip.current_stage_id}, Next Approvers: {req4_skip.next_approvers}")
        # Expect to jump from stage1_always_run to stage3_always_run
    except Exception as e:
        logger.error(f"Error in conditional workflow scenario (skip QA): {e}")

    request_context_4_run_qa = {
        "initiator_id": "normal_user",
        "initiator_department": "engineering",
        "skip_qa": False
    }
    try:
        req4_run = enforcer.start_workflow("conditional_test", "COND-002", request_context_4_run_qa)
        print(f"Request COND-002 (run QA) created. Status: {req4_run.status}, Current Stage: {req4_run.current_stage_id}, Next Approvers: {req4_run.next_approvers}")
        # Expect to start at stage1_always_run and then proceed to stage2_conditional
    except Exception as e:
        logger.error(f"Error in conditional workflow scenario (run QA): {e}")


    # --- Scenario 5: Conditional Workflow (overall workflow condition) ---
    print("
--- Starting Conditional Workflow (overall workflow condition) Scenario ---")
    request_context_5_low_value = {
        "initiator_id": "admin_user",
        "initiator_department": "admin",
        "lines_changed": 100
    }
    try:
        # This request should NOT start 'high_value_pr' workflow
        enforcer.start_workflow("high_value_pr", "PR-001", request_context_5_low_value)
        print("ERROR: PR-001 (low value) should not have started.")
    except ValueError as e:
        print(f"SUCCESS: PR-001 (low value) failed to start as expected: {e}")
    except Exception as e:
         logger.error(f"Error in conditional workflow scenario (low value): {e}")

    request_context_5_high_value = {
        "initiator_id": "admin_user",
        "initiator_department": "admin",
        "lines_changed": 600
    }
    try:
        req5_high = enforcer.start_workflow("high_value_pr", "PR-002", request_context_5_high_value)
        print(f"Request PR-002 (high value) created. Status: {req5_high.status}, Current Stage: {req5_high.current_stage_id}, Next Approvers: {req5_high.next_approvers}")
    except Exception as e:
        logger.error(f"Error in conditional workflow scenario (high value): {e}")
    
    # Clean up dummy files
    os.remove(os.environ['APPROVAL_RULES_PATH'])
    os.remove(os.environ['APPROVAL_STATE_PATH'])
    os.remove(os.environ['APPROVAL_AUDIT_LOG'])
    config_dir.rmdir()
    state_dir.rmdir()
    logs_dir.rmdir()
