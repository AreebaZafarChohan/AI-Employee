# Approval Workflow Enforcer Skill Manifest

This document outlines the components, structure, and usage of the `approval_workflow_enforcer` skill.

## Skill Details

*   **Skill Name:** `approval_workflow_enforcer`
*   **Domain:** `silver`
*   **Purpose:** Automatically manage and enforce company-defined approval workflow rules.
*   **Version:** 1.0.0

## Directory Structure

```
.
├── README.md                 # Quick start guide and overview
├── SKILL.md                  # Comprehensive skill specification
├── assets/                   # Templates and core logic
│   ├── workflow-rules.json   # JSON file defining approval workflows
│   ├── example-workflow-config.json # Example workflow definition (duplicate of workflow-rules.json for clarity)
│   ├── approval_enforcer.py  # Python script for approval enforcement
│   └── MANIFEST.md           # This manifest file
└── docs/                     # Supporting documentation
    ├── gotchas.md            # Common pitfalls and troubleshooting
    ├── impact-checklist.md   # Impact assessment guide
    └── patterns.md           # Approval workflow patterns and best practices
```

## Core Components

### `approval_enforcer.py`

*   **Description:** A Python script responsible for initiating, tracking, and enforcing multi-stage approval workflows based on defined rules. It manages request states, resolves approvers, handles timeouts, and records audit trails.
*   **Functionality:**
    *   Loads workflow rules from `workflow-rules.json`.
    *   Loads and saves approval state to `approval_state.json`.
    *   Manages starting new workflows and recording approvals/rejections.
    *   Resolves approvers dynamically based on role, department, etc.
    *   Evaluates conditional logic for stages and workflows.
    *   Checks for timeouts and triggers escalations.
    *   Writes audit logs for all significant actions.
*   **Usage:** Typically run as a long-running service or invoked via API/webhook for specific actions (start, approve, reject).

### `workflow-rules.json`

*   **Description:** A JSON file that defines the structure and rules for one or more approval workflows. Each workflow specifies its stages, approver resolution logic (`approvers_by`), timeout settings, and conditional logic.
*   **Structure:** Defines `workflows` each with an `id`, `name`, `description`, `triggers`, and an array of `stages`. Stages define `id`, `name`, `type` (sequential, any_one, all_required), `required_approvers`, `approvers_by` rules, `timeout_hours`, and `escalate_to`.

### `example-workflow-config.json`

*   **Description:** A duplicate of `workflow-rules.json`, serving as an explicit example configuration file to illustrate the expected format and content for defining approval workflows.

### State and Audit Files

*   **`state/approval_state.json`:** A JSON file managed by `approval_enforcer.py` that stores the current state of all active approval requests. This includes their status, current stage, recorded approvals, and history.
*   **`logs/approval-audit.log`:** A JSONL (JSON Lines) file where `approval_enforcer.py` appends an immutable record of every significant event in an approval workflow.

## Documentation

*   **`SKILL.md`:** Detailed specification covering overview, impact analysis, environment variables, network implications, blueprints, validation checklist, and anti-patterns.
*   **`README.md`:** A concise overview of the skill, quick start instructions, and key features.
*   **`docs/patterns.md`:** Explores different patterns for defining approval workflows (sequential, parallel, conditional, dynamic approver resolution, timeout/escalation).
*   **`docs/impact-checklist.md`:** A checklist to assess the impact of approval workflow enforcement on compliance, security, and operational efficiency.
*   **`docs/gotchas.md`:** Highlights common issues, anti-patterns, and troubleshooting tips related to defining and enforcing approval workflows.

## Environment Variables

Refer to `SKILL.md` for a comprehensive list of required and optional environment variables that configure the behavior of the `approval_workflow_enforcer` skill, including paths to rules/state/audit files, default timeouts, and integration endpoints.

## Anti-Patterns

Refer to `SKILL.md` and `docs/gotchas.md` for detailed descriptions of anti-patterns to avoid when implementing and using approval workflows, such as skipping approvals, hardcoding approvers, ignoring exceptions, and insufficient authority validation.

## Validation

The skill incorporates internal checks within `approval_enforcer.py` for validating approver authority and workflow progression. A comprehensive `Validation Checklist` is provided in `SKILL.md` to guide users in assessing the robustness, security, and compliance of their approval workflows.

---
**Last Updated:** 2026-02-06
**Maintained by:** Silver Team
