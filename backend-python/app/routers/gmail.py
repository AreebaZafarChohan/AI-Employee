from fastapi import APIRouter, Body, Query, HTTPException
from app.services.gmail_service import gmail_service
from app.services import vault_service
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import logging
from pathlib import Path
import os
import re

router = APIRouter(prefix="/gmail", tags=["gmail"])
logger = logging.getLogger(__name__)

class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str
    thread_id: Optional[str] = None

class EmailDraftRequest(BaseModel):
    to: str
    subject: str
    body: str
    thread_id: Optional[str] = None
    source_msg_id: Optional[str] = None

@router.get("/inbox")
def get_inbox(
    filter_type: str = Query("all"),
    limit: int = Query(50, ge=1, le=100)
):
    """Fetch messages with filtering for all, unread, or important."""
    try:
        query = ""
        if filter_type == "unread":
            query = "is:unread"
        elif filter_type == "important":
            query = "is:important"

        logger.info(f"Fetching Gmail inbox with query: '{query}' (filter_type={filter_type})")
        messages = gmail_service.list_messages(query=query, max_results=limit)
        logger.info(f"Found {len(messages)} messages for filter_type={filter_type}")
        return {"data": messages, "count": len(messages), "filter_type": filter_type}
    except Exception as e:
        logger.error(f"Error fetching Gmail inbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/message/{message_id}")
