# Email Drafter - Impact Checklist

This checklist helps you assess the impact of deploying or modifying the `email_drafter` skill.

---

## Pre-Deployment Checklist

### Environment Setup

- [ ] **Vault Path Configured**
  ```bash
  echo $VAULT_PATH
  # Expected: /absolute/path/to/vault
  ```

- [ ] **Email_Drafts Directory Created**
  ```bash
  test -d "$VAULT_PATH/Email_Drafts" && echo "✅ Exists" || mkdir -p "$VAULT_PATH/Email_Drafts"
  ```

- [ ] **Write Permissions Verified**
  ```bash
  test -w "$VAULT_PATH/Email_Drafts" && echo "✅ Writable" || echo "❌ Not writable"
  ```

- [ ] **Email Configuration Set** (Optional but recommended)
  ```bash
  # Check email environment variables
  env | grep EMAIL_
  ```

---

### Functional Testing

- [ ] **Test Customer Inquiry Response**
  ```javascript
  await draftEmail({
    intent: "customer_inquiry_response",
    recipient: { name: "Test Customer", email: "test@example.com", type: "customer" },
    context: { original_subject: "Test Question", original_message: "Sample inquiry" },
    tone: "friendly",
    key_points: ["Answer question", "Provide solution"]
  });
  ```

- [ ] **Test Meeting Request**
  ```javascript
  await draftEmail({
    intent: "meeting_request",
    recipient: { name: "Test Recipient", email: "test@example.com", type: "external_stakeholder" },
    context: { meeting_purpose: "Test Meeting", proposed_dates: ["2025-02-10T14:00:00Z"] },
    tone: "formal"
  });
  ```

- [ ] **Test Status Update**
  ```javascript
  await draftEmail({
    intent: "status_update",
    recipient: { name: "Team", email: "team@company.com", type: "internal_team" },
    context: { project_name: "Test Project", reporting_period: "Week 1" },
    tone: "semi-formal"
  });
  ```

- [ ] **Test Rejection Email**
  ```javascript
  await draftEmail({
    intent: "polite_rejection",
    recipient: { name: "Vendor", email: "vendor@example.com", type: "vendor" },
    context: { rejection_reason: "already_committed_to_another_vendor" },
    tone: "formal"
  });
  ```

- [ ] **Verify Unique Draft ID Generation**
  ```bash
  # Create 10 drafts and check for ID collisions
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -exec grep "draft_id:" {} \; | sort | uniq -d
  # Expected: No output (no duplicates)
  ```

---

### Output Validation

- [ ] **YAML Frontmatter Present**
  ```bash
  head -n 15 "$VAULT_PATH/Email_Drafts/"*.md | grep "draft_id:"
  ```

- [ ] **Required Fields Populated**
  - draft_id
  - created_at
  - status
  - email_type
  - recipient
  - tone

- [ ] **Email Body Not Empty**
  ```bash
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -exec grep -A 5 "## Email Body" {} \; | grep -v "^$" | wc -l
  # Expected: > 0 (non-empty bodies)
  ```

- [ ] **Subject Lines Generated**
  ```bash
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -exec grep "## Alternative Subject Lines" {} \;
  ```

- [ ] **Follow-Up Actions Included**
  ```bash
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -exec grep "## Follow-Up Actions" {} \;
  ```

---

### Security & Compliance

- [ ] **No Sensitive Data in Logs**
  ```bash
  # Verify email bodies are NOT logged to system logs
  grep -r "Email Body:" /var/log/ 2>/dev/null | wc -l
  # Expected: 0 (no email bodies in logs)
  ```

- [ ] **Email Validation Working**
  ```javascript
  // Test with invalid email
  try {
    await draftEmail({
      recipient: { email: "invalid-email" }  // Missing @domain
    });
  } catch (error) {
    console.log("✅ Validation working:", error.message);
  }
  ```

- [ ] **Path Traversal Protection**
  ```javascript
  // Test with malicious path
  try {
    await draftEmail({
      recipient: { email: "test@example.com" },
      metadata: { file_path: "../../../etc/passwd" }  // Should be rejected
    });
  } catch (error) {
    console.log("✅ Path validation working:", error.message);
  }
  ```

- [ ] **PII Handling Compliant**
  - Customer names/emails not logged
  - Draft files only accessible to authorized agents
  - Audit logs properly sanitized

---

### Integration Testing

