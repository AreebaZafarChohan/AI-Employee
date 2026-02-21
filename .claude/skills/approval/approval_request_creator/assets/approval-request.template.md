---
request_id: {{REQUEST_ID}}
created_at: {{CREATED_AT_ISO}}
expires_at: {{EXPIRES_AT_ISO}}
timeout_action: {{TIMEOUT_ACTION}}
status: pending
action_type: {{ACTION_TYPE}}
priority: {{PRIORITY}}
approver: {{APPROVER_EMAIL}}
approval_level: {{APPROVAL_LEVEL}}
approved_by: null
approved_at: null
rejected_by: null
rejected_at: null
rejection_reason: null
---

# Approval Request: {{ACTION_TYPE_DISPLAY}} - {{ACTION_DESCRIPTION}}

**Request ID:** {{REQUEST_ID}}
**Created:** {{CREATED_AT_HUMAN}}
**Expires:** {{EXPIRES_AT_HUMAN}} ({{SLA_HOURS}} hours)
**Status:** 🟡 Pending Approval

---

## Action Details

**Type:** {{ACTION_TYPE_DISPLAY}}
**Description:** {{ACTION_DESCRIPTION}}
**Environment:** {{ENVIRONMENT}}
**Initiator:** {{INITIATOR}}
**Priority:** {{PRIORITY_EMOJI}} {{PRIORITY_DISPLAY}}

**Action Details:**
{{ACTION_DETAILS_FORMATTED}}

---

## Policy Violation

**Policy:** {{POLICY_KEY}}
**Section:** {{POLICY_SECTION}}
**Severity:** {{SEVERITY_EMOJI}} {{SEVERITY}}

**Reasoning:**
{{VIOLATION_REASONING}}

**Impact Assessment:**
- **Business Risk:** {{BUSINESS_RISK}}
- **Affected Stakeholders:** {{AFFECTED_STAKEHOLDERS}}
- **Risk Level:** {{RISK_LEVEL}}

---

## Justification

**Business Reason:**
{{BUSINESS_REASON}}

**Urgency:** {{URGENCY_EMOJI}} {{URGENCY_DISPLAY}}
**Customer Impact:** {{CUSTOMER_IMPACT}}

**Alternatives Considered:** {{ALTERNATIVE_CONSIDERED}}
{{#if ALTERNATIVE_CONSIDERED}}
**Why Not:** {{ALTERNATIVE_REJECTED_REASON}}
{{else}}
**Reason:** {{ALTERNATIVE_REJECTED_REASON}}
{{/if}}

---

## Approval Required

**Required Approver:** {{REQUIRED_APPROVER}}
**Approver Contact:** {{APPROVER_EMAIL}}
**Approval Level:** {{APPROVAL_LEVEL_DISPLAY}}
**SLA:** {{SLA_HOURS}} hours

---

## How to Approve or Reject

### ✅ To Approve:

1. Add the following to the YAML frontmatter at the top of this file:
   ```yaml
   status: approved
   approved_by: "Your Name <your.email@company.com>"
   approved_at: "{{CURRENT_TIMESTAMP_ISO}}"
   ```

2. (Optional) Add approval notes in the `## Approval Decision` section below

3. Save the file

4. The agent will automatically detect approval and execute the action

### ❌ To Reject:

1. Add the following to the YAML frontmatter at the top of this file:
   ```yaml
   status: rejected
   rejected_by: "Your Name <your.email@company.com>"
   rejected_at: "{{CURRENT_TIMESTAMP_ISO}}"
   rejection_reason: "Your reason here"
   ```

2. (Optional) Provide detailed rejection reasoning in the `## Approval Decision` section below

3. Save the file

4. The agent will abort the action and log the rejection

---

## Approval Decision

<!-- Approver: Add your decision notes here -->


---

## Audit Trail

- **Session ID:** {{SESSION_ID}}
- **Audit Log ID:** {{AUDIT_LOG_ID}}
- **Handbook Version:** {{HANDBOOK_VERSION}}
- **Enforcer Version:** {{ENFORCER_VERSION}}
- **IP Address:** {{IP_ADDRESS}}
- **User Agent:** {{USER_AGENT}}

---

**🔔 Notifications:**
{{#if NOTIFICATIONS}}
{{NOTIFICATIONS_LIST}}
{{else}}
- ℹ️ No notifications configured
{{/if}}

---

## Related Resources

{{#if RELATED_LINKS}}
{{RELATED_LINKS_LIST}}
{{else}}
- No related resources
{{/if}}
