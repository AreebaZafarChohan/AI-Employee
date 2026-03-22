# MCP Odoo Server

MCP server for Odoo Community Accounting integration via JSON-RPC.

## Features

- List unpaid invoices
- List overdue payments
- Create customer invoices
- Register payments
- Get financial summaries
- Get partner balances

## Configuration

Set the following environment variables:

```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_api_key
ODOO_TIMEOUT=30000
```

## Installation

```bash
cd mcp/odoo-server
npm install
```

## Usage

```bash
# Start server
npm start

# Development mode
npm run dev
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_unpaid_invoices` | Get unpaid invoices with optional filters |
| `list_overdue_payments` | Get overdue payments by days |
| `create_invoice` | Create a new customer invoice |
| `register_payment` | Record payment for an invoice |
| `get_financial_summary` | Get P&L summary |
| `get_partner_balance` | Get customer/vendor balance |

## Example Tool Calls

### List Unpaid Invoices

```json
{
  "tool": "list_unpaid_invoices",
  "params": {
    "limit": 10
  }
}
```

### Create Invoice

```json
{
  "tool": "create_invoice",
  "params": {
    "partner_id": 12,
    "lines": [
      {
        "name": "Consulting Services",
        "quantity": 10,
        "price_unit": 100
      }
    ],
    "date_due": "2026-04-06"
  }
}
```

### Register Payment

```json
{
  "tool": "register_payment",
  "params": {
    "invoice_id": 45,
    "amount": 1000,
    "date": "2026-03-06"
  }
}
```

## Odoo Requirements

- Odoo Community Edition v16 or v17
- Accounting module installed
- API user with appropriate permissions

## Testing

```bash
npm test
```
