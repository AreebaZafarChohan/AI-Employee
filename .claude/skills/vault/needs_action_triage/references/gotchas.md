# Needs Action Triage - Gotchas & Pitfalls

This document lists common issues, edge cases, and failure modes when using the `needs_action_triage` skill.

---

## Gotcha 1: Large Files Hang Triage

**Problem:**

Attempting to triage a very large file (>100KB) causes the process to hang or timeout.

**Symptom:**
```
Triage running... (no progress for 30+ seconds)
```

**Root Cause:**

- Reading large files synchronously blocks event loop
- LLM classification on huge content exceeds token limits
- Memory usage spikes for large files

**Mitigation:**

```javascript
// BEFORE processing file
const stats = await fs.stat(filePath);
if (stats.size > 100 * 1024) {
  console.warn(`File too large: ${filePath} (${stats.size} bytes), skipping`);
  return {
    success: false,
    error: 'FILE_TOO_LARGE',
    message: `File exceeds 100KB limit: ${filePath}`
  };
}
```

**Prevention:**

- Add file size check in `validateTriageInput()`
- Reject files >100KB before reading
- Log warning with file name and size
- Return structured error (don't crash)

---

## Gotcha 2: PII Leaked in Logs

**Problem:**

Full email content logged during debugging, exposing sensitive information.

**Symptom:**
```
console.log('Processing email:', emailContent);
// Logs: "From: john@example.com, Password reset token: abc123..."
```

**Root Cause:**

- Developer logs entire file content for debugging
- Sensitive fields (body, tokens, passwords) included
- Logs persist in audit trails or monitoring systems

**Mitigation:**

```javascript
// WRONG - logs entire content
console.log('Processing email:', emailContent);

// CORRECT - sanitize before logging
const sanitized = {
  file_name: file.name,
  subject: extractedMetadata.subject,
  sender: extractedMetadata.sender,
  category: classification.category,
  priority: priorityScore
  // DO NOT LOG: body, attachments, tokens, passwords
};
console.log('Processing email:', sanitized);
```

**Prevention:**

- Never log full file content
- Create explicit sanitization function
- Whitelist safe fields for logging (subject, sender, category)
- Blacklist sensitive fields (body, attachments, API keys)

---

## Gotcha 3: LLM API Failures Break Triage

**Problem:**

When LLM API is unavailable, triage fails completely instead of falling back to rule-based classification.

**Symptom:**
```
Error: LLM API request failed: 503 Service Unavailable
Triage aborted.
```

**Root Cause:**

- No fallback mechanism for LLM classification
- Triage depends on external API availability
- Network issues or rate limits cause failures

**Mitigation:**

```javascript
async function classifyWithFallback(content, filename) {
  // Try LLM first
  if (process.env.TRIAGE_AUTO_CLASSIFY === 'true') {
    try {
      const llmResult = await classifyWithLLM(content);
      return llmResult;
    } catch (err) {
      console.warn('LLM classification failed, using rule-based fallback:', err.message);
      // Fall through to rule-based
    }
  }

  // Fallback to rule-based (always available)
  return classifyWithRules(content, filename);
}
```

**Prevention:**

- Always implement rule-based classification as fallback
- Wrap LLM calls in try/catch
- Log warnings (not errors) for LLM failures
- Document that rule-based is sufficient for most cases

---

## Gotcha 4: Low-Confidence Classifications Treated as Certain

**Problem:**

Items with low classification confidence (<0.70) are processed as if classification is correct.

**Symptom:**
```
Classified as 'email' with 52% confidence
Processing as email... (but it's actually a WhatsApp message)
```

**Root Cause:**

- No confidence threshold check
- Agent assumes all classifications are accurate
- Low-confidence items need manual review

**Mitigation:**

```javascript
function applyConfidenceThreshold(classification, threshold = 0.70) {
  if (classification.confidence < threshold) {
    console.warn(`Low confidence (${classification.confidence}), using fallback category`);
    return {
      category: process.env.TRIAGE_DEFAULT_CATEGORY || 'general',
      subcategory: 'low_confidence',
      confidence: classification.confidence,
      original_classification: classification.category
    };
  }
  return classification;
}
```

**Prevention:**

- Set minimum confidence threshold (default 0.70)
- Fallback to 'general' category if below threshold
- Log original classification for debugging
- Flag low-confidence items for manual review

---

## Gotcha 5: Missing Metadata Fields Cause Crashes

**Problem:**

Code assumes metadata fields always exist (e.g., `metadata.subject.trim()`), causing crashes when missing.

**Symptom:**
```
TypeError: Cannot read property 'trim' of undefined
  at extractMetadata (triage.js:42)
```

**Root Cause:**

- Not all files have all metadata fields
- Optional fields (deadline, financial_amount) may be missing
- Code doesn't check for undefined before accessing

**Mitigation:**

```javascript
// WRONG - crashes if undefined
const subject = metadata.subject.trim();

// CORRECT - handle missing fields
const subject = metadata.subject?.trim() || '[No Subject]';
const deadline = metadata.deadline || null;
const amount = metadata.financial_amount ?? 0;
```

**Prevention:**

- Use optional chaining (`?.`) for all metadata fields
- Provide sensible defaults (`|| 'default'`)
- Never assume fields exist
- Return partial metadata gracefully

---

## Gotcha 6: Triage Results Not Sorted by Priority

**Problem:**

Triage output is in chronological order (oldest first), burying high-priority items.

**Symptom:**
```
Items:
1. Newsletter (priority 2)
2. Feature request (priority 4)
3. URGENT: Server down (priority 9)  // Should be first!
```

**Root Cause:**

- Default sort is by file creation time (filesystem order)
- High-priority items not surfaced first
- Agent processes items in wrong order

**Mitigation:**

```javascript
// Sort by priority descending (highest first)
const sortedItems = triageResults.sort((a, b) => b.priority_score - a.priority_score);

// Then by deadline (overdue first)
const sortedWithDeadlines = sortedItems.sort((a, b) => {
  // If both have deadlines, sort by urgency
  if (a.metadata.deadline && b.metadata.deadline) {
    return new Date(a.metadata.deadline) - new Date(b.metadata.deadline);
  }
  // Items with deadlines come before those without
  if (a.metadata.deadline) return -1;
  if (b.metadata.deadline) return 1;
  return 0;
});
```

**Prevention:**

- Always sort results by priority descending
- Secondary sort by deadline (overdue first)
- Document sort order in output
- Provide top-N filter (e.g., top 5 items)

---

## Gotcha 7: Duplicate Items in Needs_Action

**Problem:**

Same item deposited multiple times by watchers, causing duplicate triage entries.

**Symptom:**
```
Triage found 2 identical items:
- email-20250203-invoice.md
- email-20250203-invoice-2.md  (duplicate)
```

**Root Cause:**

- Watcher didn't detect existing file before writing
- No deduplication logic in triage
- Multiple agents process same item

**Mitigation:**

```javascript
function deduplicateTriageResults(items) {
  const seen = new Map();

  return items.filter(item => {
    // Create fingerprint (subject + sender + date)
    const fingerprint = `${item.metadata.subject}|${item.metadata.sender}|${item.metadata.received_at}`;

    if (seen.has(fingerprint)) {
      console.warn(`Duplicate detected: ${item.file_name} (matches ${seen.get(fingerprint)})`);
      return false;  // Skip duplicate
    }

    seen.set(fingerprint, item.file_name);
    return true;  // Keep original
  });
}
```

**Prevention:**

- Implement deduplication by content fingerprint
- Watchers should check for existing files before writing
- Use unique IDs (timestamp + hash) for filenames
- Log duplicates for debugging

---

## Gotcha 8: Priority Score Always 10 (Constant Boost)

**Problem:**

All items get maximum priority score due to compounding boosts.

**Symptom:**
```
All 8 items scored as priority 10
```

**Root Cause:**

- Priority factors not balanced
- All items match "urgent" keyword (false positives)
- No normalization or clamping

**Mitigation:**

```javascript
function calculatePriorityScore(content, metadata, category) {
  let score = 3;  // Base: medium priority

  // Factor 1: Keyword boost (+0 to +2, not +5)
  if (hasUrgentKeywords(content)) {
    score += 2;  // Reasonable boost
  }

  // Factor 2: Deadline proximity (+0 to +3)
  score += deadlineBoost(metadata.deadline);

  // Factor 3: Sender importance (+0 to +2)
  score += senderBoost(metadata.sender);

  // Factor 4: Financial threshold (+0 to +3)
  score += financialBoost(metadata.financial_amount, category);

  // Clamp to 1-10 range
  return Math.min(10, Math.max(1, Math.round(score)));
}
```

**Prevention:**

- Limit each factor to reasonable range (+0 to +3 max)
- Base score should be 3 (medium)
- Clamp final score to 1-10 range
- Test with diverse inputs to verify distribution

---

## Gotcha 9: Non-Markdown Files Processed

**Problem:**

Triage attempts to process binary files (.pdf, .docx), causing errors.

**Symptom:**
```
Error parsing file: file-drop-20250203-contract.pdf
Invalid UTF-8 sequence
```

**Root Cause:**

- No file extension validation
- Binary files read as text (garbled content)
- LLM classification fails on binary data

**Mitigation:**

```javascript
function validateFileType(filename) {
  const allowedExtensions = ['.md', '.txt'];
  const ext = path.extname(filename).toLowerCase();

  if (!allowedExtensions.includes(ext)) {
    throw new Error(`Unsupported file type: ${ext} (expected: ${allowedExtensions.join(', ')})`);
  }

  return true;
}
```

**Prevention:**

- Whitelist allowed file extensions (.md, .txt only)
- Reject binary files before reading
- Log warning with filename and extension
- Watchers should convert binary to markdown first

---

## Gotcha 10: Triage Overwrites Manual Metadata

**Problem:**

Running triage again overwrites manual corrections (human changed priority, category).

**Symptom:**
```
Human set priority to 10, but triage reset it to 6
```

**Root Cause:**

- Triage doesn't check for existing metadata
- Blindly overwrites all fields
- No distinction between auto-generated and manual metadata

**Mitigation:**

```javascript
async function triageWithMerge(filePath) {
  // Read existing metadata
  const existingContent = await readFile(filePath);
  const existingMetadata = parseMetadata(existingContent);

  // Run triage
  const triageResult = await classifyAndScore(existingContent);

  // Merge: prefer existing manual fields
  const merged = {
    ...triageResult,
    // Don't overwrite if human set manually
    priority_score: existingMetadata.priority_manual
      ? existingMetadata.priority_score
      : triageResult.priority_score,
    category: existingMetadata.category_manual
      ? existingMetadata.category
      : triageResult.category
  };

  return merged;
}
```

**Prevention:**

- Never overwrite manually-set metadata
- Use `_manual` suffix to flag human edits
- Merge triage results with existing metadata
- Document that manual edits take precedence

---

## Gotcha 11: Timezone Issues with Deadlines

**Problem:**

Deadlines parsed as local time instead of UTC, causing incorrect priority calculations.

**Symptom:**
```
Deadline: 2025-02-03 23:59:59 (parsed as PST, 8 hours off)
Calculated as 'due today' when actually 'due tomorrow'
```

**Root Cause:**

- `new Date()` assumes local timezone
- No explicit UTC conversion
- Priority score boosted incorrectly

**Mitigation:**

```javascript
function parseDeadlineUTC(deadlineString) {
  try {
    // If already ISO 8601 (UTC), use directly
    if (deadlineString.endsWith('Z') || deadlineString.includes('+')) {
      return new Date(deadlineString);
    }

    // Otherwise, assume UTC (not local)
    const date = new Date(deadlineString + 'Z');
    return date;
  } catch (err) {
    console.warn('Invalid deadline format:', deadlineString);
    return null;
  }
}
```

**Prevention:**

- Always parse deadlines as UTC (append 'Z')
- Store all timestamps in ISO 8601 format
- Use `Date.UTC()` for calculations
- Test with various timezone inputs

---

## Gotcha 12: Rate Limits on LLM API

**Problem:**

Triage processes 100 items, hitting LLM API rate limit after 20 requests.

**Symptom:**
```
Error: Rate limit exceeded (429 Too Many Requests)
Remaining 80 items unprocessed
```

**Root Cause:**

- No rate limiting on client side
- Triage processes all items in parallel
- API returns 429 errors

**Mitigation:**

```javascript
const pLimit = require('p-limit');

async function triageWithRateLimit(files) {
  const limit = pLimit(5);  // Max 5 concurrent requests

  const results = await Promise.all(
    files.map(file => limit(() => triageFile(file)))
  );

  return results;
}
```

**Prevention:**

- Limit concurrent LLM requests (5 max)
- Implement exponential backoff for 429 errors
- Fallback to rule-based if rate limited
- Cache LLM results to reduce API calls

---

## Common Error Codes

| Code | Meaning | Recovery |
|------|---------|----------|
| `FILE_TOO_LARGE` | File exceeds 100KB | Skip file, log warning |
| `INVALID_FILE_TYPE` | Non-markdown file | Reject, log error |
| `LOW_CONFIDENCE` | Classification confidence <0.70 | Use fallback category |
| `LLM_API_ERROR` | LLM unavailable or rate limited | Fallback to rule-based |
| `MISSING_METADATA` | Required field not found | Use default value |
| `VAULT_PATH_MISSING` | VAULT_PATH not set in .env | Fatal, abort triage |
| `NEEDS_ACTION_NOT_FOUND` | Needs_Action/ folder missing | Fatal, create folder |

---

## Debugging Tips

1. **Check file size:** `ls -lh Needs_Action/` (reject >100KB)
2. **Validate extensions:** `find Needs_Action -type f ! -name "*.md"`
3. **Test classification:** Run on single file first
4. **Inspect metadata:** Log extracted fields (sanitized!)
5. **Verify confidence:** Check classification confidence scores
6. **Sort output:** Ensure priority descending order
7. **Monitor rate limits:** Track LLM API usage
8. **Review logs:** Look for warnings about skipped files
9. **Test offline:** Disable LLM, verify rule-based fallback
10. **Deduplicate:** Check for duplicate file fingerprints
