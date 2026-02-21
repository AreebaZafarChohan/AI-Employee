# Company Handbook Enforcer - Gotchas

Common pitfalls, edge cases, and known issues when enforcing company handbook policies.

---

## Parsing Gotchas

### Issue 1: Ambiguous Policy Language

**Problem:** Handbook uses vague terms like "reasonable", "appropriate", "timely"

**Example:**
```markdown
# In Company_Handbook.md
Payments should be processed in a reasonable timeframe.
```

**Why It's a Problem:**
- "Reasonable" is subjective
- Cannot programmatically validate
- Different interpretations possible

**Mitigation:**
1. Flag ambiguous policies during parsing
2. Request clarification from policy owner
3. Use conservative interpretation (shortest reasonable time)
4. Document interpretation in skill

**Better Handbook Language:**
```markdown
Payments must be processed within 2 business days of approval.
```

---

### Issue 2: Conflicting Policies

**Problem:** Two policies contradict each other

**Example:**
```markdown
# Policy A
All customer emails must be sent within 1 hour of request.

# Policy B
Customer emails require manager approval (SLA: 4 hours).
```

**Why It's a Problem:**
- Cannot satisfy both policies simultaneously
- Unclear which takes precedence
- Validation logic fails

**Mitigation:**
1. Detect conflicts during parsing
2. Log warning in audit trail
3. Escalate to policy owner for resolution
4. Apply most restrictive policy if no guidance

**Resolution:**
```markdown
Customer emails require manager approval (SLA: 4 hours).
Once approved, must be sent within 1 hour.
```

---

### Issue 3: Missing Policy Sections

**Problem:** Handbook doesn't cover a required policy area

**Example:**
```markdown
# Action requires data handling policy
# But Company_Handbook.md has no Privacy section
```

**Why It's a Problem:**
- Cannot validate action
- Unclear if action allowed or blocked
- Default behavior ambiguous

**Mitigation:**
1. Define default policy for missing sections
2. Flag missing sections in validation report
3. Allow action with warning in `WARN` mode
4. Block action in `STRICT` mode until policy added

**Configuration:**
```yaml
# In skill config
missing_policy_behavior:
  STRICT: "block"
  WARN: "allow_with_warning"
  SUGGEST: "allow_with_suggestion"
```

---

### Issue 4: Handbook Format Variations

**Problem:** Handbook uses inconsistent formatting

**Example:**
```markdown
# Sometimes uses headers
## Financial Policies
Payment limit: $1000

# Sometimes uses bullet points
- Payment limit without approval: $1000
- Approval required above: $1000

# Sometimes uses tables
| Policy | Limit |
|--------|-------|
| Payment | $1000 |
```

**Why It's a Problem:**
- Parsing logic breaks on unexpected format
- Values extracted incorrectly
- Policy keys inconsistent

**Mitigation:**
1. Support multiple format patterns in parser
2. Normalize extracted policies to standard structure
3. Validate parsed values against expected types
4. Log parsing warnings for manual review

**Recommended Format:**
```yaml
# Use YAML front matter for machine-readable policies
---
financial:
  payment_limit_without_approval: 1000
  approval_required_above: 1000
---

# Human-readable explanation follows...
```

---

## Validation Gotchas

### Issue 5: Context-Dependent Policies

**Problem:** Policy depends on context not captured in action

**Example:**
```markdown
Policy: "Deployments allowed Tue-Thu 10:00-16:00 UTC, except for critical hotfixes"
```

**Why It's a Problem:**
- Action: "Deploy code at 18:00 UTC on Tuesday"
- Is it a hotfix? (Not specified in action)
- Cannot validate without context

**Mitigation:**
1. Require action to include `priority` or `category` field
2. Ask user to clarify when context missing
3. Default to most restrictive interpretation
4. Support context hints in action metadata

**Better Action Structure:**
```javascript
{
  type: "deployment",
  scheduledTime: "2024-01-16T18:00:00Z",
  context: {
    priority: "critical",
    category: "hotfix",
    justification: "Security vulnerability fix"
  }
}
```

---

### Issue 6: Timezone Confusion

**Problem:** Policies specify times without clear timezone

**Example:**
```markdown
Policy: "Deployments allowed 10:00-16:00"
Action: User in PST, server in UTC, handbook author in EST
```

**Why It's a Problem:**
- 10:00 PST ≠ 10:00 UTC ≠ 10:00 EST
- Deployment may violate policy due to timezone mismatch
- Dates can shift across timezone boundaries

**Mitigation:**
1. Always parse times as UTC
2. Require timezone in policy (e.g., "10:00 UTC")
3. Convert action times to UTC before validation
4. Log timezone conversions in audit trail

