# Needs Action Triage - Complete Examples

This document provides end-to-end workflow examples showing how to use the `needs_action_triage` skill in real scenarios.

---

## Example 1: Morning Inbox Review

**Scenario:** Agent starts day by reviewing all pending items in Needs_Action folder.

### Input Files (Needs_Action/)

**File 1: `email-20250203-server-alert.md`**
```markdown
From: ops-team@company.com
Subject: URGENT: Production server down
Date: 2025-02-03T08:30:00Z

Production API server (api-prod-01) is unresponsive.
All endpoints returning 503 errors.
Customer impact: high.
Need resolution within 2 hours.
```

**File 2: `whatsapp-20250203-lunch.md`**
```markdown
2/3/25, 12:15 PM - John: Want to grab lunch today?
2/3/25, 12:16 PM - John: Thai place around 1pm?
```

**File 3: `finance-20250203-invoice.md`**
```markdown
From: billing@acme.com
Subject: Invoice #1234 payment overdue
Date: 2025-01-15T10:00:00Z

Invoice: #1234
Amount: $5,432.00
Due Date: January 31, 2025 (OVERDUE)
Payment terms: Net 30
Late fee: $50/day

Please remit payment immediately to avoid service interruption.
```

**File 4: `email-20250203-newsletter.md`**
```markdown
From: marketing@newsletter.com
Subject: Weekly Tech News Roundup
Date: 2025-02-03T06:00:00Z

This week in tech:
- AI advances
- Cloud updates
- Security patches

[Read more...]
```

### Triage Execution

```javascript
const { triageNeedsAction } = require('./needs_action_triage');

async function morningReview() {
  console.log('🌅 Starting morning inbox review...\n');

  // Run triage
  const result = await triageNeedsAction({
    minPriorityScore: 1,
    autoClassify: true,
    extractMetadata: true
  });

  console.log('📊 Inbox Summary:');
  console.log(`   Total items: ${result.summary.total}`);
  console.log(`   High priority (8-10): ${result.summary.high_priority}`);
  console.log(`   Medium priority (4-7): ${result.summary.medium_priority}`);
  console.log(`   Low priority (1-3): ${result.summary.low_priority}\n`);

  console.log('🔥 Top Priority Items:\n');

  result.items.slice(0, 3).forEach((item, index) => {
    console.log(`${index + 1}. [Priority ${item.priority_score}] ${item.metadata.subject || item.file_name}`);
    console.log(`   Category: ${item.category}`);
    console.log(`   Deadline: ${item.metadata.deadline ? new Date(item.metadata.deadline).toLocaleString() : 'None'}`);
    console.log(`   Action: ${item.suggested_action}`);
    console.log(`   Summary: ${item.summary}\n`);
  });

  return result;
}

morningReview();
```

### Output

```
🌅 Starting morning inbox review...

📊 Inbox Summary:
   Total items: 4
   High priority (8-10): 2
   Medium priority (4-7): 0
   Low priority (1-3): 2

🔥 Top Priority Items:

1. [Priority 9] Invoice #1234 payment overdue
   Category: finance
   Deadline: 1/31/2025, 11:59:59 PM (OVERDUE)
   Action: approve
   Summary: Overdue payment of $5,432.00 from Acme Corp, requires immediate approval to avoid $50/day late fees

2. [Priority 8] URGENT: Production server down
   Category: email
   Deadline: 2/3/2025, 10:30:00 AM (2 hours)
   Action: research
   Summary: Production API server unresponsive, all endpoints returning 503, high customer impact

3. [Priority 2] Want to grab lunch today?
   Category: whatsapp
   Deadline: None
   Action: delegate
   Summary: John requesting lunch meeting at Thai place around 1pm
```

**Decision:** Agent claims finance invoice first (priority 9, overdue), then server alert (priority 8, deadline 2h).

---

## Example 2: Finance-Only Triage

**Scenario:** Finance watcher deposited multiple invoices/receipts. Filter and process only finance items.