def get_message(message_id: str):
    try:
        logger.info(f"Fetching Gmail message details: {message_id}")
        message = gmail_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"data": message}
    except Exception as e:
        logger.error(f"Error fetching Gmail message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
def send_email(req: EmailSendRequest):
    try:
        logger.info(f"Sending direct email to: {req.to}")
        result = gmail_service.send_message(
            to=req.to,
            subject=req.subject,
            body=req.body,
            thread_id=req.thread_id
        )
        return {"data": {"success": True, "result": result}}
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/draft")
def create_draft(req: EmailDraftRequest):
    """Create a draft in Needs_Action for AI-generated emails requiring approval."""
    try:
        logger.info(f"Creating AI email draft for: {req.to}")
        filename = gmail_service.create_draft_for_approval(
            to=req.to,
            subject=req.subject,
            body=req.body,
            thread_id=req.thread_id,
            source_msg_id=req.source_msg_id
        )
        return {"data": {"success": True, "filename": filename}}
    except Exception as e:
        logger.error(f"Error creating email draft: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve")
def approve_email(req: dict = Body(...)):
    """Approve and send a drafted email from the vault."""
    filename = req.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # 1. Read the draft from Needs_Action
    from app.utils.markdown import parse_markdown
    from app.config import settings
    
    vault_path = Path(settings.VAULT_PATH)
    file_path = vault_path / "Needs_Action" / filename
    
    if not file_path.exists():
        # Try Pending_Approval if not in Needs_Action
        file_path = vault_path / "Pending_Approval" / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Draft file {filename} not found")
            
    content = file_path.read_text(encoding="utf-8")
    metadata, body = parse_markdown(content)
    
    # Allow overriding body from request (user edits)
    final_body = req.get("reply_content", body)
    
    # 2. Send via Gmail API
    try:
        logger.info(f"Approving and sending drafted email: {filename}")
        result = gmail_service.send_message(
            to=metadata.get("to"),
            subject=metadata.get("subject"),
            body=final_body,
            thread_id=metadata.get("thread_id")
        )
        
        # 3. Move file to Done folder as requested
        vault_service.move_file(filename, ["Needs_Action", "Pending_Approval"], "Done")
        
        return {"data": {"success": True, "result": result}}
    except Exception as e:
        logger.error(f"Error sending approved email {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.ai_service import ai_agent

class AIComposeRequest(BaseModel):
    to: str
    topic: str

class AIReplyRequest(BaseModel):
    message_id: str
    instructions: str

@router.get("/counts")
def get_counts():
    """Fetch only message counts for badges (accurate counts using service)."""
    import ssl
    import httplib2
    try:
        logger.info("Fetching Gmail badge counts")

        if not gmail_service.service:
            logger.warning("Gmail service not initialized for counts")
            return {"counts": {"all": 0, "unread": 0, "important": 0}, "service_connected": False}

        counts = {"all": 0, "unread": 0, "important": 0}
        try:
            all_result = gmail_service.service.users().messages().list(userId='me', q="", maxResults=500).execute()
            counts["all"] = len(all_result.get("messages", []))
        except (ssl.SSLError, httplib2.ServerNotFoundError, ConnectionError, OSError) as e:
            logger.warning(f"Gmail SSL/network error fetching all count: {e}")
        try:
            unread_result = gmail_service.service.users().messages().list(userId='me', q="is:unread", maxResults=500).execute()
            counts["unread"] = len(unread_result.get("messages", []))
        except (ssl.SSLError, httplib2.ServerNotFoundError, ConnectionError, OSError) as e:
            logger.warning(f"Gmail SSL/network error fetching unread count: {e}")
        try:
            important_result = gmail_service.service.users().messages().list(userId='me', q="is:important", maxResults=500).execute()
            counts["important"] = len(important_result.get("messages", []))
        except (ssl.SSLError, httplib2.ServerNotFoundError, ConnectionError, OSError) as e:
            logger.warning(f"Gmail SSL/network error fetching important count: {e}")

        logger.info(f"Badge counts fetched: {counts}")
        return {"counts": counts, "service_connected": True}
    except (ssl.SSLError, httplib2.ServerNotFoundError, ConnectionError, OSError) as e:
        logger.warning(f"Gmail SSL/network error in counts: {e}")
        return {"counts": {"all": 0, "unread": 0, "important": 0}, "service_connected": False}
    except Exception as e:
        logger.error(f"Error fetching Gmail counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
def get_profile():
    """Get the Gmail account profile information."""
    try:
        if not gmail_service.service:
            raise HTTPException(status_code=503, detail="Gmail service not connected")
        
        logger.info("Fetching Gmail profile")
        profile = gmail_service.service.users().getProfile(userId='me').execute()
        
        return {
            "email": profile.get("emailAddress"),
            "name": profile.get("displayName"),
            "total_emails": profile.get("messagesTotal", 0),
            "threads_total": profile.get("threadsTotal", 0),
            "history_id": profile.get("historyId")
        }
    except Exception as e:
        logger.error(f"Error fetching Gmail profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drafts")
def list_drafts():
    """Lists all pending email drafts from the vault."""
    from app.config import settings
    from app.utils.markdown import parse_markdown

    vault_path = Path(settings.VAULT_PATH)
    needs_action = vault_path / "Needs_Action"

    drafts = []
    if needs_action.exists():
        for f in needs_action.glob("email-draft-*.md"):
            content = f.read_text(encoding="utf-8")
            metadata, body = parse_markdown(content)
            drafts.append({
                "filename": f.name,
                "to": metadata.get("to"),
                "subject": metadata.get("subject"),
                "body": body,
                "created_at": metadata.get("created_at")
            })
    return {"data": drafts}

@router.post("/ai/generate-compose")
async def ai_generate_compose(req: AIComposeRequest):
    """Generates a new email draft via AI."""
    try:
        body = await ai_agent.draft_new_email(req.topic, req.to)
        # Create draft in vault
        filename = gmail_service.create_draft_for_approval(
            to=req.to,
            subject=f"New Message: {req.topic[:20]}...",
            body=body
        )
        return {"data": {"success": True, "filename": filename, "body": body}}
    except Exception as e:
        logger.error(f"AI Compose error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/generate-reply")
async def ai_generate_reply(req: AIReplyRequest):
    """Generates a reply draft via AI for an existing message."""
    try:
        # 1. Fetch original message
        original = gmail_service.get_message(req.message_id)
        if not original:
            raise HTTPException(status_code=404, detail="Original message not found")
        
        # 2. Generate AI reply
        body = await ai_agent.draft_email_reply(
            original_email=original.get('snippet', ''),
            sender=original.get('from', 'Unknown'),
            instructions=req.instructions
        )
        
        # 3. Create draft in vault
        from_header = original.get('from', '')
        email_match = re.search(r'<(.*?)>', from_header)
        recipient = email_match.group(1) if email_match else from_header

        filename = gmail_service.create_draft_for_approval(
            to=recipient,
            subject=f"Re: {original.get('subject')}",
            body=body,
            thread_id=original.get('threadId'),
            source_msg_id=original.get('id')
        )
        return {"data": {"success": True, "filename": filename, "body": body}}
    except Exception as e:
        logger.error(f"AI Reply error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