**Best Practice:**
```yaml
operational:
  deployment_windows:
    - day: "Tuesday"
      start: "10:00:00Z"  # Z suffix = UTC
      end: "16:00:00Z"
```

---

### Issue 7: Currency and Locale Differences

**Problem:** Financial policies don't specify currency

**Example:**
```markdown
Policy: "Payment limit: 1000"
Action: Is this $1000 USD? €1000 EUR? ¥1000 JPY?
```

**Why It's a Problem:**
- Value of 1000 varies drastically by currency
- Exchange rates fluctuate
- Multi-currency operations common

**Mitigation:**
1. Require currency in policy (USD, EUR, etc.)
2. Normalize action amounts to handbook currency
3. Use exchange rate service for conversions
4. Log original and converted amounts

**Better Policy:**
```yaml
financial:
  payment_limit_without_approval:
    amount: 1000
    currency: "USD"
  exchange_rate_source: "https://api.exchangerate.com"
```

---

### Issue 8: Threshold Edge Cases

**Problem:** Policy specifies "above" but action is exactly at limit

**Example:**
```markdown
Policy: "Approval required above $1000"
Action: Payment of exactly $1000
```

**Why It's a Problem:**
- Is $1000 "above" $1000? (No, it's equal)
- Does $1000 require approval? (Ambiguous)
- Language imprecise

**Mitigation:**
1. Treat "above" as strictly greater than (>)
2. Recommend policy use "at or above" (≥) if inclusive
3. Document interpretation in skill
4. Log edge case validations

**Clearer Policy:**
```yaml
financial:
  payment_limit_without_approval: 999.99  # Up to this is OK
  approval_required_at_or_above: 1000.00  # This and above needs approval
```

---

### Issue 9: Regex Complexity in Prohibited Phrases

**Problem:** Simple string matching misses variations

**Example:**
```yaml
prohibited_phrases: ["URGENT", "ASAP"]

Email: "This is urgent and needs attention ASAP."  # Lowercase not caught
Email: "UR GENT message"  # Spacing trick bypasses check
```

**Why It's a Problem:**
- Case sensitivity
- Creative spelling to bypass filters
- Partial matches vs whole word matches

**Mitigation:**
1. Use case-insensitive matching
2. Apply regex patterns for variations
3. Use fuzzy matching for similar phrases
4. Whitelist exceptions (e.g., "urgent care" in medical context)

**Better Validation:**
```javascript
const prohibitedPatterns = [
  /\burgent\b/i,  // Case-insensitive, whole word
  /\basap\b/i,
  /ur\s*gent/i,   // Handles "ur gent" spacing tricks
  /a\s*s\s*a\s*p/i  // Handles "a s a p" spacing tricks
];
```

---

### Issue 10: PII Detection False Positives/Negatives

**Problem:** Automated PII detection is imperfect

**False Positive Example:**
```javascript
// Not actually a phone number, but matches pattern
const testData = "Test case 123-456-7890";
```

**False Negative Example:**
```javascript
// Is a phone number, but doesn't match pattern
const phoneNumber = "1234567890";  // No dashes
```

**Why It's a Problem:**
- Regex patterns miss edge cases
- Context matters (test data vs real data)
- International formats vary widely

**Mitigation:**
1. Use multiple detection strategies:
   - Regex patterns
   - Named entity recognition (NER)
   - Context analysis (is this a test?)
2. Whitelist known test data patterns
3. Flag uncertain cases for human review
4. Prefer false positives (block more) over false negatives (miss PII)

**Better Detection:**
```javascript
function isPII(value, context) {
  // Check for test data markers
  if (context.isTestData || value.includes("test") || value.includes("example")) {
    return { isPII: false, confidence: "high", reason: "test_data" };
  }

  // Check multiple PII patterns
  const patterns = {
    ssn: /\b\d{3}-\d{2}-\d{4}\b/,
    phone: /\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/,
    email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/
  };

  for (const [type, pattern] of Object.entries(patterns)) {
    if (pattern.test(value)) {
      return { isPII: true, confidence: "high", type };
    }
  }

  // Use NER for uncertain cases
  return { isPII: "uncertain", confidence: "low", reason: "needs_review" };
}
```

---

## Enforcement Gotchas

### Issue 11: Enforcement Level Misconfiguration

**Problem:** Production runs with `WARN` instead of `STRICT`

**Why It's a Problem:**
- Policy violations allowed in production
- Compliance risk
- Audit failures

**Mitigation:**
1. Environment detection:
   ```javascript
   const defaultEnforcement = {
     production: "STRICT",
     staging: "WARN",
     development: "SUGGEST"
   };
   const level = process.env.HANDBOOK_ENFORCEMENT_LEVEL || defaultEnforcement[process.env.NODE_ENV];
   ```
2. Alert if enforcement level changed in production
3. Require approval to downgrade enforcement
4. Log enforcement level in every validation

---

### Issue 12: Approval Timeout Edge Cases

**Problem:** Approval timeout expires during approval process

**Scenario:**
1. Action submitted at 14:00, timeout = 4 hours (expires 18:00)
2. Manager starts approval at 17:55
3. Manager clicks "Approve" at 18:02 (2 minutes after timeout)
4. Is approval valid?

**Why It's a Problem:**
- Race condition
- Approval effort wasted
- User frustration

**Mitigation:**
1. Extend timeout when approval process started
2. Grace period (e.g., 5 minutes) after timeout
3. Lock approval after timeout to prevent late submissions
4. Notify approver of impending timeout

**Better Timeout Logic:**
```javascript
function isApprovalValid(request, approval) {
  const timeoutAt = new Date(request.expiresAt);
  const approvalAt = new Date(approval.timestamp);
  const graceMinutes = 5;

  // Check if approval started before timeout
  if (request.approvalStartedAt) {
    const started = new Date(request.approvalStartedAt);
    if (started < timeoutAt) {
      // Allow grace period if started on time
      const graceExpiry = new Date(timeoutAt.getTime() + graceMinutes * 60000);
      return approvalAt <= graceExpiry;
    }
  }

  // Standard timeout check
  return approvalAt <= timeoutAt;
}
```

---

### Issue 13: Approval Bypass via API

**Problem:** User bypasses approval workflow by calling API directly

**Example:**
```javascript
// Through handbook enforcer (blocked)
await processPayment(5000);  // Blocked: requires approval

// Direct API call (bypasses handbook enforcer)
await fetch('/api/payments', {
  method: 'POST',
  body: JSON.stringify({ amount: 5000 })
});  // Succeeds, bypassing policy
```

**Why It's a Problem:**
- Policy enforcement not consistent
- Security vulnerability
- Audit trail incomplete

**Mitigation:**
1. Enforce policies at API gateway level (not just agent)
2. Require authentication and authorization on all endpoints
3. API validates against handbook independently
4. Log all payment API calls for audit

**Layered Enforcement:**
```
Request → API Gateway (handbook check) → Agent (handbook check) → Service (handbook check)
```

---

### Issue 14: Stale Handbook Cache

**Problem:** Handbook updated but cache not invalidated

**Scenario:**
1. Handbook parsed and cached at 10:00 (payment limit = $1000)
2. Handbook updated at 10:30 (payment limit changed to $500)
3. Cache TTL = 1 hour
4. Payment of $750 submitted at 10:45
5. Validated against cached policy ($1000 limit) → Passes
6. Should have failed against new policy ($500 limit)

**Why It's a Problem:**
- Policy changes delayed
- Compliance violations
- Inconsistent enforcement

**Mitigation:**
1. Short cache TTL (5 minutes max for critical policies)
2. Webhook or file watch to invalidate cache on handbook update
3. Version handbook and reject validations against old versions
4. Audit log includes handbook version used

**Cache Invalidation:**
```javascript
// Watch handbook file for changes
fs.watch(HANDBOOK_PATH, (eventType) => {
  if (eventType === 'change') {
    handbookCache.invalidate(HANDBOOK_PATH);
    console.log('Handbook updated, cache invalidated');
  }
});
```

---

## Alternative Suggestion Gotchas

### Issue 15: Context Loss in Alternatives

**Problem:** Suggested alternative loses important context from original

**Example:**
```
Original: "URGENT: Customer X's order #12345 failed, they need immediate refund"

Alternative: "Important: Action Required
Please process the refund by end of day."
```

**Why It's a Problem:**
- Customer name lost
- Order number lost
- Specific issue unclear

**Mitigation:**
1. Preserve key entities when generating alternatives
2. Extract context (names, IDs, specific issues)
3. Template should include placeholders for context
4. Validate alternative contains all critical info

**Better Alternative:**
```
"Important: Action Required by 5:00 PM

Dear Team,

Customer X's order #12345 has failed and requires a refund.

Please process the refund by end of business day today.

Details:
- Customer: X
- Order: #12345
- Issue: Order processing failure
- Required action: Issue refund

If you have questions, please contact support.

Best regards,
[Sender]"
```

---

### Issue 16: Over-Formality in Communication

**Problem:** Alternative suggestion too formal for context

**Example:**
```
Original: "Hey team, can someone look at this bug?"

Alternative (overly formal): "Dear Esteemed Colleagues,

I respectfully request that a member of the engineering team allocate time to investigate the aforementioned software defect at their earliest convenience.

With gratitude,
[Sender]"
```

**Why It's a Problem:**
- Tone mismatch (internal vs external)
- Stiff and unnatural
- Slows communication

**Mitigation:**
1. Context-aware tone (internal vs customer-facing)
2. Multiple alternative templates:
   - Formal (external, legal)
   - Professional (customer-facing)
   - Casual (internal team)
3. Let user choose tone level
4. Preserve original tone when possible

**Better Alternative (Internal):**
```
"Hi team,

Could someone take a look at this bug when you have a chance?

Thanks!"
```

---

## Audit & Compliance Gotchas

### Issue 17: Audit Log Tampering

**Problem:** Audit log is mutable and can be altered

**Why It's a Problem:**
- Compliance violations can be hidden
- Fraud investigation compromised
- Legal evidence invalidated

**Mitigation:**
1. Use append-only log storage (e.g., AWS S3 Object Lock, WORM storage)
2. Sign log entries with HMAC or digital signature
3. Use external audit log service (immutable)
4. Regular log backups to tamper-evident storage
5. Alert on unexpected log modifications

**Tamper-Evident Logging:**
```javascript
async function appendAuditLog(entry) {
  const timestamp = new Date().toISOString();
  const previousHash = await getLastLogEntryHash();

  const entryWithHash = {
    ...entry,
    timestamp,
    previousHash,
    hash: await computeHash({
      ...entry,
      timestamp,
      previousHash
    })
  };

  await appendOnly.write(entryWithHash);

  return entryWithHash.hash;
}
```

---

### Issue 18: Incomplete Audit Trail

**Problem:** Some policy checks not logged

**Example:**
- Action passes validation → Not logged
- Only violations logged → Missing complete picture

**Why It's a Problem:**
- Cannot prove compliance (only violations visible)
- Cannot track policy check volume
- Cannot calculate violation rate

**Mitigation:**
1. Log ALL policy checks (pass and fail)
2. Include success rate in compliance reporting
3. Regular audits to verify logging coverage
4. Alert on missing expected log entries

**Complete Logging:**
```javascript
async function validateAction(action) {
  const result = performValidation(action);

  // Log regardless of outcome
  await auditLog.record({
    action,
    result,
    timestamp: new Date().toISOString(),
    status: result.compliant ? 'PASS' : 'FAIL'
  });

  return result;
}
```

---

## Performance Gotchas

### Issue 19: Validation Latency in Critical Path

**Problem:** Handbook validation adds latency to time-sensitive operations

**Example:**
```
User action → API request → Handbook validation (500ms) → Process → Response
Total latency: 500ms+ added
```

**Why It's a Problem:**
- User experience degraded
- Timeouts on fast operations
- Bottleneck in high-throughput systems

**Mitigation:**
1. Cache policy checks for repeated actions
2. Async validation for non-blocking operations
3. Pre-validate during planning (not execution)
4. Optimize handbook parsing (use indexes)
5. Consider policy check as async audit (validate after action in low-risk cases)

**Async Validation:**
```javascript
async function processPayment(amount) {
  // Synchronous: Only check critical policies (fast)
  const criticalCheck = await validateCriticalPolicies({ amount });
  if (!criticalCheck.compliant) {
    throw new Error('Critical policy violation');
  }

  // Process payment
  const result = await executePayment(amount);

  // Asynchronous: Full policy check (can be slower)
  validateAllPolicies({ amount }).then(fullCheck => {
    auditLog.record({ action: 'payment', amount, result: fullCheck });
    if (!fullCheck.compliant) {
      alertService.notify('Post-payment policy violation detected');
    }
  });

  return result;
}
```

---

### Issue 20: Memory Leak in Long-Running Processes

**Problem:** Policy cache grows indefinitely

**Why It's a Problem:**
- Memory usage increases over time
- Container OOM kill
- Performance degradation

**Mitigation:**
1. Set cache size limits (LRU eviction)
2. Monitor cache size metrics
3. Periodic cache pruning
4. Use external cache (Redis) for shared/persistent cache

**Cache with Size Limit:**
```javascript
const LRU = require('lru-cache');

const handbookCache = new LRU({
  max: 100,  // Max 100 cached policy sets
  maxAge: 1000 * 60 * 5,  // 5 minutes TTL
  updateAgeOnGet: true,
  dispose: (key, value) => {
    console.log(`Evicted cached policy: ${key}`);
  }
});
```

---

## Summary: Top 5 Critical Gotchas

1. **Stale Cache (Issue 14)**: Always version handbook and invalidate cache on updates
2. **Approval Bypass (Issue 13)**: Enforce policies at ALL layers (API gateway, agent, service)
3. **Audit Log Tampering (Issue 17)**: Use append-only, tamper-evident logging
4. **Context Loss (Issue 15)**: Preserve critical info when suggesting alternatives
5. **Timezone Confusion (Issue 6)**: Always use UTC, convert local times explicitly

---
