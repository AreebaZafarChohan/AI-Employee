# Company Handbook Enforcer - Patterns

## Policy Validation Patterns

### Pattern 1: Hard Rule Enforcement

**Use Case:** Binary policy checks (allowed/not allowed)

**Implementation:**
```javascript
function validateHardRule(action, policy) {
  const isViolation = policy.prohibitedValues.includes(action.value);

  return {
    compliant: !isViolation,
    policy: policy.key,
    severity: isViolation ? 'CRITICAL' : 'PASS',
    reasoning: isViolation
      ? `Action violates ${policy.key}: ${action.value} is prohibited`
      : `Action complies with ${policy.key}`
  };
}

// Example
const communicationPolicy = {
  key: 'communication.prohibited_phrases',
  prohibitedValues: ['URGENT', 'ASAP', 'IMMEDIATELY']
};

const emailAction = {
  type: 'email',
  value: 'URGENT: Fix this ASAP'
};

validateHardRule(emailAction, communicationPolicy);
// { compliant: false, policy: 'communication.prohibited_phrases', ... }
```

**When to Use:**
- Prohibited content detection (words, patterns, data types)
- Blacklist/whitelist enforcement
- Binary yes/no policy decisions

**When NOT to Use:**
- Threshold-based policies (use Pattern 2)
- Context-dependent rules (use Pattern 4)

---

### Pattern 2: Threshold Enforcement

**Use Case:** Numeric limit checks (amounts, counts, durations)

**Implementation:**
```javascript
function validateThreshold(action, policy) {
  const exceedsLimit = action.amount > policy.limit;
  const requiresApproval = exceedsLimit && policy.approvalRequired;

  return {
    compliant: !exceedsLimit || (exceedsLimit && action.approvalProvided),
    policy: policy.key,
    severity: exceedsLimit ? 'HIGH' : 'PASS',
    reasoning: exceedsLimit
      ? `Amount ${action.amount} exceeds limit ${policy.limit} by ${action.amount - policy.limit}`
      : `Amount ${action.amount} within limit ${policy.limit}`,
    requiresApproval,
    escalation: requiresApproval ? policy.approver : null
  };
}

// Example
const financialPolicy = {
  key: 'financial.payment_limit_without_approval',
  limit: 1000,
  approvalRequired: true,
  approver: 'finance-manager'
};

const paymentAction = {
  type: 'payment',
  amount: 1500,
  approvalProvided: false
};

validateThreshold(paymentAction, financialPolicy);
// { compliant: false, requiresApproval: true, escalation: 'finance-manager', ... }
```

**When to Use:**
- Financial limits (payment amounts, budgets)
- Rate limits (API calls, requests per minute)
- Resource constraints (storage, compute)
- Time-based limits (hours, response times)

**When NOT to Use:**
- Boolean checks (use Pattern 1)
- Complex conditional logic (use Pattern 4)

---

### Pattern 3: Time Window Enforcement

**Use Case:** Date/time-based policy checks (deployment windows, freeze periods)

**Implementation:**
```javascript
function validateTimeWindow(action, policy) {
  const actionTime = new Date(action.scheduledTime);

  // Check allowed windows
  const inAllowedWindow = policy.allowedWindows.some(window => {
    const start = parseTimeWindow(window.start);
    const end = parseTimeWindow(window.end);
    return actionTime >= start && actionTime <= end;
  });

  // Check freeze periods
  const inFreezeWindow = policy.freezeWindows.some(freeze => {
    const start = new Date(freeze.start);
    const end = new Date(freeze.end);
    return actionTime >= start && actionTime <= end;
  });

  const compliant = inAllowedWindow && !inFreezeWindow;

  return {
    compliant,
    policy: policy.key,
    severity: !compliant ? 'HIGH' : 'PASS',
    reasoning: !compliant
      ? inFreezeWindow
        ? `Deployment scheduled during freeze period: ${actionTime.toISOString()}`
        : `Deployment outside allowed window: ${actionTime.toISOString()}`
      : `Deployment time complies with operational windows`,
    nextAllowedTime: compliant ? null : getNextAllowedTime(policy)
  };
}

// Example
const operationalPolicy = {
  key: 'operational.deployment_windows',
  allowedWindows: [
    { start: 'Tue 10:00 UTC', end: 'Thu 16:00 UTC' }
  ],
  freezeWindows: [
    { start: '2024-12-15', end: '2025-01-05' }
  ]
};

const deploymentAction = {
  type: 'deployment',
  scheduledTime: '2024-12-20T14:00:00Z'
};

validateTimeWindow(deploymentAction, operationalPolicy);
// { compliant: false, reasoning: 'Deployment during freeze period...', ... }
```

