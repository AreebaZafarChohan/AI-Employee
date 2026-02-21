---
name: invoice_generator
description: Generate invoice metadata and optionally PDF payload instructions. Supports client billing, hours tracking, and Odoo ERP integration.
---

# Invoice Generator

## Purpose

This skill generates professional invoice metadata and structured data for billing purposes. It processes client information, billable hours, rates, and expenses to create detailed invoice documents with line items, totals, tax calculations, and payment instructions. The skill can also generate Odoo JSON payloads for direct ERP integration and provide PDF generation hints for invoice printing.

## When to Use This Skill

Use `invoice_generator` when:

- **Client billing**: Creating invoices for professional services, consulting, or freelance work
- **Time tracking integration**: Converting logged hours into billable invoices
- **Expense reimbursement**: Adding expense items with receipts to client invoices
- **Recurring invoices**: Generating monthly or quarterly invoices for retainer clients
- **Multi-currency billing**: Creating invoices in different currencies for international clients
- **ERP integration**: Generating Odoo-compatible JSON payloads for automated invoice import
- **Payment tracking**: Creating invoice records with payment status and due dates
- **Tax compliance**: Generating invoices with proper tax calculations and compliance metadata

Do NOT use this skill when:

- **Real-time payment processing**: This skill generates invoice metadata, not payment transactions
- **Large-scale batch invoicing**: For >100 invoices at once (use specialized batch processing tools)
- **Legal contract generation**: Contracts require specialized legal templates
- **Purchase orders**: Use dedicated PO generation skill instead
- **Receipts only**: For simple receipts without line items, use a lighter receipt generator

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"
INVOICE_OUTPUT_PATH="$VAULT_PATH/Invoices"  # Auto-created if missing

# Required: Company information
INVOICE_COMPANY_NAME="Your Company Name"
INVOICE_COMPANY_ADDRESS="123 Main St, City, State, ZIP"
INVOICE_COMPANY_EMAIL="billing@yourcompany.com"
INVOICE_COMPANY_PHONE="+1-555-123-4567"
INVOICE_TAX_ID="12-3456789"  # EIN or VAT number

# Optional: Invoice configuration
INVOICE_DEFAULT_CURRENCY="USD"
INVOICE_DEFAULT_PAYMENT_TERMS="Net 30"        # Net 15, Net 30, Net 60, Due on Receipt
INVOICE_DEFAULT_TAX_RATE="0.08"               # 8% sales tax (decimal format)
INVOICE_LATE_FEE_PERCENT="1.5"                # 1.5% monthly late fee
INVOICE_DISCOUNT_ENABLED="true"               # Enable early payment discounts
INVOICE_EARLY_PAYMENT_DISCOUNT="2.0"          # 2% discount for early payment

# Optional: Numbering and formatting
INVOICE_NUMBER_PREFIX="INV-"                  # Invoice number prefix
INVOICE_NUMBER_START="10001"                  # Starting invoice number
INVOICE_DATE_FORMAT="YYYY-MM-DD"              # Date format in invoices
INVOICE_INCLUDE_LOGO="true"                   # Include company logo path

# Optional: Odoo ERP integration
ODOO_API_URL=""                               # Odoo server URL (if integrating)
ODOO_DATABASE=""                              # Odoo database name
ODOO_ACCOUNT_ID=""                            # Default account ID for invoices
ODOO_JOURNAL_ID=""                            # Default journal ID

# Optional: Output preferences
INVOICE_OUTPUT_FORMAT="markdown"              # markdown | json | html
INVOICE_GENERATE_PDF_HINTS="true"             # Include PDF generation instructions
INVOICE_ATTACH_TIMESHEETS="true"              # Attach detailed timesheet breakdown
INVOICE_INCLUDE_PAYMENT_LINK="false"          # Include online payment link

# Optional: Compliance and audit
INVOICE_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
INVOICE_RETENTION_YEARS="7"                   # Invoice retention period
INVOICE_SESSION_ID=""                         # Current agent session ID
INVOICE_REQUIRE_APPROVAL="false"              # Flag invoices for approval before sending
```

**Secrets Management:**

- Odoo API credentials should be stored separately in secure vault
- Payment gateway API keys (if generating payment links) must be encrypted
- Tax ID and company financial information should be protected
- Client contact details may contain PII (handle per GDPR/CCPA)

**Variable Discovery Process:**
```bash
# Check invoice configuration
cat .env | grep INVOICE_

