# Silver Process Engine — Risk Scoring Enhancement ✅

## Summary

Enhanced the `silver_process_engine` skill with a sophisticated risk scoring system including confidence levels and detailed factor tracking.

---

## Changes Made

### 1. Risk Scoring Rules Implemented

| Rule | Condition | Score Impact |
|------|-----------|--------------|
| **Financial > $100** | Amount extracted from content/metadata > $100 | +50 (HIGH risk) |
| **Financial > $0** | Any amount mentioned | +20 |
| **Unknown Sender** | Sender not in internal domains | +25 (MEDIUM risk) |
| **Known Sender** | Sender from internal domain | +5 |
| **Urgent Keywords** | "urgent", "asap", "immediately", "rush", "deadline" | +25 (MEDIUM risk) |
| **Risk Keywords** | "legal", "payment", "password", "terminate", "critical" | +30 |
| **High Priority** | `priority: high` in frontmatter | +30 |
| **Medium Priority** | `priority: medium` in frontmatter | +20 |
| **Low Priority** | `priority: low` in frontmatter | +10 |
| **Internal File Drop** | file_drop + known sender | -20 |

### 2. Base Scores by Type

| Item Type | Base Score |
|-----------|------------|
| email     | +20        |
| file_drop | +30        |
| whatsapp  | +25        |

### 3. Risk Level Thresholds

| Score Range | Risk Level | Approval Required |
|-------------|------------|-------------------|
| 0-39        | **LOW**    | No                |
| 40-69       | **MEDIUM** | Yes               |
| 70-100      | **HIGH**   | Yes               |

### 4. Confidence Score Calculation

- **Base:** 60%
- **+10%** for each available factor:
  - Sender information present
  - Priority field present
  - Financial amount detected
  - Content available for analysis
- **Maximum:** 100%

---

## Updated Files

| File | Changes |
|------|---------|
| `silver_process_engine.py` | Added risk scoring functions, confidence calculation, amount extraction |
| `SKILL.md` | Updated risk classification rules, added scoring table, examples |
| `test_risk_scoring.py` | New test script for validation |

---

## Test Results

### Test 1: HIGH RISK Email ✅
```
From: external@gmail.com
Priority: high
Amount: $500
Content: "Urgent! Payment of $500 needed immediately"

Result:
- Risk Level: HIGH
- Confidence: 100%
- Score: 100/100
- Factors: email (+20), high priority (+30), amount >$100 (+50), 
           unknown sender (+25), urgent keywords (+25), risk keywords (+30)
```

### Test 2: LOW RISK Internal File ✅
```
From: john@company.com
Type: file_drop
Content: "Monthly report attached"

Result:
- Risk Level: LOW
- Confidence: 80%
- Score: 15/100
- Factors: file_drop (+30), known sender (+5), internal file_drop (-20)
```

### Test 3: MEDIUM RISK Email ✅
```
From: client@external.com
Priority: medium
Content: "Question about the project"

Result:
- Risk Level: MEDIUM
- Confidence: 90%
- Score: 65/100
- Factors: email (+20), medium priority (+20), unknown sender (+25)
```

### Test 4: Amount Detection from Content ✅
```
From: vendor@external.com
Content: "Please pay $150 for the invoice"

Result:
- Risk Level: HIGH
- Confidence: 90%
- Score: 100/100
- Factors: email (+20), amount >$100 (+50), unknown sender (+25), risk keywords (+30)
```

---

## Updated Plan File Format

### Frontmatter (New Fields)

```yaml
---
plan_id: abc12345
source_file: email-urgent-payment.md
item_type: email
risk_level: high
risk_score: 100          # NEW: 0-100 score
confidence_score: 95     # NEW: 0-100%
requires_approval: true
status: pending_approval
created_at: "2026-02-25T12:00:00Z"
---
```

### Risk Level Section (New Format)

```markdown
## Risk Level
**HIGH** (Score: 100/100, Confidence: 95%)

**Risk Score:** 100/100
**Confidence:** 95%

**Factors:**
  - email type (+20)
  - high priority (+30)
  - amount $500.00 > $100.0 (+50)
  - unknown sender (+25)
  - urgent keywords (+25)
  - risk keywords present (+30)

High priority item — requires careful handling and explicit approval.
```

---

## New Functions Added

### `_extract_amount(content, meta) -> float`
Extracts financial amounts from:
- Metadata `amount` field
- Content patterns: `$100`, `USD 100`, `100 dollars`

### `_is_unknown_sender(meta) -> bool`
Checks if sender is from external domain:
- Internal domains: `company.com`, `internal`, `localhost`
- Returns `True` for unknown/external senders

### `_has_urgent_keywords(content) -> bool`
Detects urgency indicators:
- Keywords: `urgent`, `asap`, `immediately`, `rush`, `deadline`, `today only`

### `classify_risk(item_type, meta, content) -> tuple`
Returns:
- `risk_level`: 'low' | 'medium' | 'high'
- `confidence_score`: 0-100
- `risk_factors`: dict with scoring breakdown

---

## Benefits

1. **Transparent Decision Making** — Every risk factor is logged and visible
2. **Confidence Tracking** — Know how certain the assessment is
3. **Financial Protection** — Automatic high risk for amounts >$100
4. **Sender Verification** — External senders get higher scrutiny
5. **Keyword Detection** — Urgent and risk keywords escalate appropriately
6. **Audit Trail** — Full factor breakdown in plan files

---

## Usage

```bash
# Run the enhanced engine
python .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py

# Debug mode (see risk factors in logs)
SILVER_PE_LOG_LEVEL=DEBUG python ...

# Dry run (test without writing files)
SILVER_PE_DRY_RUN=true python ...
```

---

## Backward Compatibility

- Existing plans without `risk_score` and `confidence_score` still work
- Default values provided for optional parameters
- Old risk classification logic replaced with scored system

---

**Status: Production Ready** 🚀

All tests passed. Risk scoring system fully operational.
