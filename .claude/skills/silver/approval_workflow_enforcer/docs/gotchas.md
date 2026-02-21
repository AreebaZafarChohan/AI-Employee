# Approval Workflow Enforcer - Common Gotchas & Troubleshooting

## Overview
This document outlines common pitfalls, anti-patterns, and troubleshooting tips encountered when managing and enforcing approval workflows using the `approval_workflow_enforcer` skill.

---

## 1. Workflow Definition Issues (`workflow-rules.json`)

### Gotcha: Ambiguous Approver Resolution

**Symptom:**
Requests get stuck because no approvers are identified for a stage, or the wrong approvers are notified.

**Problem:**
-   `approvers_by` rules (e.g., `role`, `department`) in `workflow-rules.json` do not match actual user data in the integrated user directory.
-   The `_resolve_approvers` function in `approval_enforcer.py` has logic errors or doesn't handle all defined `approvers_by` criteria.
-   The external user directory API is unavailable or returns unexpected data.

**Solution:**
-   **Test `_resolve_approvers`:** Rigorously test the `_resolve_approvers` function with various `approvers_by` configurations and mock user data.
-   **Fallback Approvers:** Implement fallback approvers or escalation to an admin if no approvers are resolved.
-   **User Directory Sync:** Ensure the user directory (e.g., LDAP, internal API) is consistently updated and its schema matches expectations.
-   **Comprehensive Logging:** Log the outcome of approver resolution, including any failures to find matching users.

### Gotcha: `conditional_logic` Not Behaving as Expected

**Symptom:**
Workflows take unexpected paths, stages are skipped when they shouldn't be, or vice-versa.

**Problem:**
-   Syntax errors or logical flaws in the `conditional_logic` string within `workflow-rules.json`.
-   The `request.context` object (used in `eval`) does not contain the expected keys or values.
-   Reliance on Python's `eval()` for complex expressions can be brittle and unsafe if not properly sandboxed.

**Solution:**
-   **Simplify Conditions:** Keep `conditional_logic` expressions as simple as possible.
-   **Inspect `request.context`:** Log the `request.context` object before the `conditional_logic` is evaluated to verify its contents.
-   **External Expression Evaluator:** For production, replace direct `eval()` with a safer, dedicated expression parsing library (e.g., `asteval`, `simpleeval`) that allows strict control over available functions and variables.
-   **Unit Test Conditions:** Create unit tests specifically for each `conditional_logic` expression to ensure it behaves as intended with various contexts.

### Gotcha: Loop in Workflow or Unreachable Stages

**Symptom:**
Requests continuously cycle through stages, or a workflow cannot progress past a certain point.

**Problem:**
-   Misconfigured `conditional_logic` that always routes back to a previous stage.
-   `required_approvers` is set to a number that can never be met (e.g., higher than the number of possible approvers).
-   Logic for `_get_next_stage` is faulty, skipping valid next stages or creating infinite loops.

**Solution:**
-   **Workflow Visualization:** Use Mermaid flowcharts or other tools to visually map out complex workflows to spot loops or dead ends.
-   **Validate Workflow Graph:** Implement a script to programmatically validate workflow definitions against common anti-patterns (e.g., cycles, unreachable nodes).
-   **Timeout Stages:** Ensure every stage has a reasonable `timeout_hours` and `escalate_to` to prevent indefinite stalling.

---

## 2. Enforcement Logic Issues (`approval_enforcer.py`)

### Gotcha: `record_approval` Fails Due to Authority

**Symptom:**
Approvers attempting to approve a request are denied with a `PermissionError` or similar message, even if they believe they are authorized.

**Problem:**
-   The `approver_id` provided does not match any of the `request.next_approvers` identified by `_resolve_approvers`.
-   The `_resolve_approvers` function returned an empty list or an incorrect list of approvers for the current stage.
-   An approver is trying to approve a request that is not currently in their stage.

**Solution:**
-   **Verify `next_approvers`:** When a request reaches a stage, log the `request.next_approvers` to verify who was assigned.
-   **Communicating Authorized Approvers:** Ensure that notifications sent to approvers explicitly state who *is* authorized for the current stage.
-   **Debug `_resolve_approvers`:** Step through the logic in `_resolve_approvers` to see why a particular approver is not being identified.

