#!/usr/bin/env python3
"""Re-authorize Gmail OAuth with full scopes for sending emails.

This script will:
1. Load existing credentials from credentials.json
2. Request authorization with ALL required scopes including:
   - gmail.readonly
   - gmail.modify
   - gmail.send (for sending emails)
   - gmail.compose (for creating drafts)
3. Save new token.json with refresh token
4. Extract and display the refresh token for .env

Usage:
    python setup_email_oauth.py
"""

import json
import os
import sys
import time
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "google-auth", "google-auth-oauthlib", 
                          "google-auth-httplib2", "google-api-python-client"])
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

# Gmail API scopes - FULL access for MCP server
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',    # Read inbox
    'https://www.googleapis.com/auth/gmail.modify',      # Modify labels
    'https://www.googleapis.com/auth/gmail.send',        # Send emails
    'https://www.googleapis.com/auth/gmail.compose',     # Create drafts
]

CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'
TOKEN_FILE = Path(__file__).parent / 'token_mcp.json'  # Separate token for MCP

def main():
    print("=" * 60)
    print("Gmail OAuth Setup for MCP Email Server")
    print("=" * 60)
    print()
    
    # Check credentials file
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: Credentials file not found: {CREDENTIALS_FILE}")
        print("Please download OAuth2 client secrets from Google Cloud Console")
        print("and save as credentials.json")
        sys.exit(1)
    
    print(f"[OK] Credentials file: {CREDENTIALS_FILE}")
    print()
    
    # Load existing token if available
    creds = None
    if TOKEN_FILE.exists():
        print(f"Found existing token: {TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and creds.valid:
                print("[OK] Existing token is valid")
            elif creds and creds.expired and creds.refresh_token:
                print("Token expired, will refresh...")
                try:
                    creds.refresh(Request())
                    print("[OK] Token refreshed successfully")
                except Exception as e:
                    print(f"Refresh failed: {e}")
                    creds = None
        except Exception as e:
            print(f"Error loading token: {e}")
            creds = None
    print()
    
    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        print("Starting OAuth authorization flow...")
        print()
        print("SCOPES requested:")
        for scope in SCOPES:
            print(f"  - {scope}")
        print()
        print("This will open a browser window.")
        print("Please sign in with your Google account and grant permissions.")
        print()
        # Skip interactive prompt for automated runs
        # input("Press Enter to continue...")
        print("Opening browser in 3 seconds...")
        time.sleep(3)
        print()
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            
            # Use local server flow for desktop
            creds = flow.run_local_server(port=0, open_browser=True)
            
            print("[OK] Authorization successful!")
            print()
            
        except Exception as e:
            print(f"ERROR: Authorization failed: {e}")
            print()
            print("Troubleshooting:")
            print("  1. Make sure Gmail API is enabled in Google Cloud Console")
            print("  2. Check that OAuth consent screen is configured")
            print("  3. Verify credentials.json is valid")
            sys.exit(1)
    
    # Save the credentials
    print(f"Saving token to: {TOKEN_FILE}")
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    print("[OK] Token saved!")
    print()
    
    # Extract refresh token
    refresh_token = creds.refresh_token
    if refresh_token:
        print("=" * 60)
        print("REFRESH TOKEN (copy this to .env):")
        print("=" * 60)
        print(refresh_token)
        print("=" * 60)
        print()
        
        # Update .env file automatically
        env_file = Path(__file__).parent / 'mcp' / 'email-server' / '.env'
        if env_file.exists():
            print(f"Updating {env_file}...")
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Replace refresh token
            import re
            old_token_match = re.search(r'GMAIL_REFRESH_TOKEN=.*', content)
            if old_token_match:
                content = content.replace(
                    old_token_match.group(0),
                    f'GMAIL_REFRESH_TOKEN={refresh_token}'
                )
                with open(env_file, 'w') as f:
                    f.write(content)
                print("[OK] .env file updated!")
            else:
                print("WARNING: Could not find GMAIL_REFRESH_TOKEN in .env")
        print()
        
        print("[OK] Setup complete!")
        print()
        print("Next steps:")
        print("  1. Restart Claude Desktop")
        print("  2. Test with: send a test email to test@example.com")
        
    else:
        print("WARNING: No refresh token obtained!")
        print("This means you won't be able to send emails without re-authorizing.")
        print()
        print("Possible causes:")
        print("  - You're using a G Suite account with restricted access")
        print("  - The OAuth app is not verified")
        print("  - You canceled during the authorization flow")

if __name__ == '__main__':
    main()