**When to Use:**
- Deployment and maintenance windows
- Change freeze periods (holidays, critical events)
- Business hours enforcement
- SLA response time validation

**When NOT to Use:**
- Non-temporal rules (use Pattern 1 or 2)
- Simple date comparisons (use built-in date logic)

---

### Pattern 4: Context-Aware Validation

**Use Case:** Policies dependent on multiple factors or environmental context

**Implementation:**
```javascript
function validateWithContext(action, policy, context) {
  const rules = policy.contextRules[context.environment];

  if (!rules) {
    return {
      compliant: false,
      policy: policy.key,
      severity: 'ERROR',
      reasoning: `No policy defined for environment: ${context.environment}`
    };
  }

  // Apply environment-specific rules
  const violations = [];

  if (action.type === 'data_access' && rules.requiresAuthentication) {
    if (!action.authentication) {
      violations.push('Authentication required but not provided');
    }
  }

  if (action.containsPII && rules.piiRestrictions) {
    if (!action.encrypted) {
      violations.push('PII must be encrypted in this environment');
    }
    if (rules.piiRestrictions.prohibitedRegions.includes(action.targetRegion)) {
      violations.push(`PII cannot be sent to region: ${action.targetRegion}`);
    }
  }

  return {
    compliant: violations.length === 0,
    policy: policy.key,
    severity: violations.length > 0 ? 'HIGH' : 'PASS',
    reasoning: violations.length > 0
      ? `Context violations detected: ${violations.join('; ')}`
      : `Action complies with ${context.environment} environment policies`,
    violations
  };
}

// Example
const privacyPolicy = {
  key: 'privacy.pii_handling',
  contextRules: {
    production: {
      requiresAuthentication: true,
      piiRestrictions: {
        prohibitedRegions: ['non-gdpr'],
        encryptionRequired: true
      }
    },
    development: {
      requiresAuthentication: false,
      piiRestrictions: null
    }
  }
};

const dataAccessAction = {
  type: 'data_access',
  containsPII: true,
  encrypted: false,
  authentication: null,
  targetRegion: 'non-gdpr'
};

const context = { environment: 'production' };

validateWithContext(dataAccessAction, privacyPolicy, context);
// { compliant: false, violations: [...], ... }
```

**When to Use:**
- Environment-specific rules (dev vs prod)
- Multi-factor policy decisions
- Role-based access control
- Geographic or regional policies

**When NOT to Use:**
- Simple binary checks (use Pattern 1)
- Single-factor rules (use Pattern 2 or 3)

---

## Alternative Generation Patterns

### Pattern 5: Template-Based Alternatives

**Use Case:** Suggest pre-defined compliant templates

**Implementation:**
```javascript
function generateTemplateAlternative(action, policy, templates) {
  const violationType = identifyViolationType(action, policy);
  const template = templates[violationType];

  if (!template) {
    return {
      alternativeAvailable: false,
      reasoning: 'No template available for this violation type'
    };
  }

  // Fill template with action context
  const compliantVersion = fillTemplate(template, {
    recipient: action.recipient,
    subject: action.subject,
    deadline: action.deadline || 'end of business day',
    contactInfo: policy.supportContact
  });

  return {
    alternativeAvailable: true,
    original: action.content,
    compliant: compliantVersion,
    changes: getDiff(action.content, compliantVersion),
    reasoning: `Applied ${violationType} compliant template`
  };
}

// Example templates
const communicationTemplates = {
  'prohibited_phrases': `Dear {{recipient}},

