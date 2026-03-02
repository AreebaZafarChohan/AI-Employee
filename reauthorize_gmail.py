#!/usr/bin/env python3
"""Re-authorize Gmail with full send/compose scopes.

This script opens a browser window for OAuth authorization.
After authorization, it saves the new token and updates the MCP server .env file.
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Full scopes for MCP email server
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
]

CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'
TOKEN_FILE = Path(__file__).parent / 'token_mcp.json'
ENV_FILE = Path(__file__).parent / 'mcp' / 'email-server' / '.env'

def main():
    print("=" * 70)
    print("Gmail OAuth Re-authorization")
    print("=" * 70)
    print()
    print("This will authorize the following scopes:")
    for scope in SCOPES:
        print(f"  - {scope}")
    print()
    print("A browser window will open in 3 seconds...")
    print("Please sign in and grant permissions.")
    print()
    import time
    time.sleep(3)
    print("Opening browser...")
    print()
    
    # Start OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE, SCOPES)
    
    try:
        creds = flow.run_local_server(port=0, open_browser=True)
    except Exception as e:
        print(f"Authorization failed: {e}")
        print()
        print("Common issues:")
        print("  1. Gmail API not enabled in Google Cloud Console")
        print("  2. OAuth consent screen not configured")
        print("  3. Browser blocked the popup - try allowing popups")
        sys.exit(1)
    
    print("[OK] Authorization successful!")
    print()
    
    # Save token
    print(f"Saving token to: {TOKEN_FILE}")
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    print("[OK] Token saved!")
    print()
    
    # Get refresh token
    refresh_token = creds.refresh_token
    if not refresh_token:
        print("[WARNING] No refresh token obtained!")
        print("This may happen with certain Google account types.")
        sys.exit(0)
    
    print("=" * 70)
    print("REFRESH TOKEN:")
    print("=" * 70)
    print(refresh_token)
    print("=" * 70)
    print()
    
    # Update .env file
    if ENV_FILE.exists():
        print(f"Updating {ENV_FILE}...")
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()
        
        with open(ENV_FILE, 'w') as f:
            for line in lines:
                if line.startswith('GMAIL_REFRESH_TOKEN='):
                    f.write(f'GMAIL_REFRESH_TOKEN={refresh_token}\n')
                else:
                    f.write(line)
        print("[OK] .env file updated!")
        print()
    
    print("=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Restart Claude Desktop")
    print("  2. Test sending an email through Claude")
    print()
    print("Example: 'Send an email to test@example.com with subject Hello'")
    print()

if __name__ == '__main__':
    main()
