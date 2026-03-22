#!/usr/bin/env python3
"""Test Gmail API counts directly"""
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from pathlib import Path

TOKEN_FILE = Path("/mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee/token.json")

def get_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), ["https://www.googleapis.com/auth/gmail.modify"])
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('gmail', 'v1', credentials=creds)

service = get_service()

# Test different queries
queries = [
    ("", "All"),
    ("is:unread", "Unread"),
    ("is:important", "Important"),
    ("label:INBOX", "Inbox only")
]

for query, label in queries:
    result = service.users().messages().list(userId='me', q=query, maxResults=500).execute()
    messages = result.get("messages", [])
    result_size = result.get("resultSizeEstimate", 0)
    print(f"{label:15} | Messages: {len(messages):3} | resultSizeEstimate: {result_size}")

# Get profile
profile = service.users().getProfile(userId='me').execute()
print(f"\nProfile: {profile.get('emailAddress')}")
print(f"Total in profile: {profile.get('messagesTotal', 0)}")