### Input Files (Needs_Action/)

**File 1: `finance-20250203-office-supplies.md`**
```markdown
Receipt: Office Depot
Amount: $127.50
Date: 2025-02-02
Items: Paper, pens, staples
```

**File 2: `finance-20250203-cloud-bill.md`**
```markdown
Invoice: AWS Monthly Bill
Amount: $3,245.67
Due: 2025-02-15
Account: prod-12345
Services: EC2, S3, RDS
```

**File 3: `email-20250203-meeting-notes.md`**
```markdown
From: team@company.com
Subject: Q1 planning meeting notes
...
```

### Triage Execution

```javascript
async function triageFinance() {
  console.log('💰 Finance-only triage...\n');

  // Run triage
  const result = await triageNeedsAction({ autoClassify: true });

  // Filter finance items
  const financeItems = result.items.filter(item => item.category === 'finance');

  console.log(`Found ${financeItems.length} finance items:\n`);

  // Group by subcategory
  const byType = financeItems.reduce((acc, item) => {
    const type = item.subcategory || 'other';
    acc[type] = acc[type] || [];
    acc[type].push(item);
    return acc;
  }, {});

  Object.entries(byType).forEach(([type, items]) => {
    console.log(`\n${type.toUpperCase()}:`);
    items.forEach(item => {
      console.log(`  - ${item.metadata.subject || item.file_name}`);
      console.log(`    Amount: $${item.metadata.financial_amount?.toLocaleString()}`);
      console.log(`    Priority: ${item.priority_score}`);
      console.log(`    Deadline: ${item.metadata.deadline || 'None'}`);
      console.log(`    Action: ${item.suggested_action}`);
    });
  });

  return financeItems;
}

triageFinance();
```

### Output

```
💰 Finance-only triage...

Found 2 finance items:

RECEIPT:
  - Office Depot
    Amount: $127.50
    Priority: 4
    Deadline: None
    Action: archive

INVOICE:
  - AWS Monthly Bill
    Amount: $3,245.67
    Priority: 6
    Deadline: 2025-02-15T23:59:59Z
    Action: approve
```

**Decision:** Approve AWS bill (priority 6, due in 12 days), archive receipt (priority 4, routine expense).

---

## Example 3: Priority-Based Task Claiming

**Scenario:** Agent needs to claim next task but should prioritize based on triage scores.

### Triage + Claim Workflow

```javascript
const { triageNeedsAction } = require('./needs_action_triage');
const { claimTask } = require('./task_lifecycle_manager');

async function claimNextHighPriorityTask(agentName) {
  console.log(`🤖 ${agentName} looking for work...\n`);

  // Step 1: Triage inbox (only medium+ priority)
  const triage = await triageNeedsAction({
    minPriorityScore: 5,  // Skip low priority
    autoClassify: true
  });

  if (triage.items.length === 0) {
    console.log('📭 No medium+ priority items available');
    return null;
  }

  console.log(`Found ${triage.items.length} medium+ priority items\n`);

  // Step 2: Try to claim highest-priority item
  for (const item of triage.items) {
    console.log(`Attempting to claim: ${item.metadata.subject || item.file_name} (priority ${item.priority_score})`);

    const claimResult = await claimTask(item.file_name, agentName);

    if (claimResult.success) {
      console.log(`✅ Successfully claimed!\n`);
      console.log(`Task Details:`);
      console.log(`  ID: ${claimResult.taskId}`);
      console.log(`  Priority: ${item.priority_score}`);
      console.log(`  Category: ${item.category}`);
      console.log(`  Deadline: ${item.metadata.deadline || 'None'}`);
      console.log(`  Suggested action: ${item.suggested_action}`);
      console.log(`  Estimated effort: ${item.estimated_effort}`);
      console.log(`  Requires approval: ${item.requires_human_approval}`);
      console.log(`\nSummary: ${item.summary}`);

      return {
        taskId: claimResult.taskId,
        triageData: item
      };
    } else {
      console.log(`❌ Already claimed by another agent\n`);
      // Try next item
    }
  }

  console.log('⚠️  All high-priority tasks already claimed');
  return null;
}

// Agent claims work
claimNextHighPriorityTask('lex');
```

