# Invoice Generator - Patterns and Best Practices

Common patterns and best practices for using the invoice generator skill effectively.

---

## Pattern 1: Hourly Billing Workflow

**When to use:** Consulting, freelance, or agency work billed by the hour

**Best Practices:**
1. Track time daily in a time tracking system
2. Group hours by role, rate, or project phase
3. Include date ranges for each line item
4. Attach detailed timesheet for transparency
5. Round hours consistently (to nearest 0.25, 0.5, or 1.0)

**Example:**
```javascript
const timeEntries = await fetchTimeEntries({
  client_id: "CLIENT-001",
  period: "2025-01-01 to 2025-01-31",
  billable: true
});

const lineItems = groupByRole(timeEntries).map(group => ({
  description: `${group.role} - ${group.description}`,
  quantity: group.total_hours,
  unit: "hours",
  rate: group.rate,
  date_range: formatDateRange(group.start_date, group.end_date)
}));

const invoice = await generateInvoice({
  client: clientInfo,
  items: lineItems,
  options: {
    include_timesheet: true,
    payment_terms: "Net 30"
  }
});
```

**Common Pitfalls:**
- ❌ Not rounding hours consistently
- ❌ Forgetting to mark non-billable time
- ❌ Mixing different billing periods in one invoice
- ✅ Always include date ranges for clarity

---

## Pattern 2: Project Milestone Billing

**When to use:** Fixed-price projects with deliverable-based payments

**Best Practices:**
1. Define clear milestones upfront in contract
2. Tie each invoice to specific deliverables
3. Include milestone descriptions and acceptance criteria
4. Track project progress separately from invoicing
5. Invoice only upon milestone completion/approval

**Example:**
```javascript
const milestones = [
  { name: "Discovery & Planning", percent: 20, amount: 10000 },
  { name: "Design & Prototyping", percent: 30, amount: 15000 },
  { name: "Development", percent: 40, amount: 20000 },
  { name: "Testing & Launch", percent: 10, amount: 5000 }
];

// Invoice Milestone 2
const invoice = await generateInvoice({
  client: clientInfo,
  project: {
    name: "Website Redesign Project",
    project_id: "PROJ-2025-001",
    milestone: "Milestone 2: Design & Prototyping Complete"
  },
  items: [{
    description: "Website Redesign - Milestone 2: Design & Prototyping",
    quantity: 1,
    unit: "milestone",
    rate: 15000.00,
    details: [
      "Wireframes for all 15 pages",
      "High-fidelity mockups",
      "Interactive prototype",
      "Design system documentation",
      "2 rounds of client revisions"
    ]
  }],
  options: {
    payment_terms: "Net 15"
  },
  notes: [
    "Milestone 2 of 4 completed as of 2025-01-31.",
    "Client approval received on 2025-01-28.",
    "Next milestone: Development (estimated start: 2025-02-05)"
  ]
});
```

**Common Pitfalls:**
- ❌ Invoicing before milestone approval
- ❌ Vague milestone descriptions
- ❌ Not documenting deliverables completed
- ✅ Get written milestone acceptance before invoicing

---

## Pattern 3: Monthly Retainer with Overages

**When to use:** Ongoing support/maintenance agreements with a fixed monthly fee plus additional work

**Best Practices:**
1. Clearly define included retainer hours
2. Specify overage rate (often higher than retainer rate)
3. Track retainer vs. overage hours separately
4. Consider rollover policy for unused hours
5. Invoice on consistent day each month
6. Set up recurring invoice automation

**Example:**
```javascript
const retainerConfig = {
  monthly_hours: 40,
  retainer_rate: 5000,  // $125/hour effective rate
  overage_rate: 175,    // Higher rate for extra work
  rollover_enabled: true,
  max_rollover_hours: 10
};

const monthlyUsage = await getMonthlyUsage("CLIENT-004", "2025-01");

const items = [
  {
    description: `Monthly Retainer - Technical Support (${retainerConfig.monthly_hours} hours included)`,
    quantity: 1,
    unit: "month",
    rate: retainerConfig.retainer_rate,
    type: "retainer"
  }
];

// Add overage line item if applicable
if (monthlyUsage.hours > retainerConfig.monthly_hours) {
  const overageHours = monthlyUsage.hours - retainerConfig.monthly_hours;
  items.push({
    description: "Additional Hours (beyond retainer)",
    quantity: overageHours,
    unit: "hours",
    rate: retainerConfig.overage_rate,
    type: "overage"
  });
}

// Add rollover notice
const notes = [];
if (monthlyUsage.rollover_hours > 0) {
  notes.push(`${monthlyUsage.rollover_hours} unused hours rolled over from previous month.`);
}

const invoice = await generateInvoice({
  client: clientInfo,
  recurring_config: {
    type: "monthly_retainer",
    billing_period: "2025-01-01 to 2025-01-31"
  },
  items: items,
  options: {
    payment_terms: "Due on Receipt"
  },
  notes: notes,
  metadata: {
    recurring_invoice_id: "RECURRING-004",
    next_invoice_date: "2025-03-01"
  }
});
```

