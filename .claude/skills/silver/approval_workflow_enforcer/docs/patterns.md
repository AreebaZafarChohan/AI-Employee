# Approval Workflow Enforcer - Common Patterns

## Overview
This document describes common patterns, strategies, and best practices for defining and enforcing robust approval workflows.

---

## Pattern 1: Sequential Approval Workflow

### Use Case
For processes where requests must be approved by a series of distinct individuals or teams, each reviewing and signing off before the next can proceed. Common in code deployments, budget approvals, or legal reviews.

### Strategy
1.  **Ordered Stages:** Define stages with an explicit order of execution.
2.  **Single-Point Approval per Stage:** Each stage typically requires one or more approvals from a designated group, but the workflow only proceeds *after* the current stage's requirements are met.
3.  **Clear Hand-offs:** Ensure notifications are sent to the next set of approvers once their stage is active.
4.  **Early Exit on Rejection:** Any rejection at any stage typically halts the entire workflow.

### Example Workflow Rule (`workflow-rules.json`)
```json
{
  "id": "code_deployment_staging",
  "name": "Staging Deployment Approval",
  "stages": [
    {
      "id": "dev_lead_review",
      "name": "Development Lead Review",
      "type": "any_one",
      "required_approvers": 1,
      "approvers_by": {"role": "dev-lead", "team": "impacted"},
      "timeout_hours": 24
    },
    {
      "id": "qa_review",
      "name": "QA Team Sign-off",
      "type": "any_one",
      "required_approvers": 1,
      "approvers_by": {"role": "qa-lead"},
      "timeout_hours": 48
    }
  ]
}
```

---

## Pattern 2: Parallel Approval Workflow

### Use Case
When multiple independent approvals are needed concurrently, and the order does not matter. The workflow progresses only when *all* (or a specific number) of the parallel approvals are obtained. Common in cross-functional reviews (e.g., security, legal, finance) or large-scale project approvals.

### Strategy
1.  **Concurrent Notifications:** All approvers for a parallel stage are notified simultaneously.
2.  **Type `all_required` or `any_one`:**
    *   `all_required`: Every designated approver must approve.
    *   `any_one`: At least one designated approver must approve to proceed.
3.  **Consolidation:** The system waits for all required responses before moving to the next sequential stage (if any).

### Example Workflow Rule (`workflow-rules.json`)
```json
{
  "id": "feature_release_signoff",
  "name": "Feature Release Final Sign-off",
  "stages": [
    {
      "id": "cross_functional_review",
      "name": "Cross-Functional Review",
      "type": "all_required",
      "required_approvers": "all",
      "approvers_by": [
        {"role": "product-owner"},
        {"role": "security-lead"},
        {"role": "legal-advisor"}
      ],
      "timeout_hours": 72
    }
  ]
}
```

---

## Pattern 3: Conditional Approval Workflow

### Use Case
Workflows that vary based on the characteristics of the request (e.g., amount of a budget request, severity of a change, environment of a deployment).

### Strategy
1.  **Contextual Evaluation:** Use `conditional_logic` fields at the workflow or stage level to dynamically alter the path or requirements.
2.  **Branching:** Conditions can lead to different sets of stages or skip certain stages entirely.
3.  **Thresholds:** Define rules based on numerical thresholds (e.g., budget > $10,000).

### Example Workflow Rule (`workflow-rules.json`)
```json
{
  "id": "expense_claim",
  "name": "Expense Claim Approval",
  "stages": [
    {
      "id": "manager_approval",
      "name": "Direct Manager Approval",
      "type": "any_one",
      "approvers_by": {"relation": "manager"},
      "timeout_hours": 24
    },
    {
      "id": "finance_review_high_value",
      "name": "Finance Review (High Value)",
      "type": "any_one",
      "required_approvers": 1,
      "approvers_by": {"role": "finance-approver"},
      "conditional_logic": "request.amount > 5000",
      "timeout_hours": 48
    }
  ]
}
```

---

## Pattern 4: Dynamic Approver Resolution

### Use Case
When the actual approvers are not static but depend on the request initiator, project, or impacted teams.

### Strategy
1.  **User Directory Integration:** Use an external system (e.g., LDAP, HR system, internal user directory API) to look up approvers.
2.  **Attributes for Resolution:** Define approvers based on attributes like:
    *   `role`: "security-lead", "dev-lead"
    *   `department`: "finance", "engineering"
    *   `relation`: "manager of initiator", "peer of initiator"
    *   `contextual`: "lead of impacted team"
3.  **Fallback Mechanisms:** Define default approvers or escalation paths if dynamic resolution fails.

### Example `approvers_by` Rule (`workflow-rules.json`)
```json
"approvers_by": {
  "role": "security-lead",
  "department": "security",
  "region": "request.region_of_impact"
}
```
*Note: The `_resolve_approvers` function in `approval_enforcer.py` would implement the logic to query the user directory based on these attributes.*

---

## Pattern 5: Timeout and Escalation

### Use Case
To prevent workflows from getting stuck indefinitely due to unresponsive approvers, ensuring timely processing of requests.

### Strategy
1.  **Timeout per Stage:** Define `timeout_hours` for each stage.
2.  **Automated Escalation:** If a stage times out, automatically escalate the request to a predefined `escalate_to` role or individual.
3.  **Notifications:** Send clear notifications to the original approvers, the escalated party, and the request initiator about the timeout and escalation.

### Example Workflow Rule (`workflow-rules.json`)
```json
{
  "id": "critical_bug_fix_approval",
  "name": "Critical Bug Fix Approval",
  "stages": [
    {
      "id": "eng_manager_signoff",
      "name": "Engineering Manager Sign-off",
      "type": "any_one",
      "approvers_by": {"role": "eng-manager"},
      "timeout_hours": 12,
      "escalate_to": "director_of_eng"
    }
  ]
}
```

---

## Best Practices for Approval Workflows

1.  **Simple First:** Start with the simplest possible workflow and add complexity as needed.
2.  **Clear Rules:** Ensure all rules are unambiguous and cover all expected scenarios.
3.  **Define Roles, Not People:** Design workflows around roles (e.g., "Security Lead") rather than specific individuals.
4.  **Automate Notifications:** Use integrated notification services to keep all parties informed.
5.  **Audit Everything:** Log every action, decision, and state change for compliance and debugging.
6.  **Handle Exceptions:** Plan for rejections, timeouts, and unavailable approvers.
7.  **Regular Review:** Periodically review and update workflow rules to reflect organizational changes or process improvements.
8.  **Test Thoroughly:** Test all paths, including happy paths, rejections, and timeouts, before deploying.
9.  **User Experience:** While this is an enforcer, consider the user experience for approvers (e.g., easy-to-use notification links).

---

**Last Updated:** 2026-02-06