### Output (Success Case)

```
🤖 lex looking for work...

Found 3 medium+ priority items

Attempting to claim: Invoice #1234 payment overdue (priority 9)
✅ Successfully claimed!

Task Details:
  ID: task-1738587600-abc123
  Priority: 9
  Category: finance
  Deadline: 2025-01-31T23:59:59Z (OVERDUE)
  Suggested action: approve
  Estimated effort: low
  Requires approval: true

Summary: Overdue payment of $5,432.00 from Acme Corp, requires immediate approval to avoid $50/day late fees
```

### Output (Conflict Case)

```
🤖 lex looking for work...

Found 3 medium+ priority items

Attempting to claim: Invoice #1234 payment overdue (priority 9)
❌ Already claimed by another agent

Attempting to claim: URGENT: Production server down (priority 8)
✅ Successfully claimed!

Task Details:
  ID: task-1738587601-def456
  Priority: 8
  Category: email
  Deadline: 2025-02-03T10:30:00Z
  Suggested action: research
  Estimated effort: medium
  Requires approval: false

Summary: Production API server unresponsive, all endpoints returning 503, high customer impact
```

---

## Example 4: Daily Dashboard Generation

**Scenario:** Generate human-readable summary for dashboard.

### Dashboard Generator

```javascript
async function generateDailyDashboard() {
  const today = new Date().toISOString().split('T')[0];
  console.log(`📊 Generating dashboard for ${today}...\n`);

  // Run triage
  const triage = await triageNeedsAction({ autoClassify: true });

  // Build markdown summary
  let markdown = `# Daily Inbox Summary\n\n`;
  markdown += `**Date:** ${new Date().toLocaleDateString()}\n`;
  markdown += `**Generated:** ${new Date().toLocaleTimeString()}\n`;
  markdown += `**Total Items:** ${triage.summary.total}\n\n`;

  markdown += `## Priority Breakdown\n\n`;
  markdown += `- 🔴 **High (8-10):** ${triage.summary.high_priority} items\n`;
  markdown += `- 🟡 **Medium (4-7):** ${triage.summary.medium_priority} items\n`;
  markdown += `- 🟢 **Low (1-3):** ${triage.summary.low_priority} items\n\n`;

  markdown += `## Category Breakdown\n\n`;
  const icons = { email: '📧', whatsapp: '💬', finance: '💰', file_drop: '📁', general: '📝' };
  Object.entries(triage.summary.by_category).forEach(([cat, count]) => {
    markdown += `- ${icons[cat] || '📄'} **${cat}:** ${count}\n`;
  });

  markdown += `\n## Immediate Action Required (Priority 8-10)\n\n`;
  const immediate = triage.items.filter(i => i.priority_score >= 8);
  if (immediate.length > 0) {
    markdown += `| Priority | Category | Subject | Deadline | Action |\n`;
    markdown += `|----------|----------|---------|----------|--------|\n`;
    immediate.forEach(item => {
      const deadline = item.metadata.deadline
        ? new Date(item.metadata.deadline).toLocaleDateString()
        : 'None';
      markdown += `| ${item.priority_score} | ${item.category} | ${item.metadata.subject || item.file_name} | ${deadline} | ${item.suggested_action} |\n`;
    });
  } else {
    markdown += `*No immediate items*\n`;
  }

  markdown += `\n## Today's Tasks (Priority 6-7)\n\n`;
  const today_tasks = triage.items.filter(i => i.priority_score >= 6 && i.priority_score < 8);
  if (today_tasks.length > 0) {
    today_tasks.forEach(item => {
      markdown += `- **${item.metadata.subject || item.file_name}** (${item.suggested_action})\n`;
      markdown += `  - ${item.summary}\n`;
    });
  } else {
    markdown += `*No tasks scheduled for today*\n`;
  }

  markdown += `\n## Low Priority (Deferred)\n\n`;
  const low = triage.items.filter(i => i.priority_score < 6);
  markdown += `*${low.length} low-priority items can be processed later*\n`;

  // Write to Updates/
  const fs = require('fs').promises;
  const outputPath = `${process.env.VAULT_PATH}/Updates/inbox-summary-${today}.md`;
  await fs.writeFile(outputPath, markdown);

  console.log(`✅ Dashboard saved to: Updates/inbox-summary-${today}.md`);
  console.log(`\nPreview:\n`);
  console.log(markdown);

  return markdown;
}