{{subject}} requires your attention by {{deadline}}.

Here's what you need to do:
{{action_steps}}

If you have questions, please contact us at {{contactInfo}}.

Best regards,
{{sender}}`,

  'missing_context': `Dear {{recipient}},

Background:
{{context}}

What this means for you:
{{impact}}

Next steps:
{{action_steps}}

Expected completion: {{deadline}}

Please let us know if you need assistance.

Best regards,
{{sender}}`
};

const emailAction = {
  type: 'email',
  content: 'URGENT: Fix this ASAP!',
  recipient: 'customer@example.com',
  subject: 'Service Issue'
};

const policy = { key: 'communication.prohibited_phrases' };

generateTemplateAlternative(emailAction, policy, communicationTemplates);
// { alternativeAvailable: true, compliant: '...formatted email...', ... }
```

**When to Use:**
- Communication policy violations
- Standard document templates
- Repeated violation patterns
- High-volume operations

**When NOT to Use:**
- Unique, one-off situations
- Highly context-specific content
- Creative or marketing content

---

### Pattern 6: Incremental Fix Suggestions

**Use Case:** Step-by-step remediation for complex violations

**Implementation:**
```javascript
function generateIncrementalFix(action, violations, policy) {
  const fixes = violations.map((violation, index) => {
    const fix = {
      step: index + 1,
      issue: violation.description,
      currentValue: violation.currentValue,
      requiredValue: violation.requiredValue,
      action: null,
      validation: null
    };

    // Generate specific fix action
    switch (violation.type) {
      case 'threshold_exceeded':
        fix.action = `Reduce ${violation.field} from ${violation.currentValue} to ${violation.requiredValue} or obtain approval for the excess`;
        fix.validation = `Verify ${violation.field} <= ${violation.requiredValue} OR approval.status === 'approved'`;
        break;

      case 'missing_required':
        fix.action = `Add required field: ${violation.field}`;
        fix.validation = `Verify ${violation.field} is present and non-empty`;
        break;

      case 'prohibited_value':
        fix.action = `Replace "${violation.currentValue}" with an approved alternative`;
        fix.validation = `Verify ${violation.field} not in [${policy.prohibitedValues.join(', ')}]`;
        break;

      default:
        fix.action = `Review and correct ${violation.field}`;
        fix.validation = `Manual review required`;
    }

    return fix;
  });

  return {
    fixesAvailable: true,
    totalSteps: fixes.length,
    fixes,
    estimatedComplexity: calculateComplexity(fixes),
    reasoning: 'Follow these steps in order to achieve compliance'
  };
}

// Example
const paymentAction = {
  amount: 5000,
  approval: null,
  description: null
};

const violations = [
  {
    type: 'threshold_exceeded',
    field: 'amount',
    currentValue: 5000,
    requiredValue: 1000,
    description: 'Payment exceeds authorization limit'
  },
  {
    type: 'missing_required',
    field: 'approval',
    description: 'Approval required for amounts over $1000'
  },
  {
    type: 'missing_required',
    field: 'description',
    description: 'Payment description required for audit trail'
  }
];

generateIncrementalFix(paymentAction, violations, policy);
// {
//   fixesAvailable: true,
//   totalSteps: 3,
//   fixes: [
//     { step: 1, issue: 'Payment exceeds...', action: 'Reduce...', ... },
//     { step: 2, issue: 'Approval required...', action: 'Add...', ... },
//     { step: 3, issue: 'Payment description...', action: 'Add...', ... }
//   ],
//   ...
// }
```

**When to Use:**
- Multiple violations in single action
- Complex remediation requirements
- Educational/training scenarios
- Actions with dependencies between fixes