**Common Pitfalls:**
- ❌ Not tracking retainer vs. overage hours separately
- ❌ Unclear rollover policy
- ❌ Not communicating when approaching retainer limit
- ✅ Send monthly usage reports before invoice

---

## Pattern 4: Expense Reimbursement Integration

**When to use:** Client work requiring travel or other reimbursable expenses

**Best Practices:**
1. Get pre-approval for major expenses
2. Keep all receipts (digital copies)
3. Categorize expenses clearly
4. Don't apply tax to reimbursable expenses
5. Include receipt references in invoice
6. Consider expense limit policies

**Example:**
```javascript
const expenses = await fetchExpenses({
  client_id: "CLIENT-003",
  period: "2025-01-01 to 2025-01-31",
  approved: true
});

const expenseItems = expenses.map(exp => ({
  description: exp.description,
  amount: exp.amount,
  date: exp.date,
  category: exp.category,
  receipt_path: exp.receipt_path,
  receipt_number: exp.receipt_number
}));

const invoice = await generateInvoice({
  client: clientInfo,
  items: [
    {
      description: "Consulting Services",
      quantity: 24,
      unit: "hours",
      rate: 250.00
    }
  ],
  expenses: expenseItems,
  options: {
    tax_rate: 0.08,
    tax_applies_to: ["services"],  // Tax only services, not expenses
    payment_terms: "Net 30"
  }
});
```

**Expense Categories:**
- **Travel:** Flights, trains, rental cars, gas
- **Lodging:** Hotels, Airbnb
- **Transportation:** Taxis, Uber, parking
- **Meals:** Client dinners, team lunches
- **Equipment:** Hardware/software purchased for project
- **Other:** Supplies, printing, shipping

**Common Pitfalls:**
- ❌ Not getting pre-approval for large expenses
- ❌ Missing receipt documentation
- ❌ Applying tax to non-taxable expense reimbursements
- ✅ Document expense policy in client agreement

---

## Pattern 5: Multi-Currency International Billing

**When to use:** Billing international clients in their local currency

**Best Practices:**
1. Agree on currency upfront in contract
2. Document exchange rate and date used
3. Consider currency hedging for large projects
4. Understand local tax implications (VAT, GST, etc.)
5. Include reverse charge notice for EU B2B
6. Provide payment instructions for international transfers

**Example:**
```javascript
const exchangeRates = await getExchangeRates("2025-02-04");

const invoice = await generateInvoice({
  client: {
    name: "European Tech GmbH",
    email: "buchhaltung@europeantech.de",
    address: "Hauptstraße 123, 10115 Berlin, Germany",
    vat_number: "DE123456789"
  },
  items: [
    {
      description: "Software Development Services",
      quantity: 80,
      unit: "hours",
      rate: 140.00  // EUR rate
    }
  ],
  options: {
    currency: "EUR",
    tax_rate: 0.19,  // 19% German VAT
    include_reverse_charge: true,  // EU B2B reverse charge
    exchange_rate_info: {
      reference_currency: "USD",
      rate: exchangeRates.EUR_USD,
      date: "2025-02-04"
    },
    international_payment: {
      iban: "DE89370400440532013000",
      swift: "COBADEFFXXX",
      bank_name: "Commerzbank AG",
      bank_address: "Frankfurt, Germany"
    }
  }
});
```

**Tax Considerations by Region:**

| Region | Tax Type | Rate | Notes |
|--------|----------|------|-------|
| **EU (B2B)** | VAT | 19-25% | Reverse charge applies |
| **EU (B2C)** | VAT | 19-25% | Must charge VAT |
| **US** | Sales Tax | 0-10% | Varies by state |
| **UK** | VAT | 20% | Post-Brexit rules |
| **Canada** | GST/HST | 5-15% | Varies by province |
| **Australia** | GST | 10% | Registration required |

**Common Pitfalls:**
- ❌ Not understanding local tax rules
- ❌ Using stale exchange rates
- ❌ Missing VAT registration requirements
- ✅ Consult with international tax advisor