# Verify Invoices folder exists
test -d "$VAULT_PATH/Invoices" && echo "OK" || mkdir -p "$VAULT_PATH/Invoices"

# Count generated invoices
find "$VAULT_PATH/Invoices" -name 'INV-*.md' | wc -l

# Check latest invoice number
ls "$VAULT_PATH/Invoices" | grep -oP 'INV-\K\d+' | sort -n | tail -1
```

### 2. Network & Topology Implications

**Port Discovery:**

Optional external integrations:
- Odoo API: Port 8069 (HTTP) or 443 (HTTPS)
- Payment gateway API: Port 443 (HTTPS)

**Dependency Topology:**

```
Invoice Generator
  ├── Vault State Manager (file writes to Invoices/)
  │   └── Filesystem (Invoices/ folder)
  ├── Optional: Odoo ERP Integration
  │   └── HTTP/HTTPS → Odoo API (port 8069/443)
  ├── Optional: Time Tracking System
  │   └── Read timesheet data (CSV/JSON)
  └── Optional: Payment Gateway
      └── HTTPS → Payment API (port 443)
```

**Topology Notes:**
- Primary operation: local file generation (no external dependencies required)
- Optional Odoo integration via REST API
- Optional payment gateway integration for payment links
- No database dependencies (flat file storage in vault)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as read-write volume: `-v /host/vault:/vault:rw`
- Ensure `Invoices/` folder is writable
- If using Odoo integration, allow outbound HTTPS to Odoo server
- Expose environment variables for company info (or mount config file)

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for local filesystem operations
- Odoo integration requires API key authentication (HTTP Basic Auth or OAuth)
- Payment gateway requires API key/secret (HTTPS only)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Client PII exposure** | Encrypt client contact information in vault |
| **Financial data leakage** | Never log amounts, rates, or payment details |
| **Invoice tampering** | Generate cryptographic checksums for each invoice |
| **Unauthorized access** | Restrict filesystem permissions to vault directory only |
| **API key exposure** | Store API keys in secure vault, never in invoice files |

**Validation Rules:**

Before generating any invoice:
```javascript
function validateInvoiceData(invoice) {
  // Required fields check
  if (!invoice.client || !invoice.items || invoice.items.length === 0) {
    throw new Error("Invoice missing required fields: client, items");
  }

  // Client validation
  if (!invoice.client.name || !invoice.client.email) {
    throw new Error("Client must have name and email");
  }

  // Email format validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(invoice.client.email)) {
    throw new Error("Invalid client email format");
  }

  // Line items validation
  invoice.items.forEach((item, index) => {
    if (!item.description || !item.quantity || !item.rate) {
      throw new Error(`Line item ${index + 1} missing required fields`);
    }
    if (item.quantity <= 0 || item.rate < 0) {
      throw new Error(`Line item ${index + 1} has invalid quantity or rate`);
    }
  });

  // Invoice number validation
  if (invoice.invoice_number && !/^[A-Z0-9-]+$/.test(invoice.invoice_number)) {
    throw new Error("Invoice number must contain only uppercase letters, numbers, and hyphens");
  }

  return true;
}
```

---

## Usage Patterns

### Pattern 1: Simple Hourly Service Invoice

**Use Case:** Generating an invoice for consulting services based on tracked hours

**Input:**
```javascript
const { generateInvoice } = require('./invoice_generator');

const invoice = await generateInvoice({
  client: {
    name: "Acme Corporation",
    email: "billing@acme.com",
    address: "456 Business Ave, Suite 200, New York, NY 10001",
    contact_person: "Jane Smith",
    client_id: "CLIENT-001"
  },
  items: [
    {
      description: "Software Development - Frontend",
      quantity: 40,
      unit: "hours",
      rate: 150.00,
      date_range: "2025-01-01 to 2025-01-15"
    },
    {
      description: "Software Development - Backend",
      quantity: 30,
      unit: "hours",
      rate: 175.00,
      date_range: "2025-01-01 to 2025-01-15"
    },
    {
      description: "Project Management",
      quantity: 10,
      unit: "hours",
      rate: 125.00,
      date_range: "2025-01-01 to 2025-01-15"
    }
  ],
  options: {
    payment_terms: "Net 30",
    due_date: "2025-03-04",
    tax_rate: 0.08,
    currency: "USD",
    include_timesheet: true
  },
  metadata: {
    agent: "lex",
    session_id: "session_inv_001",
    timestamp: "2025-02-04T10:00:00Z"
  }
});

