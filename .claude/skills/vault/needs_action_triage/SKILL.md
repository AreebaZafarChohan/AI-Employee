---
name: needs_action_triage
description: Scans and classifies items in the Needs_Action folder by type (email, whatsapp, file_drop, finance), assigns priority scores, adds metadata, and provides structured recommendations for next steps.
---

# Needs Action Triage

## Purpose

This skill provides intelligent triage and classification of incoming items in the Needs_Action folder. It analyzes markdown files, categorizes them by source type, assigns priority scores, extracts key metadata, and presents structured recommendations for downstream processing.

The skill is designed to be used by the Local Executive Agent (lex) as the first stage of the Digital FTE workflow, immediately after watcher agents deposit new items.

## When to Use This Skill

Use `needs_action_triage` when:

- **Reviewing inbox**: Scan all files in `Needs_Action/` to understand incoming work
- **Prioritizing tasks**: Get a sorted list of items by urgency and importance
- **Categorizing inputs**: Automatically tag items by source (email, WhatsApp, file drop, finance)
- **Extracting metadata**: Pull out key fields (sender, subject, date, amount, deadline)
- **Planning work**: Generate next-step recommendations for each item
- **Dashboard updates**: Prepare summary statistics for human review
- **Initial assessment**: Before claiming tasks, understand what's available

Do NOT use this skill when:

- **Processing individual tasks**: Use `task_lifecycle_manager` for execution
- **Reading specific files**: Use `vault_state_manager` for direct file access
- **Already-triaged items**: This is for raw inputs in Needs_Action only
- **Non-markdown files**: This skill expects `.md` files with structured content
- **Manual review**: Humans can review items directly in Obsidian

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required (inherited from vault_state_manager)
VAULT_PATH="/absolute/path/to/vault"

# Optional: Triage tuning
TRIAGE_MIN_PRIORITY_SCORE="1"          # Range: 1-10 (filter low priority)
TRIAGE_AUTO_CLASSIFY="true"            # Enable AI classification
TRIAGE_KEYWORD_BOOST="urgent,asap"     # Comma-separated priority keywords
TRIAGE_DEFAULT_CATEGORY="general"      # Fallback if classification fails
TRIAGE_EXTRACT_METADATA="true"         # Parse structured fields from content

# Optional: LLM configuration (if AI classification enabled)
TRIAGE_MODEL="gemini-2.5-flash"        # Model for classification
TRIAGE_TEMPERATURE="0.1"               # Low temp for consistent categorization
TRIAGE_MAX_TOKENS="500"                # Limit for classification response
```

**Secrets Management:**

- This skill does NOT handle secrets
- May reference email addresses, sender names (not sensitive)
- Does not store or process credentials
- API keys for LLM (if used) managed via separate env vars

**Variable Discovery Process:**
```bash
# Check triage configuration
cat .env | grep TRIAGE_

# Verify Needs_Action folder exists
test -d "$VAULT_PATH/Needs_Action" && echo "OK" || echo "Missing"