---

## Pattern 6: Subscription/SaaS Billing Automation

**When to use:** Recurring monthly/annual SaaS subscriptions

**Best Practices:**
1. Automate invoice generation on billing date
2. Include usage-based charges in same invoice
3. Provide subscription management portal
4. Send invoice before auto-charge
5. Handle failed payments gracefully
6. Pro-rate for plan changes mid-cycle

**Example:**
```javascript
const subscription = await getSubscription("SUB-008");

// Calculate usage charges
const usageCharges = await calculateUsage({
  subscription_id: "SUB-008",
  period: "2025-02-01 to 2025-02-28"
});

const items = [
  {
    description: `${subscription.plan} Subscription (${subscription.user_count} users)`,
    quantity: 1,
    unit: "month",
    rate: subscription.base_price,
    type: "subscription"
  }
];

// Add usage-based charges
if (usageCharges.api_calls > subscription.included_api_calls) {
  items.push({
    description: `API Usage Overage (${usageCharges.api_calls - subscription.included_api_calls} calls)`,
    quantity: usageCharges.api_calls - subscription.included_api_calls,
    unit: "API calls",
    rate: subscription.overage_rate,
    type: "usage"
  });
}

// Add add-ons
subscription.addons.forEach(addon => {
  items.push({
    description: addon.name,
    quantity: 1,
    unit: "month",
    rate: addon.price,
    type: "addon"
  });
});

const invoice = await generateInvoice({
  client: subscription.client,
  subscription: {
    plan: subscription.plan,
    billing_cycle: "monthly",
    period: "2025-02-01 to 2025-02-28"
  },
  items: items,
  options: {
    payment_terms: "Due on Receipt",
    auto_charge: true,
    currency: "USD"
  },
  metadata: {
    subscription_id: subscription.id,
    next_billing_date: "2025-03-01"
  }
});

// Auto-charge payment method on file
await chargePaymentMethod(subscription.payment_method_id, invoice.total);
```

**Common Pitfalls:**
- ❌ Not sending invoice before auto-charge
- ❌ Poor failed payment retry logic
- ❌ Not pro-rating plan changes
- ✅ Provide usage dashboards for transparency

---

## Pattern 7: Approval Workflow for High-Value Invoices

**When to use:** Enterprise clients or internal approval policies

**Best Practices:**
1. Define approval threshold ($10K+)
2. Route to appropriate approver
3. Track approval status
4. Don't send invoice until approved
5. Log approval in audit trail
6. Notify stakeholders of approval

**Example:**
```javascript
const APPROVAL_THRESHOLD = 10000;

const invoice = await generateInvoice({
  client: clientInfo,
  items: lineItems,
  options: {
    payment_terms: "Net 45"
  }
});

// Check if approval needed
if (invoice.total > APPROVAL_THRESHOLD) {
  // Set status to pending approval
  await updateInvoiceStatus(invoice.invoice_number, "pending_approval");

  // Create approval request
  const approval = await createApprovalRequest({
    type: "invoice_approval",
    subject: `Approve Invoice ${invoice.invoice_number} - ${invoice.client.name}`,
    amount: invoice.total_formatted,
    details: {
      client: invoice.client.name,
      total: invoice.total,
      line_items_count: invoice.items.length,
      invoice_path: invoice.file_path
    },
    approvers: ["finance_manager@company.com"],
    metadata: {
      invoice_number: invoice.invoice_number
    }
  });

  console.log(`⏳ Approval required: ${approval.approval_id}`);

  // Wait for approval (async)
  approval.on("approved", async (result) => {
    await updateInvoiceStatus(invoice.invoice_number, "approved");
    await sendInvoiceEmail(invoice);
    console.log(`✅ Invoice ${invoice.invoice_number} approved and sent`);
  });

  approval.on("rejected", async (result) => {
    await updateInvoiceStatus(invoice.invoice_number, "rejected");
    console.log(`❌ Invoice ${invoice.invoice_number} rejected: ${result.reason}`);
  });
} else {
  // Below threshold, send immediately
  await sendInvoiceEmail(invoice);
  console.log(`✅ Invoice ${invoice.invoice_number} sent (no approval required)`);
}
```

**Common Pitfalls:**
- ❌ Sending invoice before approval
- ❌ No escalation for delayed approvals
- ❌ Unclear approval criteria
- ✅ Define clear approval policies

---

## Pattern 8: Payment Tracking Integration

**When to use:** Connecting invoices with incoming payments