console.log(`Invoice generated: ${invoice.invoice_number}`);
console.log(`Total amount: ${invoice.total_formatted}`);
console.log(`File path: ${invoice.file_path}`);
```

**Output File:** `Invoices/INV-10001-acme-corporation.md`

**File Content:**
```markdown
---
invoice_id: INV-10001
invoice_number: INV-10001
invoice_date: 2025-02-04
due_date: 2025-03-04
status: draft
client_id: CLIENT-001
client_name: Acme Corporation
subtotal: 11500.00
tax_rate: 0.08
tax_amount: 920.00
total: 12420.00
currency: USD
payment_terms: Net 30
created_at: 2025-02-04T10:00:00Z
---

# INVOICE

**Invoice Number:** INV-10001
**Invoice Date:** February 4, 2025
**Due Date:** March 4, 2025
**Payment Terms:** Net 30

---

## Bill From

**Your Company Name**
123 Main St
City, State, ZIP
Email: billing@yourcompany.com
Phone: +1-555-123-4567
Tax ID: 12-3456789

---

## Bill To

**Acme Corporation**
Attn: Jane Smith
456 Business Ave, Suite 200
New York, NY 10001
Email: billing@acme.com
Client ID: CLIENT-001

---

## Line Items

| Description | Quantity | Unit | Rate | Amount |
|-------------|----------|------|------|--------|
| Software Development - Frontend<br>*2025-01-01 to 2025-01-15* | 40 | hours | $150.00 | $6,000.00 |
| Software Development - Backend<br>*2025-01-01 to 2025-01-15* | 30 | hours | $175.00 | $5,250.00 |
| Project Management<br>*2025-01-01 to 2025-01-15* | 10 | hours | $125.00 | $1,250.00 |

---

## Invoice Summary

| Description | Amount |
|-------------|--------|
| **Subtotal** | $11,500.00 |
| **Sales Tax (8.0%)** | $920.00 |
| **Total Due** | **$12,420.00** |

---

## Payment Information

**Payment Terms:** Net 30
**Due Date:** March 4, 2025

**Payment Methods:**
- **Bank Transfer:**
  - Account Name: Your Company Name
  - Account Number: XXXX-XXXX-1234
  - Routing Number: 123456789
  - Reference: INV-10001

- **Check:**
  - Payable to: Your Company Name
  - Mail to: 123 Main St, City, State, ZIP
  - Memo: INV-10001

- **Wire Transfer:**
  - SWIFT: ABCDUS33XXX
  - Account: 1234567890
  - Reference: INV-10001

---

## Notes

Thank you for your business! Payment is due within 30 days of the invoice date. Late payments may incur a 1.5% monthly fee.

If you have any questions regarding this invoice, please contact us at billing@yourcompany.com or +1-555-123-4567.

---

## Terms and Conditions

1. **Payment Terms:** Payment is due within 30 days of the invoice date (Net 30).
2. **Late Fees:** Overdue invoices will incur a late fee of 1.5% per month.
3. **Early Payment Discount:** Pay within 10 days and receive a 2% discount.
4. **Disputes:** Any disputes must be raised within 7 days of invoice date.
5. **Services Rendered:** All services have been completed as agreed upon.

---

## Timesheet Details

### Software Development - Frontend (40 hours @ $150/hr)

| Date | Hours | Description |
|------|-------|-------------|
| 2025-01-02 | 8.0 | Implemented user dashboard UI |
| 2025-01-03 | 8.0 | Built responsive navigation component |
| 2025-01-04 | 8.0 | Integrated API endpoints with frontend |
| 2025-01-05 | 8.0 | Added form validation and error handling |
| 2025-01-08 | 8.0 | Completed user profile management page |

### Software Development - Backend (30 hours @ $175/hr)

| Date | Hours | Description |
|------|-------|-------------|
| 2025-01-02 | 6.0 | Designed database schema |
| 2025-01-03 | 8.0 | Implemented REST API endpoints |
| 2025-01-04 | 8.0 | Added authentication and authorization |
| 2025-01-05 | 8.0 | Built data validation and error handling |

### Project Management (10 hours @ $125/hr)

