# Email Drafter - Installation & Testing Guide

Complete guide to install, configure, and test the email_drafter skill.

---

## Prerequisites

- Node.js 16+ or compatible runtime environment
- Access to vault directory with write permissions
- Environment variable management system (.env support)

---

## Installation Steps

### Step 1: Verify Skill Files

Ensure all skill files are present:

```bash
ls -la .claude/skills/communication/email_drafter/
```

**Expected output:**
```
SKILL.md
README.md
EXAMPLES.md
INSTALLATION.md
references/
  patterns.md
  gotchas.md
  impact-checklist.md
assets/
  .env.example
  email-draft.template.md
```

### Step 2: Set Up Environment

```bash
# Copy environment template
cp .claude/skills/communication/email_drafter/assets/.env.example .env

# Edit .env file with your values
nano .env
```

**Minimum required configuration:**
```bash
VAULT_PATH="/absolute/path/to/vault"
EMAIL_DRAFTS_PATH="${VAULT_PATH}/Email_Drafts"
```

**Recommended configuration:**
```bash
VAULT_PATH="/absolute/path/to/vault"
EMAIL_DRAFTS_PATH="${VAULT_PATH}/Email_Drafts"
EMAIL_DEFAULT_TONE="formal"
EMAIL_SIGNATURE_NAME="Your Company Name"
EMAIL_SIGNATURE_TITLE="Support Team"
EMAIL_SIGNATURE_COMPANY="Acme Corp"
EMAIL_SIGNATURE_CONTACT="support@acme.com"
EMAIL_AUTO_SUBJECT="true"
EMAIL_INCLUDE_FOLLOWUP="true"
```

### Step 3: Create Required Directories

```bash
# Create Email_Drafts directory
mkdir -p "$VAULT_PATH/Email_Drafts"

# Verify write permissions
test -w "$VAULT_PATH/Email_Drafts" && echo "✅ Writable" || echo "❌ Not writable"

# Optional: Create archive directory
mkdir -p "$VAULT_PATH/Email_Drafts_Archive"

# Optional: Create templates directory
mkdir -p "$VAULT_PATH/Email_Templates"
```

### Step 4: Verify Environment Variables

```bash
# Source .env file
source .env

# Verify required variables
echo "VAULT_PATH: $VAULT_PATH"
echo "EMAIL_DRAFTS_PATH: $EMAIL_DRAFTS_PATH"

# Check all email configuration
env | grep EMAIL_
```

---

## Testing

### Test 1: Basic Draft Creation

Create a simple customer inquiry response:

```javascript
// test-basic-draft.js
const { draftEmail } = require('./email_drafter');

async function testBasicDraft() {
  console.log('🧪 Testing basic email draft creation...\n');

  try {
    const draft = await draftEmail({
      intent: "customer_inquiry_response",
      recipient: {
        name: "Test Customer",
        email: "test@example.com",
        type: "customer"
      },
      context: {
        original_subject: "Test Question",
        original_message: "This is a test question.",
        customer_plan: "Pro"
      },
      tone: "friendly",
      key_points: [
        "Acknowledge the question",
        "Provide a helpful response",
        "Offer further assistance"
      ],
      metadata: {
        agent: "test_agent",
        session_id: "test_session_001",
        timestamp: new Date().toISOString()
      }
    });

    if (draft.success) {
      console.log('✅ Draft created successfully!');
      console.log(`   Draft ID: ${draft.draft_id}`);
      console.log(`   File Path: ${draft.file_path}`);
      console.log(`   Status: ${draft.status}`);
      return true;
    } else {
      console.error('❌ Draft creation failed:', draft.error);
      return false;
    }
  } catch (error) {
    console.error('❌ Error during test:', error.message);
    return false;
  }
}

testBasicDraft();
```

**Run test:**
```bash
node test-basic-draft.js
```

**Expected output:**
```
🧪 Testing basic email draft creation...

✅ Draft created successfully!
   Draft ID: DRAFT-20250204-XXXXXX-XXXXXX
   File Path: /path/to/vault/Email_Drafts/20250204-XXXXXX-customer-inquiry-test-customer.md
   Status: draft
```

### Test 2: Verify Draft File Contents

```bash
# List created drafts
ls -lh "$VAULT_PATH/Email_Drafts/"

# View the most recent draft
cat "$VAULT_PATH/Email_Drafts/"*.md | head -n 50
```

**Expected draft structure:**
```markdown
---
draft_id: DRAFT-20250204-XXXXXX-XXXXXX
created_at: 2025-02-04T15:30:22Z
status: draft
email_type: customer_inquiry_response
recipient: test@example.com
tone: friendly
---

# Email Draft: Customer Inquiry Response

## Email Body
[Email content here]

## Alternative Subject Lines
1. [Subject 1]
2. [Subject 2]
3. [Subject 3]

## Follow-Up Actions
- [ ] [Action 1]
- [ ] [Action 2]
```

