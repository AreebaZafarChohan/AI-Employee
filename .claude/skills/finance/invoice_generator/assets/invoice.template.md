---
invoice_id: "{{INVOICE_ID}}"
invoice_number: "{{INVOICE_NUMBER}}"
invoice_date: "{{INVOICE_DATE}}"
due_date: "{{DUE_DATE}}"
status: "{{STATUS}}"
client_id: "{{CLIENT_ID}}"
client_name: "{{CLIENT_NAME}}"
subtotal: {{SUBTOTAL}}
tax_rate: {{TAX_RATE}}
tax_amount: {{TAX_AMOUNT}}
discount_amount: {{DISCOUNT_AMOUNT}}
expense_total: {{EXPENSE_TOTAL}}
total: {{TOTAL}}
amount_paid: {{AMOUNT_PAID}}
balance_due: {{BALANCE_DUE}}
currency: "{{CURRENCY}}"
payment_terms: "{{PAYMENT_TERMS}}"
created_at: "{{CREATED_AT}}"
updated_at: "{{UPDATED_AT}}"
sent_at: {{SENT_AT}}
paid_at: {{PAID_AT}}
---

# INVOICE

**Invoice Number:** {{INVOICE_NUMBER}}
**Invoice Date:** {{INVOICE_DATE_FORMATTED}}
**Due Date:** {{DUE_DATE_FORMATTED}}
**Payment Terms:** {{PAYMENT_TERMS}}