# Count pending items
find "$VAULT_PATH/Needs_Action" -name '*.md' | wc -l
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Needs Action Triage
  ├── Vault State Manager (file reads)
  │   └── Filesystem (Needs_Action/ folder)
  └── Optional: LLM API (for AI classification)
      └── Gemini API (https://generativelanguage.googleapis.com)
```

**Topology Notes:**
- Primary operation: local file reads (no writes during triage)
- Optional: external LLM API calls for classification (if TRIAGE_AUTO_CLASSIFY=true)
- No database dependencies
- Stateless operation (no caching between runs)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as read-only volume during triage: `-v /host/vault:/vault:ro`
- If using LLM API, ensure outbound HTTPS allowed
- No persistent storage needed (stateless)
- Can run in parallel across multiple agents (read-only)

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for filesystem access (local only)
- If using LLM API: requires API key in environment
- Agent authorization: lex has read access to Needs_Action/ (per AGENTS.md §3)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **PII exposure** | Sanitize logs; never log full email content |
| **Prompt injection** | Validate file content before LLM classification |
| **Malicious files** | Reject files > 100KB, non-markdown extensions |
| **Path traversal** | Validate all paths via vault_state_manager |
| **API key leakage** | Never log API keys; use env vars only |
| **Classification errors** | Fallback to manual category if LLM fails |

**Validation Rules:**

Before processing any file:
```javascript
function validateTriageInput(file) {
  // File size check
  if (file.size > 100 * 1024) {
    throw new Error("File too large for triage (>100KB)");
  }

  // Extension check
  if (!file.name.endsWith('.md')) {
    throw new Error("Only markdown files supported");
  }

  // Path validation
  if (!file.path.startsWith('Needs_Action/')) {
    throw new Error("File not in Needs_Action folder");
  }

  return true;
}
```

**PII Handling:**

Per AGENTS.md, triage metadata may contain:
- Sender names/emails (public identifiers)
- Subject lines (may contain sensitive info - sanitize in logs)
- Financial amounts (not PII, but sensitive - redact in logs)
- Deadlines (not sensitive)

Never log full email content or message bodies.

## Blueprints & Templates Used

### Blueprint: Triage Result Structure

**Purpose:** Standardize triage output for downstream processing

**Template Variables:**
```yaml
# Triage metadata (added to each item)
triage_result:
  file_name: "{{FILE_NAME}}"                    # Original filename
  file_path: "{{RELATIVE_PATH}}"                # Relative to vault root

  # Classification
  category: "{{CATEGORY}}"                      # email | whatsapp | file_drop | finance | general
  subcategory: "{{SUBCATEGORY}}"                # Optional: invoice, receipt, thread, notification
  confidence: "{{CONFIDENCE_SCORE}}"            # 0.0-1.0 (if AI classification used)

  # Priority scoring
  priority_score: {{PRIORITY_SCORE}}            # 1-10 (1=low, 10=critical)
  priority_factors:
    - keyword_match: {{KEYWORD_BOOST}}          # +2 if "urgent" found
    - deadline_proximity: {{DEADLINE_POINTS}}   # +3 if deadline < 24h
    - sender_importance: {{SENDER_WEIGHT}}      # +2 if from VIP
    - financial_threshold: {{AMOUNT_TRIGGER}}   # +3 if >$1000

  # Extracted metadata
  metadata:
    source_type: "{{SOURCE_TYPE}}"              # email, message, file, manual
    sender: "{{SENDER_NAME}}"                   # Extracted sender/author
    subject: "{{SUBJECT_LINE}}"                 # Email subject or message title
    received_at: "{{TIMESTAMP_ISO}}"            # When item arrived
    deadline: "{{DEADLINE_ISO}}"                # Extracted deadline (if any)
    financial_amount: {{AMOUNT}}                # Dollar amount (if finance category)
    tags: ["{{TAG1}}", "{{TAG2}}"]              # Auto-generated tags

  # Recommendations
  suggested_action: "{{ACTION}}"                # research | approve | reject | delegate
  estimated_effort: "{{EFFORT}}"                # low | medium | high
  requires_human_approval: {{BOOLEAN}}          # true if high-risk
  autonomy_tier: "{{TIER}}"                     # bronze | silver | gold | platinum

  # Analysis
  summary: "{{ONE_LINE_SUMMARY}}"               # 1-sentence description
  key_entities: ["{{ENTITY1}}", "{{ENTITY2}}"]  # People, orgs, products mentioned
  sentiment: "{{SENTIMENT}}"                    # positive | neutral | negative | urgent
```

**Impact Notes:**
- All timestamps in ISO 8601 (UTC)
- Priority score calculated using weighted factors
- Confidence score only present if AI classification used
- Financial amounts in USD (convert if needed)
- Tags auto-generated from content + category

### Blueprint: Category Classification Rules

**Purpose:** Define heuristics for categorizing items without LLM

**Rule-Based Classification:**

```javascript
function classifyCategory(content, filename, metadata) {
  // Email indicators
  if (
    content.includes('From:') && content.includes('Subject:') ||
    filename.includes('email-') ||
    metadata.source === 'gmail' || metadata.source === 'outlook'
  ) {
    return {
      category: 'email',
      subcategory: detectEmailType(content),  // thread, notification, newsletter
      confidence: 0.95
    };
  }

  // WhatsApp indicators
  if (
    content.match(/\d{1,2}\/\d{1,2}\/\d{2,4}, \d{1,2}:\d{2}\s*[AP]M\s*-/) ||
    filename.includes('whatsapp-') ||
    content.includes('WhatsApp Chat')
  ) {
    return {
      category: 'whatsapp',
      subcategory: 'message',
      confidence: 0.90
    };
  }

  // Finance indicators
  if (
    content.match(/\$[\d,]+\.\d{2}/) ||
    content.toLowerCase().includes('invoice') ||
    content.toLowerCase().includes('receipt') ||
    content.toLowerCase().includes('payment') ||
    filename.toLowerCase().includes('invoice') ||
    filename.toLowerCase().includes('receipt')
  ) {
    return {
      category: 'finance',
      subcategory: detectFinanceType(content),  // invoice, receipt, statement
      confidence: 0.85
    };
  }

  // File drop indicators (PDFs, images, documents)
  if (
    content.includes('Attached:') ||
    content.includes('File:') ||
    filename.includes('file-drop-') ||
    metadata.has_attachments === true
  ) {
    return {
      category: 'file_drop',
      subcategory: detectFileType(content),
      confidence: 0.80
    };
  }

  // Fallback: general
  return {
    category: process.env.TRIAGE_DEFAULT_CATEGORY || 'general',
    subcategory: 'uncategorized',
    confidence: 0.50
  };
}
```

**Impact Notes:**
- Rule-based classification runs first (fast, no API cost)
- Falls back to LLM only if confidence < 0.70
- Confidence thresholds tunable via config
- Multiple indicators increase confidence

### Blueprint: Priority Scoring Algorithm

**Purpose:** Calculate priority score (1-10) based on weighted factors

**Scoring Formula:**

```javascript
function calculatePriorityScore(content, metadata, category) {
  let score = 3;  // Base score (medium priority)

  // Factor 1: Keyword boost (+0 to +3)
  const urgentKeywords = (process.env.TRIAGE_KEYWORD_BOOST || 'urgent,asap,critical,immediate').split(',');
  const contentLower = content.toLowerCase();

  for (const keyword of urgentKeywords) {
    if (contentLower.includes(keyword.trim())) {
      score += 2;
      break;  // Max +2 for keyword match
    }
  }

  // Factor 2: Deadline proximity (+0 to +3)
  if (metadata.deadline) {
    const hoursUntilDeadline = (new Date(metadata.deadline) - Date.now()) / (1000 * 60 * 60);

    if (hoursUntilDeadline < 0) {
      score += 3;  // Overdue
    } else if (hoursUntilDeadline < 24) {
      score += 3;  // Due today
    } else if (hoursUntilDeadline < 72) {
      score += 2;  // Due within 3 days
    } else if (hoursUntilDeadline < 168) {
      score += 1;  // Due within 1 week
    }
  }

  // Factor 3: Sender importance (+0 to +2)
  const vipSenders = (process.env.TRIAGE_VIP_SENDERS || '').split(',').map(s => s.trim().toLowerCase());
  if (metadata.sender && vipSenders.some(vip => metadata.sender.toLowerCase().includes(vip))) {
    score += 2;
  }

  // Factor 4: Financial threshold (+0 to +3)
  if (category === 'finance' && metadata.financial_amount) {
    if (metadata.financial_amount > 10000) {
      score += 3;  // >$10k
    } else if (metadata.financial_amount > 1000) {
      score += 2;  // >$1k
    } else if (metadata.financial_amount > 100) {
      score += 1;  // >$100
    }
  }

  // Factor 5: Category-specific adjustments
  if (category === 'finance') {
    score += 1;  // Finance always elevated
  }

  // Clamp to 1-10 range
  return Math.min(10, Math.max(1, Math.round(score)));
}
```

**Impact Notes:**
- Base score 3 (medium) for all items
- Multiple factors can compound (max score 10)
- Overdue items always high priority
- Financial items get automatic boost
- VIP senders configurable via env var

### Blueprint: Metadata Extraction

**Purpose:** Parse structured fields from markdown content

**Extraction Patterns:**

```javascript
function extractMetadata(content, filename) {
  const metadata = {};

  // Sender extraction (email format)
  const fromMatch = content.match(/From:\s*([^\n<]+)(?:<([^>]+)>)?/i);
  if (fromMatch) {
    metadata.sender = fromMatch[1].trim();
    metadata.sender_email = fromMatch[2]?.trim();
  }

  // Subject extraction
  const subjectMatch = content.match(/Subject:\s*([^\n]+)/i);
  if (subjectMatch) {
    metadata.subject = subjectMatch[1].trim();
  }

  // Timestamp extraction (ISO 8601 or common formats)
  const dateMatch = content.match(/Date:\s*([^\n]+)/i) ||
                    content.match(/Received:\s*([^\n]+)/i) ||
                    content.match(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
  if (dateMatch) {
    try {
      metadata.received_at = new Date(dateMatch[1] || dateMatch[0]).toISOString();
    } catch (err) {
      // Invalid date, skip
    }
  }

  // Deadline extraction
  const deadlineMatch = content.match(/(?:deadline|due by|due date):\s*([^\n]+)/i);
  if (deadlineMatch) {
    try {
      metadata.deadline = new Date(deadlineMatch[1]).toISOString();
    } catch (err) {
      // Invalid date, skip
    }
  }

  // Financial amount extraction
  const amountMatch = content.match(/\$\s*([\d,]+(?:\.\d{2})?)/);
  if (amountMatch) {
    metadata.financial_amount = parseFloat(amountMatch[1].replace(/,/g, ''));
  }

  // Tag extraction (hashtags or YAML front-matter)
  const tagMatches = content.match(/#([\w-]+)/g);
  if (tagMatches) {
    metadata.tags = tagMatches.map(tag => tag.slice(1));
  }

  // Source type (from filename prefix)
  if (filename.startsWith('email-')) {
    metadata.source_type = 'email';
  } else if (filename.startsWith('whatsapp-')) {
    metadata.source_type = 'whatsapp';
  } else if (filename.startsWith('file-drop-')) {
    metadata.source_type = 'file';
  } else {
    metadata.source_type = 'manual';
  }

  return metadata;
}
```

**Impact Notes:**
- Extracts all standard email fields
- Handles multiple date formats
- Detects financial amounts in various formats ($1,000.00, $1000)
- Falls back gracefully if fields missing
- Never throws errors (returns partial metadata)

### Blueprint: Triage Summary Table

**Purpose:** Present triage results in structured, sortable format

**Output Format:**

```markdown
# Needs_Action Triage Report

**Generated:** {{TIMESTAMP}}
**Total Items:** {{COUNT}}
**High Priority (8-10):** {{HIGH_COUNT}}
**Medium Priority (4-7):** {{MEDIUM_COUNT}}
**Low Priority (1-3):** {{LOW_COUNT}}

---

## Priority Items (Score ≥ 7)

| Priority | Category | Subject | Sender | Deadline | Action |
|----------|----------|---------|--------|----------|--------|
| 9 | finance | Invoice #1234 overdue | Acme Corp | OVERDUE | approve |
| 8 | email | Urgent: Server down | ops-team | 2h | research |
| 7 | whatsapp | Meeting reschedule | John Doe | today | delegate |

## Medium Priority (Score 4-6)

| Priority | Category | Subject | Sender | Deadline | Action |
|----------|----------|---------|--------|----------|--------|
| 6 | email | Weekly report due | manager | 3 days | research |
| 5 | file_drop | Contract for review | legal-team | 1 week | approve |
| 4 | general | Feature request | customer | none | delegate |

## Low Priority (Score 1-3)

| Priority | Category | Subject | Sender | Deadline | Action |
|----------|----------|---------|--------|----------|--------|
| 3 | email | Newsletter | marketing | none | archive |
| 2 | whatsapp | Lunch plans | friend | none | ignore |

---

## Category Breakdown

- **Email:** 5 items (3 high, 2 medium)
- **WhatsApp:** 2 items (1 high, 1 low)
- **Finance:** 1 item (1 high)
- **File Drop:** 1 item (1 medium)
- **General:** 1 item (1 medium)

## Suggested Next Steps

1. **Immediate (Priority 9-10):** 1 item
   - Claim finance invoice (overdue payment)

2. **Today (Priority 7-8):** 2 items
   - Research server issue, delegate meeting reschedule

3. **This Week (Priority 4-6):** 3 items
   - Prepare weekly report, review contract, triage feature request

4. **Low Priority (Priority 1-3):** 2 items
   - Archive newsletter, defer lunch plans

## Files Analyzed

- `email-20250203-invoice-overdue.md`
- `email-20250203-server-alert.md`
- `whatsapp-20250203-meeting.md`
- `email-20250203-weekly-report.md`
- `file-drop-20250203-contract.md`
- `general-20250203-feature-request.md`
- `email-20250203-newsletter.md`
- `whatsapp-20250203-lunch.md`
```

**Impact Notes:**
- Sorted by priority (highest first)
- Includes all key metadata in table
- Grouped by priority tier for scanning
- Category breakdown for visibility
- Actionable next steps with time-boxed recommendations

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [x] Uses canonical folder structure: `SKILL.md`, `references/`, `assets/`
- [x] Contains complete impact analysis (Env, Network, Auth)
- [x] No `localhost` hardcoding (N/A - filesystem + optional API)
- [x] No secrets or passwords in templates
- [x] Auth/CORS impact explicitly documented (API key via env var)
- [x] Supports containerization (Docker read-only volume documented)
- [x] Gotchas document has known failures and mitigation
- [x] Anti-patterns list common mistakes
- [x] All templates use parameterized placeholders `{{VARIABLE}}`
- [x] Templates include IMPACT NOTES comments
- [x] References folder structure documented
- [x] SKILL.md contains all required sections

### Quality Checks (Skill Degraded If Failed)

- [x] Default values for non-sensitive variables
- [x] Variable naming follows consistent pattern
- [x] API endpoint documented (Anthropic API for LLM)
- [x] Graceful degradation (falls back to rule-based if LLM fails)
- [x] PII sanitization in logs
- [x] Structured output format (markdown table)

### Triage-Specific Checks

- [x] Rule-based classification implemented (no LLM required)
- [x] Priority scoring algorithm documented
- [x] Metadata extraction handles missing fields gracefully
- [x] Supports multiple categories (email, whatsapp, finance, file_drop, general)
- [x] Output sorted by priority (highest first)
- [x] Summary statistics included
- [x] Next-step recommendations provided
- [x] File validation (size, extension, path)

## Anti-Patterns

### ❌ Logging Full Email Content

**Problem:** PII and sensitive data leaked in logs

**Example:**
```javascript
// WRONG - logs entire email body
console.log('Processing email:', emailContent);

// CORRECT - sanitize before logging
console.log('Processing email:', {
  subject: email.subject,
  sender: email.sender,
  category: email.category
  // Don't log: body, attachments, personal info
});
```

### ❌ Hardcoding Priority Keywords

**Problem:** Cannot customize urgency triggers

**Example:**
```javascript
// WRONG - hardcoded keywords
if (content.includes('urgent') || content.includes('asap')) {
  score += 2;
}

// CORRECT - configurable via env var
const urgentKeywords = process.env.TRIAGE_KEYWORD_BOOST.split(',');
if (urgentKeywords.some(kw => content.toLowerCase().includes(kw.trim()))) {
  score += 2;
}
```

### ❌ Failing on Missing Metadata

**Problem:** Crashes if email has no subject or sender

**Example:**
```javascript
// WRONG - assumes fields always exist
const subject = metadata.subject.trim();  // Crashes if undefined

// CORRECT - handle missing fields
const subject = metadata.subject?.trim() || '[No Subject]';
```

### ❌ Not Validating File Size

**Problem:** Triage hangs on huge files

**Example:**
```javascript
// WRONG - reads file without size check
const content = await fs.readFile(filePath, 'utf8');

// CORRECT - validate size first
const stats = await fs.stat(filePath);
if (stats.size > 100 * 1024) {
  throw new Error('File too large for triage');
}
const content = await fs.readFile(filePath, 'utf8');
```

### ❌ Ignoring LLM API Failures

**Problem:** Triage fails completely if API down

**Example:**
```javascript
// WRONG - no fallback
const category = await classifyWithLLM(content);

// CORRECT - fallback to rule-based
let category;
try {
  category = await classifyWithLLM(content);
} catch (err) {
  console.warn('LLM classification failed, using rule-based:', err.message);
  category = classifyWithRules(content);
}
```

### ❌ Not Sorting Results

**Problem:** High-priority items buried in output

**Example:**
```javascript
// WRONG - unsorted (chronological order)
const results = triageResults;

// CORRECT - sort by priority descending
const results = triageResults.sort((a, b) => b.priority_score - a.priority_score);
```

### ❌ Overwriting Existing Triage Metadata

**Problem:** Loses manual tags or corrections

**Example:**
```javascript
// WRONG - overwrites entire file
await writeFile(filePath, triageResult);

// CORRECT - merge with existing metadata
const existing = await readFile(filePath);
const merged = { ...existing, triage_result: triageResult };
await writeFile(filePath, merged);
```

### ❌ No Confidence Thresholds

**Problem:** Low-confidence classifications treated as certain

**Example:**
```javascript
// WRONG - uses all classifications regardless of confidence
const category = classification.category;

// CORRECT - fallback if low confidence
const category = classification.confidence > 0.70
  ? classification.category
  : 'general';
```

## Enforcement Behavior

When this skill is active:

### Agent Responsibilities

1. **Run triage before claiming tasks** - understand inbox first
2. **Respect priority scores** - process high-priority items first
3. **Sanitize logs** - never log full email content or PII
4. **Handle missing metadata gracefully** - don't crash on incomplete files
5. **Fallback to rule-based classification** - don't depend on LLM availability
6. **Sort results by priority** - present highest-priority items first
7. **Validate file inputs** - check size, extension, path before processing

### User Expectations

- All items in Needs_Action/ are triaged and categorized
- Priority scores are consistent and explainable
- High-priority items are surfaced immediately
- Summary statistics provide inbox overview
- Next-step recommendations are actionable
- Triage runs quickly (<5s for 10 items)

### Error Handling

All functions return structured results:

```typescript
interface TriageResult {
  success: boolean;
  items: TriageItem[];
  summary: {
    total: number;
    high_priority: number;
    medium_priority: number;
    low_priority: number;
    by_category: Record<string, number>;
  };
  errors?: string[];  // Files that failed to process
}

interface TriageItem {
  file_name: string;
  file_path: string;
  category: string;
  subcategory?: string;
  confidence: number;
  priority_score: number;
  metadata: Record<string, any>;
  suggested_action: string;
  summary: string;
}
```

Agents must check `success` field and handle partial failures (some files skipped).

## Integration with AGENTS.md

This skill supports the workflow orchestration defined in AGENTS.md §4:

- **§4.1 Inbox Processing**: First stage after watchers deposit items
- **§4.2 Priority-Based Claiming**: Enables lex to claim high-priority tasks first
- **§4.3 Category-Based Routing**: Different handling for email vs finance vs file_drop
- **§4.4 Metadata Enrichment**: Adds structured data for downstream processing

All agents using this skill MUST respect the read-only nature of triage (no writes to Needs_Action during scan).

## Usage Examples

See `references/patterns.md` for concrete code examples and workflow patterns.
