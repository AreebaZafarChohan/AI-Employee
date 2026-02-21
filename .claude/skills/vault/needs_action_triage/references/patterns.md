# Needs Action Triage - Usage Patterns

This document provides concrete code examples and workflow patterns for the `needs_action_triage` skill.

---

## Pattern 1: Basic Inbox Triage

**Use Case:** Scan Needs_Action folder and get prioritized list

**Code Example:**

```javascript
const { triageNeedsAction } = require('./needs_action_triage');

async function scanInbox() {
  // Run triage on all items in Needs_Action/
  const result = await triageNeedsAction({
    minPriorityScore: 1,  // Include all items
    autoClassify: true,   // Use LLM if available
    extractMetadata: true // Parse structured fields
  });

  if (!result.success) {
    console.error('Triage failed:', result.errors);
    return;
  }

  // Display summary
  console.log(`\n📥 Inbox Summary:`);
  console.log(`   Total: ${result.summary.total}`);
  console.log(`   High Priority: ${result.summary.high_priority}`);
  console.log(`   Medium Priority: ${result.summary.medium_priority}`);
  console.log(`   Low Priority: ${result.summary.low_priority}`);

  // Show top 3 priority items
  console.log(`\n🔥 Top Priority Items:`);
  result.items.slice(0, 3).forEach((item, i) => {
    console.log(`${i + 1}. [${item.priority_score}] ${item.metadata.subject || item.file_name}`);
    console.log(`   Category: ${item.category}`);
    console.log(`   Action: ${item.suggested_action}`);
    console.log(`   Summary: ${item.summary}`);
  });

  return result;
}

// Run triage
scanInbox();
```

**Output:**
```
📥 Inbox Summary:
   Total: 8
   High Priority: 2
   Medium Priority: 4
   Low Priority: 2

🔥 Top Priority Items:
1. [9] Invoice #1234 overdue
   Category: finance
   Action: approve
   Summary: Overdue payment of $5,432.00 from Acme Corp, requires immediate approval

2. [8] Urgent: Server down
   Category: email
   Action: research
   Summary: Production server outage reported by ops-team, deadline 2 hours

3. [7] Meeting reschedule
   Category: whatsapp
   Action: delegate
   Summary: Client requests to reschedule meeting from today to tomorrow
```

---

## Pattern 2: Prioritized Task Claiming

**Use Case:** Claim highest-priority task from inbox

**Code Example:**

```javascript
const { triageNeedsAction } = require('./needs_action_triage');
const { claimTask } = require('./task_lifecycle_manager');

async function claimNextTask(agentName) {
  // Step 1: Triage inbox
  const triage = await triageNeedsAction({
    minPriorityScore: 5,  // Only medium+ priority
    autoClassify: true
  });

  if (triage.items.length === 0) {
    console.log('No medium+ priority items available');
    return null;
  }

  // Step 2: Try to claim highest-priority item
  for (const item of triage.items) {
    const claimResult = await claimTask(item.file_name, agentName);

    if (claimResult.success) {
      console.log(`✅ Claimed task: ${item.metadata.subject || item.file_name}`);
      console.log(`   Priority: ${item.priority_score}`);
      console.log(`   Category: ${item.category}`);
      console.log(`   Suggested action: ${item.suggested_action}`);

      return {
        taskId: claimResult.taskId,
        triageData: item
      };
    } else {
      console.log(`❌ Task already claimed: ${item.file_name}`);
      // Try next item
    }
  }

  console.log('All high-priority tasks already claimed');
  return null;
}

// Agent claims work
claimNextTask('lex');
```

**Output:**
```
✅ Claimed task: Invoice #1234 overdue
   Priority: 9
   Category: finance
   Suggested action: approve
```

---

## Pattern 3: Category-Specific Filtering

**Use Case:** Process only finance items

**Code Example:**

```javascript
async function triageFinanceItems() {
  const triage = await triageNeedsAction({ autoClassify: true });

  // Filter by category
  const financeItems = triage.items.filter(item => item.category === 'finance');

  console.log(`\n💰 Finance Items (${financeItems.length}):`);

  financeItems.forEach(item => {
    console.log(`\n📄 ${item.metadata.subject || item.file_name}`);
    console.log(`   Amount: $${item.metadata.financial_amount?.toLocaleString()}`);
    console.log(`   Sender: ${item.metadata.sender || 'Unknown'}`);
    console.log(`   Priority: ${item.priority_score}`);
    console.log(`   Deadline: ${item.metadata.deadline || 'None'}`);
    console.log(`   Action: ${item.suggested_action}`);
  });

  return financeItems;
}

triageFinanceItems();
```