**Best Practices:**
1. Update invoice status when paid
2. Match payments to invoices automatically
3. Handle partial payments
4. Send payment confirmation
5. Update accounts receivable dashboard
6. Archive paid invoices

**Example:**
```javascript
// When payment received
const payment = await receivePayment({
  amount: 6480.00,
  reference: "INV-10001",
  payment_date: "2025-02-28",
  payment_method: "bank_transfer"
});

// Match payment to invoice
const invoice = await findInvoiceByNumber(payment.reference);

if (invoice) {
  // Update invoice
  await updateInvoice(invoice.invoice_number, {
    status: "paid",
    amount_paid: payment.amount,
    balance_due: 0,
    paid_at: payment.payment_date
  });

  // Log transaction
  await logTransaction({
    type: "payment_received",
    invoice_number: invoice.invoice_number,
    amount: payment.amount,
    payment_date: payment.payment_date,
    payment_method: payment.payment_method
  });

  // Send confirmation email
  await draftEmail({
    intent: "payment_confirmation",
    recipient: { email: invoice.client.email },
    context: {
      invoice_number: invoice.invoice_number,
      amount: formatCurrency(payment.amount),
      payment_date: payment.payment_date
    }
  });

  // Update dashboard
  await updateDashboard({
    section: "accounts_receivable",
    action: "remove_outstanding_invoice",
    invoice_number: invoice.invoice_number
  });

  console.log(`✅ Payment received for ${invoice.invoice_number}`);
}
```

**Common Pitfalls:**
- ❌ Manual payment matching (error-prone)
- ❌ Not handling partial payments
- ❌ No payment confirmation to client
- ✅ Automate with transaction_classifier skill

---

## Pattern 9: Late Fee Calculation

**When to use:** Enforcing payment terms with overdue invoices

**Best Practices:**
1. Define late fee policy in contract
2. Include late fee terms on invoice
3. Provide grace period (3-5 days)
4. Calculate fees automatically
5. Send overdue reminders before applying fees
6. Issue credit note if fees waived

**Example:**
```javascript
const LATE_FEE_PERCENT = 1.5;  // 1.5% per month
const GRACE_PERIOD_DAYS = 5;

// Check for overdue invoices daily
const overdueInvoices = await getOverdueInvoices();

for (const invoice of overdueInvoices) {
  const daysOverdue = getDaysOverdue(invoice.due_date);

  if (daysOverdue > GRACE_PERIOD_DAYS) {
    // Calculate late fee
    const monthsOverdue = Math.ceil(daysOverdue / 30);
    const lateFee = invoice.total * (LATE_FEE_PERCENT / 100) * monthsOverdue;

    // Send overdue notice
    await draftEmail({
      intent: "overdue_notice",
      recipient: { email: invoice.client.email },
      context: {
        invoice_number: invoice.invoice_number,
        original_total: formatCurrency(invoice.total),
        days_overdue: daysOverdue,
        late_fee: formatCurrency(lateFee),
        new_total: formatCurrency(invoice.total + lateFee)
      }
    });

    // Update invoice with late fee
    await updateInvoice(invoice.invoice_number, {
      late_fee_applied: lateFee,
      total: invoice.total + lateFee,
      balance_due: invoice.balance_due + lateFee
    });

    console.log(`⚠️ Late fee applied to ${invoice.invoice_number}: ${formatCurrency(lateFee)}`);
  }
}
```

**Common Pitfalls:**
- ❌ Applying fees without warning
- ❌ No grace period
- ❌ Compounding fees daily (too aggressive)
- ✅ Be reasonable, preserve client relationships

---

## Summary

These patterns cover:
- ✅ Hourly billing with time tracking
- ✅ Project milestone payments
- ✅ Monthly retainers with overages
- ✅ Expense reimbursement
- ✅ International/multi-currency billing
- ✅ SaaS subscription automation
- ✅ Approval workflows
- ✅ Payment tracking
- ✅ Late fee management

**Key Principles:**
1. **Automate repetitive tasks** (recurring invoices, payment matching)
2. **Document everything** (timesheets, expenses, milestones)
3. **Communicate clearly** (payment terms, late fees, discounts)
4. **Integrate with other systems** (time tracking, ERP, email)
5. **Track status** (draft → sent → paid → archived)
6. **Maintain audit trail** (who, what, when, why)

For more information:
- **SKILL.md** - Complete documentation
- **EXAMPLES.md** - Code examples
- **gotchas.md** - Common issues
- **impact-checklist.md** - Deployment checklist