{{#if IS_CREDIT_NOTE}}
**Type:** CREDIT NOTE (Refund)
**Original Invoice:** {{ORIGINAL_INVOICE}}
**Reason:** {{CREDIT_NOTE_REASON}}
{{/if}}

---

## Bill From

**{{COMPANY_NAME}}**
{{COMPANY_ADDRESS}}
Email: {{COMPANY_EMAIL}}
Phone: {{COMPANY_PHONE}}
{{#if TAX_ID}}Tax ID: {{TAX_ID}}{{/if}}

---

## Bill To

**{{CLIENT_NAME}}**
{{#if CLIENT_CONTACT_PERSON}}Attn: {{CLIENT_CONTACT_PERSON}}{{/if}}
{{CLIENT_ADDRESS}}
Email: {{CLIENT_EMAIL}}
{{#if CLIENT_PHONE}}Phone: {{CLIENT_PHONE}}{{/if}}
{{#if CLIENT_ID}}Client ID: {{CLIENT_ID}}{{/if}}
{{#if CLIENT_VAT_NUMBER}}VAT Number: {{CLIENT_VAT_NUMBER}}{{/if}}

---

{{#if PROJECT_INFO}}
## Project Information

**Project Name:** {{PROJECT_NAME}}
**Project ID:** {{PROJECT_ID}}
{{#if PROJECT_MILESTONE}}**Milestone:** {{PROJECT_MILESTONE}}{{/if}}
{{#if PROJECT_DESCRIPTION}}**Description:** {{PROJECT_DESCRIPTION}}{{/if}}

---

{{/if}}

## Line Items

| Description | Quantity | Unit | Rate | Amount |
|-------------|----------|------|------|--------|
{{#each LINE_ITEMS}}
| {{this.description}}{{#if this.date_range}}<br>*{{this.date_range}}*{{/if}}{{#if this.details}}<br>{{#each this.details}}- {{this}}<br>{{/each}}{{/if}} | {{this.quantity}} | {{this.unit}} | {{this.rate_formatted}} | {{this.amount_formatted}} |
{{/each}}

{{#if EXPENSES}}

---

## Reimbursable Expenses

| Description | Date | Category | Receipt | Amount |
|-------------|------|----------|---------|--------|
{{#each EXPENSES}}
| {{this.description}} | {{this.date}} | {{this.category}} | {{#if this.receipt_number}}{{this.receipt_number}}{{else}}N/A{{/if}} | {{this.amount_formatted}} |
{{/each}}

{{/if}}

---

## Invoice Summary

| Description | Amount |
|-------------|--------|
| **Subtotal** | {{SUBTOTAL_FORMATTED}} |
{{#if EXPENSES}}
| Expenses | {{EXPENSE_TOTAL_FORMATTED}} |
{{/if}}
{{#if TAX_AMOUNT_VALUE}}
| **{{TAX_LABEL}} ({{TAX_RATE_PERCENT}}%)** | {{TAX_AMOUNT_FORMATTED}} |
{{/if}}
{{#if DISCOUNT_AMOUNT_VALUE}}
| **Discount** | -{{DISCOUNT_AMOUNT_FORMATTED}} |
{{/if}}
| **Total Due** | **{{TOTAL_FORMATTED}}** |
{{#if AMOUNT_PAID_VALUE}}
| Amount Paid | -{{AMOUNT_PAID_FORMATTED}} |
| **Balance Due** | **{{BALANCE_DUE_FORMATTED}}** |
{{/if}}

---

## Payment Information

**Payment Terms:** {{PAYMENT_TERMS}}
**Due Date:** {{DUE_DATE_FORMATTED}}
{{#if INVOICE_STATUS}}**Status:** {{INVOICE_STATUS}}{{/if}}

{{#if EARLY_PAYMENT_DISCOUNT}}

### Early Payment Discount Available

Pay by **{{DISCOUNT_DEADLINE_DATE}}** ({{DISCOUNT_PERIOD_DAYS}} days) and receive a **{{EARLY_PAYMENT_DISCOUNT}}%** discount!

**Discounted Total:** {{DISCOUNTED_TOTAL_FORMATTED}}
**Savings:** {{DISCOUNT_SAVINGS_FORMATTED}}

{{/if}}

**Payment Methods:**

{{#if BANK_TRANSFER_INFO}}
- **Bank Transfer:**
  - Account Name: {{BANK_ACCOUNT_NAME}}
  - Account Number: {{BANK_ACCOUNT_NUMBER}}
  - Routing Number: {{BANK_ROUTING_NUMBER}}
  - Reference: {{INVOICE_NUMBER}}
{{/if}}

{{#if WIRE_TRANSFER_INFO}}
- **Wire Transfer:**
  - SWIFT: {{SWIFT_CODE}}
  - Account: {{WIRE_ACCOUNT_NUMBER}}
  - Reference: {{INVOICE_NUMBER}}
{{/if}}

{{#if CHECK_PAYMENT_INFO}}
- **Check:**
  - Payable to: {{COMPANY_NAME}}
  - Mail to: {{CHECK_MAILING_ADDRESS}}
  - Memo: {{INVOICE_NUMBER}}
{{/if}}

{{#if PAYMENT_LINK}}
- **Online Payment:**
  - [Pay Invoice Online]({{PAYMENT_LINK}})
{{/if}}

{{#if INTERNATIONAL_PAYMENT}}

### International Payment Information

**For international wire transfers:**
- IBAN: {{IBAN}}
- BIC/SWIFT: {{SWIFT_CODE}}
- Bank Name: {{BANK_NAME}}
- Bank Address: {{BANK_ADDRESS}}

{{/if}}

---

## Notes

{{#if CUSTOM_NOTES}}
{{#each CUSTOM_NOTES}}
{{this}}

{{/each}}
{{/if}}

Thank you for your business! Payment is due within {{PAYMENT_DAYS}} days of the invoice date.{{#if LATE_FEE_PERCENT}} Late payments may incur a {{LATE_FEE_PERCENT}}% monthly fee.{{/if}}

If you have any questions regarding this invoice, please contact us at {{COMPANY_EMAIL}} or {{COMPANY_PHONE}}.

{{#if SUBSCRIPTION_INFO}}

---

## Subscription Details

**Plan:** {{SUBSCRIPTION_PLAN}}
**Billing Cycle:** {{SUBSCRIPTION_BILLING_CYCLE}}
**Current Period:** {{SUBSCRIPTION_PERIOD}}
**Next Billing Date:** {{NEXT_BILLING_DATE}}
{{#if AUTO_CHARGE}}**Auto-charge:** Enabled (payment method on file will be charged automatically){{/if}}

{{/if}}

{{#if RECURRING_INFO}}

---

## Recurring Invoice Information

**Recurring Invoice ID:** {{RECURRING_INVOICE_ID}}
**Billing Period:** {{BILLING_PERIOD}}
**Retainer Hours:** {{RETAINER_HOURS}}
{{#if ROLLOVER_HOURS}}**Rollover Hours from Previous Period:** {{ROLLOVER_HOURS}}{{/if}}
**Next Invoice Date:** {{NEXT_INVOICE_DATE}}

{{/if}}

---

## Terms and Conditions

1. **Payment Terms:** Payment is due within {{PAYMENT_DAYS}} days of the invoice date ({{PAYMENT_TERMS}}).
{{#if LATE_FEE_PERCENT}}
2. **Late Fees:** Overdue invoices will incur a late fee of {{LATE_FEE_PERCENT}}% per month{{#if LATE_FEE_GRACE_DAYS}}, applied after a {{LATE_FEE_GRACE_DAYS}}-day grace period{{/if}}.
{{/if}}
{{#if EARLY_PAYMENT_DISCOUNT}}
3. **Early Payment Discount:** Pay within {{DISCOUNT_PERIOD_DAYS}} days and receive a {{EARLY_PAYMENT_DISCOUNT}}% discount.
{{/if}}
4. **Disputes:** Any disputes must be raised within 7 days of invoice date.
5. **Services Rendered:** All services have been completed as agreed upon.
{{#if RETENTION_CLAUSE}}
6. **Record Retention:** This invoice will be retained for {{RETENTION_YEARS}} years as required by law.
{{/if}}
{{#if REVERSE_CHARGE}}
7. **VAT Reverse Charge:** VAT reverse charge applies for EU B2B transactions per Article 196 of Council Directive 2006/112/EC.
{{/if}}

{{#if INCLUDE_TIMESHEET}}

---

## Timesheet Details

{{#each TIMESHEET_GROUPS}}
### {{this.title}} ({{this.total_hours}} hours @ {{this.rate_formatted}}/hr)

| Date | Hours | Description |
|------|-------|-------------|
{{#each this.entries}}
| {{this.date}} | {{this.hours}} | {{this.description}} |
{{/each}}

**Subtotal:** {{this.subtotal_formatted}}

{{/each}}

**Total Hours:** {{TOTAL_HOURS}}
**Total Billable Amount:** {{TIMESHEET_TOTAL_FORMATTED}}

{{/if}}

{{#if EXPENSE_RECEIPTS}}

---

## Expense Documentation

{{#each EXPENSE_RECEIPTS}}
### {{this.description}}

- **Date:** {{this.date}}
- **Amount:** {{this.amount_formatted}}
- **Category:** {{this.category}}
- **Receipt Number:** {{this.receipt_number}}
- **Receipt Path:** {{this.receipt_path}}

{{/each}}

{{/if}}

---

## Metadata

- **Generated By:** {{AGENT_NAME}}{{#if SESSION_ID}} (Session: {{SESSION_ID}}){{/if}}
- **Invoice Generator:** v{{SKILL_VERSION}}
- **Generated At:** {{CREATED_AT}}
{{#if UPDATED_AT_DIFFERENT}}
- **Last Updated:** {{UPDATED_AT}}
{{/if}}

{{#if PDF_GENERATION_HINTS}}

---

## PDF Generation Instructions

To convert this invoice to PDF, use one of the following methods:

### Method 1: Pandoc
```bash
pandoc {{INVOICE_FILENAME}}.md -o {{INVOICE_FILENAME}}.pdf --pdf-engine=xelatex
```

### Method 2: Weasyprint
```bash
# First convert to HTML, then to PDF
pandoc {{INVOICE_FILENAME}}.md -o {{INVOICE_FILENAME}}.html
weasyprint {{INVOICE_FILENAME}}.html {{INVOICE_FILENAME}}.pdf
```

### Method 3: Node.js markdown-pdf
```bash
npm install -g markdown-pdf
markdown-pdf {{INVOICE_FILENAME}}.md
```

### Method 4: Custom Template
Use your company's invoice PDF template system with the data from this file's YAML frontmatter.

{{/if}}

{{#if ODOO_INTEGRATION}}

---

## Odoo ERP Integration

### Odoo Payload Generated

**File:** `{{ODOO_PAYLOAD_PATH}}`

### Option 1: Import via Odoo UI
1. Log in to Odoo ({{ODOO_API_URL}})
2. Go to Accounting → Customers → Invoices
3. Click "Import" and upload `{{ODOO_PAYLOAD_FILENAME}}`
4. Review imported invoice and confirm

### Option 2: Import via API
```bash
curl -X POST "{{ODOO_API_URL}}/jsonrpc" \
  -H "Content-Type: application/json" \
  -d @{{ODOO_PAYLOAD_PATH}}
```

### Option 3: Manual Entry
If automated import is not available, manually create invoice in Odoo with these details:
- **Customer:** {{CLIENT_NAME}} (Partner ID: {{ODOO_PARTNER_ID}})
- **Invoice Date:** {{INVOICE_DATE}}
- **Due Date:** {{DUE_DATE}}
- **Reference:** {{INVOICE_NUMBER}}
- **Line Items:** (see Line Items section above)

{{/if}}

---

## Audit Trail

- **Invoice ID:** {{INVOICE_ID}}
- **Invoice Number:** {{INVOICE_NUMBER}}
- **Client ID:** {{CLIENT_ID}}
- **Generated By:** {{AGENT_NAME}}
- **Generated At:** {{CREATED_AT}}
- **Last Updated:** {{UPDATED_AT}}
{{#if SESSION_ID}}
- **Session ID:** {{SESSION_ID}}
{{/if}}
- **Invoice Generator Version:** v{{SKILL_VERSION}}
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

**Generated by Invoice Generator Skill v{{SKILL_VERSION}}**

{{#if COMPANY_LOGO_PATH}}
![{{COMPANY_NAME}} Logo]({{COMPANY_LOGO_PATH}})
{{/if}}