| Date | Hours | Description |
|------|-------|-------------|
| 2025-01-02 | 2.0 | Sprint planning and task breakdown |
| 2025-01-05 | 2.0 | Daily standup meetings |
| 2025-01-08 | 3.0 | Sprint retrospective and documentation |
| 2025-01-12 | 3.0 | Client status updates and planning |

---

## Metadata

- **Generated By:** lex (Local Executive Agent)
- **Session ID:** session_inv_001
- **Invoice Generator:** v1.0
- **Generated At:** 2025-02-04T10:00:00Z

---

**This invoice was automatically generated by Invoice Generator Skill v1.0**
```

---

### Pattern 2: Invoice with Expenses and Odoo Integration

**Use Case:** Creating an invoice with both hourly work and reimbursable expenses, plus Odoo JSON payload

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Tech Startup Inc",
    email: "accounting@techstartup.io",
    address: "789 Innovation Drive, San Francisco, CA 94102",
    client_id: "CLIENT-002"
  },
  items: [
    {
      description: "Consulting Services - System Architecture",
      quantity: 20,
      unit: "hours",
      rate: 200.00,
      type: "service"
    },
    {
      description: "Cloud Infrastructure Setup (AWS)",
      quantity: 1,
      unit: "project",
      rate: 2500.00,
      type: "service"
    }
  ],
  expenses: [
    {
      description: "Flight to client site (SFO to NYC)",
      amount: 485.00,
      date: "2025-01-15",
      category: "travel",
      receipt_path: "receipts/flight-2025-01-15.pdf"
    },
    {
      description: "Hotel accommodation (3 nights)",
      amount: 720.00,
      date: "2025-01-15",
      category: "lodging",
      receipt_path: "receipts/hotel-2025-01-15.pdf"
    },
    {
      description: "Client dinner meeting",
      amount: 180.00,
      date: "2025-01-16",
      category: "meals",
      receipt_path: "receipts/dinner-2025-01-16.pdf"
    }
  ],
  options: {
    payment_terms: "Net 15",
    due_date: "2025-02-19",
    tax_rate: 0.0725,  // 7.25% CA sales tax
    currency: "USD",
    generate_odoo_payload: true,
    odoo_config: {
      partner_id: 47,         // Client's Odoo partner ID
      account_id: 400001,     // Revenue account
      journal_id: 1           // Sales journal
    }
  },
  metadata: {
    agent: "lex",
    session_id: "session_inv_002"
  }
});

console.log(`Invoice: ${invoice.invoice_number}`);
console.log(`Total: ${invoice.total_formatted}`);
console.log(`Odoo payload: ${invoice.odoo_payload_path}`);
```

**Output File 1:** `Invoices/INV-10002-tech-startup-inc.md`

**Output File 2:** `Invoices/INV-10002-odoo-payload.json`

**Odoo JSON Payload Content:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{ODOO_DATABASE}}",
      "{{ODOO_USER_ID}}",
      "{{ODOO_PASSWORD}}",
      "account.move",
      "create",
      {
        "move_type": "out_invoice",
        "partner_id": 47,
        "invoice_date": "2025-02-04",
        "invoice_date_due": "2025-02-19",
        "ref": "INV-10002",
        "journal_id": 1,
        "currency_id": 1,
        "invoice_line_ids": [
          {
            "name": "Consulting Services - System Architecture",
            "quantity": 20.0,
            "price_unit": 200.00,
            "account_id": 400001,
            "tax_ids": [[6, 0, [1]]]
          },
          {
            "name": "Cloud Infrastructure Setup (AWS)",
            "quantity": 1.0,
            "price_unit": 2500.00,
            "account_id": 400001,
            "tax_ids": [[6, 0, [1]]]
          },
          {
            "name": "Expense: Flight to client site (SFO to NYC)",
            "quantity": 1.0,
            "price_unit": 485.00,
            "account_id": 400001,
            "tax_ids": [[6, 0, []]]
          },
          {
            "name": "Expense: Hotel accommodation (3 nights)",
            "quantity": 1.0,
            "price_unit": 720.00,
            "account_id": 400001,
            "tax_ids": [[6, 0, []]]
          },
          {
            "name": "Expense: Client dinner meeting",
            "quantity": 1.0,
            "price_unit": 180.00,
            "account_id": 400001,
            "tax_ids": [[6, 0, []]]
          }
        ],
        "narration": "Invoice for consulting services and reimbursable expenses. Generated by Invoice Generator v1.0."
      }
    ]
  },
  "id": "invoice_generator_INV-10002"
}
```

**Odoo Integration Instructions (included in markdown):**
```markdown
## Odoo ERP Integration

