#!/usr/bin/env python3
"""
Test Odoo Connection with Real API
"""

import os
import httpx
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
url = os.getenv('ODOO_URL', 'https://areebazafar-ai-employee2.odoo.com')
db = os.getenv('ODOO_DB', 'areebazafar-ai-employee2')
username = os.getenv('ODOO_USERNAME', 'Areeba_Zafar')
password = os.getenv('ODOO_PASSWORD', '6a9c11753f81793c707fdeca8f9047ddecbb3709')

print('=== Odoo Connection Test ===')
print(f'URL: {url}')
print(f'DB: {db}')
print(f'Username: {username}')
print()

# Test authentication
payload = {
    'jsonrpc': '2.0',
    'method': 'call',
    'params': {
        'service': 'common',
        'method': 'authenticate',
        'args': [db, username, password, {}]
    }
}

try:
    response = httpx.post(f'{url}/jsonrpc', json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    if 'error' in result:
        print(f'❌ Authentication FAILED: {result["error"].get("message", "Unknown error")}')
        exit(1)
    else:
        uid = result.get('result')
        print(f'✅ Authentication SUCCESS!')
        print(f'User ID: {uid}')
        
        # Test getting unpaid invoices
        print()
        print('=== Testing: Get Unpaid Invoices ===')
        
        execute_payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'object',
                'method': 'execute_kw',
                'args': [db, uid, password, 'account.move', 'search_read', [[
                    ('move_type', 'in', ['out_invoice', 'in_invoice']),
                    ('payment_state', '=', 'not_paid'),
                    ('parent_state', '=', 'posted')
                ]], {'fields': ['id', 'name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date_due'], 'limit': 5}]
            }
        }
        
        result = httpx.post(f'{url}/jsonrpc', json=execute_payload, timeout=30).json()
        
        if 'error' in result:
            print(f'Query Error: {result["error"].get("message", "Unknown")}')
        else:
            invoices = result.get('result', [])
            print(f'Found {len(invoices)} unpaid invoices')
            for inv in invoices[:3]:
                partner_name = inv.get('partner_id', [None, 'Unknown'])[1]
                print(f'  - {inv.get("name")}: ${inv.get("amount_residual", 0):.2f} (Due: {inv.get("invoice_date_due")}) - {partner_name}')
        
        # Test getting partners
        print()
        print('=== Testing: Get Partners ===')
        
        partners_payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'object',
                'method': 'execute_kw',
                'args': [db, uid, password, 'res.partner', 'search_read', [[]], {'fields': ['id', 'name', 'email'], 'limit': 3}]
            }
        }
        
        result = httpx.post(f'{url}/jsonrpc', json=partners_payload, timeout=30).json()
        
        if 'error' in result:
            print(f'Query Error: {result["error"].get("message", "Unknown")}')
        else:
            partners = result.get('result', [])
            print(f'Found {len(partners)} partners')
            for p in partners:
                print(f'  - {p.get("name")} ({p.get("email", "No email")})')
        
        print()
        print('=== All Odoo Tests PASSED! ===')
                
except Exception as e:
    print(f'❌ Connection FAILED: {e}')
    exit(1)