### Gotcha: Workflow Stuck at `all_required` Stage

**Symptom:**
Multiple approvers have approved a stage configured as `all_required`, but the workflow does not progress.

**Problem:**
-   The logic for checking `stage_complete` in `record_approval` for `all_required` stages is incorrect (e.g., comparing `len(stage_approvals)` to `required_approvers` instead of `len(request.next_approvers)`).
-   One or more approvers have not yet responded, or their response was a rejection.

**Solution:**
-   **Review `record_approval` Logic:** Carefully check the condition for `stage_complete` in `approval_enforcer.py` for `all_required` types. It should count approved responses *against the total number of designated approvers for that stage*.
-   **List Pending Approvers:** Provide a clear way to list *who* is still pending approval for an `all_required` stage.

---

## 3. Configuration & Integration Issues

### Gotcha: `APPROVAL_STATE_PATH` Not Persisting State

**Symptom:**
After restarting the `approval_enforcer` script, all pending requests are lost or revert to an old state.

**Problem:**
-   The `_save_approval_state()` method is not being called frequently enough or consistently.
-   Permissions issues prevent writing to `APPROVAL_STATE_PATH`.
-   The `_load_approval_state()` method has issues parsing the JSON file.

**Solution:**
-   **Call `_save_approval_state()`:** Ensure `_save_approval_state()` is called after every state-changing operation (workflow start, approval recorded, escalation).
-   **Check Permissions:** Verify `rw` permissions on the `state_path` for the process running the enforcer.
-   **JSON Format Validation:** Use a JSON linter to validate the `approval_state.json` file if manual inspection is needed.

### Gotcha: Notifications Not Sent or Received

**Symptom:**
Approvers are not notified when a request is assigned to them, or stakeholders don't receive status updates.

**Problem:**
-   `APPROVAL_NOTIFICATION_SERVICE` environment variable is not set or points to an invalid endpoint.
-   Authentication for the notification service (e.g., `APPROVAL_API_AUTH_TOKEN`) is incorrect or expired.
-   Network issues preventing calls to the notification service.
-   The `_notify_approvers`, `_notify_on_status_change`, `_notify_on_escalation` methods have not been fully implemented to interact with a real notification API.

**Solution:**
-   **Verify Environment Variables:** Confirm all notification-related environment variables are correctly set.
-   **Test Notification Integrations:** Use a dedicated test script to ensure the notification service API is reachable and correctly authenticated.
-   **Implement Full Notification Logic:** Ensure the notification methods in `approval_enforcer.py` contain the actual API calls to your chosen notification platform.

---

## Quick Reference: Error Messages

| Error Message                                     | Common Cause                                                   | Solution                                                                |
|---------------------------------------------------|----------------------------------------------------------------|-------------------------------------------------------------------------|
| `ValueError: Workflow 'id' not found.`            | `start_workflow` called with a non-existent `workflow_id`.     | Check `workflow-rules.json` for correct `workflow_id`.                  |
| `ValueError: Approval request 'id' already exists.` | Attempting to start a workflow with a duplicate `request_id`.  | Ensure `request_id` is unique.                                          |
| `FileNotFoundError: Workflow rules file not found.` | `APPROVAL_RULES_PATH` points to a non-existent file.           | Verify `APPROVAL_RULES_PATH` and file existence.                        |
| `PermissionError: Approver 'id' is not authorized.` | An `approver_id` tried to approve a request for which they were not designated. | Check `_resolve_approvers` logic and `approvers_by` rules.              |
| `Error evaluating conditional logic '...'`        | Syntax error in `conditional_logic` or `request.context` mismatch. | Simplify condition, inspect `request.context`, use safer evaluator.     |
| Requests stuck in 'pending' status.               | Timeout not configured, `check_for_timeouts_and_escalations` not running, or approvers are unresponsive. | Set `timeout_hours`, ensure periodic check.                             |
| State not persisting after restart.               | `_save_approval_state` not called, or permissions issue.       | Ensure `_save_approval_state` is called consistently and check write permissions. |

---

**Last Updated:** 2026-02-06