- [ ] **Works with vault_state_manager**
  ```javascript
  const { readVaultFile } = require('../vault/vault_state_manager');
  const draftContent = await readVaultFile('Email_Drafts/[draft-file].md');
  console.log("✅ Vault integration working");
  ```

- [ ] **Works with company_handbook_enforcer** (if deployed)
  ```javascript
  const { checkPolicyCompliance } = require('../compliance/company_handbook_enforcer');
  const draft = await draftEmail({ ... });
  const compliance = await checkPolicyCompliance({ type: "email", content: draft.body });
  console.log("✅ Compliance check working");
  ```

- [ ] **Works with approval_request_creator** (if deployed)
  ```javascript
  const draft = await draftEmail({
    recipient: { type: "external_stakeholder", ... },
    requires_approval: true
  });
  // Verify approval request is created
  ```

---

### Performance Testing

- [ ] **Single Draft Generation Time**
  ```javascript
  const start = Date.now();
  await draftEmail({ ... });
  const elapsed = Date.now() - start;
  console.log(`✅ Draft created in ${elapsed}ms`);
  // Expected: < 2000ms (2 seconds)
  ```

- [ ] **Batch Draft Generation (10 drafts)**
  ```javascript
  const start = Date.now();
  await Promise.all([...Array(10)].map(() => draftEmail({ ... })));
  const elapsed = Date.now() - start;
  console.log(`✅ 10 drafts created in ${elapsed}ms`);
  // Expected: < 10000ms (10 seconds)
  ```

- [ ] **File System Performance**
  ```bash
  # Check disk space
  df -h "$VAULT_PATH"
  # Ensure sufficient space for drafts
  ```

---

## Deployment Impact Assessment

### Storage Impact

- [ ] **Estimate Storage Requirements**
  ```bash
  # Average draft file size
  du -sh "$VAULT_PATH/Email_Drafts"/*.md | awk '{sum+=$1} END {print sum/NR " KB per draft"}'
  ```

- [ ] **Calculate Monthly Storage Needs**
  ```
  Expected drafts per day: _______
  Average draft size: _______ KB
  Monthly storage: _______ MB
  ```

### Network Impact

- [ ] **No Network Calls Required** ✅
  - Skill operates entirely on local filesystem
  - No external API dependencies
  - No email server connections (draft only)

### Compute Impact

- [ ] **CPU Usage Acceptable**
  ```bash
  # Monitor CPU during draft generation
  top -b -n 1 | grep [process-name]
  ```

- [ ] **Memory Usage Acceptable**
  ```bash
  # Monitor memory during draft generation
  ps aux | grep [process-name] | awk '{print $6 " KB"}'
  ```

---

## Operational Readiness

### Monitoring

- [ ] **Draft Creation Metrics**
  ```bash
  # Count drafts created today
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -mtime -1 | wc -l
  ```

- [ ] **Draft Status Distribution**
  ```bash
  # Count by status
  grep -r "status:" "$VAULT_PATH/Email_Drafts" | cut -d':' -f3 | sort | uniq -c
  ```

- [ ] **Error Rate Tracking**
  ```bash
  # Check for failed draft attempts (if logging is enabled)
  grep "Failed to create email draft" "$VAULT_PATH/Audit_Logs"/*.log | wc -l
  ```

### Alerting

- [ ] **Disk Space Alert** (>80% full)
  ```bash
  df -h "$VAULT_PATH" | awk 'NR==2 {if (substr($5,1,length($5)-1) > 80) print "⚠️  Disk space low"}'
  ```

- [ ] **Stale Drafts Alert** (>30 days old)
  ```bash
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -mtime +30 | wc -l
  ```

### Runbook Tasks

- [ ] **Clean Up Old Drafts**
  ```bash
  # Archive drafts older than 90 days
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -mtime +90 -exec mv {} "$VAULT_PATH/Email_Drafts_Archive/" \;
  ```

- [ ] **Backup Email_Drafts Folder**
  ```bash
  # Daily backup
  tar -czf "$VAULT_PATH/Email_Drafts.backup.$(date +%Y%m%d).tar.gz" "$VAULT_PATH/Email_Drafts"
  ```

- [ ] **Verify Draft Integrity**
  ```bash
  # Check for corrupted YAML frontmatter
  find "$VAULT_PATH/Email_Drafts" -name '*.md' -exec sh -c 'head -n 1 "$1" | grep -q "^---$" || echo "Corrupted: $1"' _ {} \;
  ```

---

## Risk Mitigation