### Test 3: Test Multiple Email Types

```javascript
// test-email-types.js
const { draftEmail } = require('./email_drafter');

const emailTypes = [
  {
    name: "Customer Inquiry",
    intent: "customer_inquiry_response",
    tone: "friendly"
  },
  {
    name: "Meeting Request",
    intent: "meeting_request",
    tone: "formal"
  },
  {
    name: "Status Update",
    intent: "status_update",
    tone: "semi-formal"
  },
  {
    name: "Polite Rejection",
    intent: "polite_rejection",
    tone: "formal"
  }
];

async function testMultipleTypes() {
  console.log('🧪 Testing multiple email types...\n');

  const results = [];

  for (const type of emailTypes) {
    console.log(`Testing: ${type.name}...`);

    try {
      const draft = await draftEmail({
        intent: type.intent,
        recipient: {
          name: "Test Recipient",
          email: "test@example.com",
          type: "customer"
        },
        context: {
          test_type: type.name,
          original_message: "Test message"
        },
        tone: type.tone,
        key_points: ["Point 1", "Point 2", "Point 3"]
      });

      if (draft.success) {
        console.log(`  ✅ ${type.name} - Success\n`);
        results.push({ type: type.name, success: true });
      } else {
        console.log(`  ❌ ${type.name} - Failed: ${draft.error}\n`);
        results.push({ type: type.name, success: false, error: draft.error });
      }
    } catch (error) {
      console.log(`  ❌ ${type.name} - Error: ${error.message}\n`);
      results.push({ type: type.name, success: false, error: error.message });
    }
  }

  console.log('\n📊 Test Summary:');
  const successful = results.filter(r => r.success).length;
  console.log(`   ✅ Successful: ${successful}/${results.length}`);
  console.log(`   ❌ Failed: ${results.length - successful}/${results.length}`);

  return results;
}

testMultipleTypes();
```

**Run test:**
```bash
node test-email-types.js
```

### Test 4: Validation Tests

Test error handling and validation:

```javascript
// test-validation.js
const { draftEmail } = require('./email_drafter');

async function testValidation() {
  console.log('🧪 Testing validation and error handling...\n');

  const tests = [
    {
      name: "Missing recipient email",
      input: {
        intent: "customer_inquiry_response",
        recipient: { name: "Test" },  // Missing email
        tone: "friendly"
      },
      expectError: true
    },
    {
      name: "Invalid email format",
      input: {
        intent: "customer_inquiry_response",
        recipient: {
          name: "Test",
          email: "invalid-email"  // Missing @domain
        },
        tone: "friendly"
      },
      expectError: true
    },
    {
      name: "Empty key points",
      input: {
        intent: "customer_inquiry_response",
        recipient: {
          name: "Test",
          email: "test@example.com"
        },
        tone: "friendly",
        key_points: []  // Empty array
      },
      expectError: true
    },
    {
      name: "Valid minimal input",
      input: {
        intent: "customer_inquiry_response",
        recipient: {
          name: "Test Customer",
          email: "test@example.com",
          type: "customer"
        },
        tone: "friendly",
        key_points: ["Test point"]
      },
      expectError: false
    }
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    console.log(`Testing: ${test.name}...`);

    try {
      const draft = await draftEmail(test.input);

      if (test.expectError) {
        console.log(`  ❌ Expected error but got success\n`);
        failed++;
      } else if (draft.success) {
        console.log(`  ✅ Passed (valid input accepted)\n`);
        passed++;
      } else {
        console.log(`  ❌ Valid input rejected: ${draft.error}\n`);
        failed++;
      }
    } catch (error) {
      if (test.expectError) {
        console.log(`  ✅ Passed (error caught as expected: ${error.message})\n`);
        passed++;
      } else {
        console.log(`  ❌ Unexpected error: ${error.message}\n`);
        failed++;
      }
    }
  }

  console.log('📊 Validation Test Summary:');
  console.log(`   ✅ Passed: ${passed}/${tests.length}`);
  console.log(`   ❌ Failed: ${failed}/${tests.length}`);
}

testValidation();
```

### Test 5: Performance Test

Test batch draft generation:

```bash
# test-performance.sh
#!/bin/bash

echo "🧪 Testing performance with batch generation..."
echo

# Generate 10 drafts in parallel
start=$(date +%s)

for i in {1..10}; do
  node -e "
    const { draftEmail } = require('./email_drafter');
    draftEmail({
      intent: 'customer_inquiry_response',
      recipient: { name: 'Customer $i', email: 'customer$i@example.com', type: 'customer' },
      tone: 'friendly',
      key_points: ['Point 1', 'Point 2']
    });
  " &
done

wait

end=$(date +%s)
elapsed=$((end - start))

echo "✅ Generated 10 drafts in ${elapsed} seconds"
echo "   Average: $((elapsed * 100 / 10))ms per draft"

# Count total drafts created
total=$(find "$VAULT_PATH/Email_Drafts" -name "*.md" | wc -l)
echo "   Total drafts in vault: $total"
```