generateDailyDashboard();
```

### Output File (Updates/inbox-summary-2025-02-03.md)

```markdown
# Daily Inbox Summary

**Date:** 2/3/2025
**Generated:** 9:00:00 AM
**Total Items:** 8

## Priority Breakdown

- 🔴 **High (8-10):** 2 items
- 🟡 **Medium (4-7):** 4 items
- 🟢 **Low (1-3):** 2 items

## Category Breakdown

- 📧 **email:** 4
- 💬 **whatsapp:** 2
- 💰 **finance:** 1
- 📁 **file_drop:** 1

## Immediate Action Required (Priority 8-10)

| Priority | Category | Subject | Deadline | Action |
|----------|----------|---------|----------|--------|
| 9 | finance | Invoice #1234 payment overdue | 1/31/2025 | approve |
| 8 | email | URGENT: Production server down | 2/3/2025 | research |

## Today's Tasks (Priority 6-7)

- **Meeting reschedule** (delegate)
  - Client requests to reschedule meeting from today to tomorrow, coordinate calendar

- **Weekly report due** (research)
  - Manager requesting Q1 progress report, due Friday

## Low Priority (Deferred)

*2 low-priority items can be processed later*
```

---

## Example 5: Error Handling & Fallback

**Scenario:** LLM API unavailable, triage falls back to rule-based classification.

### Robust Triage with Fallback

```javascript
async function robustTriageWithFallback() {
  console.log('🔄 Running robust triage with fallback...\n');

  try {
    // Try LLM classification first
    console.log('Attempting LLM classification...');
    const result = await triageNeedsAction({
      autoClassify: true,
      extractMetadata: true
    });

    console.log(`✅ LLM classification successful`);
    console.log(`   Avg confidence: ${(result.items.reduce((sum, i) => sum + i.confidence, 0) / result.items.length * 100).toFixed(1)}%\n`);

    return result;

  } catch (err) {
    if (err.code === 'LLM_API_ERROR') {
      console.warn(`⚠️  LLM API unavailable: ${err.message}`);
      console.log('Falling back to rule-based classification...\n');

      // Retry with rule-based only
      const result = await triageNeedsAction({
        autoClassify: false,  // Disable LLM
        extractMetadata: true
      });

      console.log(`✅ Rule-based classification successful`);
      console.log(`   Avg confidence: ${(result.items.reduce((sum, i) => sum + i.confidence, 0) / result.items.length * 100).toFixed(1)}%\n`);

      // Flag low-confidence items
      const lowConfidence = result.items.filter(i => i.confidence < 0.70);
      if (lowConfidence.length > 0) {
        console.log(`⚠️  ${lowConfidence.length} items have low confidence (<70%), may need manual review:`);
        lowConfidence.forEach(item => {
          console.log(`   - ${item.file_name}: ${item.category} (${(item.confidence * 100).toFixed(0)}%)`);
        });
        console.log();
      }

      return result;
    } else {
      // Unexpected error
      console.error(`❌ Triage failed: ${err.message}`);
      throw err;
    }
  }
}

robustTriageWithFallback();
```

### Output (LLM Success)

```
🔄 Running robust triage with fallback...