### High-Risk Scenarios

- [ ] **Sensitive Email Leaked**
  - **Mitigation:** Never log email content; restrict file access to authorized agents
  - **Detection:** Monitor audit logs for unauthorized access
  - **Response:** Rotate credentials if breach detected

- [ ] **Wrong Recipient Specified**
  - **Mitigation:** Require human review for external emails (`EMAIL_REQUIRE_REVIEW=true`)
  - **Detection:** Validation checks on recipient email format
  - **Response:** Manual review before sending

- [ ] **Non-Compliant Email Content**
  - **Mitigation:** Integrate with `company_handbook_enforcer`
  - **Detection:** Policy compliance checks before draft finalization
  - **Response:** Flag draft for review; do not send

- [ ] **Disk Space Exhaustion**
  - **Mitigation:** Implement draft retention policy (auto-archive after 90 days)
  - **Detection:** Disk space monitoring alerts
  - **Response:** Clean up old drafts; increase storage capacity

---

## Rollback Plan

If deployment fails or issues arise:

### Step 1: Stop Draft Generation
```bash
# Disable email_drafter skill
mv .claude/skills/communication/email_drafter .claude/skills/communication/email_drafter.disabled
```

### Step 2: Preserve Existing Drafts
```bash
# Backup all drafts created during deployment
cp -r "$VAULT_PATH/Email_Drafts" "$VAULT_PATH/Email_Drafts.rollback.$(date +%Y%m%d)"
```

### Step 3: Restore Previous Version (if applicable)
```bash
# Restore from git
git checkout HEAD~1 -- .claude/skills/communication/email_drafter/
```

### Step 4: Verify Rollback Success
```bash
# Check skill is disabled
ls .claude/skills/communication/ | grep email_drafter
# Expected: email_drafter.disabled (or nothing)
```

### Step 5: Notify Stakeholders
```bash
# Send notification
echo "email_drafter skill rolled back due to [reason]" | mail -s "Skill Rollback" team@company.com
```

---

## Success Criteria

Deployment is successful if ALL of the following are true:

- [ ] All functional tests pass
- [ ] No errors in logs during test period (24 hours)
- [ ] Draft generation time < 2 seconds per draft
- [ ] No security vulnerabilities detected
- [ ] Integration tests pass with other skills
- [ ] Human review confirms email quality is acceptable
- [ ] Compliance checks pass (if applicable)
- [ ] Monitoring and alerting functional
- [ ] Runbook tested and documented
- [ ] Rollback plan validated

---

## Post-Deployment Validation

### Day 1: Initial Validation
- [ ] Monitor first 10 drafts manually
- [ ] Verify no errors in logs
- [ ] Check draft file integrity
- [ ] Confirm email quality meets standards

### Week 1: Ongoing Monitoring
- [ ] Review draft creation metrics daily
- [ ] Check for any compliance issues
- [ ] Gather feedback from email recipients
- [ ] Adjust tone/formatting based on feedback

### Month 1: Performance Review
- [ ] Analyze draft quality trends
- [ ] Review error rates and root causes
- [ ] Assess storage and compute usage
- [ ] Plan optimizations if needed

---

## Continuous Improvement

### Metrics to Track

1. **Draft Quality Score** (manual review sample)
   - Target: >90% acceptable quality
   - Measure: Weekly sample of 10 random drafts

2. **Draft Generation Success Rate**
   - Target: >99%
   - Measure: (Successful drafts / Total attempts) * 100

3. **Average Draft Creation Time**
   - Target: <2 seconds
   - Measure: Timestamp in metadata

4. **Human Review Rate** (for sensitive emails)
   - Target: 100% for external stakeholder emails
   - Measure: Drafts with `requires_review: true`

5. **Compliance Violation Rate**
   - Target: 0%
   - Measure: Policy violations detected by handbook enforcer

---

## Contact Information

**Skill Owner:** [Team/Person responsible]
**On-Call Support:** [Contact details]
**Documentation:** `.claude/skills/communication/email_drafter/SKILL.md`
**Issue Tracker:** [Link to issue tracker]

---

## Approval Sign-Off

- [ ] **Technical Lead:** _____________________ Date: _______
- [ ] **Security Review:** _____________________ Date: _______
- [ ] **Compliance Review:** _____________________ Date: _______
- [ ] **Product Owner:** _____________________ Date: _______

---

**Deployment Date:** _______________________
**Deployed By:** _______________________
**Version:** v1.0.0