---

## Post-Installation Verification

### Checklist

- [ ] All skill files present in `.claude/skills/communication/email_drafter/`
- [ ] Environment variables configured in `.env`
- [ ] `Email_Drafts` directory created with write permissions
- [ ] Basic draft creation test passes
- [ ] Draft file has correct YAML frontmatter structure
- [ ] Multiple email types tested successfully
- [ ] Validation tests pass (errors caught appropriately)
- [ ] Performance acceptable (<2 seconds per draft)

### Verification Commands

```bash
# 1. Check skill files
ls -R .claude/skills/communication/email_drafter/

# 2. Verify environment
source .env && env | grep EMAIL_

# 3. Test directory permissions
test -w "$VAULT_PATH/Email_Drafts" && echo "✅" || echo "❌"

# 4. Count drafts
find "$VAULT_PATH/Email_Drafts" -name "*.md" | wc -l

# 5. Check most recent draft
ls -lt "$VAULT_PATH/Email_Drafts" | head -n 2

# 6. Validate draft structure
head -n 20 "$VAULT_PATH/Email_Drafts/"*.md | grep -E "(^---|draft_id:|status:|email_type:)"
```

---

## Troubleshooting Installation

### Issue: "Permission denied" errors

**Solution:**
```bash
# Fix directory permissions
chmod 755 "$VAULT_PATH/Email_Drafts"

# Verify ownership
ls -la "$VAULT_PATH" | grep Email_Drafts
```

### Issue: Environment variables not loading

**Solution:**
```bash
# Verify .env file exists
test -f .env && echo "✅ .env exists" || echo "❌ .env missing"

# Manually source
source .env

# Or use direnv (recommended)
echo "source .env" >> .envrc
direnv allow
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Install required dependencies (if using npm/yarn)
npm install js-yaml crypto

# Or ensure skill is in correct location
pwd
# Should be in project root where .claude/skills exists
```

### Issue: Draft files not being created

**Solution:**
```bash
# Check disk space
df -h "$VAULT_PATH"

# Verify write permissions
touch "$VAULT_PATH/Email_Drafts/test.txt" && rm "$VAULT_PATH/Email_Drafts/test.txt" && echo "✅ Writable"

# Check for errors in logs
tail -f /var/log/agent.log  # Adjust path as needed
```

---

## Integration Testing

### With vault_state_manager

```javascript
const { readVaultFile } = require('../vault/vault_state_manager');

// Create draft
const draft = await draftEmail({ ... });

// Read back via vault manager
const content = await readVaultFile(draft.file_path);
console.log('✅ Vault integration working');
```

### With company_handbook_enforcer

```javascript
const { checkPolicyCompliance } = require('../compliance/company_handbook_enforcer');

// Create draft
const draft = await draftEmail({ ... });

// Check compliance
const compliance = await checkPolicyCompliance({
  type: "email_communication",
  content: draft.body
});

console.log('✅ Compliance integration working');
```

---

## Production Deployment Checklist

Before deploying to production:

- [ ] All tests pass
- [ ] Environment configured with production values
- [ ] Backup/archive strategy configured
- [ ] Monitoring and alerting set up
- [ ] Documentation reviewed by team
- [ ] Security review completed
- [ ] Compliance requirements verified
- [ ] Rollback plan documented
- [ ] On-call contacts identified
- [ ] Stakeholders notified

---

## Next Steps

After successful installation:

1. **Review Documentation**
   - Read [SKILL.md](./SKILL.md) for comprehensive overview
   - Study [EXAMPLES.md](./EXAMPLES.md) for real-world use cases
   - Check [references/patterns.md](./references/patterns.md) for best practices

2. **Customize Configuration**
   - Update signature information
   - Configure tone defaults
   - Set up compliance rules
   - Enable audit logging

3. **Train Users**
   - Share README with team
   - Walk through examples
   - Demonstrate best practices
   - Document team-specific workflows

4. **Monitor Usage**
   - Track draft creation metrics
   - Review email quality
   - Collect user feedback
   - Iterate on improvements

---

## Support

- **Documentation:** `.claude/skills/communication/email_drafter/`
- **Common Issues:** [references/gotchas.md](./references/gotchas.md)
- **Usage Patterns:** [references/patterns.md](./references/patterns.md)
- **Deployment Guide:** [references/impact-checklist.md](./references/impact-checklist.md)

For additional help, file issues in the project issue tracker.

---

**Installation complete!** 🎉

You're ready to start drafting professional emails with the email_drafter skill.