**When NOT to Use:**
- Single violation (provide direct fix)
- Template-based fixes available (use Pattern 5)
- Simple substitutions

---

## Escalation Patterns

### Pattern 7: Approval Workflow

**Use Case:** Route violations requiring human approval

**Implementation:**
```javascript
async function createApprovalWorkflow(action, violation, policy) {
  const approvalRequest = {
    id: generateUUID(),
    timestamp: new Date().toISOString(),
    action: {
      type: action.type,
      description: action.description,
      details: sanitizeForApproval(action)
    },
    violation: {
      policy: violation.policy,
      severity: violation.severity,
      reasoning: violation.reasoning
    },
    approval: {
      status: 'pending',
      requiredApprover: policy.approver,
      approvedBy: null,
      approvedAt: null,
      justification: null
    },
    timeout: {
      expiresAt: calculateTimeout(policy.approvalTimeout),
      onTimeout: policy.timeoutAction || 'reject'
    }
  };

  // Send approval request
  await sendApprovalNotification(approvalRequest);

  // Wait for approval (with timeout)
  const result = await waitForApproval(approvalRequest.id, {
    timeout: policy.approvalTimeout,
    pollInterval: 10000  // Check every 10 seconds
  });

  // Record outcome
  await auditLog.record({
    event: 'approval_workflow',
    request_id: approvalRequest.id,
    outcome: result.status,
    approver: result.approvedBy,
    timestamp: result.approvedAt
  });

  return result;
}

// Example
const paymentAction = {
  type: 'payment',
  description: 'Customer refund',
  amount: 5000,
  customer_id: 'CUST-001'
};

const violation = {
  policy: 'financial.payment_limit_without_approval',
  severity: 'HIGH',
  reasoning: 'Amount exceeds $1000 limit'
};

const policy = {
  approver: 'finance-manager',
  approvalTimeout: 14400000,  // 4 hours in ms
  timeoutAction: 'reject'
};

const approvalResult = await createApprovalWorkflow(paymentAction, violation, policy);
// {
//   status: 'approved' | 'rejected' | 'timeout',
//   approvedBy: 'manager@company.com',
//   approvedAt: '2024-01-15T14:30:00Z',
//   justification: 'Valid customer refund request'
// }
```

**When to Use:**
- Financial transactions above limits
- Security-sensitive operations
- Policy exceptions and overrides
- High-impact changes

**When NOT to Use:**
- Hard violations (should always block, no approval)
- Low-severity suggestions
- Time-critical operations (approval latency too high)

---

### Pattern 8: Audit Trail Generation

**Use Case:** Record all policy checks for compliance reporting

**Implementation:**
```javascript
async function recordPolicyCheck(action, validationResult, context) {
  const auditEntry = {
    id: generateUUID(),
    timestamp: new Date().toISOString(),

    // Action details
    action: {
      type: action.type,
      description: action.description,
      initiator: context.agent || context.user,
      environment: context.environment
    },

    // Validation details
    validation: {
      policy: validationResult.policy,
      compliant: validationResult.compliant,
      severity: validationResult.severity,
      reasoning: validationResult.reasoning,
      violations: validationResult.violations || []
    },

    // Outcome
    outcome: {
      action_taken: validationResult.compliant ? 'approved' : 'blocked',
      alternative_suggested: validationResult.alternativeAvailable || false,
      approval_requested: validationResult.requiresApproval || false,
      approval_id: validationResult.approvalId || null
    },

    // Metadata
    metadata: {
      handbook_version: await getHandbookVersion(),
      enforcement_level: context.enforcementLevel,
      session_id: context.sessionId
    }
  };

  // Store in audit log
  await auditLog.append(auditEntry);

  // Trigger alerts for critical violations
  if (validationResult.severity === 'CRITICAL') {
    await alertService.notify({
      level: 'critical',
      message: `Policy violation: ${validationResult.policy}`,
      details: auditEntry
    });
  }

  return auditEntry.id;
}

// Example
const action = { type: 'payment', description: 'Process refund', amount: 1500 };
const validationResult = {
  compliant: false,
  policy: 'financial.payment_limit',
  severity: 'HIGH',
  reasoning: 'Exceeds $1000 limit',
  requiresApproval: true
};
const context = {
  agent: 'ai-agent-001',
  environment: 'production',
  enforcementLevel: 'STRICT'
};

const auditId = await recordPolicyCheck(action, validationResult, context);
// 'audit-550e8400-e29b-41d4-a716-446655440000'
```