Attempting LLM classification...
✅ LLM classification successful
   Avg confidence: 92.3%
```

### Output (LLM Failure → Rule-Based Fallback)

```
🔄 Running robust triage with fallback...

Attempting LLM classification...
⚠️  LLM API unavailable: 503 Service Unavailable
Falling back to rule-based classification...

✅ Rule-based classification successful
   Avg confidence: 81.5%

⚠️  2 items have low confidence (<70%), may need manual review:
   - general-20250203-feature-request.md: general (50%)
   - file-drop-20250203-unknown.md: file_drop (65%)
```

---

## Example 6: Periodic Monitoring

**Scenario:** Run triage every 5 minutes, notify only when new high-priority items arrive.

### Periodic Triage Monitor

```javascript
let processedFiles = new Set();

async function periodicMonitor(intervalMinutes = 5) {
  console.log(`🔔 Starting periodic triage monitor (every ${intervalMinutes} min)...\n`);

  setInterval(async () => {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] Running triage...`);

    const result = await triageNeedsAction({
      minPriorityScore: 7,  // Only high priority
      autoClassify: true
    });

    // Filter new high-priority items
    const newItems = result.items.filter(item => {
      const isNew = !processedFiles.has(item.file_name);
      if (isNew) {
        processedFiles.add(item.file_name);
      }
      return isNew && item.priority_score >= 7;
    });

    if (newItems.length > 0) {
      console.log(`\n🚨 NEW HIGH PRIORITY ITEMS: ${newItems.length}\n`);

      newItems.forEach((item, index) => {
        console.log(`${index + 1}. [Priority ${item.priority_score}] ${item.metadata.subject || item.file_name}`);
        console.log(`   Category: ${item.category}`);
        console.log(`   Deadline: ${item.metadata.deadline || 'None'}`);
        console.log(`   Action: ${item.suggested_action}`);
        console.log(`   ${item.summary}\n`);
      });

      // Notify human (write to Updates/)
      await notifyNewItems(newItems);
    } else {
      console.log(`   No new high-priority items\n`);
    }
  }, intervalMinutes * 60 * 1000);
}

async function notifyNewItems(items) {
  const timestamp = new Date().toISOString();
  const notification = `# New High Priority Items\n\n**Time:** ${new Date().toLocaleString()}\n\n${items.map(i => `- [${i.priority_score}] ${i.metadata.subject || i.file_name}`).join('\n')}\n`;

  await fs.writeFile(
    `${process.env.VAULT_PATH}/Updates/alert-${timestamp}.md`,
    notification
  );

  console.log(`✅ Notification saved to Updates/alert-${timestamp}.md\n`);
}

periodicMonitor(5);
```

### Output

```
🔔 Starting periodic triage monitor (every 5 min)...

[9:00:00 AM] Running triage...
   No new high-priority items

[9:05:00 AM] Running triage...

🚨 NEW HIGH PRIORITY ITEMS: 1

1. [Priority 9] Invoice #1234 payment overdue
   Category: finance
   Deadline: 2025-01-31T23:59:59Z
   Action: approve
   Overdue payment of $5,432.00 from Acme Corp, requires immediate approval

✅ Notification saved to Updates/alert-2025-02-03T09:05:00Z.md

[9:10:00 AM] Running triage...
   No new high-priority items
```

---

## Summary

These examples demonstrate:

1. **Morning review**: Full inbox scan with prioritized output
2. **Finance filtering**: Category-specific triage for specialized workflows
3. **Task claiming**: Integration with task lifecycle for automated claiming
4. **Dashboard generation**: Human-readable summaries for oversight
5. **Error handling**: Graceful fallback when LLM unavailable
6. **Periodic monitoring**: Automated alerts for new high-priority items

All examples follow best practices:
- Structured error handling
- Sanitized logging (no PII)
- Priority-based processing
- Graceful degradation
- Human oversight integration