**Output:**
```
💰 Finance Items (2):

📄 Invoice #1234 overdue
   Amount: $5,432.00
   Sender: Acme Corp
   Priority: 9
   Deadline: OVERDUE
   Action: approve

📄 Receipt for office supplies
   Amount: $127.50
   Sender: Office Depot
   Priority: 4
   Deadline: None
   Action: archive
```

---

## Pattern 4: Dashboard Summary Generation

**Use Case:** Generate summary for human review

**Code Example:**

```javascript
async function generateDashboardSummary() {
  const triage = await triageNeedsAction({ autoClassify: true });

  // Build summary markdown
  let summary = `# Daily Inbox Summary\n\n`;
  summary += `**Date:** ${new Date().toLocaleDateString()}\n`;
  summary += `**Total Items:** ${triage.summary.total}\n\n`;

  summary += `## Priority Breakdown\n\n`;
  summary += `- 🔴 High (8-10): ${triage.summary.high_priority}\n`;
  summary += `- 🟡 Medium (4-7): ${triage.summary.medium_priority}\n`;
  summary += `- 🟢 Low (1-3): ${triage.summary.low_priority}\n\n`;

  summary += `## Category Breakdown\n\n`;
  Object.entries(triage.summary.by_category).forEach(([cat, count]) => {
    const icon = { email: '📧', whatsapp: '💬', finance: '💰', file_drop: '📁', general: '📝' }[cat] || '📄';
    summary += `- ${icon} ${cat}: ${count}\n`;
  });

  summary += `\n## Top 5 Priority Items\n\n`;
  summary += `| Priority | Category | Subject | Deadline |\n`;
  summary += `|----------|----------|---------|----------|\n`;

  triage.items.slice(0, 5).forEach(item => {
    const deadline = item.metadata.deadline
      ? new Date(item.metadata.deadline).toLocaleDateString()
      : 'None';

    summary += `| ${item.priority_score} | ${item.category} | ${item.metadata.subject || item.file_name} | ${deadline} |\n`;
  });

  summary += `\n## Recommended Actions\n\n`;
  const immediateItems = triage.items.filter(i => i.priority_score >= 8);
  const todayItems = triage.items.filter(i => i.priority_score >= 6 && i.priority_score < 8);

  if (immediateItems.length > 0) {
    summary += `### 🚨 Immediate (Priority 8-10)\n\n`;
    immediateItems.forEach(item => {
      summary += `- **${item.metadata.subject || item.file_name}**\n`;
      summary += `  - Action: ${item.suggested_action}\n`;
      summary += `  - ${item.summary}\n\n`;
    });
  }

  if (todayItems.length > 0) {
    summary += `### 📅 Today (Priority 6-7)\n\n`;
    todayItems.forEach(item => {
      summary += `- ${item.metadata.subject || item.file_name} (${item.suggested_action})\n`;
    });
  }

  // Write to Updates/ folder for human review
  const fs = require('fs').promises;
  const vaultPath = process.env.VAULT_PATH;
  const filename = `inbox-summary-${new Date().toISOString().split('T')[0]}.md`;

  await fs.writeFile(`${vaultPath}/Updates/${filename}`, summary);

  console.log(`✅ Dashboard summary saved to Updates/${filename}`);
  return summary;
}

generateDashboardSummary();
```

**Output File (Updates/inbox-summary-2025-02-03.md):**
```markdown
# Daily Inbox Summary

**Date:** 2/3/2025
**Total Items:** 8

## Priority Breakdown

- 🔴 High (8-10): 2
- 🟡 Medium (4-7): 4
- 🟢 Low (1-3): 2

## Category Breakdown

- 📧 email: 4
- 💬 whatsapp: 2
- 💰 finance: 1
- 📁 file_drop: 1

## Top 5 Priority Items

| Priority | Category | Subject | Deadline |
|----------|----------|---------|----------|
| 9 | finance | Invoice #1234 overdue | OVERDUE |
| 8 | email | Urgent: Server down | 2/3/2025 |
| 7 | whatsapp | Meeting reschedule | 2/3/2025 |
| 6 | email | Weekly report due | 2/6/2025 |
| 5 | file_drop | Contract for review | 2/10/2025 |

