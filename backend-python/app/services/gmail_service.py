import os
import base64
import json
import logging
import ssl
import certifi
from email.mime.text import MIMEText
from pathlib import Path

import httplib2
from googleapiclient.errors import BatchError

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from app.config import settings

# WSL2 often has broken system SSL certs — use certifi + allow fallback to unverified
def _make_http():
    """Create an httplib2.Http that works in WSL2 environments."""
    try:
        # First try with certifi bundle (most reliable in WSL)
        return httplib2.Http(ca_certs=certifi.where())
    except Exception:
        pass
    try:
        return httplib2.Http()
    except Exception:
        # Last resort: disable SSL verification (dev only)
        return httplib2.Http(disable_ssl_certificate_validation=True)

logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self):
        self.creds = self._get_credentials()
        try:
            if self.creds:
                self.service = build('gmail', 'v1', credentials=self.creds, http=_make_http())
                logger.info("Gmail service initialized successfully")
            else:
                self.service = None
                logger.warning("Gmail service NOT initialized (no valid credentials found)")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            self.service = None

    def _get_credentials(self):
        # 1. Try individual variables from .env first (User-provided are usually more reliable)
        if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET and settings.GMAIL_REFRESH_TOKEN:
            try:
                logger.info("Attempting to load Gmail credentials from .env variables...")
                creds_data = {
                    "token": None,
                    "refresh_token": settings.GMAIL_REFRESH_TOKEN,
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": settings.GMAIL_CLIENT_ID,
                    "client_secret": settings.GMAIL_CLIENT_SECRET,
                    "scopes": ["https://www.googleapis.com/auth/gmail.modify"]
                }
                creds = Credentials.from_authorized_user_info(creds_data)
                if not creds.valid:
                    if creds.expired and creds.refresh_token:
                        creds.refresh(self._make_auth_request())
                return creds
            except Exception as e:
                logger.error(f"Error loading from .env variables: {e}")

        # 2. Fallback to token.json
        token_path = Path(settings.GMAIL_TOKEN_FILE)
        if token_path.exists():
            try:
                logger.info(f"Attempting to load Gmail credentials from {token_path}...")
                creds = Credentials.from_authorized_user_file(str(token_path), ["https://www.googleapis.com/auth/gmail.modify"])
                if creds:
                    if not creds.valid:
                        if creds.expired and creds.refresh_token:
                            creds.refresh(self._make_auth_request())
                    return creds
            except Exception as e:
                logger.error(f"Error loading from token.json: {e}")
        
        return None

    def list_messages(self, query="", max_results=10):
        if not self.service:
            logger.error("list_messages: Gmail service not initialized. Check your credentials.")
            return []

        try:
            logger.info(f"Listing messages with query='{query}', max_results={max_results}")
            try:
                results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            except (ssl.SSLError, httplib2.ServerNotFoundError, ConnectionError, OSError) as ssl_err:
                logger.warning(f"Gmail SSL/network error (returning empty): {ssl_err}")
                return []
            messages_stubs = results.get('messages', [])
            logger.info(f"Found {len(messages_stubs)} message stubs")

            if not messages_stubs:
                return []

            detailed_messages = []
            
            # Process messages in smaller batches to avoid timeout
            batch_size = 5
            for i in range(0, len(messages_stubs), batch_size):
                batch_stubs = messages_stubs[i:i+batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_stubs)} messages")
                
                def callback(request_id, response, exception):
                    if exception is not None:
                        logger.error(f"Batch request error for {request_id}: {exception}")
                    else:
                        msg = response
                        headers = msg.get('payload', {}).get('headers', [])
                        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                        snippet = msg.get('snippet', '')

                        detailed_messages.append({
                            "id": msg.get('id'),
                            "threadId": msg.get('threadId'),
                            "subject": subject,
                            "from": sender,
                            "date": date,
                            "snippet": snippet,
                            "labels": msg.get('labelIds', []),
                            "hasAttachment": 'parts' in msg.get('payload', {})
                        })

                batch = self.service.new_batch_http_request(callback=callback)
                for m in batch_stubs:
                    batch.add(self.service.users().messages().get(userId='me', id=m['id']))

                try:
                    batch.execute()
                except (ssl.SSLError, httplib2.ServerNotFoundError, ConnectionError, OSError, BatchError) as ssl_err:
                    logger.warning(f"Gmail batch SSL/network error (skipping batch): {ssl_err}")
                    break
                logger.info(f"Batch {i//batch_size + 1} complete. Total detailed messages: {len(detailed_messages)}")

            return detailed_messages
        except (ssl.SSLError, httplib2.ServerNotFoundError, ConnectionError, OSError, BatchError) as ssl_err:
            logger.warning(f"Gmail SSL/network error (returning empty): {ssl_err}")
            return []
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def get_message(self, message_id):
        if not self.service: return None
        try:
            msg = self.service.users().messages().get(userId='me', id=message_id).execute()

            # Auto mark as read when fetching details
            if 'UNREAD' in msg.get('labelIds', []):
                self.service.users().messages().batchModify(
                    userId='me',
                    body={'ids': [message_id], 'removeLabelIds': ['UNREAD']}
                ).execute()
                logger.info(f"Message {message_id} marked as read")

            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            snippet = msg.get('snippet', '')
            return {
                "id": message_id,
                "threadId": msg.get('threadId'),
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": snippet,
                "labels": msg.get('labelIds', []),
                "hasAttachment": 'parts' in msg.get('payload', {})
            }
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            return None

    def send_message(self, to, subject, body, thread_id=None):
        if not self.service: raise Exception("Gmail service not initialized")
        try:
            message = MIMEText(body)
            message['to'] = to
            message['from'] = settings.GMAIL_USER
            message['subject'] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            msg_body = {'raw': raw}
            if thread_id: msg_body['threadId'] = thread_id
            return self.service.users().messages().send(userId='me', body=msg_body).execute()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise e

    def create_draft_for_approval(self, to, subject, body, thread_id=None, source_msg_id=None):
        vault_path = Path(settings.VAULT_PATH)
        needs_action_dir = vault_path / "Needs_Action"
        needs_action_dir.mkdir(parents=True, exist_ok=True)
        filename = f"email-draft-{os.urandom(4).hex()}.md"
        file_path = needs_action_dir / filename
        content = f"---\ntype: email\nstatus: pending_approval\nto: {to}\nsubject: {subject}\nthread_id: {thread_id or ''}\nsource_msg_id: {source_msg_id or ''}\ncreated_at: {self._now_iso()}\nrisk_level: low\n---\n\n{body}\n"
        file_path.write_text(content, encoding="utf-8")
        return filename

    def _make_auth_request(self):
        """Create a google-auth Request that works in WSL2 (uses certifi certs)."""
        import requests as req_lib
        session = req_lib.Session()
        session.verify = certifi.where()
        return Request(session=session)

    def _now_iso(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

gmail_service = GmailService()