### Option 1: Import via Odoo UI
1. Log in to Odoo ({{ODOO_API_URL}})
2. Go to Accounting → Customers → Invoices
3. Click "Import" and upload `INV-10002-odoo-payload.json`
4. Review imported invoice and confirm

### Option 2: Import via API
```bash
curl -X POST "{{ODOO_API_URL}}/jsonrpc" \
  -H "Content-Type: application/json" \
  -d @Invoices/INV-10002-odoo-payload.json
```

### Option 3: Manual Entry
If automated import is not available, manually create invoice in Odoo with these details:
- Customer: Tech Startup Inc (Partner ID: 47)
- Invoice Date: 2025-02-04
- Due Date: 2025-02-19
- Reference: INV-10002
- Line Items: (see Line Items section above)
```

---

### Pattern 3: Recurring Invoice Generation

**Use Case:** Generating a monthly retainer invoice for ongoing services

**Input:**
```javascript
const invoice = await generateRecurringInvoice({
  client: {
    name: "Enterprise Solutions Ltd",
    email: "ap@enterprise-solutions.com",
    address: "1000 Corporate Plaza, Chicago, IL 60601",
    client_id: "CLIENT-003"
  },
  recurring_config: {
    type: "monthly_retainer",
    start_date: "2025-01-01",
    billing_period: "2025-01-01 to 2025-01-31",
    auto_generate: true
  },
  items: [
    {
      description: "Monthly Retainer - Software Maintenance and Support",
      quantity: 1,
      unit: "month",
      rate: 5000.00,
      type: "retainer"
    },
    {
      description: "Additional Consulting Hours (beyond retainer)",
      quantity: 8,
      unit: "hours",
      rate: 175.00,
      type: "additional"
    }
  ],
  options: {
    payment_terms: "Due on Receipt",
    tax_rate: 0.05,
    currency: "USD",
    early_payment_discount: 2.0,  // 2% discount if paid within 5 days
    discount_period_days: 5
  },
  metadata: {
    agent: "lex",
    session_id: "session_recurring_001",
    recurring_invoice_id: "RECURRING-001"
  }
});