## Recommended Actions

### 🚨 Immediate (Priority 8-10)

- **Invoice #1234 overdue**
  - Action: approve
  - Overdue payment of $5,432.00 from Acme Corp, requires immediate approval

- **Urgent: Server down**
  - Action: research
  - Production server outage reported by ops-team, deadline 2 hours

### 📅 Today (Priority 6-7)

- Meeting reschedule (delegate)
- Weekly report due (research)
```

---

## Pattern 5: Rule-Based Classification Fallback

**Use Case:** Triage without LLM (offline mode)

**Code Example:**

```javascript
async function triageOffline() {
  // Disable LLM classification
  const triage = await triageNeedsAction({
    autoClassify: false,  // Use only rule-based classification
    extractMetadata: true
  });

  console.log(`\n📊 Triage Results (Rule-Based):`);
  console.log(`   Processed: ${triage.summary.total} items`);

  // Show confidence scores
  const avgConfidence = triage.items.reduce((sum, item) => sum + item.confidence, 0) / triage.items.length;
  console.log(`   Avg Confidence: ${(avgConfidence * 100).toFixed(1)}%`);

  // Flag low-confidence items for manual review
  const lowConfidence = triage.items.filter(item => item.confidence < 0.70);
  if (lowConfidence.length > 0) {
    console.log(`\n⚠️  Low Confidence Items (${lowConfidence.length}):`);
    lowConfidence.forEach(item => {
      console.log(`   - ${item.file_name}: ${item.category} (${(item.confidence * 100).toFixed(0)}%)`);
    });
  }

  return triage;
}

triageOffline();
```

**Output:**
```
📊 Triage Results (Rule-Based):
   Processed: 8 items
   Avg Confidence: 84.4%

⚠️  Low Confidence Items (2):
   - general-20250203-feature-request.md: general (50%)
   - file-drop-20250203-unknown.md: file_drop (65%)
```

---

## Pattern 6: Metadata Enrichment for Planning

**Use Case:** Extract metadata to inform plan generation

**Code Example:**

```javascript
async function enrichTaskMetadata(taskFile) {
  // Triage single file
  const triage = await triageNeedsAction({
    filterFiles: [taskFile],  // Process only this file
    extractMetadata: true
  });

  if (triage.items.length === 0) {
    throw new Error(`File not found: ${taskFile}`);
  }

  const item = triage.items[0];

  // Build enriched metadata for task lifecycle
  const enrichedMetadata = {
    // Original triage data
    category: item.category,
    subcategory: item.subcategory,
    priority_score: item.priority_score,

    // Extracted fields
    source_type: item.metadata.source_type,
    sender: item.metadata.sender,
    subject: item.metadata.subject,
    received_at: item.metadata.received_at,
    deadline: item.metadata.deadline,
    financial_amount: item.metadata.financial_amount,
    tags: item.metadata.tags,

    // Recommendations
    suggested_action: item.suggested_action,
    estimated_effort: item.estimated_effort,
    requires_human_approval: item.requires_human_approval,
    autonomy_tier: item.autonomy_tier,

    // Analysis
    summary: item.summary,
    key_entities: item.key_entities,
    sentiment: item.sentiment
  };

  console.log(`✅ Enriched metadata for: ${taskFile}`);
  console.log(JSON.stringify(enrichedMetadata, null, 2));

  return enrichedMetadata;
}

// Enrich before planning
const metadata = await enrichTaskMetadata('email-20250203-invoice.md');

// Use metadata in plan generation
const plan = await generatePlan({
  taskFile: 'email-20250203-invoice.md',
  triageMetadata: metadata
});
```

**Output:**
```json
✅ Enriched metadata for: email-20250203-invoice.md
{
  "category": "finance",
  "subcategory": "invoice",
  "priority_score": 9,
  "source_type": "email",
  "sender": "Acme Corp <billing@acme.com>",
  "subject": "Invoice #1234 overdue",
  "received_at": "2025-01-15T10:00:00Z",
  "deadline": "2025-01-31T23:59:59Z",
  "financial_amount": 5432.00,
  "tags": ["urgent", "payment", "overdue"],
  "suggested_action": "approve",
  "estimated_effort": "low",
  "requires_human_approval": true,
  "autonomy_tier": "silver",
  "summary": "Overdue payment of $5,432.00 from Acme Corp, requires immediate approval",
  "key_entities": ["Acme Corp", "Invoice #1234"],
  "sentiment": "urgent"
}
```

---

## Pattern 7: Periodic Triage with Change Detection

**Use Case:** Run triage periodically, only report new high-priority items

**Code Example:**

```javascript
let lastTriageTimestamp = null;
const processedFiles = new Set();