**When to Use:**
- All policy checks (both compliant and violations)
- Approval workflows
- Policy overrides
- Compliance reporting

**When NOT to Use:**
- Never skip audit logging in production
- Can be disabled in dev/test with explicit configuration

---

## Performance Optimization Patterns

### Pattern 9: Policy Caching

**Use Case:** Avoid re-parsing handbook on every validation

**Implementation:**
```javascript
class HandbookCache {
  constructor(ttl = 300000) {  // 5 minutes default
    this.cache = new Map();
    this.ttl = ttl;
  }

  async get(handbookPath) {
    const cached = this.cache.get(handbookPath);

    if (cached && (Date.now() - cached.timestamp < this.ttl)) {
      return cached.policies;
    }

    // Cache miss or expired - reload
    const policies = await this.loadAndParse(handbookPath);

    this.cache.set(handbookPath, {
      policies,
      timestamp: Date.now(),
      version: await getFileHash(handbookPath)
    });

    return policies;
  }

  async loadAndParse(handbookPath) {
    const content = await fs.readFile(handbookPath, 'utf-8');
    return parseHandbook(content);
  }

  invalidate(handbookPath) {
    this.cache.delete(handbookPath);
  }

  clear() {
    this.cache.clear();
  }
}

// Usage
const handbookCache = new HandbookCache(300000);  // 5 min TTL

async function validateAction(action) {
  const policies = await handbookCache.get(process.env.HANDBOOK_PATH);
  return validateAgainstPolicies(action, policies);
}
```

**When to Use:**
- High-frequency validations
- Handbook file access is slow (remote, large file)
- Multiple validations per request

**Trade-offs:**
- Faster validation (cached)
- Policy updates may be delayed by TTL
- Memory overhead for cached policies

---

### Pattern 10: Parallel Validation

**Use Case:** Validate multiple policy categories simultaneously

**Implementation:**
```javascript
async function validateAllPolicies(action, policies) {
  const validations = [
    validateCommunicationPolicies(action, policies.communication),
    validateFinancialPolicies(action, policies.financial),
    validatePrivacyPolicies(action, policies.privacy),
    validateOperationalPolicies(action, policies.operational)
  ];

  const results = await Promise.all(validations);

  // Aggregate results
  const violations = results
    .filter(r => !r.compliant)
    .map(r => ({
      policy: r.policy,
      severity: r.severity,
      reasoning: r.reasoning
    }));

  const compliant = violations.length === 0;
  const highestSeverity = compliant ? 'PASS' : getHighestSeverity(violations);

  return {
    compliant,
    severity: highestSeverity,
    violations,
    results,
    reasoning: compliant
      ? 'Action complies with all policies'
      : `Action violates ${violations.length} policy/policies`
  };
}

// Example
const action = { type: 'customer_notification', ... };
const policies = await handbookCache.get(HANDBOOK_PATH);

const validationResult = await validateAllPolicies(action, policies);
// {
//   compliant: false,
//   severity: 'HIGH',
//   violations: [
//     { policy: 'communication.tone', ... },
//     { policy: 'operational.notification_approval', ... }
//   ],
//   ...
// }
```

**When to Use:**
- Actions span multiple policy categories
- Independent policy checks (no dependencies)
- Performance-critical validation paths

**When NOT to Use:**
- Sequential dependencies (one policy check informs another)
- Very fast individual checks (overhead > benefit)

---