console.log(`Recurring invoice: ${invoice.invoice_number}`);
console.log(`Period: ${invoice.billing_period}`);
console.log(`Next invoice date: ${invoice.next_invoice_date}`);
```

**Output File:** `Invoices/INV-10003-enterprise-solutions-ltd-2025-01.md`

**Markdown includes:**
- Standard invoice sections
- Retainer agreement details
- Rollover hours tracking (if applicable)
- Early payment discount information
- Next scheduled invoice date
- Recurring billing schedule

---

## Key Guarantees

1. **Accurate Calculations**: All line item totals, subtotals, tax, and final totals are mathematically correct
2. **Unique Invoice Numbers**: Sequential invoice numbering with no duplicates
3. **Structured Output**: Consistent markdown format with YAML frontmatter
4. **Compliance Metadata**: Includes all required tax and audit information
5. **PDF Generation Hints**: Clear instructions for converting markdown to PDF
6. **Odoo Integration**: Valid JSON payloads compatible with Odoo ERP API
7. **Payment Tracking**: Status field for tracking draft/sent/paid/overdue states
8. **Audit Trail**: Full metadata tracking of invoice generation and modifications

---

## Output Schema

**Invoice File:**
- **Location:** `Invoices/`
- **Naming:** `INV-{number}-{client-slug}-{optional-period}.md`
- **Format:** Markdown with YAML frontmatter

**Frontmatter Fields:**
```yaml
invoice_id: "INV-10001"
invoice_number: "INV-10001"
invoice_date: "YYYY-MM-DD"
due_date: "YYYY-MM-DD"
status: "draft | sent | paid | overdue | cancelled"
client_id: "CLIENT-XXX"
client_name: "Client Name"
subtotal: 1000.00
tax_rate: 0.08
tax_amount: 80.00
discount_amount: 0.00
total: 1080.00
amount_paid: 0.00
balance_due: 1080.00
currency: "USD"
payment_terms: "Net 30"
created_at: "ISO8601 timestamp"
sent_at: "ISO8601 timestamp or null"
paid_at: "ISO8601 timestamp or null"
```

---

## Supported Features

| Feature | Description | Configuration |
|---------|-------------|---------------|
| **Hourly billing** | Bill by hours with different rates per role | Default |
| **Project billing** | Fixed-price project invoices | `type: "project"` |
| **Retainer billing** | Monthly recurring retainer invoices | `recurring_config` |
| **Expense reimbursement** | Add reimbursable expenses with receipts | `expenses: []` |
| **Multi-currency** | Invoice in USD, EUR, GBP, etc. | `currency: "USD"` |
| **Tax calculation** | Automatic tax calculation | `tax_rate: 0.08` |
| **Early payment discount** | Offer discounts for early payment | `early_payment_discount: 2.0` |
| **Late fees** | Calculate late fees for overdue invoices | `late_fee_percent: 1.5` |
| **Timesheet attachment** | Include detailed timesheet breakdown | `include_timesheet: true` |
| **Odoo integration** | Generate Odoo-compatible JSON payloads | `generate_odoo_payload: true` |
| **PDF hints** | Include PDF generation instructions | `generate_pdf_hints: true` |

---

## Integration Points

**Upstream Skills:**
- `time_event_scheduler` → Schedule recurring invoice generation
- `company_handbook_enforcer` → Ensure invoices comply with financial policies
- `approval_request_creator` → Require approval for high-value invoices

**Downstream Skills:**
- `vault_state_manager` → Store invoices and track payment status
- `email_drafter` → Send invoice emails to clients
- `dashboard_writer` → Display outstanding invoices and revenue metrics

**Related Skills:**
- `transaction_classifier` → Classify incoming payments against invoices

---

## Error Handling

**Common Errors:**

1. **Missing Client Information:**
   ```
   Error: Client name and email are required
   Solution: Provide complete client information
   ```

2. **Invalid Line Items:**
   ```
   Error: Line item missing quantity or rate
   Solution: Ensure all line items have quantity, unit, and rate
   ```

3. **Duplicate Invoice Number:**
   ```
   Error: Invoice number INV-10001 already exists
   Solution: System will auto-increment to next available number
   ```

4. **Invalid Tax Rate:**
   ```
   Error: Tax rate must be between 0 and 1 (decimal format)
   Solution: Use 0.08 for 8%, not 8
   ```

---

## Configuration Examples

### Minimal Configuration:
```bash
VAULT_PATH="/path/to/vault"
INVOICE_COMPANY_NAME="Your Company"
INVOICE_COMPANY_EMAIL="billing@yourcompany.com"
```

### Production Setup:
```bash
VAULT_PATH="/path/to/vault"
INVOICE_COMPANY_NAME="Your Company Name"
INVOICE_COMPANY_ADDRESS="123 Main St, City, State, ZIP"
INVOICE_COMPANY_EMAIL="billing@yourcompany.com"
INVOICE_COMPANY_PHONE="+1-555-123-4567"
INVOICE_TAX_ID="12-3456789"
INVOICE_DEFAULT_TAX_RATE="0.08"
INVOICE_DEFAULT_PAYMENT_TERMS="Net 30"
INVOICE_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
INVOICE_RETENTION_YEARS="7"
```

### With Odoo Integration:
```bash
# ... (all above variables) ...
ODOO_API_URL="https://your-company.odoo.com"
ODOO_DATABASE="production"
ODOO_ACCOUNT_ID="400001"
ODOO_JOURNAL_ID="1"
```

---

## Testing Checklist

Before deploying this skill:

- [ ] Verify `Invoices/` folder exists and is writable
- [ ] Test single invoice generation
- [ ] Test invoice with expenses
- [ ] Test invoice number auto-increment
- [ ] Test tax calculation accuracy
- [ ] Test subtotal/total calculations
- [ ] Test Odoo payload generation (if enabled)
- [ ] Test with missing required fields (expect validation error)
- [ ] Test with invalid email format (expect validation error)
- [ ] Test recurring invoice generation
- [ ] Test early payment discount calculation
- [ ] Test late fee calculation
- [ ] Verify unique invoice ID generation
- [ ] Test PDF generation hints

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - Invoice generation with line items
  - Hourly, project, and retainer billing support
  - Expense reimbursement
  - Tax calculation
  - Odoo JSON payload generation
  - PDF generation hints
  - Early payment discounts
  - Late fee calculation
  - Timesheet attachment
  - Multi-currency support
  - Audit trail integration
