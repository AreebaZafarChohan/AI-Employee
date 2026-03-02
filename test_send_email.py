#!/usr/bin/env python3
"""Test sending a real email using the existing Gmail credentials."""

import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
except ImportError:
    print("Installing required packages...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "google-auth", "google-auth-oauthlib", 
                          "google-auth-httplib2", "google-api-python-client"])
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request

TOKEN_FILE = Path(__file__).parent / 'token_mcp.json'  # Use new token with full scopes
CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'

# Full scopes including send and compose
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

def create_message(to, subject, body):
    """Create a MIME message for Gmail API."""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = 'me'
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def main():
    print("=" * 60)
    print("Gmail Send Test")
    print("=" * 60)
    print()
    
    # Load credentials
    if not TOKEN_FILE.exists():
        print(f"ERROR: Token file not found: {TOKEN_FILE}")
        print("Please run gmail_watcher.py first to authorize.")
        return
    
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: Credentials file not found: {CREDENTIALS_FILE}")
        return
    
    # Load token
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    
    # Refresh if needed
    if not creds.valid or creds.expired:
        print("Refreshing token...")
        try:
            creds.refresh(Request())
            print("[OK] Token refreshed")
        except Exception as e:
            print(f"[FAIL] Token refresh failed: {e}")
            print("You may need to re-authorize with gmail.send scope")
            return
    
    # Build Gmail service
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("[OK] Gmail service created")
    except Exception as e:
        print(f"[FAIL] Failed to create Gmail service: {e}")
        return
    
    # Test: Get profile (verifies read access)
    try:
        profile = service.users().getProfile(userId='me').execute()
        print(f"[OK] Connected to: {profile['emailAddress']}")
    except Exception as e:
        print(f"[FAIL] Profile fetch failed: {e}")
        return
    
    # Test: Send email
    print()
    print("Testing email send capability...")
    print()
    
    # Ask user for test recipient
    test_email = input("Enter test email address (or press Enter for self-test): ").strip()
    if not test_email:
        test_email = profile['emailAddress']
        print(f"Will send to self: {test_email}")
    
    subject = "MCP Email Server Test"
    body = f"""Hello,

This is a test email from the MCP Email Server.

If you received this, the email sending functionality is working correctly.

Best regards,
AI Employee
"""
    
    try:
        message = create_message(test_email, subject, body)
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        print(f"[OK] Email sent successfully!")
        print(f"Message ID: {sent_message['id']}")
        print(f"Thread ID: {sent_message['threadId']}")
        print()
        print("Check your inbox (or spam folder) to verify receipt.")
        
    except Exception as e:
        error_msg = str(e)
        print(f"[FAIL] Email send failed: {e}")
        print()
        if 'insufficient scope' in error_msg.lower() or 'forbidden' in error_msg.lower():
            print("ERROR: Your token does not have gmail.send scope.")
            print()
            print("To fix this:")
            print("  1. Run: python setup_email_oauth.py")
            print("  2. Complete the OAuth flow in your browser")
            print("  3. Grant all requested permissions")
        else:
            print("Possible causes:")
            print("  - Gmail API send scope not authorized")
            print("  - Network error")
            print("  - Gmail API quota exceeded")

if __name__ == '__main__':
    main()