async function periodicTriage(intervalMinutes = 5) {
  setInterval(async () => {
    console.log(`\n🔄 Running periodic triage...`);

    const triage = await triageNeedsAction({
      minPriorityScore: 7,  // Only high priority
      autoClassify: true
    });

    // Filter new items
    const newHighPriority = triage.items.filter(item => {
      const isNew = !processedFiles.has(item.file_name);
      if (isNew) {
        processedFiles.add(item.file_name);
      }
      return isNew && item.priority_score >= 7;
    });

    if (newHighPriority.length > 0) {
      console.log(`\n🚨 New High Priority Items: ${newHighPriority.length}`);

      newHighPriority.forEach(item => {
        console.log(`\n📬 ${item.metadata.subject || item.file_name}`);
        console.log(`   Priority: ${item.priority_score}`);
        console.log(`   Category: ${item.category}`);
        console.log(`   Action: ${item.suggested_action}`);
        console.log(`   ${item.summary}`);
      });

      // Notify human (e.g., write to Updates/)
      await notifyNewPriorityItems(newHighPriority);
    } else {
      console.log('   No new high-priority items');
    }

    lastTriageTimestamp = new Date().toISOString();
  }, intervalMinutes * 60 * 1000);
}

// Run every 5 minutes
periodicTriage(5);
```

---

## Error Handling Pattern

**Use Case:** Robust error handling for triage operations

**Code Example:**

```javascript
async function robustTriage() {
  try {
    const result = await triageNeedsAction({
      autoClassify: true,
      extractMetadata: true
    });

    // Check for partial failures
    if (result.errors && result.errors.length > 0) {
      console.warn(`⚠️  ${result.errors.length} files failed to process:`);
      result.errors.forEach(err => console.warn(`   - ${err}`));
    }

    // Proceed with successfully processed items
    if (result.items.length === 0) {
      console.log('📭 Inbox is empty');
      return null;
    }

    console.log(`✅ Successfully triaged ${result.items.length} items`);
    return result;

  } catch (err) {
    // Handle critical errors
    if (err.code === 'VAULT_PATH_MISSING') {
      console.error('❌ VAULT_PATH not configured in .env');
    } else if (err.code === 'NEEDS_ACTION_NOT_FOUND') {
      console.error('❌ Needs_Action folder not found in vault');
    } else if (err.code === 'LLM_API_ERROR') {
      console.warn('⚠️  LLM API unavailable, falling back to rule-based classification');
      // Retry without LLM
      return await triageNeedsAction({ autoClassify: false });
    } else {
      console.error('❌ Triage failed:', err.message);
    }

    return null;
  }
}

robustTriage();
```

---

## Best Practices

1. **Always run triage before claiming** - understand inbox state first
2. **Sort by priority** - process highest-priority items first
3. **Handle partial failures gracefully** - some files may be corrupted or malformed
4. **Fallback to rule-based classification** - don't depend on LLM availability
5. **Sanitize logs** - never log full email content or PII
6. **Validate file inputs** - check size, extension, path before processing
7. **Use metadata for planning** - enrich tasks with triage data
8. **Run periodic triage** - detect new high-priority items automatically
9. **Generate human-readable summaries** - write dashboard updates to Updates/ folder
10. **Track processed files** - avoid re-processing same items

---

## Performance Tips

- **Batch processing:** Triage processes all files in single pass (efficient)
- **Rule-based first:** Try rule-based classification before LLM (faster, free)
- **Filter by priority:** Use `minPriorityScore` to skip low-priority items
- **Category filtering:** Process only relevant categories for specific workflows
- **File size limits:** Reject files >100KB to prevent hangs
- **Parallel execution:** Multiple agents can triage concurrently (read-only)

---

## Integration Points

- **Watcher Agents:** Triage processes outputs from all watchers
- **Local Executive Agent (lex):** Uses triage to prioritize work
- **Task Lifecycle Manager:** Enriches task metadata with triage data
- **Human Dashboard:** Generates daily summaries for review
- **Cloud Executive Agent (cex):** Receives triage data for planning context
