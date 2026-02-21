---
classification_id: "{{CLASSIFICATION_ID}}"
transaction_id: "{{TRANSACTION_ID}}"
date: "{{TRANSACTION_DATE}}"
amount: {{AMOUNT}}
currency: "{{CURRENCY}}"
category: "{{CATEGORY}}"
subcategory: "{{SUBCATEGORY}}"
confidence: {{CONFIDENCE}}
status: "{{STATUS}}"
requires_review: {{REQUIRES_REVIEW}}
anomaly_score: {{ANOMALY_SCORE}}
created_at: "{{CREATED_AT}}"
updated_at: "{{UPDATED_AT}}"
---

# Transaction Classification

**Classification ID:** {{CLASSIFICATION_ID}}
**Date:** {{TRANSACTION_DATE}}
**Amount:** {{AMOUNT_FORMATTED}} {{CURRENCY}}
**Merchant:** {{MERCHANT_NAME}}
**Status:** {{STATUS_EMOJI}} {{STATUS}}

---

## Classification Results

**Primary Category:** {{CATEGORY}}
**Subcategory:** {{SUBCATEGORY}}
**Confidence Score:** {{CONFIDENCE_PERCENT}}%

**Reasoning:**
{{REASONING_TEXT}}

---

## Transaction Details

**Transaction ID:** {{TRANSACTION_ID}}
**Account ID:** {{ACCOUNT_ID}}
**Date:** {{TRANSACTION_DATE}}
**Amount:** {{AMOUNT_FORMATTED}} {{CURRENCY}}
**Merchant:** {{MERCHANT_NAME}}
**Description:** {{DESCRIPTION}}
**Transaction Type:** {{TRANSACTION_TYPE}}

{{#if LOCATION}}
**Location:** {{LOCATION}}
{{/if}}

{{#if PAYMENT_METHOD}}
**Payment Method:** {{PAYMENT_METHOD}}
{{/if}}

---

## Suggested Actions

{{#each SUGGESTED_ACTIONS}}
- [ ] {{this}}
{{/each}}

---

## Category Breakdown

**Main Category:** {{CATEGORY}}
- **Definition:** {{CATEGORY_DEFINITION}}
- **Tax Treatment:** {{TAX_TREATMENT}}
- **Budget Impact:** {{BUDGET_IMPACT}}

**Subcategory:** {{SUBCATEGORY}}
- **Typical Merchants:** {{TYPICAL_MERCHANTS}}
- **Spending Trends:** {{SPENDING_TRENDS}}
- **Optimization Tips:** {{OPTIMIZATION_TIPS}}

---

## Anomaly Analysis

**Anomaly Score:** {{ANOMALY_SCORE}} ({{ANOMALY_LEVEL}})
**Risk Level:** {{RISK_LEVEL}}
**Flags:** {{#if ANOMALY_FLAGS}}{{ANOMALY_FLAGS}}{{else}}None{{/if}}

**Analysis:**
{{ANOMALY_ANALYSIS_TEXT}}

{{#if ANOMALY_FLAGS}}
**Anomaly Details:**
{{#each ANOMALY_FLAGS}}
- ⚠️ {{this.flag}}: {{this.description}}
{{/each}}
{{/if}}

---

{{#if HISTORICAL_CONTEXT}}
## Historical Context

**Previous Transactions from this Merchant:**
{{#each PREVIOUS_TRANSACTIONS}}
- {{this.date}}: {{this.amount}} ({{this.category}} - {{this.subcategory}})
{{/each}}

{{#if IS_SUBSCRIPTION}}
**Subscription Metrics:**
- Average monthly charge: {{AVG_MONTHLY_CHARGE}}
- Subscription duration: {{SUBSCRIPTION_DURATION}}
- Charge consistency: {{CHARGE_CONSISTENCY}}
- Price stability: {{PRICE_STABILITY}}
{{/if}}
{{/if}}

---

## Statistical Analysis

{{#if BASELINE_STATS}}
**Baseline Comparison ({{BASELINE_PERIOD}} days):**
- Average transaction in category: {{BASELINE_AVG}}
- Standard deviation: {{BASELINE_STDDEV}}
- Z-score for this transaction: {{Z_SCORE}}σ
- Percentile: {{PERCENTILE}}th percentile

{{#if DEVIATION_ANALYSIS}}
**Deviation Analysis:**
{{DEVIATION_ANALYSIS}}
{{/if}}
{{/if}}

---

## Confidence Factors

**Factors Increasing Confidence:**
{{#each CONFIDENCE_POSITIVE}}
- ✅ {{this}}
{{/each}}

{{#if CONFIDENCE_NEGATIVE}}
**Factors Decreasing Confidence:**
{{#each CONFIDENCE_NEGATIVE}}
- ⚠️ {{this}}
{{/each}}
{{/if}}

---

## Metadata

- **Agent:** {{AGENT_NAME}}
- **Session ID:** {{SESSION_ID}}
- **Classification Model:** {{MODEL_VERSION}}
- **Processing Time:** {{PROCESSING_TIME}}ms
- **Manual Review Required:** {{REQUIRES_REVIEW}}

{{#if SIMILAR_TRANSACTIONS}}
- **Similar Transactions Found:** {{SIMILAR_TRANSACTIONS_COUNT}}
{{/if}}

---

## Approval Workflow

**Review Required:** {{REQUIRES_REVIEW}}

{{#if REQUIRES_REVIEW}}
### Review Instructions

**To Approve:**
1. Update the YAML frontmatter:
   ```yaml
   status: reviewed
   reviewed_by: "Your Name <your.email@company.com>"
   reviewed_at: "{{CURRENT_TIMESTAMP}}"
   ```
2. (Optional) Add review notes below
3. Save the file

**To Reject:**
1. Update the YAML frontmatter:
   ```yaml
   status: rejected
   reviewed_by: "Your Name <your.email@company.com>"
   reviewed_at: "{{CURRENT_TIMESTAMP}}"
   rejection_reason: "Your reason here"
   correct_category: "correct_category_here"
   ```
2. (Optional) Provide detailed reasoning below
3. Save the file

**To Reclassify:**
1. Edit the category/subcategory fields in frontmatter
2. Update confidence score if needed
3. Add reclassification note below
4. Mark status as `reclassified`

---

## Review Notes

<!-- Reviewer: Add your notes here -->
{{/if}}

---

## Classification History

- **v1.0** - {{CREATED_AT}} - Initial classification{{#if AUTO_APPROVED}} (auto-approved, confidence: {{CONFIDENCE_PERCENT}}%){{/if}}
{{#each VERSION_HISTORY}}
- **v{{this.version}}** - {{this.timestamp}} - {{this.change_description}}
{{/each}}

---

## Audit Trail

- **Classification ID:** {{CLASSIFICATION_ID}}
- **Transaction ID:** {{TRANSACTION_ID}}
- **Classified By:** {{AGENT_NAME}}
- **Classified At:** {{CREATED_AT}}
- **Last Updated:** {{UPDATED_AT}}
- **Session ID:** {{SESSION_ID}}
- **Classifier Version:** v{{SKILL_VERSION}}

{{#if AUDIT_LOG_ID}}
- **Audit Log ID:** {{AUDIT_LOG_ID}}
- **Audit Log Path:** {{AUDIT_LOG_PATH}}
{{/if}}

---

{{#if RELATED_DOCUMENTS}}
## Related Documents

{{#each RELATED_DOCUMENTS}}
- [{{this.title}}]({{this.path}})
{{/each}}
{{/if}}

---

**Generated by Transaction Classifier Skill v{{SKILL_VERSION}}**
